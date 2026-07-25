import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import asyncpg
from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseVectorClient:
    """
    Enterprise database client for Supabase pgvector supporting HNSW, GIN,
    and Reciprocal Rank Fusion (RRF) hybrid search.
    """
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """
        Establishes an async connection pool to the Supabase Postgres instance.
        """
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set in AppSettings or passed directly to SupabaseVectorClient.")
        
        async def init_connection(conn):
            # Pre-register/warm the pgvector OID on startup to prevent PgBouncer OID lookups deadlocks during runtime queries
            try:
                await conn.execute("SELECT '[0.0]'::vector;")
                logger.info("Successfully pre-warmed pgvector OID on pool connection.")
            except Exception as e:
                logger.warning(f"Could not pre-warm pgvector OID on connection: {e}")

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=3,
                init=init_connection,
                command_timeout=15.0
            )
            logger.info("Successfully established connection pool to Supabase.")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise e

    async def close(self):
        """
        Closes the database connection pool.
        """
        if self.pool:
            await self.pool.close()
            logger.info("Supabase connection pool closed.")

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Safely acquires a connection from the pool, executes the fetch query
        under a strict timeout, and releases the connection.
        """
        logger.info(f"DB Query start: {query[:100].strip()}... (Args: {len(args)})")
        if not self.pool:
            await self.connect()
            
        try:
            async with self.pool.acquire(timeout=3.0) as conn:
                res = await conn.fetch(query, *args, timeout=5.0)
                logger.info(f"DB Query complete. Returned {len(res)} rows.")
                return res
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []

    async def init_database(self):
        """
        Initializes pgvector extensions, schemas, tables, indexes, and RRF search functions.
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                logger.info("Initializing Supabase database schema and extensions...")
                
                # 1. Enable pgvector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # 2. Parent documents table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS parent_documents (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
                # 3. Child chunks table (with 1536-dimensional vector for Qwen3 embedding)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS child_documents (
                        id UUID PRIMARY KEY,
                        parent_id TEXT REFERENCES parent_documents(id) ON DELETE CASCADE,
                        content TEXT NOT NULL,
                        fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
                        embedding vector(1536),
                        metadata JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
                # 4. Indexes
                logger.info("Creating high-performance indexes...")
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_child_documents_embedding 
                    ON child_documents USING hnsw (embedding vector_cosine_ops) 
                    WITH (m = 16, ef_construction = 64);
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_child_documents_fts 
                    ON child_documents USING gin (fts);
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_child_documents_metadata 
                    ON child_documents USING gin (metadata);
                """)
                
                # 5. Reciprocal Rank Fusion (RRF) Hybrid Search Function
                logger.info("Creating RRF hybrid search function...")
                await conn.execute("""
                    CREATE OR REPLACE FUNCTION match_hybrid_documents_rrf(
                        query_text TEXT,
                        query_embedding vector(1536),
                        match_count INT DEFAULT 10,
                        rrf_k INT DEFAULT 60,
                        filter JSONB DEFAULT '{}'::jsonb
                    )
                    RETURNS TABLE (
                        parent_id TEXT,
                        child_id UUID,
                        content TEXT,
                        metadata JSONB,
                        rrf_score FLOAT
                    )
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        RETURN QUERY
                        WITH vector_matches AS (
                            SELECT 
                                id,
                                parent_id,
                                content,
                                metadata,
                                ROW_NUMBER() OVER (ORDER BY embedding <=> query_embedding ASC) AS rank
                            FROM child_documents
                            WHERE metadata @> filter
                            ORDER BY embedding <=> query_embedding ASC
                            LIMIT match_count * 2
                        ),
                        fts_matches AS (
                            SELECT 
                                id,
                                parent_id,
                                content,
                                metadata,
                                ROW_NUMBER() OVER (ORDER BY ts_rank_cd(fts, plainto_tsquery('english', query_text)) DESC) AS rank
                            FROM child_documents
                            WHERE fts @@ plainto_tsquery('english', query_text)
                              AND metadata @> filter
                            ORDER BY rank ASC
                            LIMIT match_count * 2
                        )
                        SELECT
                            COALESCE(v.parent_id, f.parent_id) AS parent_id,
                            COALESCE(v.id, f.id) AS child_id,
                            COALESCE(v.content, f.content) AS content,
                            COALESCE(v.metadata, f.metadata) AS metadata,
                            (
                                COALESCE(1.0 / (rrf_k + v.rank), 0.0) +
                                COALESCE(1.0 / (rrf_k + f.rank), 0.0)
                            )::FLOAT AS rrf_score
                        FROM vector_matches v
                        FULL OUTER JOIN fts_matches f ON v.id = f.id
                        ORDER BY rrf_score DESC
                        LIMIT match_count;
                    END;
                    $$;
                """)
                logger.info("Database schema and search function initialized successfully.")

    async def insert_parent_documents(self, documents: List[Dict[str, Any]]):
        """
        Batch inserts parent documents into pgvector.
        """
        if not self.pool:
            await self.connect()

        query = """
            INSERT INTO parent_documents (id, content, metadata) 
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE 
            SET content = EXCLUDED.content, metadata = EXCLUDED.metadata;
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Prepare record tuples
                records = [(d["id"], d["content"], json.dumps(d.get("metadata", {}))) for d in documents]
                await conn.executemany(query, records)
                logger.info(f"Upserted {len(documents)} parent documents.")

    async def insert_child_documents(self, chunks: List[Dict[str, Any]]):
        """
        Batch inserts child documents into pgvector.
        """
        if not self.pool:
            await self.connect()

        query = """
            INSERT INTO child_documents (id, parent_id, content, embedding, metadata)
            VALUES ($1, $2, $3, $4, $5);
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Prepare record tuples
                # Convert the float list embedding to pgvector string format '[val1, val2, ...]'
                records = [
                    (
                        c["id"], 
                        c["parent_id"], 
                        c["content"], 
                        str(c["embedding"]), 
                        json.dumps(c.get("metadata", {}))
                    ) 
                    for c in chunks
                ]
                await conn.executemany(query, records)
                logger.info(f"Inserted {len(chunks)} child chunks.")

    async def match_hybrid_documents_rrf(
        self, 
        query_text: str, 
        query_embedding: List[float], 
        match_count: int = 10, 
        rrf_k: int = 60, 
        filter_json: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries the database using Reciprocal Rank Fusion (RRF) and metadata containment filters.
        """
        if not self.pool:
            await self.connect()

        filter_str = json.dumps(filter_json or {})
        query = """
            SELECT parent_id, child_id, content, metadata, rrf_score
            FROM match_hybrid_documents_rrf($1, $2, $3, $4, $5::jsonb);
        """
        
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, query_text, query_embedding, match_count, rrf_k, filter_str)
            return [dict(r) for r in records]
