# 🌍 Gabesi AIGuardian — Smart Environmental & Emergency Intelligence Platform

An AI-powered geographic and emergency intelligence system for **Gabès, Tunisia**. It actively collects, verifies, and maps strategic industrial and geographical zones, whilst empowering citizens with a highly-reactive **AI Emergency Assistant** equipped with real-time pollution metrics and strict medical RAG logic.

---

## 🎯 Project Overview & Pipeline

This platform performs two critical pipelines:

### 1. Geographic Discovery & Mapping Pipeline
1. **Searches** locations via SerpAPI (Google Maps engine) to get GPS coordinates.
2. **Verifies** each location is genuinely in Gabès (AI Verification Agent).
3. **Classifies** each location into a specific category (OpenAI GPT-4o-mini).
4. **Detects duplicates** via coordinate proximity.
5. **Displays** all filtered zones dynamically on a custom Leaflet map dashboard.

### 2. Emergency Decision Pipeline (The Assistant)
1. **User Interaction**: Citizen accesses a glassmorphism floating chat widget.
2. **Location Contexting**: Widget auto-detects or allows map-clicking to cross-reference location with the nearest pollution facilities on the Geographic Map.
3. **Intent Detection**: The Chatbot uses a lightweight LLM router to strictly classify the emergency intent (e.g., `trauma`, `respiratory`, `cardiac`, `toxic`).
4. **RAG Extraction**: The Agent queries a high-speed vector database (**Qdrant**) containing embedded medical protocols to strictly extract exact step-by-step first aid procedures without hallucination.
5. **Smart Scoring & Memory**: Calculates an `Emergency Score` based on symptoms and local pollution risks. If the score exceeds 80 or the user stops responding for 60 seconds, an automated UI Alert kicks in.

---

## 🗺️ Roadmap

- [x] **Phase 1:** Core Flask Backend & SerpAPI Integration for Map building.
- [x] **Phase 2:** Langchain Verification and Classification (Isolate out-of-scope GPS hits).
- [x] **Phase 3:** Qdrant Vector DB Medical injection (`medical_assistant_docs`).
- [x] **Phase 4:** LangGraph State Machine for strict AI medical guidance (Zero-hallucination RAG).
- [x] **Phase 5:** Conversational Memory LLM integration + UI Auto-Alarm Timer (60s).
- [ ] **Phase 6:** Push Notifications and 190 Center API integrations for actual SMS dispatches.
- [ ] **Phase 7:** Multimodal inputs (User can upload a picture of a chemical spill or wound).

---

## 🧠 AI Architecture

### Smart Mapping Agents
- **Agent 1 (Classification)**: Asserts categories (`industrial`, `agriculture`, `coastal`, `urban`).
- **Agent 2 (Verification)**: Validates bounds against the Gabès governorate.

### Emergency Decision Agents (LangGraph)
- **Node: Detection**: Translates natural phrases ("I broke my leg") into standard triggers using LLM intent classification.
- **Node: RAG Query**: Native `QdrantClient.query_points()` interface to extract 3-step protocols based on intent.
- **Node: LLM Formatter**: Wraps static steps into multi-lingual, empathetic messages checking the live `history` memory loop.

---

## 🧱 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, Flask, LangGraph |
| Map APIs | SerpAPI, Leaflet.js |
| AI / LLM | OpenAI GPT-4o-mini, LangChain |
| Vector DB | Qdrant (Cloud) |
| Frontend | HTML5, Vanilla JS, CSS3 (Glassmorphism) |

---

## 🏗️ Execution Flow & Use Cases

### Example Use Case 1: Citizen caught in Gas Leak
1. User opens the application and clicks **"Use my location"** in the Assistant.
2. The agent notes the user is within 5km of the Gabès Chemical Group (GCT).
3. User types: *"I smell toxic gas and it's hard to breathe"*.
4. **Agent Action:** RAG queries Qdrant for toxic exposure, checks pollution score, and issues a ⚠️ CAUTION alert advising the user to close windows, providing exact medical RAG steps in the user's spoken language.

### Example Use Case 2: Unresponsive Patient
1. User accesses the widget and types *"person passed out"*.
2. **Agent Action:** Extracts the CPR protocol from Qdrant.
3. The user stops interacting to perform CPR.
4. **Trigger:** The 60-second frontend inactivity timer pops. The UI borders pulse blood-red and automatically generates a visual alarm message simulating a call to emergency services (190).

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- SerpAPI key (serpapi.com)
- OpenAI API key (platform.openai.com)
- Qdrant Cluster URL and Key (qdrant.tech)

### Instructions

```bash
# Clone the repository
git clone https://github.com/omarfh111/Gabesi-AIGuardian.git
cd Gabesi-AIGuardian
git checkout backend-map-service

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI, SERPAPI, and QDRANT keys.
```

---

## 🚀 Execution

### 1. Vector DB Ingestion (One-time)
If this is a fresh setup, you must ingest the medical PDFs into Qdrant first.
```bash
python scriptinjection/inject_data.py
```

### 2. Start the Server
```bash
python app.py
```
The server starts on `http://localhost:3000`. Navigate there in your browser to access the Gabès Dashboard and the Emergency Medical Widget!

---

## 📝 License
Proprietary project developed for advanced geographic and emergency analysis of the Gabès region in Tunisia.
