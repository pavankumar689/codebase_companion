# Codebase Companion

A small, local codebase question-answering demo that indexes a Git repository, builds embeddings with Hugging Face / OpenAI-style embeddings, stores vectors in Chroma, and exposes a simple FastAPI backend with a minimal frontend UI.

This repository contains two main parts:

- `backend/` — A FastAPI backend that can clone a Git repository, load code/text files, create embeddings, persist a Chroma vector store, and provide a `/chat` endpoint to query the indexed code. It also includes a small example RAG backend under `temp_repo/meeting_rag/backend`.
- `frontend/` — A tiny static frontend (HTML/JS/CSS) that talks to the backend to analyze a repo and ask questions.

## Quick structure

- `backend/main.py` — Primary FastAPI app. Endpoints:
  - `POST /analyze` — Accepts JSON `{ "url": "<git-repo-url>" }`, clones the repo into `./temp_repo`, indexes files into `./chroma_db`.
  - `POST /chat` — Accepts JSON `{ "question": "..." }` and queries the vector DB + LLM chain to return an answer.
  - `GET /` — Health route.
- `backend/requirements.txt` — Python dependencies for the main backend.
- `backend/chroma_db/` — Example persisted Chroma DB used during development.
- `backend/temp_repo/meeting_rag/backend/` — Smaller example RAG service with `main.py`, `rag_handler.py`, and its own `requirements.txt`.
- `frontend/` — Static frontend assets: `index.html`, `script.js`, `style.css`.

## Requirements

- Python 3.10+ (recommended). Ensure pip is available.
- Node is not required to run the static frontend — it's plain HTML/JS/CSS served from the filesystem or via a simple static server.

The backend has many ML and LLM-related dependencies. See `backend/requirements.txt` for the full list. Installing these may take time and require a machine with the appropriate native build tools (for packages like `torch`, `onnxruntime`, etc.).

## Environment variables

The backend reads environment variables from a `.env` file (through `python-dotenv`). Common variables used in the code:

- `GOOGLE_API_KEY` — used by the Google GenAI integration in `backend/main.py`.
- Any other keys required by the chosen embedding/LLM provider (OpenAI keys, Hugging Face tokens, etc.) depending on which handler you use.

Create a `.env` file in the `backend/` directory like:

```
GOOGLE_API_KEY=your_google_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here
```

## Install and run (backend)

Open PowerShell and run the following commands from the repository root.

Create a virtual environment and install dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the FastAPI app (development):

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Notes:
- The `requirements.txt` includes heavy packages (transformers, torch, chromadb, etc.). If you only want to run the small example under `temp_repo/meeting_rag`, install its `requirements.txt` instead.
- If you run into permissions issues removing `temp_repo` or `chroma_db`, ensure your PowerShell session has the appropriate file permissions.

## Run the smaller example RAG backend

The repo contains a small example under `backend/temp_repo/meeting_rag/backend` intended as a simpler RAG demo. To run that service separately:

```powershell
cd backend\temp_repo\meeting_rag\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.0 --port 8000
```

This example expects a `../rag_text.txt` file next to the `backend` folder in the meeting_rag example. You can create a sample text file for testing.

## Frontend (static)

The frontend is a static set of files in `frontend/`. You can either open `frontend/index.html` directly in a browser or serve it with a simple static server.

Quick local view using Python's built-in http server (from the repository root):

```powershell
cd frontend
# Python 3.x
python -m http.server 3000

# Then open http://127.0.0.1:3000 in your browser
```

The frontend expects the backend to be available at `http://127.0.0.1:8000` (see `frontend/script.js`). If you run the backend on a different host/port, update the `BACKEND_URL` variable in `frontend/script.js`.

## Troubleshooting

- Missing packages or binary wheels: some packages (torch, onnxruntime, sentence-transformers) often need platform-specific wheels. On Windows you may need to install prebuilt wheels or use conda.
- GPU/CPU differences: model loading may require CUDA-enabled builds if you intend to use GPU acceleration.
- If you only want a lightweight setup for development, consider creating a trimmed `requirements-light.txt` that excludes heavy ML packages and uses remote APIs (OpenAI, Google GenAI) for embeddings and LLM calls.

## Security & Cost

- Indexing private repositories: this code clones arbitrary repositories — be cautious and avoid indexing private repositories unless you understand where the embeddings and documents are stored.
- LLM API usage: using OpenAI/Google/other LLM providers may incur costs. Make sure to control usage and keep API keys secret.

## Suggested next steps (optional)

- Add a lightweight Dockerfile for reproducible runs.
- Add a `requirements-lite.txt` that uses remote APIs to avoid heavy local ML installs.
- Add tests for the backend endpoints.

---

If you'd like, I can also:

- Add a minimal Dockerfile and docker-compose for easy start-up.
- Create a trimmed `requirements-lite.txt` and update the README with that workflow.
- Update the frontend to allow configuring the backend URL in the UI.

Let me know which of these you'd like next.
