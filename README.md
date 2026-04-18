# 🩺 Gabès Medical Triage & Agentic RAG System
### Phase 2: Multi-Agent Clinical Consultations & Specialist Handoffs

A state-of-the-art medical triage system evolved into a **Multi-Agent Agentic RAG** architecture. Beyond initial routing, the system now facilitates **Live Clinical Consultations** where specialized medical agents (GPs and Specialists) manage patient records, perform ambiguity resolution, and execute intelligent clinical handoffs triggered by real-time diagnostic reasoning.

---

## 🏗️ System Architecture

The system operates as a tiered agentic network:

### 1. Triage & Clinical Correlation Engine
*   **LLM Analysis**: Powered by `gpt-4o-mini` for high-speed constellation analysis.
*   **Routing Safeguards**: Implements a **0.7 Confidence Gatekeeper**. Ambiguous or non-specific symptoms (e.g., slight headache) are automatically routed to the **Generalist Agent** for clarification before specialization is allowed.

### 2. Multi-Agent Specialist Network
Every specialty is a dedicated, stateful agent with its own RAG knowledge base:
*   **Generalist (GP) 🩺**: The primary diagnostic intermediary and gateway.
*   **Pneumologist 🫁**: Senior specialist in respiratory health & industrial exposure.
*   **Cardiologist 🫀**: Heart health and hypertension specialist.
*   **Neurologist 🧠**: Brain and nervous system expert.
*   **Oncologist 🔬**: Cancer staging and diagnostic planning.
*   **Dermatologist 🧴**: Clinical skin and chemical irritation specialist.
*   **Toxicologist 🧪**: Industrial toxicant (fluoride, sulfur) poisoning expert.

### 3. Agentic Capabilities
*   **Dynamic Initialization**: Agents read the patient's `CIN`-linked record and provide a personalized clinical opening.
*   **One-Question Rule**: Agents are strictly constrained to ask exactly one high-precision question per turn to ensure focused diagnostic loops.
*   **Specialist Handoff**: The Generalist can trigger a `[SUGGEST_TRANSFER]` command. The UI executes a seamless handover, updating the specialist's icon and providing a "Case Handoff" summary to the new doctor.
*   **Professional Reporting**: Once a conclusion is reached, the agent generates a structured **Medical Consultation Report** including **Diagnosis**, **Prescriptions (with dosages)**, and **Gabès-specific recommendations**.

---

## 🧠 Memory & Persistence
*   **Persistent Chat History**: All consultation turns are saved in real-time as a `chat_history` payload within the patient's master record in Qdrant. **Optimized with Batched Persistence** to reduce database round-trips and minimize latency.
*   **CIN Identity Tracking**: Patients are uniquely tracked via their 8-digit **CIN**, allowing for long-term medical history retrieval across multiple sessions and agents.

---

## 🌍 Multilingual Performance
*   **Strict Language Pinning**: Agents detect the patient's preferred language (Arabic, French, or English) during the very first interaction and **pin it** to the patient's dossier. The language is then strictly enforced across all agents, even during specialist handoffs, to ensure absolute clinical consistency and professionalism.
*   **Clinical Formalization**: While the engine interprets informal **Tunisian Darija** and **Arabizi**, it sets the pinned response language to a formal, professional standard.

---

## 🔍 Observability & Precision Retrieval
*   **Production-Grade Tracing**: Fully instrumented with **LangSmith**. Every interaction produces a single, unified performance waterfall trace containing deeply nested steps for retrieval, language detection, persistence, and LLM reasoning.
*   **Clinical Query Rewriting**: Transforms vague patient inputs (e.g., "really sharp") into high-precision scientific search queries (e.g., "sharp chest pain causes phosphate exposure") to ensure that retrieved context from the `gabes_knowledge` vector base is hyper-relevant.

---

## 🚀 Technical Stack
*   **Core Logic**: Python / FastAPI
*   **Language Models**: GPT-4o-mini (Triage & Agents) for optimal speed/reasoning balance.
*   **Vector Database**: **Qdrant Cloud** (High-density indexing for 7 specialty collections).
*   **Embeddings**: `text-embedding-3-large` (3072 dims) for high-precision medical matching.

---

## 📁 Updated Project structure
*   `agents/`: 
    *   `base.py`: Core Agent logic (Memory, RAG, Completion).
    *   `generalist_agent.py`: The primary GP persona.
    *   `pneumologue_agent.py`, `cardiologue_agent.py`, ... : Specialized specialist agents.
*   `main.py`: Agent Factory and FastAPI endpoints.
*   `static/`: Premium glassmorphism UI with integrated **Agentic Chatroom**.

---

## 🛡️ Medical Disclaimer
This system is an **Agentic Triage Aid**. It provides professional clinical suggestions and triage reports but does not replace the judgment of a licensed human physician.

---
**Advanced Agentic Triage | Developed for the Gabès Medical Community | 2026**
