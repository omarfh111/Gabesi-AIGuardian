<div align="center">

# 🌿 Gabesi AIGuardian

**An agentic AI system that gives Gabès oasis farmers real-time environmental
intelligence — soil health, pollution exposure, irrigation guidance, and crop
diagnostics — powered by satellite data and a grounded RAG knowledge base.**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-purple)](https://github.com/langchain-ai/langgraph)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector_db-red)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 🌍 The Problem

Gabès, Tunisia is home to the **only coastal oasis in the Mediterranean** — and
it is being destroyed. The Tunisian Chemical Group (GCT) has discharged over
150 million tonnes of phosphogypsum into the Gulf since 1972. SO₂, fluoride,
and heavy metals blanket the oasis zones. Soil salinity rises every year.

The environmental cost: **76 million Tunisian dinars per year**.
The farmers who bear this cost have **zero access to the data that documents it**.

---

## 💡 What Gabesi AIGuardian Does

A farmer opens the app and asks: *"Why are my palm trees yellowing?"*

The system:
1. Retrieves pollution exposure history for their plot from Sentinel-5P satellite data
2. Checks current soil salinity index from Sentinel-2 imagery
3. Cross-references symptoms against a grounded knowledge base of scientific
   research on fluoride damage, heavy metal contamination, and oasis ecology
4. Returns a plain-language diagnosis with a concrete action and a timestamped
   pollution log the farmer can use as evidence

No other system does this for Gabès.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FARMER CHATBOT                        │
│                  (Gemini 2.0 Flash)                      │
└────────────────────┬────────────────────────────────────┘
                     │ LangGraph Agent
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
   RAG Search   NASA POWER   Open-Meteo    Sentinel APIs
   (Qdrant)     (ET₀/climate) (weather)   (NDVI/SO₂/salinity)
        │
        ▼
┌──────────────────────────────────────┐
│         gabes_knowledge              │
│  1718 chunks across 21 documents     │
│  • PDL Gabès 2023 (municipal audit)  │
│  • 6 scientific papers               │
│  • 9 EU environmental project reports│
│  • FAO-56 crop reference             │
│  • Arabic strategic study 2015-2035  │
│  • Structured oasis/GCT/crop JSON    │
└──────────────────────────────────────┘
```

---

## 📂 Project Structure

```
Gabesi-AIGuardian/
├── data/                        # Knowledge corpus (gitignored, large files)
│   ├── papers/                  # Scientific PDFs (open access)
│   ├── pdl_reports/             # Municipal + EU project reports
│   ├── processed/               # Preprocessed markdown (PDL tables preserved)
│   ├── references/              # FAO-56 irrigation reference
│   └── structured/              # JSON: oasis zones, GCT coords, crop Kc values
├── scripts/
│   ├── preprocess_docx.py       # Convert PDL docx tables to clean markdown
│   ├── ingest.py                # Load, chunk, embed, upsert to Qdrant
│   └── smoke_test.py            # Retrieval verification (6 targeted queries)
├── .env.example                 # Environment variable template
├── requirements.txt             # Pinned Python dependencies
└── README.md
```

---

## 🚀 Setup

### Prerequisites

- Python 3.12
- A [Qdrant Cloud](https://cloud.qdrant.io) account (free tier works)
- OpenAI API key (for embeddings — ~$0.04 per full ingestion)
- Google Gemini API key (for the LLM agent)

### Installation

```bash
git clone https://github.com/omarfh111/Gabesi-AIGuardian.git
cd Gabesi-AIGuardian

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

### Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### Data

The `data/` folder is gitignored because it contains large PDFs and
proprietary municipal documents. To reproduce the knowledge base:

1. Obtain the source documents (see `data/` folder structure above)
2. Run preprocessing: `python scripts/preprocess_docx.py`
3. Run ingestion: `python scripts/ingest.py`
4. Verify: `python scripts/smoke_test.py`

---

## 📊 Knowledge Base Stats

| Collection | Documents | Chunks | Purpose |
|---|---|---|---|
| `gabes_knowledge` | 21 | 1,718 | Static knowledge RAG |
| `satellite_timeseries` | — | 0* | Weekly oasis plot snapshots |
| `farmer_context` | — | 0* | Per-farmer memory |

*Populated at runtime by the agent pipeline.

---

## 🛠️ Scripts Reference

### `scripts/preprocess_docx.py`
Converts the PDL Gabès municipal report (`.docx`) into clean markdown,
preserving all 41 tables as atomic chunks. Must run before ingestion.

```bash
python scripts/preprocess_docx.py
# Output: data/processed/PDL_GABES_clean.md
```

### `scripts/ingest.py`
Loads all documents, chunks with Chonkie semantic chunker,
embeds with `text-embedding-3-large`, and upserts to Qdrant.

```bash
python scripts/ingest.py             # Full ingestion
python scripts/ingest.py --dry-run   # Stats only, no API spend
python scripts/ingest.py --resume    # Skip already-ingested documents
python scripts/ingest.py --doc "filename.pdf"  # Single document
```

### `scripts/smoke_test.py`
Runs 6 targeted retrieval queries to verify the knowledge base is working.

```bash
python scripts/smoke_test.py
```

---

## 🗺️ Roadmap

- [x] RAG knowledge base — ingestion pipeline
- [x] Retrieval verification — smoke tests
- [ ] LangGraph agent — tool routing and orchestration
- [ ] Satellite data tools — Sentinel-2 NDVI, Sentinel-5P SO₂
- [ ] Irrigation advisory tool — NASA POWER ET₀ + FAO-56
- [ ] Pollution exposure logger — per-plot timestamped dossier
- [ ] REST API backend — FastAPI
- [ ] Farmer-facing chat interface — React frontend
- [ ] DeepEval retrieval evaluation pipeline

---

## 🌱 Why This Matters

Gabès farmers have watched their oasis disappear for 50 years with no data,
no evidence, and no recourse. Gabesi AIGuardian gives them both: a daily
intelligence feed about their own land, and an automatically generated
pollution dossier they can bring to a meeting, a journalist, or a court.

The invisible becomes visible. The anecdotal becomes documented.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built for the farmers of Gabès, Tunisia 🌴
</div>
