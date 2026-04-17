import os
from typing import List, Dict, Any
from openai import OpenAI
from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        self.enabled = True
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "gabes_knowledge"
        
        # Re-enabled sparse search logic
        cache_dir = os.path.join(os.getcwd(), ".cache")
        self.sparse_model = SparseTextEmbedding(
            model_name="prithivida/Splade_PP_en_v1",
            cache_dir=cache_dir
        )

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
