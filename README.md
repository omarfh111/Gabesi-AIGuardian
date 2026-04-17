<div align="center">

# 🌿 Gabesi AIGuardian

**An agentic AI system that gives Gabès oasis farmers real-time environmental
intelligence — soil health, pollution exposure, irrigation guidance, and crop
diagnostics — powered by satellite data and a grounded RAG knowledge base.**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-purple)](https://github.com/langchain-ai/langgraph)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector_db-red)](https://qdrant.tech)
[![DeepEval](https://img.shields.io/badge/DeepEval-evaluation-orange)](https://deepeval.com)
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
1. Retrieves pollution exposure history for their plot from satellite data
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
│                   (LangGraph Agent)                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
   RAG Search   NASA POWER   Open-Meteo    Sentinel APIs
   (Qdrant)     (ET₀/climate) (weather)   (NDVI/SO₂/salinity)
        │
        ▼
┌──────────────────────────────────────┐
│         gabes_knowledge              │
│  1718 chunks · 21 documents          │
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
├── data/                          # Knowledge corpus (gitignored — large files)
│   ├── papers/                    # Scientific PDFs (open access)
│   ├── pdl_reports/               # Municipal + EU project reports
│   ├── processed/                 # Preprocessed markdown (41 PDL tables preserved)
│   ├── references/                # FAO-56 irrigation reference
│   └── structured/                # JSON: oasis zones, GCT coords, crop Kc values
├── eval_data/                     # Synthetic golden dataset (gitignored)
│   └── goldens.json               # 68 synthetic Q&A pairs (80% domain relevance)
├── eval_results/                  # Evaluation run outputs (gitignored)
├── scripts/
│   ├── preprocess_docx.py         # Convert PDL docx → markdown, preserve tables
│   ├── ingest.py                  # Chunk, embed, upsert to Qdrant
│   ├── smoke_test.py              # 6-query retrieval verification
│   └── evaluate_retrieval.py      # DeepEval retrieval evaluation pipeline
├── .env.example                   # Environment variable template
└── README.md
```

---

## 🚀 Setup

### Prerequisites

- Python 3.12
- [Qdrant Cloud](https://cloud.qdrant.io) account (free tier works)
- OpenAI API key (embeddings + evaluation judge — ~$0.04 per full ingestion)

### Installation

```bash
git clone https://github.com/omarfh111/Gabesi-AIGuardian.git
cd Gabesi-AIGuardian

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r backend/requirements.txt
```

### Environment

```bash
cp .env.example .env
# Fill in: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY
```

### Reproduce the Knowledge Base

The `data/` folder is gitignored (large PDFs, proprietary municipal documents).
To reproduce:

```bash
python scripts/preprocess_docx.py   # PDL docx → markdown
python scripts/ingest.py            # chunk + embed + upsert to Qdrant
python scripts/smoke_test.py        # verify retrieval works
```

---

## 📊 Knowledge Base

| Collection | Documents | Chunks | Purpose |
|---|---|---|---|
| `gabes_knowledge` | 21 | 1,718 | Static domain knowledge RAG |
| `satellite_timeseries` | — | 0* | Weekly oasis plot snapshots |
| `farmer_context` | — | 0* | Per-farmer memory |

*Populated at runtime by the agent pipeline.

**Ingestion specs:** `text-embedding-3-large` · Chonkie SemanticChunker ·
dense + sparse (BM25/IDF) vectors · payload indexes on `source_type`, `language`, `doc_name`

---

## 📈 Retrieval Evaluation

Evaluated with DeepEval on 68 synthetic goldens generated from real Qdrant chunks
(80% domain relevance rate, GPT-4o-mini as synthesis + judge model).

| Metric | Score | Pass Rate | Verdict |
|---|---|---|---|
| Contextual Recall | **0.9512** | **98.33%** | ✅ Target met (≥ 0.70) |
| Contextual Relevancy | 0.4395 | 41.67% | ⚠️ Known limitation |

**Why relevancy is lower than recall:** `ContextualRelevancyMetric` penalises
multi-topic chunks. The PDL Gabès corpus contains tabular chunks that cover
multiple oases simultaneously (avg 841 chars per chunk). A chunk that correctly
answers a query about Oasis Bahria also contains data on Ouesta and Chenini,
which the judge scores as off-topic. Recall (0.95) is the operationally meaningful
metric — it confirms the right information is retrieved for 98% of queries.
Relevancy reflects chunking strategy, not retrieval failure.

To reproduce the evaluation:

```bash
# Generate goldens and inspect quality
python scripts/evaluate_retrieval.py --synthesize-only --use-openai-synthesis --n-contexts 120

# Run evaluation on saved goldens
python scripts/evaluate_retrieval.py --eval-only --top-k 5
```

---

## 🛠️ Scripts Reference

### `scripts/preprocess_docx.py`
Converts the PDL Gabès municipal report (`.docx`) into clean markdown,
preserving all 41 tables as atomic chunks.

```bash
python scripts/preprocess_docx.py
# Output: data/processed/PDL_GABES_clean.md
```

### `scripts/ingest.py`
Loads all documents, chunks with Chonkie semantic chunker,
embeds with `text-embedding-3-large`, upserts to Qdrant.

```bash
python scripts/ingest.py             # Full ingestion (~$0.04, ~266K tokens)
python scripts/ingest.py --dry-run   # Stats only, no API spend
python scripts/ingest.py --resume    # Skip already-ingested documents
python scripts/ingest.py --doc "filename.pdf"  # Single document
```

### `scripts/smoke_test.py`
Six targeted retrieval queries covering all source types.

```bash
python scripts/smoke_test.py
# Expected: 5/6 pass (1 acceptable false negative — see script comments)
```

### `scripts/evaluate_retrieval.py`
Full DeepEval evaluation pipeline: stratified Qdrant sampling →
domain-filtered synthesis → golden inspection → live retrieval → metric scoring.

```bash
# Full pipeline
python scripts/evaluate_retrieval.py --use-openai-synthesis

# Synthesis only (inspect goldens before spending judge budget)
python scripts/evaluate_retrieval.py --synthesize-only --use-openai-synthesis --n-contexts 120

# Evaluation only (reuse saved goldens)
python scripts/evaluate_retrieval.py --eval-only --top-k 5

# Custom parameters
python scripts/evaluate_retrieval.py --n-contexts 60 --goldens-per-context 3 --top-k 7
```

---

## 🗺️ Roadmap

- [x] Knowledge base — preprocessing pipeline (41 PDL tables preserved)
- [x] Ingestion pipeline — 1,718 chunks, 21 docs, dense + sparse vectors
- [x] Retrieval verification — 6-query smoke test suite
- [x] Retrieval evaluation — DeepEval pipeline, Recall 0.95 / 98.33% pass rate
- [ ] LangGraph agent — tool orchestration and routing
- [ ] RAG search tool — Qdrant integration for the agent
- [ ] Irrigation advisory tool — NASA POWER ET₀ + FAO-56 crop coefficients
- [ ] Satellite data tools — Sentinel-2 NDVI, Sentinel-5P SO₂
- [ ] Pollution exposure logger — per-plot timestamped dossier (PDF export)
- [ ] REST API backend — FastAPI
- [ ] Farmer-facing chat interface — React frontend
- [ ] End-to-end evaluation — Faithfulness + Answer Relevancy after agent is built

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

---
