import os
import sys
import uuid
import argparse
import asyncio
import logging
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add the project root to sys.path to allow absolute imports of 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Absolute import paths relative to app folder
from app.core.config import settings
from app.core.embeddings import OpenRouterEmbeddingClient
from app.db.pgvector_client import SupabaseVectorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest_documents")

# Scope and Role mapping for multi-tenant security
DEPT_ROLES_MAP = {
    "hr": ["employee", "hr_admin"],
    "it": ["employee", "it_admin"],
    "support": ["guest", "employee", "support_agent"],
    "sales": ["lead", "sales_rep"]
}

class PDFParser:
    """
    Parser to extract text page-by-page from local PDF documents.
    """
    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a PDF file and returns a list of pages with text.
        """
        pages = []
        try:
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": idx + 1,
                    "text": text.strip()
                })
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {e}")
            raise e
        return pages

class DocumentChunker:
    """
    Splits text content into child chunks for vector index search.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits a single text block into a list of smaller text chunks.
        """
        return self.splitter.split_text(text)

class IngestionPipeline:
    """
    Orchestrator class for scanning documents, chunking, embedding,
    and upserting into Supabase pgvector.
    """
    def __init__(self, documents_dir: str):
        self.documents_dir = os.path.abspath(documents_dir)
        self.db_client = SupabaseVectorClient()
        self.embedding_client = OpenRouterEmbeddingClient()
        self.pdf_parser = PDFParser()
        # ~100 words per chunk for high vector retrieval precision
        self.chunker = DocumentChunker(chunk_size=600, chunk_overlap=100)

    async def initialize_db(self):
        """
        Initializes vector database schema and RRF functions.
        """
        await self.db_client.init_database()

    async def ingest(self):
        """
        Main ingestion execution cycle.
        """
        # Ensure database is connected and initialized
        await self.initialize_db()
        
        if not os.path.exists(self.documents_dir):
            logger.error(f"Documents directory does not exist: {self.documents_dir}")
            return

        logger.info(f"Scanning for PDFs in: {self.documents_dir}")
        departments = [d for d in os.listdir(self.documents_dir) if os.path.isdir(os.path.join(self.documents_dir, d))]
        
        total_pdfs = 0
        total_parents = 0
        total_children = 0

        # Loop through department folders (scopes)
        for dept in departments:
            if dept not in DEPT_ROLES_MAP:
                logger.warning(f"Skipping unknown department folder: {dept}")
                continue

            dept_path = os.path.join(self.documents_dir, dept)
            pdf_files = [f for f in os.listdir(dept_path) if f.endswith(".pdf")]
            logger.info(f"Department '{dept}' -> Found {len(pdf_files)} PDFs.")

            allowed_roles = DEPT_ROLES_MAP[dept]

            for pdf_file in pdf_files:
                file_path = os.path.join(dept_path, pdf_file)
                doc_id = f"pdf_{dept}_{pdf_file.replace('.pdf', '')}"
                
                # Check if document already exists to avoid duplicates when resuming
                already_ingested = await self.db_client.pool.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM child_documents WHERE metadata->>'doc_id' = $1);",
                    doc_id
                )
                if already_ingested:
                    logger.info(f"Document {pdf_file} is already fully ingested. Skipping.")
                    continue
                
                logger.info(f"Processing document: {pdf_file} (doc_id={doc_id})")
                
                # Parse PDF page by page
                pages = self.pdf_parser.parse_pdf(file_path)
                
                parent_docs = []
                child_chunks = []
                child_texts_to_embed = []
                
                # Each page becomes a parent document record
                for page in pages:
                    page_num = page["page_number"]
                    page_text = page["text"]
                    
                    if not page_text:
                        logger.warning(f"Empty page {page_num} in {pdf_file}. Skipping.")
                        continue
                        
                    parent_id = f"{doc_id}_page_{page_num}"
                    
                    # Create parent document payload
                    parent_metadata = {
                        "doc_id": doc_id,
                        "scope": dept,
                        "allowed_roles": allowed_roles,
                        "source_file": pdf_file,
                        "page_number": page_num,
                        "created_at": "2026-07-24"
                    }
                    parent_docs.append({
                        "id": parent_id,
                        "content": page_text,
                        "metadata": parent_metadata
                    })
                    
                    # Split page text into smaller child chunks
                    chunks = self.chunker.chunk_text(page_text)
                    
                    for chunk_idx, chunk_text in enumerate(chunks):
                        child_id = str(uuid.uuid4())
                        child_metadata = parent_metadata.copy()
                        child_metadata["parent_id"] = parent_id
                        child_metadata["chunk_index"] = chunk_idx
                        
                        child_chunks.append({
                            "id": child_id,
                            "parent_id": parent_id,
                            "content": chunk_text,
                            "metadata": child_metadata
                        })
                        child_texts_to_embed.append(chunk_text)

                if parent_docs:
                    # 1. Insert Parent Documents
                    await self.db_client.insert_parent_documents(parent_docs)
                    total_parents += len(parent_docs)
                    
                    # 2. Generate Embeddings for Child Chunks in batch via OpenRouter
                    logger.info(f"Generating embeddings for {len(child_texts_to_embed)} child chunks...")
                    try:
                        embeddings = await self.embedding_client.embed_documents_async(child_texts_to_embed)
                        
                        # Map embeddings back to child chunks
                        for idx, embedding in enumerate(embeddings):
                            child_chunks[idx]["embedding"] = embedding
                            
                        # 3. Insert Child Chunks
                        await self.db_client.insert_child_documents(child_chunks)
                        total_children += len(child_chunks)
                        total_pdfs += 1
                        logger.info(f"Successfully ingested {pdf_file}: {len(parent_docs)} pages, {len(child_chunks)} chunks.")
                    except Exception as e:
                        logger.error(f"Failed to complete ingestion for {pdf_file}: {e}")
                        # Continue with other files if error is file-specific
                        continue

        logger.info("Ingestion completed successfully.")
        logger.info(f"Summary: processed {total_pdfs} PDFs, inserted {total_parents} parent pages, inserted {total_children} child chunks.")
        
        # Cleanup
        await self.db_client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-tenant RAG Document Ingestion Pipeline")
    parser.add_argument("--docs-dir", default="./documents", help="Directory containing PDF folders (defaults to './documents')")
    parser.add_argument("--init-db", action="store_true", help="Only initialize pgvector schema, indexes, and exit")
    args = parser.parse_args()

    # If docs-dir is default, look in backend directory or script parent directory
    docs_path = args.docs_dir
    if docs_path == "./documents":
        # Resolve path relative to scripts folder
        docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents"))

    pipeline = IngestionPipeline(documents_dir=docs_path)

    if args.init_db:
        logger.info("Database initialization option selected.")
        asyncio.run(pipeline.initialize_db())
        logger.info("Database schema creation complete.")
    else:
        logger.info("Starting ingestion workflow...")
        asyncio.run(pipeline.ingest())
