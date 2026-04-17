from qdrant_client import QdrantClient
from openai import OpenAI
from app.config import Settings
from app.models.diagnosis import RetrievedChunk

class RetrievalError(Exception):
    """Raised when retrieval from Qdrant fails."""
    pass

class QdrantRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60,
            prefer_grpc=False
        )
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def retrieve(self, query: str, top_k: int = None) -> list[RetrievedChunk]:
        if top_k is None:
            top_k = self.settings.top_k
            
        try:
            # Embed query
            response = self.openai_client.embeddings.create(
                input=[query],
                model=self.settings.embedding_model
            )
            vector = response.data[0].embedding

            # Search Qdrant
            results = self.qdrant_client.query_points(
                collection_name=self.settings.collection_name,
                query=vector,
                limit=top_k,
                with_payload=True
            ).points

            chunks = [
                RetrievedChunk(
                    text=r.payload.get("text", ""),
                    doc_name=r.payload.get("doc_name", "unknown"),
                    source_type=r.payload.get("source_type", "unknown"),
                    score=r.score
                )
                for r in results
            ]
            
            # Sort by score descending (Qdrant should already do this, but just in case)
            chunks.sort(key=lambda x: x.score, reverse=True)
            
            return chunks
            
        except Exception as e:
            raise RetrievalError(f"Failed to retrieve from Qdrant: {str(e)}")
