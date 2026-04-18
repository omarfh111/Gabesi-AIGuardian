# 🌍 Gabès Environmental Intelligence Platform

A map-based, anonymous environmental reporting system powered by AI.  
Citizens can report environmental issues (smoke, smell, waste, water contamination, dust, health symptoms) directly on an interactive map of **Gabès, Tunisia**. Reports are enriched with AI classification, similarity detection, and summarization.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 (Vite) + TypeScript + TailwindCSS v4 |
| **Map** | React-Leaflet + OpenStreetMap (free tiles) |
| **State** | Zustand |
| **Backend** | FastAPI (Python) |
| **Database** | Supabase (PostgreSQL) |
| **Vector DB** | Qdrant |
| **AI** | OpenAI (embeddings + GPT-3.5-turbo for summaries) |

---

## 📦 Project Structure

```
warnings/
├── main.py              # FastAPI application
├── database.py          # Supabase client setup
├── ai_pipeline.py       # OpenAI + Qdrant AI pipeline
├── schemas.py           # Pydantic request/response models
├── schema.sql           # Supabase database schema
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (fill in your keys)
├── .gitignore
└── frontend/
    ├── src/
    │   ├── App.tsx          # Root component
    │   ├── api.ts           # Axios API client
    │   ├── store.ts         # Zustand state management
    │   ├── index.css        # Global styles (TailwindCSS v4)
    │   └── components/
    │       ├── MapView.tsx       # Leaflet map with clustering
    │       ├── ReportModal.tsx   # Report submission form
    │       ├── ReportPopup.tsx   # Marker popup with AI insights
    │       └── FiltersPanel.tsx  # Filter by type/severity
    ├── package.json
    └── vite.config.ts
```

---

## 🚀 Setup Instructions

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **Supabase** account (free tier) → [supabase.com](https://supabase.com)
- **Qdrant** cloud instance (free tier) or local Docker → [qdrant.tech](https://qdrant.tech)
- **OpenAI** API key → [platform.openai.com](https://platform.openai.com)

### 1. Clone & Install Backend

```bash
cd warnings
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and fill in your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your-qdrant-key
OPENAI_API_KEY=sk-your-openai-key
```

### 3. Create Database Tables

Run the contents of `schema.sql` in your Supabase SQL Editor:
1. Go to Supabase Dashboard → SQL Editor
2. Paste the contents of `schema.sql`
3. Click **Run**

### 4. Install & Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

### 5. Run Backend

```bash
# From the project root (warnings/)
uvicorn main:app --reload
```

Backend runs at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reports` | Submit a new environmental report |
| `GET` | `/reports` | Fetch reports (with optional filters) |
| `GET` | `/reports/{id}` | Get single report with AI analysis |
| `GET` | `/health` | Health check |

### Query Parameters for `GET /reports`

- `issue_type` — Filter by type: `smoke`, `smell`, `dust`, `water`, `waste`, `symptoms`
- `severity` — Filter by: `low`, `medium`, `high`

---

## 🧠 AI Pipeline

When a report is submitted, the backend automatically:

1. **Classifies** the issue and normalizes severity
2. **Generates embeddings** using OpenAI `text-embedding-3-large`
3. **Searches Qdrant** for similar past reports (cosine similarity ≥ 0.85)
4. **Computes** confidence score based on cluster density
5. **Generates summary** using GPT-3.5-turbo (neutral, objective language)

---

## 🔒 Privacy & Safety

- **Anonymous** — No login, no personal data collected
- **Coordinates rounded** to ~100m precision for public display
- **Neutral language** — AI never accuses specific entities
- **Rate limiting** ready via `report_meta` table (IP hash tracking)

---

## 📋 Features

- ✅ Interactive map centered on Gabès, Tunisia
- ✅ Click-to-report with modal form
- ✅ Color-coded markers by issue type
- ✅ Marker clustering for performance
- ✅ Filter panel (issue type + severity)
- ✅ AI-powered report summaries
- ✅ Similar report detection via vector search
- ✅ Confidence scoring
- ✅ Mobile responsive
- ✅ Real-time report polling (30s interval)

---

## License

MIT
