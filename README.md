# ♻️ GreenPack EPR System

A state-of-the-art Extended Producer Responsibility (EPR) Compliance and Reconciliation platform for plastic packaging. Built with a fast, async FastAPI backend, MongoDB, Qdrant vector database, Google Gemini, and a premium, dark-mode glassmorphic frontend.

---

## ⭐️ Situation

Extended Producer Responsibility (EPR) regulations require plastic packaging manufacturers and brand owners to declare their monthly packaging usage and ensure it aligns within a **5% tolerance limit** against actual procurement records. Navigating hundreds of pages of compliance circulars is highly complex. Companies need a robust system that simplifies reporting, performs deterministic reconciliation, validates declarations, handles database fallbacks, and features a smart, document-grounded AI assistant.

---

## 🎯 Task

Create an end-to-end web application that:
1. **Validates & Stores Declarations**: Handles schema-strict submissions of monthly rigid, flexible, and multilayer plastic declarations in MongoDB.
2. **Deterministic Reconciliation**: Automatically reconciles declarations against ERP procurement logs (`data/erp_feed.csv`) with automatic fallback to MongoDB's `erp_data` collection if the CSV is missing.
3. **Smart Error Reporting**: Communicates explicit validation and availability errors to the client:
   * Returns `"Data is not declared by company"` (HTTP 404) if no declaration is recorded in MongoDB.
   * Returns `"Data is not available"` (HTTP 404) if a declaration exists but no corresponding ERP procurement logs can be found.
4. **Document-Grounded RAG Assistant**: Searches vector representations of official EPR guidelines stored in Qdrant, using Google Gemini to answer questions with zero hallucination.
5. **Modern Dashboard Interface**: Reorders tabs natively for seamless reporting workflow: **Submit Declaration** ➡️ **Reconciliation** ➡️ **Compliance AI**.

---

## 🚀 Action & Architecture

### 📂 Project Structure

```text
Greenpack EPR System/
│   .env                      # Local environment configurations (ignored by git)
│   .gitignore                # Standard Python/IDE ignore file
│   README.md                 # Project documentation
│   requirements.txt          # Third-party dependency definitions
│   docker-compose.yml        # Multi-container orchestration (Qdrant)
│
├─ app/                       # FastAPI application core
│   ├─ main.py                # App entrypoint and static assets mounting
│   ├─ config.py              # Strict environment schema parsing using Pydantic
│   ├─ db.py                  # PyMongo client initialization
│   ├─ ingest.py              # Local PDF parsing & Qdrant vector ingestion pipeline
│   ├─ schemas.py             # Strict Pydantic models for request payloads
│   │
│   ├─ routes/                # API Endpoints
│   │   ├─ submit.py          # /submit - Declaration uploads
│   │   ├─ summary.py         # /summary - Reconciliation logic & custom HTTP 404s
│   │   └─ ask.py             # /ask - Grounded compliance question answering
│   │
│   └─ services/              # Core business layers
│       ├─ llm.py             # Google GenAI SDK (gemini-2.5-flash-lite) interface
│       ├─ rag.py             # SentenceTransformers embedding generation & Qdrant search
│       └─ reconciliation.py  # Tolerance comparison and mismatch flagging
│
└─ frontend/                  # Modern frontend assets
    ├─ index.html             # Premium glassmorphic structure
    ├─ index.css              # Custom harmonized dark-mode styles
    └─ app.js                 # Event listeners, typewriters, & API bindings
```

### 🛠️ Tech Stack

* **Backend**: FastAPI, Python 3.10+, Uvicorn (async execution engine)
* **Databases**: MongoDB (declaration storage), Qdrant (vector storage)
* **AI & LLM**: Google GenAI SDK (`gemini-2.5-flash-lite` for expert compliance summaries and answers)
* **Embeddings & PDF Parsing**: SentenceTransformers (`all-MiniLM-L6-v2` generating 384-dimensional dense vectors), PyPDF
* **Data Processing**: Pandas (ERP alignment and database fallback resolution)
* **Frontend**: Responsive Vanilla HTML5, CSS3, & Modern JavaScript (Default Dark Mode, Custom Glassmorphism, Micro-animations)

---

## 🔧 Prerequisites & Local Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/technopradyumn/GreenPack-EPR-System.git
cd "Greenpack EPR System"
```

### 2️⃣ Environment Configuration
Create a `.env` file in the project root:
```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=greenpack

QDRANT_HOST=localhost
QDRANT_PORT=6333

GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3️⃣ Start Database Services
You can run MongoDB locally, or orchestrate Qdrant instantly using Docker:
```bash
docker-compose up -d
```

### 4️⃣ Set Up Python Virtual Environment
```bash
python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 5️⃣ Run Vector Ingestion Pipeline
Place your official compliance PDFs inside `data/docs/` and run the vectorizer pipeline. This parses the files, generates 384D cosine-metric vectors using `SentenceTransformers`, and inserts them into Qdrant:
```bash
python -m app.ingest
```

### 6️⃣ Run the Application
Start the FastAPI backend server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🧪 Core API Endpoints

### 📥 1. Submit Declaration
* **Endpoint**: `POST /submit`
* **Purpose**: Accepts and stores monthly plastic packaging weights in MongoDB.
* **Payload**:
  ```json
  {
    "producer_id": "GREENPACK-001",
    "month": "2026-04",
    "declared_quantities_kg": {
      "rigid_plastic": 5877,
      "flexible_plastic": 6767,
      "multilayer_plastic": 65765
    }
  }
  ```

### 📊 2. Reconciliation Summary
* **Endpoint**: `GET /summary/{producer_id}/{month}`
* **Purpose**: Reconciles MongoDB declaration records against ERP procurement. First checks `data/erp_feed.csv`; falls back to MongoDB's `erp_data` collection if empty or missing.
* **Response Statuses & Errors**:
  * **200 OK**: Return reconciliation JSON and Gemini-generated compliance narrative.
  * **404 Not Found (Missing Declaration)**: Returns:
    ```json
    { "detail": "Data is not declared by company" }
    ```
  * **404 Not Found (Missing ERP Logs)**: Returns:
    ```json
    { "detail": "Data is not available" }
    ```

### 🤖 3. RAG Compliance AI Assistant
* **Endpoint**: `POST /ask`
* **Purpose**: Answers complex EPR questions strictly using vectorized document context. If answer context is absent, returns exactly: `"I do not know based on the provided documents"`.
* **Payload**:
  ```json
  { "question": "What is the mismatch limit for rigid plastic?" }
  ```

---

## 🖥️ Frontend & UI Experience

* **Submit Declaration Screen**: Instantly inputs rigid, flexible, and multilayer weights with strict visual validation and outputs a receipt block containing record IDs and UTC timestamps on success.
* **Reconciliation Screen**: Highlights category discrepancies visually. Green tags mark compliant records within the **5% limit**, while vibrant red tags flag category mismatch issues.
* **RAG Assistant**: Renders a dark, glassmorphic interactive assistant featuring typewriter micro-animations and toggling source citation widgets showing files and page numbers.
* **Responsive Styling**: Crafted using vanilla HSL CSS, Jakarta Sans typography, sleek card borders, and custom background blurs for a high-end application experience.

---

## 🤝 Code Guidelines & Standards

1. **No-Comment Standard**: Keep modified JS, Python, HTML, and CSS files completely free of inline or block comments. Essential, structural docstrings in Python functions are permitted.
2. **FastAPI reload-watch**: Ensure any route changes align with settings schema definitions in `app/config.py`.

---

*Stay compliant and keep packaging sustainable!*