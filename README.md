# 🌟 GreenPack EPR System

---

## ⭐️ Situation

*The world is moving towards stricter **Extended Producer Responsibility (EPR)** regulations for plastic packaging. Companies need an easy‑to‑use dashboard to reconcile their monthly plastic declarations with ERP procurement data and get AI‑driven compliance assistance.*

---

## 🎯 Task

*Provide a **single‑page FastAPI backend** and a **modern vanilla‑JS/HTML frontend** that:

- Accepts monthly plastic declarations (`/submit`).
- Summarises reconciliation results (`/summary/{producer_id}/{month}`).
- Offers an **AI assistant** (`/ask`) that answers compliance questions **grounded only on uploaded documents**.
- Shows a clean UI without any leftover comment noise or “Recommended Questions” sidebar.

---

## 🚀 Action

### 1️⃣ Clone & Prepare the Project
```bash
# Clone (if you haven’t already)
git clone https://github.com/technopradyumn/GreenPack-EPR-System.git
cd "Greenpack EPR System"
```

### 2️⃣ Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Run the API Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The server will be reachable at `http://127.0.0.1:8000`.

### 4️⃣ Open the Front‑end
Open `frontend/index.html` in a browser (or serve it via a simple HTTP server for CORS‑free operation):
```bash
# from the project root
python -m http.server 3000 --directory frontend
# then visit http://localhost:3000
```

---

## 🛠️ Local Ollama LLM Integration
The AI assistant currently calls a remote LLM endpoint defined in **`app/services/llm.py`**:
```python
# app/services/llm.py
def generate_text(prompt: str) -> str:
    # Default uses OpenAI/Ollama remote host
    response = requests.post(
        "http://localhost:11434/api/generate",  # <-- change this URL for your Ollama server
        json={"model": "gemma:2b", "prompt": prompt},
    )
    return response.json()["response"]
```
### How to switch to a locally‑running Ollama model
1. **Start Ollama** (install from https://ollama.com):
```bash
ollama serve   # runs on http://localhost:11434 by default
ollama pull llama2   # or any model you prefer
```
2. **Edit the URL / model name** in `app/services/llm.py` to match your local model, e.g.:
```python
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama2", "prompt": prompt},
)
```
3. Restart the FastAPI server – the assistant will now answer using the **local Ollama model**.

---

## 📖 Usage Guide
| Feature | How to Use |
| ------- | ---------- |
| **Submit Declaration** | Fill the form under **“Submit Declaration”**, hit **Submit** – the UI will display a receipt with the record ID.
| **Reconciliation** | Choose **“Reconciliation”**, provide *Producer ID* and *Month*, click **Run Reconciliation** – you’ll see compliance cards and an AI‑generated narrative.
| **AI Assistant** | Switch to the **“Compliance AI Assistant”** tab, type a question (e.g., *“What is the tolerance for flexible plastic?”*), and press **Enter** – the answer is grounded in the uploaded documents only.
| **Reset Forms** | Click **“Submit Another Declaration”** or navigate back via the sidebar.

---

## 🧪 Testing & Validation
```bash
# Simple sanity check – ensure the API is reachable
default_url="http://127.0.0.1:8000"
python - <<PY
import requests
print(requests.get(f"{default_url}/health").status_code)
PY
```
You can also run the built‑in FastAPI docs at `http://127.0.0.1:8000/docs` to explore the OpenAPI schema.

---

## 📂 Project Structure
```
Greenpack EPR System/
│   README.md          # <-- this file
│   requirements.txt
│   docker-compose.yml
│
├─ app/                # FastAPI backend
│   ├─ main.py
│   ├─ routes/          # API endpoints (ask, submit, summary)
│   ├─ services/        # LLM & RAG helpers
│   └─ schemas.py
│
└─ frontend/           # Vanilla HTML/JS UI
    ├─ index.html
    ├─ index.css
    └─ app.js
```

---

## 🤝 Contributing
1. Fork the repo.
2. Create a feature branch.
3. Run the comment‑stripping script (`strip_comments_and_ui.py`) if you add new files – it will keep the codebase clean.
4. Submit a pull request.

---

## 📜 License
This project is licensed under the **MIT License**.

---

*Happy coding and stay compliant!*