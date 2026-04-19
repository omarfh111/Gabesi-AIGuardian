import os
import re
from typing import List, Dict, Any
from datetime import datetime
from openai import OpenAI
from langsmith import wrappers, traceable
from qdrant_client import QdrantClient, models

class BaseAgent:
    def __init__(self, specialty_collection: str):
        self.specialty_collection = specialty_collection
        self.history_collection = "historical_cases"
        self.knowledge_collection = "gabes_knowledge"
        
        self.client = wrappers.wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
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
            self.qdrant.create_payload_index(
                collection_name=self.history_collection,
                field_name="is_bilan",
                field_schema=models.PayloadSchemaType.BOOL
            )
        except Exception:
            pass # Index probably exists

    def _get_dossier_point(self, cin: str):
        """Returns the dossier point object (with payload) for a CIN, or None."""
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
                return results[0][0]
            return None
        except Exception:
            return None

    @traceable(run_type="retriever", name="Fetch Patient Dossier")
    def get_patient_dossier(self, cin: str) -> Dict[str, Any]:
        """Retrieves the master medical record for a CIN using stabilized schema."""
        try:
            dossier_point = self._get_dossier_point(cin)
            if dossier_point:
                return dossier_point.payload
            return {}
        except Exception as e:
            print(f"Error fetching dossier: {e}")
            return {}

    @traceable(run_type="tool", name="Update Dossier Fields")
    def update_dossier_fields(self, cin: str, fields: Dict[str, Any]):
        """Partially updates dossier payload fields for a CIN."""
        try:
            point = self._get_dossier_point(cin)
            if not point:
                return
            self.qdrant.set_payload(
                collection_name=self.history_collection,
                payload=fields,
                points=[point.id]
            )
        except Exception as e:
            print(f"Error updating dossier fields: {e}")

    @traceable(run_type="retriever", name="Fetch Latest Bilan Text")
    def get_latest_bilan_text(self, cin: str) -> str:
        """Returns latest uploaded blood-test text for a CIN from historical_cases."""
        try:
            results = self.qdrant.scroll(
                collection_name=self.history_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="cin", match=models.MatchValue(value=cin)),
                        models.FieldCondition(key="is_bilan", match=models.MatchValue(value=True))
                    ]
                ),
                limit=100,
                with_payload=True
            )
            points = results[0] or []
            if not points:
                return ""

            def sort_key(point):
                value = point.payload.get("uploaded_at", "")
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except Exception:
                    return datetime.min

            latest = sorted(points, key=sort_key, reverse=True)[0]
            return latest.payload.get("text", "") or ""
        except Exception as e:
            print(f"Error fetching latest bilan text: {e}")
            return ""

    @traceable(run_type="retriever", name="Fetch Collection Context")
    def get_context_from_collection(self, collection_name: str, query: str, limit: int = 5) -> str:
        """Generic dense retrieval helper for any collection."""
        try:
            emb = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-large"
            ).data[0].embedding
            results = self.qdrant.query_points(
                collection_name=collection_name,
                query=emb,
                limit=limit
            )
            return "\n\n".join([
                f"[Doc: {res.payload.get('title', 'Clinical Guide')}]\n{res.payload.get('text', '')}"
                for res in results.points
            ])
        except Exception as e:
            print(f"Error fetching context from {collection_name}: {e}")
            return ""

    @traceable(run_type="tool", name="Persist Chat History")
    def update_chat_history(self, cin: str, messages_to_add: List[Dict[str, str]] | Dict[str, str]):
        """Appends a new turn or multiple turns to the patient's chat_history payload."""
        try:
            if isinstance(messages_to_add, dict):
                messages_to_add = [messages_to_add]
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
                history.extend(messages_to_add)
                
                # 2. Perform partial update
                self.qdrant.set_payload(
                    collection_name=self.history_collection,
                    payload={"chat_history": history},
                    points=[point.id]
                )
        except Exception as e:
            print(f"Error updating chat history: {e}")

    @traceable(run_type="tool", name="Query Ranking & Rewriting")
    def _rewrite_query(self, user_input: str, dossier: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
        """Transforms user input into a professional clinical search query using patient context."""
        try:
            # 1. Extract context
            summary = dossier.get("triage_summary") or dossier.get("summary", "")
            last_turns = chat_history[-2:] if chat_history else []
            
            # 2. Call LLM for rewriting
            system_prompt = """You are a medical research assistant. Your task is to transform a vague patient comment into a high-precision clinical search query for a medical knowledge base.
Use the patient's record to understand the context.
Output ONLY the search query (max 10 words)."""
            
            user_prompt = f"""[PATIENT SUMMARY]: {summary}
[RECENT CHAT]: {last_turns}
[LAST COMMENT]: {user_input}

CONVERT THE LAST COMMENT INTO A SCIENTIFIC SEARCH QUERY:"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                max_tokens=50
            )
            rewritten = response.choices[0].message.content.strip()
            # Clean up quotes if LLM added them
            return rewritten.strip('"').strip("'")
        except Exception as e:
            print(f"Query rewriting error: {e}")
            return user_input

    @traceable(run_type="retriever", name="Fetch Specialty Knowledge")
    def get_specialty_context(self, user_input: str, dossier: Dict[str, Any] = None, chat_history: List[Dict[str, str]] = None, limit: int = 5) -> str:
        """Searches the agent's dedicated specialty collection with query rewriting."""
        try:
            # 1. Query Rewriting
            search_query = user_input
            if dossier and user_input != "[INITIALIZE]":
                search_query = self._rewrite_query(user_input, dossier, chat_history or [])
            
            # 2. Generate embedding for the clarified query
            emb = self.client.embeddings.create(
                input=search_query,
                model="text-embedding-3-large"
            ).data[0].embedding
            
            # 3. Vector Search
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

    @traceable(run_type="tool", name="Pin Session Language")
    def set_pinned_language(self, cin: str, language: str):
        """Saves the detected language to the patient's dossier in Qdrant."""
        try:
            results = self.qdrant.scroll(
                collection_name=self.history_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="cin", match=models.MatchValue(value=cin)),
                        models.FieldCondition(key="is_dossier", match=models.MatchValue(value=True))
                    ]
                ),
                limit=1
            )
            if results[0]:
                self.qdrant.set_payload(
                    collection_name=self.history_collection,
                    payload={"pinned_language": language},
                    points=[results[0][0].id]
                )
        except Exception as e:
            print(f"Error pinning language: {e}")

    @traceable(run_type="tool", name="Patient Language Detection")
    def _detect_language(self, text: str) -> str:
        """Helper to detect language using LLM."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Detect the language of the following text. Output ONLY one word: 'arabic', 'french', or 'english'."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip().lower()
        except:
            return "english"

    @traceable(run_type="llm", name="Agent Completion")
    def get_completion(self, system_prompt: str, user_query: str, history: List[Dict[str, str]], cin: str = None, dossier: Dict[str, Any] = None):
        """Standard OpenAI completion for agents with strict language pinning."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        
        # 1. Check for pinned language in dossier
        pinned_lang = None
        if cin:
            if dossier is None:
                dossier = self.get_patient_dossier(cin)
            pinned_lang = dossier.get("pinned_language")
            
            # 2. If not pinned, detect and pin it
            if not pinned_lang:
                # Try finding in history first
                user_msgs = [m for m in history if m["role"] == "user"]
                if user_msgs:
                    pinned_lang = self._detect_language(user_msgs[0]["content"])
                    self.set_pinned_language(cin, pinned_lang)
                elif user_query != "[INITIALIZE]" and "being transferred" not in user_query:
                    # Detect from current query
                    pinned_lang = self._detect_language(user_query)
                    self.set_pinned_language(cin, pinned_lang)
        
        # 3. Apply strict language instruction
        if pinned_lang:
            target_lang_reminder = f"STRICT RULE: You MUST respond EXCLUSIVELY in the following language: {pinned_lang.upper()}. Do NOT switch to any other language even if the patient does."
        else:
            # Fallback for initialization or if cin is missing
            target_lang_reminder = "IMPORTANT: You MUST respond in the same language as the patient's most recent message or the language found in the medical record."
            if user_query == "[INITIALIZE]" or "Please provide your first specialized insight" in user_query:
                 target_lang_reminder = "IMPORTANT: This is the start of the chat. Respond in the language found in the PATIENT DATA (triage_summary or main_problem)."
        
        messages.append({"role": "system", "content": target_lang_reminder})
        messages.append({"role": "user", "content": user_query})
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content

    def _can_emit_final_report(self, user_input: str) -> bool:
        """Only allow final specialist report on explicit close token."""
        if not user_input:
            return False
        signal = user_input.lower()
        return (
            "[finalize_specialist_report]" in signal
            or "[conclude_case]" in signal
            or "[close_case]" in signal
        )

    @traceable(run_type="tool", name="Final Report Gating")
    def enforce_final_report_gating(
        self,
        response: str,
        user_input: str,
        system_content: str,
        chat_history: List[Dict[str, str]],
        cin: str,
        dossier: Dict[str, Any]
    ) -> str:
        """
        Prevents premature [FINAL_SPECIALIST_REPORT] unless explicit close token is present.
        """
        if "[FINAL_SPECIALIST_REPORT]" not in (response or ""):
            return response
        if self._can_emit_final_report(user_input):
            return response

        followup_prompt = (
            "IMPORTANT: Do NOT provide the final specialist report now. "
            "The case is not concluded yet. "
            "Ask exactly ONE targeted clinical follow-up question. "
            "Do NOT output [FINAL_SPECIALIST_REPORT]."
        )
        retry = self.get_completion(
            system_content,
            followup_prompt,
            chat_history,
            cin=cin,
            dossier=dossier
        )
        if "[FINAL_SPECIALIST_REPORT]" in (retry or ""):
            return "I need one more precise clinical detail before issuing the final report. Can you clarify your latest symptom progression?"
        return retry

    def _extract_primary_question(self, text: str) -> str:
        """Extract a normalized primary question string for dedup checks."""
        if not text:
            return ""
        match = re.search(r"([^?]{4,}\?)", text, flags=re.DOTALL)
        question = match.group(1) if match else ""
        normalized = re.sub(r"\s+", " ", question.lower()).strip()
        normalized = re.sub(r"[^a-z0-9\s\?]", "", normalized)
        return normalized

    def _is_repeated_question(self, response: str, chat_history: List[Dict[str, str]]) -> bool:
        current_q = self._extract_primary_question(response)
        if not current_q:
            return False
        assistant_questions = []
        for msg in chat_history[-12:]:
            if msg.get("role") == "assistant":
                q = self._extract_primary_question(msg.get("content", ""))
                if q:
                    assistant_questions.append(q)
        if not assistant_questions:
            return False

        current_tokens = set(current_q.replace("?", "").split())
        for prev_q in assistant_questions:
            if current_q == prev_q:
                return True
            prev_tokens = set(prev_q.replace("?", "").split())
            if not current_tokens or not prev_tokens:
                continue
            overlap = len(current_tokens & prev_tokens) / max(len(current_tokens), 1)
            if overlap >= 0.8:
                return True
        return False

    @traceable(run_type="tool", name="No Repeat Question Guard")
    def enforce_no_repeated_question(
        self,
        response: str,
        user_input: str,
        system_content: str,
        chat_history: List[Dict[str, str]],
        cin: str,
        dossier: Dict[str, Any]
    ) -> str:
        """Avoid asking the same clinical question repeatedly."""
        if not self._is_repeated_question(response, chat_history):
            return response

        asked_questions = []
        for msg in chat_history[-12:]:
            if msg.get("role") == "assistant":
                q = self._extract_primary_question(msg.get("content", ""))
                if q:
                    asked_questions.append(q)

        followup_prompt = (
            "IMPORTANT: Your proposed question is too repetitive.\n"
            f"Already asked questions: {asked_questions}\n"
            "Ask ONE new high-value clinical question that is different and non-overlapping.\n"
            "If enough data is already collected, provide next-step action without asking another repetitive question."
        )
        retry = self.get_completion(
            system_content,
            followup_prompt,
            chat_history,
            cin=cin,
            dossier=dossier
        )
        if self._is_repeated_question(retry, chat_history):
            return "I already have enough detail on that point. Can you tell me one new symptom that has appeared recently?"
        return retry
