import os
from typing import List, Dict, Any
from openai import OpenAI
from qdrant_client import QdrantClient, models

class BaseAgent:
    def __init__(self, specialty_collection: str):
        self.specialty_collection = specialty_collection
        self.history_collection = "historical_cases"
        self.knowledge_collection = "gabes_knowledge"
        
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensures stable payload indexes for CIN lookup."""
        try:
            self.qdrant.create_payload_index(
                collection_name=self.history_collection,
                field_name="cin",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            self.qdrant.create_payload_index(
                collection_name=self.history_collection,
                field_name="is_dossier",
                field_schema=models.PayloadSchemaType.BOOL
            )
        except Exception:
            pass # Index probably exists

    def get_patient_dossier(self, cin: str) -> Dict[str, Any]:
        """Retrieves the master medical record for a CIN using stabilized schema."""
        try:
            results = self.qdrant.scroll(
                collection_name=self.history_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="cin", match=models.MatchValue(value=cin)),
                        models.FieldCondition(key="is_dossier", match=models.MatchValue(value=True))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            if results[0]:
                return results[0][0].payload
            return {}
        except Exception as e:
            print(f"Error fetching dossier: {e}")
            return {}

    def update_chat_history(self, cin: str, message: Dict[str, str]):
        """Appends a new turn to the patient's chat_history payload."""
        try:
            # 1. Find the point ID using standardized schema
            results = self.qdrant.scroll(
                collection_name=self.history_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="cin", match=models.MatchValue(value=cin)),
                        models.FieldCondition(key="is_dossier", match=models.MatchValue(value=True))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            if results[0]:
                point = results[0][0]
                history = point.payload.get("chat_history", [])
                history.append(message)
                
                # 2. Perform partial update
                self.qdrant.set_payload(
                    collection_name=self.history_collection,
                    payload={"chat_history": history},
                    points=[point.id]
                )
        except Exception as e:
            print(f"Error updating chat history: {e}")

    def get_specialty_context(self, query: str, limit: int = 5) -> str:
        """Searches the agent's dedicated specialty collection."""
        try:
            # Note: Using simple search for now, can be expanded to hybrid
            # Generate embedding
            emb = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-large"
            ).data[0].embedding
            
            # Using query_points (newer API) to be safe and avoid attribute errors
            results = self.qdrant.query_points(
                collection_name=self.specialty_collection,
                query=emb,
                limit=limit
            )
            
            context = "\n\n".join([
                f"[Doc: {res.payload.get('title', 'Clinical Guide')}]\n{res.payload.get('text', '')}"
                for res in results.points
            ])
            return context
        except Exception as e:
            print(f"Error fetching specialty context: {e}")
            return ""

    def get_completion(self, system_prompt: str, user_query: str, history: List[Dict[str, str]]):
        """Standard OpenAI completion for agents."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        
        # Determine the target language from the most recent human message in history
        # Or from the current query if it's not a system command
        target_lang_reminder = "IMPORTANT: You MUST respond in the same language as the patient's most recent message."
        if user_query == "[INITIALIZE]" or "Please provide your first specialized insight" in user_query:
             target_lang_reminder = "IMPORTANT: This is the start of the chat. Respond in the language found in the PATIENT DATA (triage_summary or main_problem)."
        
        messages.append({"role": "system", "content": target_lang_reminder})
        messages.append({"role": "user", "content": user_query})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini", # Switched to mini as requested
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content
