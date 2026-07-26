import logging
import asyncio
import json
from typing import List, Dict, Any
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.db.pgvector_client import SupabaseVectorClient
from app.core.embeddings import OpenRouterEmbeddingClient

logger = logging.getLogger(__name__)

class ScopedHybridRetrieverManager:
    """
    Enterprise hybrid retriever that combines PostgreSQL vector similarity search (dense)
    and in-memory BM25 search (sparse) using Reciprocal Rank Fusion (RRF) in Python.
    Enforces strict multi-tenant scope and role security boundaries.
    """
    def __init__(self, db_client: SupabaseVectorClient, embedding_client: OpenRouterEmbeddingClient):
        self.db_client = db_client
        self.embedding_client = embedding_client

    async def retrieve(self, query: str, scope: str, role: str, top_n: int = 5, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Retrieves top_n RRF-fused documents matching the query, restricted to the user's scope and role.
        """
        # Ensure database client is connected
        if not self.db_client.pool:
            await self.db_client.connect()

        # Normalize scope identifier (e.g. 'customer_support' -> 'support')
        db_scope = "support" if scope.lower() in ["support", "customer_support"] else scope.lower()

        # Define JSONB containment filter
        filter_data = {
            "scope": db_scope
        }
        filter_str = json.dumps(filter_data)

        # 1. Fetch all matching documents for the local BM25 corpus
        logger.info(f"Fetching scoped document chunks for scope={scope}, role={role}...")
        corpus_query = """
            SELECT id::text, parent_id, content, metadata
            FROM child_documents
            WHERE metadata @> $1::jsonb;
        """
        
        corpus_records = await self.db_client.fetch(corpus_query, filter_str)
        
        if not corpus_records:
            logger.warning(f"No documents found for scope={scope}, role={role}. Returning empty list.")
            return []

        logger.info(f"Loaded {len(corpus_records)} chunks for BM25 corpus.")

        # 2. Run Local Sparse Search (BM25)
        # Convert records to LangChain Documents
        lc_docs = [
            Document(
                page_content=r["content"],
                metadata={
                    "id": r["id"],
                    "parent_id": r["parent_id"],
                    "metadata": json.loads(r["metadata"])
                }
            )
            for r in corpus_records
        ]
        
        # Initialize BM25 retriever
        bm25_retriever = BM25Retriever.from_documents(lc_docs)
        # Fetch top candidate matches from BM25 (fetch up to 15 to allow RRF fusion)
        bm25_retriever.k = min(15, len(lc_docs))
        bm25_results = bm25_retriever.invoke(query)

        # 3. Run Dense Vector Similarity Search in pgvector (with High-Availability Fallback)
        vector_records = []
        try:
            logger.info("Generating query embedding...")
            query_vector = await asyncio.wait_for(
                self.embedding_client.embed_query_async(query),
                timeout=1.2
            )

            vector_query = """
                SELECT id::text, parent_id, content, metadata
                FROM child_documents
                WHERE metadata @> $1::jsonb
                ORDER BY embedding <=> $2::vector
                LIMIT 15;
            """
            vector_records = await self.db_client.fetch(vector_query, filter_str, str(query_vector))
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Dense vector embedding API delayed/failed ({e}). Falling back to Naive BM25 Keyword Search.")

        # 4. Perform Reciprocal Rank Fusion (RRF)
        # We assign ranks and compute fusion score: 1.0 / (k + rank)
        rrf_scores = {}
        doc_details = {}

        # Process vector matches
        for rank, r in enumerate(vector_records, 1):
            doc_id = r["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            doc_details[doc_id] = {
                "id": doc_id,
                "parent_id": r["parent_id"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"])
            }

        # Process BM25 matches
        for rank, doc in enumerate(bm25_results, 1):
            doc_id = doc.metadata["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            if doc_id not in doc_details:
                doc_details[doc_id] = {
                    "id": doc_id,
                    "parent_id": doc.metadata["parent_id"],
                    "content": doc.page_content,
                    "metadata": doc.metadata["metadata"]
                }

        # Sort documents by RRF score descending
        sorted_docs = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Take top_n results
        final_results = []
        for doc_id in sorted_docs[:top_n]:
            doc_info = doc_details[doc_id]
            doc_info["rrf_score"] = rrf_scores[doc_id]
            final_results.append(doc_info)

        logger.info(f"Hybrid retrieval complete. Retrieved {len(final_results)} RRF-fused documents.")
        return final_results
