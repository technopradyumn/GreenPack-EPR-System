# ♻️ GreenPack EPR Compliance System

A FastAPI backend service for **GreenPack Industries** to manage Extended Producer Responsibility (EPR) compliance — submit monthly plastic declarations, reconcile them against ERP procurement records, and query an AI assistant grounded in official EPR policy documents.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack & Choices](#tech-stack--choices)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [API Endpoints](#api-endpoints)
- [Demo — curl Script](#demo--curl-script)
- [RAG Corpus & Sources](#rag-corpus--sources)
- [AI Coding Assistant Usage](#ai-coding-assistant-usage)
- [Trade-offs & What I'd Do Differently](#trade-offs--what-id-do-differently)

---

## Overview

GreenPack must comply with India's EPR rules: every month they declare how much plastic packaging they put into the market, and that declaration must reconcile within a **5% tolerance** against actual ERP procurement records.

This service handles three workflows:

1. **`POST /submit`** — Accept and validate a monthly plastic declaration (deterministic, no LLM).
2. **`GET /summary/{producer_id}/{month}`** — Reconcile declaration vs. ERP data; use an LLM only to narrate the findings in plain English.
3. **`POST /ask`** — RAG-powered Q&A over EPR/plastic compliance policy documents.

---

## Architecture

```
POST /submit          → Pydantic validation → MongoDB storage
                        (NO LLM — validation is a deterministic problem)

GET /summary          → Load declaration from MongoDB
                        → Load ERP feed from erp_feed.csv (fallback: MongoDB erp_data collection)
                        → Deterministic reconciliation (5% threshold)
                        → Gemini generates plain-English narrative from structured result
                        → Return JSON: { reconciliation, narrative }

POST /ask             → Embed question (SentenceTransformers)
                        → Retrieve top-k chunks from Qdrant
                        → Gemini answers strictly from retrieved context
                        → Return answer + citations (doc title + page)
                        → If unanswerable: "I do not know based on the provided documents"
```

**Key design decision:** The LLM is never used for analysis or validation. It only generates narrative from already-computed structured data (Endpoint 2) or answers strictly grounded questions (Endpoint 3). This keeps the system deterministic where determinism is possible.

---

## Tech Stack & Choices

| Component | Choice | Why |
|---|---|---|
| **Framework** | FastAPI | Async-native, auto-generates OpenAPI docs, Pydantic built-in |
| **LLM** | `gemini-2.5-flash-lite` (Google Gemini) | Free-tier sufficient, fast latency, strong instruction-following for structured generation; chosen over GPT-4o to avoid spend during screening |
| **Embeddings** | `all-MiniLM-L6-v2` (SentenceTransformers) | Runs fully locally, no API cost, 384-dim vectors are fast to query, well-benchmarked for semantic similarity on short policy text |
| **Vector Store** | Qdrant | Runs via Docker with no cloud dependency, cosine-metric support, simple Python client |
| **Primary DB** | MongoDB | Flexible document store — EPR declarations are naturally JSON-shaped; PyMongo is straightforward |
| **Data Layer** | CSV (`erp_feed.csv`) + MongoDB fallback | CSV simulates a simple ERP export; MongoDB fallback means the service doesn't break if the file is missing |

---

## Project Structure

```
GreenPack-EPR-System/
│
├── app/
│   ├── main.py               # FastAPI app entrypoint, mounts static frontend
│   ├── config.py             # Pydantic Settings — reads .env with strict schema
│   ├── db.py                 # PyMongo client init
│   ├── ingest.py             # PDF → chunk → embed → Qdrant ingestion pipeline
│   ├── schemas.py            # Pydantic request/response models
│   │
│   ├── routes/
│   │   ├── submit.py         # POST /submit
│   │   ├── summary.py        # GET /summary/{producer_id}/{month}
│   │   └── ask.py            # POST /ask
│   │
│   └── services/
│       ├── llm.py            # Gemini API wrapper
│       ├── rag.py            # Embedding + Qdrant retrieval
│       └── reconciliation.py # 5% tolerance logic (pure Python, no LLM)
│
├── data/
│   ├── erp_feed.csv          # Mock ERP procurement records
│   └── docs/                 # RAG corpus PDFs (see Sources section)
│
├── frontend/                 # Vanilla HTML/CSS/JS dashboard (bonus)
│   ├── index.html
│   ├── index.css
│   └── app.js
│
├── .env.example              # Environment variable template
├── docker-compose.yml        # Spins up Qdrant
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- A Google Gemini API key ([get one free](https://aistudio.google.com/))

### 1. Clone the repo

```bash
git clone https://github.com/technopradyumn/GreenPack-EPR-System.git
cd GreenPack-EPR-System
```

### 2. Configure environment

```bash
cp .env.example .env
# Then edit .env and add your GEMINI_API_KEY
```

`.env` structure:

```
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=greenpack
QDRANT_HOST=localhost
QDRANT_PORT=6333
GEMINI_API_KEY=your_key_here
```

### 3. Start Qdrant (and optionally MongoDB via Docker)

```bash
docker-compose up -d
```

> If you have MongoDB installed locally, it will start automatically on port 27017. Otherwise, add a MongoDB service to `docker-compose.yml`.

### 4. Create virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt
```

### 5. Ingest RAG corpus into Qdrant

```bash
python -m app.ingest
```

This parses PDFs in `data/docs/`, splits into ~500-token chunks, embeds with `all-MiniLM-L6-v2`, and upserts into Qdrant collection `epr_docs`.

### 6. Start the server

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs available at: `http://127.0.0.1:8000/docs`

---

## API Endpoints

### `POST /submit`

Validates and stores a monthly plastic declaration. **No LLM is called here** — validation is a deterministic problem.

**Request:**
```json
{
  "producer_id": "GREENPACK-001",
  "month": "2026-04",
  "declared_quantities_kg": {
    "rigid_plastic": 12000,
    "flexible_plastic": 8500,
    "multilayer_plastic": 3200
  }
}
```

**Validations (deterministic, Pydantic):**
- All fields required
- `month` must match `YYYY-MM` format
- All quantity values must be positive integers

**Response (201):**
```json
{
  "record_id": "uuid-...",
  "producer_id": "GREENPACK-001",
  "month": "2026-04",
  "declared_quantities_kg": { ... },
  "created_at": "2026-05-20T10:30:00Z"
}
```

---

### `GET /summary/{producer_id}/{month}`

Reconciles declaration vs. ERP procurement records and returns both structured results and an LLM-generated narrative.

**Example:** `GET /summary/GREENPACK-001/2026-04`

**Response (200):**
```json
{
  "producer_id": "GREENPACK-001",
  "month": "2026-04",
  "reconciliation": [
    {
      "category": "rigid_plastic",
      "declared_kg": 12000,
      "procured_kg": 11800,
      "difference_pct": 1.69,
      "status": "OK"
    },
    {
      "category": "flexible_plastic",
      "declared_kg": 8500,
      "procured_kg": 9100,
      "difference_pct": 6.59,
      "status": "FLAGGED"
    },
    {
      "category": "multilayer_plastic",
      "declared_kg": 3200,
      "procured_kg": 3150,
      "difference_pct": 1.59,
      "status": "OK"
    }
  ],
  "narrative": "GreenPack's April 2026 declaration is largely aligned with procurement records, with two of three categories within the 5% compliance threshold. However, flexible plastic shows a 6.6% discrepancy — declared at 8,500 kg against 9,100 kg procured — which exceeds the permitted tolerance. It is recommended that GreenPack review purchase orders and invoice records for flexible plastic in April and file a corrected declaration before the regulatory deadline."
}
```

**Error responses:**
- `404 { "detail": "Data is not declared by company" }` — no declaration found
- `404 { "detail": "Data is not available" }` — declaration found but no ERP records

---

### `POST /ask`

Answers EPR compliance questions using a RAG pipeline over the ingested document corpus.

**Request:**
```json
{ "question": "What is the penalty for non-compliance under EPR rules?" }
```

**Response:**
```json
{
  "answer": "Under the Plastic Waste Management Rules 2016 (amended 2022), producers who fail to meet EPR targets may face penalties up to ₹1 lakh per day of non-compliance, as per Section 15 of the Environment Protection Act 1986.",
  "citations": [
    {
      "document": "CPCB_EPR_Guidelines_2022.pdf",
      "section": "Section 4.3 — Penalties and Enforcement",
      "page": 12
    }
  ]
}
```

If the answer is not in the corpus:
```json
{ "answer": "I do not know based on the provided documents" }
```

---

## Demo — curl Script

Run all three endpoints in sequence:

```bash
#!/bin/bash
BASE="http://127.0.0.1:8000"

echo "===== STEP 1: Submit Declaration ====="
curl -s -X POST "$BASE/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_id": "GREENPACK-001",
    "month": "2026-04",
    "declared_quantities_kg": {
      "rigid_plastic": 12000,
      "flexible_plastic": 8500,
      "multilayer_plastic": 3200
    }
  }' | python3 -m json.tool

echo ""
echo "===== STEP 2: Get Reconciliation Summary ====="
curl -s "$BASE/summary/GREENPACK-001/2026-04" | python3 -m json.tool

echo ""
echo "===== STEP 3: Ask Compliance Question ====="
curl -s -X POST "$BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the EPR targets for plastic packaging producers in India?"}' \
  | python3 -m json.tool
```

Save as `demo.sh`, then:
```bash
chmod +x demo.sh
./demo.sh
```

---

## RAG Corpus & Sources

The `/ask` endpoint's RAG pipeline is built over the following documents, stored in `data/docs/`:

| File | Source | Description |
|---|---|---|
| `PWM_Rules_2016_amended_2022.pdf` | [MoEFCC Gazette Notification](https://moef.gov.in) | Plastic Waste Management Rules 2016, amended 2022 — core legal framework |
| `CPCB_EPR_Guidelines_2022.pdf` | [CPCB Official Portal](https://cpcb.nic.in/eprnorms.php) | Central Pollution Control Board — EPR registration, targets, and compliance procedure |
| `mock_epr_policy_summary.txt` | Fabricated for this task | 2-page plain-English summary of EPR obligations, penalty structure, and monthly declaration process — created to fill gaps in the public docs and test the "I do not know" fallback |
| `plastic_waste_wiki_excerpt.txt` | Wikipedia — [Extended Producer Responsibility](https://en.wikipedia.org/wiki/Extended_producer_responsibility) | Background on EPR as a regulatory concept globally and in India |
| `EPR_FAQ_CPCB_2023.pdf` | [CPCB FAQ document](https://cpcb.nic.in) | Frequently asked questions from CPCB on EPR registration and plastic credit system |

> **Note:** Two documents are fabricated mock policy summaries (clearly marked). The RAG pipeline treats all documents equally — the point is the retrieval and citation mechanism, not the legal accuracy.

---

## AI Coding Assistant Usage

**Tool used:** Claude (claude.ai) and GitHub Copilot

**Specifically used for:**

- `app/services/reconciliation.py` — Asked Claude to generate the initial 5% tolerance comparison function with edge case handling (zero values, missing categories). Reviewed and adjusted the output.
- `app/ingest.py` — Used Copilot autocomplete to scaffold the PDF → chunk → embed → upsert loop. Manually added the metadata schema (doc title, page number) for citation support.
- `app/services/rag.py` — Prompted Claude: *"Write a function that takes a question string, embeds it with SentenceTransformers all-MiniLM-L6-v2, queries a Qdrant collection for top 5 results, and returns the payload with scores."* Adapted the output to fit the project's config/schema layer.
- `app/routes/summary.py` — Used Copilot for the boilerplate 404 error handling pattern; wrote the reconciliation orchestration logic manually.
- `frontend/app.js` — Used Claude to generate the typewriter animation and citation toggle; styled manually.

The AI assistant was used as a **fast scaffolding and boilerplate tool**, not as a replacement for architectural thinking. All core logic (reconciliation threshold, RAG citation schema, LLM prompt design) was written and reviewed manually.

---

## Trade-offs & What I'd Do Differently

### Trade-off I made: MongoDB over SQLite

The task explicitly allowed SQLite or even in-memory storage. I chose MongoDB because EPR declarations are naturally document-shaped and the schema can evolve (new plastic categories, multi-site producers). The trade-off is **operational complexity** — MongoDB requires a running service (added to Docker Compose), whereas SQLite is a single file with zero infrastructure. For a screening task prototype, SQLite would have been the simpler, faster choice. I chose MongoDB to demonstrate that I think about production-readiness, but I acknowledge it added setup friction.

### One thing I'd do differently with another day

**Structured outputs on the LLM call.** Right now the summary narrative from Gemini is a raw string. With another day I'd add a Pydantic response schema and use Gemini's structured output mode (`response_mime_type: application/json`) to make the narrative parse deterministically — guaranteeing the response always fits the expected JSON shape and never returns malformed text. I'd also add a retry/fallback in case the LLM call times out, so the endpoint still returns structured reconciliation data even if the narrative generation fails.

---

## Requirements

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
pymongo
pandas
google-generativeai
qdrant-client
sentence-transformers
pypdf
python-dotenv
httpx
```

---

## License

MIT — built for the Innotechwise screening task. Keep it on your GitHub, reference it in any future interview.