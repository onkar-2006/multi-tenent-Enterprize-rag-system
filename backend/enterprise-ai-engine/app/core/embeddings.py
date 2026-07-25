import httpx
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenRouterEmbeddingClient:
    """
    Enterprise embedding client for OpenRouter supporting the Qwen3 Embedding model.
    """
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, dimensions: int = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSION
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://apextech.internal",
            "X-Title": "ApexTech Enterprise AI Engine"
        }

    def _post_request(self, payload: dict) -> dict:
        url = f"{self.base_url.rstrip('/')}/embeddings"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                response.raise_for_status()
            return response.json()

    async def _post_request_async(self, payload: dict) -> dict:
        url = f"{self.base_url.rstrip('/')}/embeddings"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                logger.error(f"OpenRouter API async error: {response.status_code} - {response.text}")
                response.raise_for_status()
            return response.json()

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """
        Embeds a list of documents in batches to avoid payload limit errors.
        """
        if not texts:
            return []

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.model,
                "input": batch,
                "dimensions": self.dimensions
            }
            try:
                result = self._post_request(payload)
                # Sort by index to preserve order
                sorted_data = sorted(result["data"], key=lambda x: x["index"])
                embeddings.extend([item["embedding"] for item in sorted_data])
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}-{i+len(batch)}: {e}")
                raise e
        return embeddings

    async def embed_documents_async(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """
        Asynchronously embeds a list of documents in batches.
        """
        if not texts:
            return []

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.model,
                "input": batch,
                "dimensions": self.dimensions
            }
            try:
                result = await self._post_request_async(payload)
                sorted_data = sorted(result["data"], key=lambda x: x["index"])
                embeddings.extend([item["embedding"] for item in sorted_data])
            except Exception as e:
                logger.error(f"Failed to generate async embeddings for batch {i}-{i+len(batch)}: {e}")
                raise e
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single search query.
        """
        payload = {
            "model": self.model,
            "input": [text],
            "dimensions": self.dimensions
        }
        result = self._post_request(payload)
        return result["data"][0]["embedding"]

    async def embed_query_async(self, text: str) -> List[float]:
        """
        Asynchronously embeds a single search query.
        """
        payload = {
            "model": self.model,
            "input": [text],
            "dimensions": self.dimensions
        }
        result = await self._post_request_async(payload)
        return result["data"][0]["embedding"]
