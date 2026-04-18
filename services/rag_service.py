import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.enabled = True
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "gabes_knowledge"
        self.history_collection = "historical_cases"
        
        # Initialize collections if they don't exist
        self._ensure_collections()
        
        # Re-enabled sparse search logic
        cache_dir = os.path.join(os.getcwd(), ".cache")
        self.sparse_model = SparseTextEmbedding(
            model_name="prithivida/Splade_PP_en_v1",
            cache_dir=cache_dir
        )

    def _ensure_collections(self):
        """Creates historical_cases collection if it doesn't exist."""
        try:
            collections = self.qdrant_client.get_collections().collections
            existing = [c.name for c in collections]
            
            if self.history_collection not in existing:
                self.qdrant_client.create_collection(
                    collection_name=self.history_collection,
                    vectors_config=models.VectorParams(
                        size=3072,  # text-embedding-3-large
                        distance=models.Distance.COSINE
                    )
                )
                # Note: Not adding sparse for history for now to keep it simple, 
                # but could be added later if keyword matching is critical.
                log.info(f"Created collection: {self.history_collection}")
        except Exception as e:
            print(f"Error ensuring collections: {e}")

    @traceable(run_type="embedding", name="OpenAI Embedding")
    def get_dense_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding

    def get_sparse_embedding(self, text: str) -> Dict[str, Any]:
        # FastEmbed returns a generator of sparse vectors
        sparse_embeddings = list(self.sparse_model.embed([text]))
        vector = sparse_embeddings[0]
        return {
            "indices": vector.indices.tolist(),
            "values": vector.values.tolist()
        }

    @traceable(run_type="retriever", name="Hybrid Knowledge Ranking")
    def search(self, query: str, limit: int = 5) -> str:
        if not self.enabled:
            return "RAG Search Disabled (Ablation Mode)."
        try:
            dense_vector = self.get_dense_embedding(query)
            sparse_vector = self.get_sparse_embedding(query)

            # Perform Hybrid Search with Fusion (Dense + Sparse)
            search_results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(
                        query=dense_vector,
                        using=None, # Targets the unnamed (default) 3072-dim vector
                        limit=limit,
                    ),
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_vector["indices"],
                            values=sparse_vector["values"]
                        ),
                        using="text-sparse", 
                        limit=limit,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=limit,
            )

            context = "\n\n".join([
                f"[Source: {res.payload.get('doc_name', 'Unknown')}]\n{res.payload.get('text', '')}"
                for res in search_results.points
            ])

            return context if context else "No specific context found in knowledge base."

        except Exception as e:
            print(f"RAG Search Error: {e}")
            return "Knowledge base search unavailable."

    def index_case(
        self, 
        case_id: str, 
        payload: Dict[str, Any],
        text_for_embedding: str
    ):
        """Indexes a completed triage case with a nested rich payload."""
        try:
            vector = self.get_dense_embedding(text_for_embedding)
            
            self.qdrant_client.upsert(
                collection_name=self.history_collection,
                points=[
                    models.PointStruct(
                        id=case_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            cin = payload.get("cin", "unknown")
            print(f"✅ Successfully indexed high-density case {case_id} (CIN: {cin}) in Qdrant.")
        except Exception as e:
            print(f"❌ Error indexing case in Qdrant: {e}")

    @traceable(run_type="retriever", name="Find Similar Cases")
    def find_similar_cases(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Searches for past similar cases."""
        try:
            vector = self.get_dense_embedding(query)
            results = self.qdrant_client.search(
                collection_name=self.history_collection,
                query_vector=vector,
                limit=limit,
                with_payload=True
            )
            return [
                {
                    "case_id": r.payload.get("case_id"),
                    "specialty": r.payload.get("specialty"),
                    "summary": r.payload.get("summary"),
                    "score": round(r.score, 4)
                }
                for r in results
            ]
        except Exception as e:
            print(f"Error searching similar cases: {e}")
            return []
