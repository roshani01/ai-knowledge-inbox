# AI Knowledge Inbox

> A production-minded full-stack application that saves plain-text notes and web URLs, chunks content into semantic segments, indexes vectors using PostgreSQL and **pgvector**, and provides grounded question answering with verifiable source citations.

---

## 1. Project Overview & Features

**AI Knowledge Inbox** allows knowledge workers and engineering teams to ingest unstructured text and web documentation into a unified repository, index content using high-dimensional vector embeddings, and query it in natural language.

### Core Capabilities
1. **Multi-Source Ingestion (`POST /ingest`)**:
   - **Text Notes**: Ingest plain text notes with client and server-side length validation.
   - **Web URLs**: Fetch web pages on the backend with strict **Server-Side Request Forgery (SSRF)** protection, stripping HTML noise (scripts, styles, navs) via BeautifulSoup.
2. **Recursive Semantic Chunking**:
   - Boundary-aware text splitter that splits on paragraphs, sentences, and words (~500 tokens target with ~80 tokens overlap).
   - Handles short notes without unnecessary fragmentation and long documents without exceeding embedding limits.
3. **Vector Embeddings & PostgreSQL pgvector**:
   - Employs OpenAI's `text-embedding-3-small` (1536 dimensions).
   - Stores vectors in PostgreSQL with `pgvector` HNSW cosine distance indexing (`<=>`).
   - Includes transparent SQLite dialect support for isolated automated tests without external database dependencies.
4. **Grounded Question Answering (`POST /query`)**:
   - Top-5 vector similarity retrieval based on cosine distance.
   - Instructs `gpt-4o-mini` to answer **strictly and exclusively** from retrieved context.
   - Transparently handles insufficient context (honest disclaimer when evidence is lacking).
5. **Verifiable Citations**:
   - Every answer returns citations linking directly to parent items, chunk IDs, source URLs, similarity percentages, and text snippets.
6. **Modern Reactive UI**:
   - Next.js App Router, React 19, TypeScript, and Tailwind CSS.
   - Live backend health monitoring, segmented ingestion forms, card-based inbox browser, and interactive Q&A interface.

---

## 2. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | Next.js (App Router), React 19, TypeScript, Tailwind CSS | Modular components, Lucide icons, responsive dark-mode UI |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic v2 | Async ASGI service with centralized error handlers and CORS |
| **Extraction** | HTTPX, BeautifulSoup4 | Asynchronous SSRF-safe URL extraction and HTML sanitization |
| **Database** | PostgreSQL 16+ & pgvector (or SQLite for lightweight tests) | Hybrid relational & vector storage with HNSW cosine index |
| **AI / Embeddings** | OpenAI Python SDK | `text-embedding-3-small` (1536d) & `gpt-4o-mini` |
| **Testing** | pytest, pytest-asyncio, HTTPX AsyncClient | 100% mocked offline automated test suite |

---

## 3. Repository Structure

```
ai-knowledge-inbox/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py        # GET /health
│   │   │       ├── ingest.py        # POST /ingest
│   │   │       ├── items.py         # GET /items
│   │   │       └── query.py         # POST /query
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings
│   │   │   ├── errors.py            # Custom exceptions & handlers
│   │   │   └── logging.py           # Structured logging
│   │   ├── db/
│   │   │   ├── base.py              # DeclarativeBase
│   │   │   └── session.py           # Async engine & pgvector init
│   │   ├── models/
│   │   │   └── knowledge.py         # KnowledgeItem & KnowledgeChunk models
│   │   ├── schemas/
│   │   │   ├── ingest.py            # Request/response validation
│   │   │   ├── items.py             # Item listing schemas
│   │   │   └── query.py             # RAG question & citation schemas
│   │   ├── services/
│   │   │   ├── chunker.py           # Recursive text chunking
│   │   │   ├── embedder.py          # Batched OpenAI embeddings
│   │   │   ├── ingestion_service.py # Ingestion orchestrator & transactions
│   │   │   ├── rag.py               # RAG completion & citations
│   │   │   ├── url_extractor.py     # SSRF-protected webpage extractor
│   │   │   └── vector_search.py     # Cosine vector similarity retrieval
│   │   └── main.py                  # FastAPI entry point & lifespan
│   ├── tests/
│   │   ├── conftest.py              # Test database & mock fixtures
│   │   ├── test_chunker.py          # Chunker unit tests
│   │   ├── test_embedder.py         # Embedding validation tests
│   │   ├── test_health.py           # Health endpoint integration test
│   │   ├── test_ingest.py           # Ingestion, validation & SSRF tests
│   │   ├── test_items.py            # Items listing & ordering tests
│   │   ├── test_query.py            # Grounded RAG & citation tests
│   │   └── test_url_extractor.py    # SSRF & HTML extraction tests
│   ├── requirements.txt             # Python backend dependencies
│   ├── .env.example                 # Backend environment variable template
│   └── pytest.ini                   # Pytest test runner configuration
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # Root HTML shell & dark theme
│   │   ├── page.tsx                 # Main dashboard view
│   │   └── globals.css              # Tailwind CSS styles
│   ├── components/
│   │   ├── AddKnowledgeCard.tsx     # Note & URL ingestion forms
│   │   ├── AskKnowledgeSection.tsx  # Natural language Q&A & citations
│   │   ├── Navbar.tsx               # Branding & backend health indicator
│   │   └── SavedKnowledgeList.tsx   # Saved knowledge cards & preview
│   ├── lib/
│   │   └── api.ts                   # Typed API client
│   ├── types/
│   │   └── index.ts                 # TypeScript domain interfaces
│   ├── package.json                 # Next.js & dependencies
│   └── .env.example                 # Frontend environment template
├── DESIGN.md                        # Architecture & technical design
├── TRADEOFFS.md                     # Engineering tradeoffs & scaling analysis
├── .gitignore                       # Clean ignores for Python, Node, & secrets
└── README.md                        # Documentation & setup guide
```

---

## 4. Prerequisites

- **Python**: Version 3.10+ (tested on Python 3.14).
- **Node.js**: Version 18+ (tested on Node v24).
- **PostgreSQL**: Version 15+ with the `pgvector` extension enabled (or Docker).
  *(Note: For rapid local evaluation or automated testing without PostgreSQL, SQLite is supported out-of-the-box via `DATABASE_URL=sqlite+aiosqlite:///./ai_inbox.db`).*
- **OpenAI API Key**: Required for live embeddings and grounded chat completions.

---

## 5. PostgreSQL and pgvector Setup

### Option A: Using Docker (Recommended for Local Development)
Run a pre-configured PostgreSQL container with pgvector:
```bash
docker run -d \
  --name ai-inbox-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_inbox \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Option B: Using an Existing Local PostgreSQL Instance
1. Install pgvector following the instructions at [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector).
2. Connect to your database using `psql`:
   ```sql
   CREATE DATABASE ai_inbox;
   \c ai_inbox;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
*(The backend also automatically runs `CREATE EXTENSION IF NOT EXISTS vector;` on startup).*

---

## 6. Environment Configuration

### Backend Configuration
Copy the example environment file in `backend/`:
```bash
cd backend
cp .env.example .env
```
Edit `backend/.env`:
```ini
# For PostgreSQL with pgvector:
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_inbox

# Or for lightweight local testing without PostgreSQL:
# DATABASE_URL=sqlite+aiosqlite:///./ai_inbox.db

# For Google Gemini (Active):
GEMINI_API_KEY=your-actual-gemini-api-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_EMBEDDING_MODEL=gemini-embedding-001
OPENAI_CHAT_MODEL=gemini-3.5-flash
EMBEDDING_DIMENSION=768

# Or for OpenAI:
# OPENAI_API_KEY=sk-your-actual-openai-api-key
# OPENAI_BASE_URL=
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_CHAT_MODEL=gpt-4o-mini
# EMBEDDING_DIMENSION=1536
FRONTEND_ORIGIN=http://localhost:3000
LOG_LEVEL=INFO
```

### Frontend Configuration
Copy the example environment file in `frontend/`:
```bash
cd frontend
cp .env.example .env.local
```
Edit `frontend/.env.local`:
```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 7. Installation & Startup Commands

### Backend Startup
From the project root:
```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the backend API server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will start at `http://localhost:8000`.
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

### Frontend Startup
In a separate terminal:
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies (if not already installed)
npm install

# 3. Start development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 8. Running Automated Tests

All tests are written with `pytest` and mock external OpenAI and HTTP calls so that **no paid API credits or live database instances are required**.

To run the complete test suite:
```bash
# Ensure you are at the repository root with the backend venv activated
# Set PYTHONPATH to the repo root:

# Windows PowerShell:
$env:PYTHONPATH="."
.\backend\venv\Scripts\python.exe -m pytest backend/tests

# macOS / Linux:
PYTHONPATH=. backend/venv/bin/pytest backend/tests
```

### Test Coverage Highlights
- **Health**: Database connectivity and version verification (`test_health.py`).
- **Ingestion**: Valid note creation, empty/whitespace input validation, URL ingestion with mocked HTML, timeouts, and embedding failure recovery (`test_ingest.py`).
- **Security & SSRF**: Blocked loopback (`127.0.0.1`, `::1`), private networks (`10.0.0.0/8`, `192.168.0.0/16`), cloud metadata (`169.254.169.254`), and non-HTTP schemes (`test_url_extractor.py`).
- **Chunking**: Short notes, multi-paragraph long documents, custom separators, and empty string handling (`test_chunker.py`).
- **Embeddings**: Dimension checking (ensuring 1536d output) and batching logic (`test_embedder.py`).
- **Items**: Empty inbox response and newest-first ordering (`test_items.py`).
- **Query & RAG**: Empty inbox handling, grounded answer generation, verifiable citation structure, and LLM error handling (`test_query.py`).

---

## 9. API Endpoint Reference

### 1. `POST /ingest`
Ingests a note or URL.
- **Request (Note)**:
  ```json
  {
    "source_type": "note",
    "title": "Architecture Overview",
    "content": "We use PostgreSQL and pgvector for unified storage."
  }
  ```
- **Request (URL)**:
  ```json
  {
    "source_type": "url",
    "url": "https://example.com/docs"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "id": "c0a80101-0000-0000-0000-000000000001",
    "title": "Architecture Overview",
    "source_type": "note",
    "original_url": null,
    "indexing_status": "indexed",
    "chunk_count": 1,
    "created_at": "2026-10-19T10:00:00Z",
    "message": "Knowledge item successfully ingested and indexed."
  }
  ```

### 2. `GET /items`
Lists saved knowledge items, sorted newest first.
- **Response (`200 OK`)**:
  ```json
  {
    "items": [
      {
        "id": "c0a80101-0000-0000-0000-000000000001",
        "title": "Architecture Overview",
        "source_type": "note",
        "original_url": null,
        "created_at": "2026-10-19T10:00:00Z",
        "indexing_status": "indexed",
        "error_message": null,
        "chunk_count": 1,
        "preview": "We use PostgreSQL and pgvector for unified storage."
      }
    ],
    "total": 1
  }
  ```

### 3. `POST /query`
Performs vector similarity search and answers questions strictly from retrieved context.
- **Request**:
  ```json
  {
    "question": "What database do we use?"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "question": "What database do we use?",
    "answer": "Based on your saved notes, PostgreSQL with the pgvector extension is used for storage.",
    "citations": [
      {
        "chunk_id": "d0b90202-0000-0000-0000-000000000002",
        "item_id": "c0a80101-0000-0000-0000-000000000001",
        "title": "Architecture Overview",
        "source_type": "note",
        "url": null,
        "snippet": "We use PostgreSQL and pgvector for unified storage.",
        "similarity_score": 0.942
      }
    ],
    "has_sufficient_context": true
  }
  ```

### 4. `GET /health`
Returns service status, database connectivity, and configured AI models.

---

## 10. Troubleshooting & Common Setup Issues

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **`CREATE EXTENSION vector` fails** | pgvector extension is not compiled/installed in Postgres | Install pgvector or use the `pgvector/pgvector:pg16` Docker image. Alternatively, use SQLite mode. |
| **`greenlet` import error on startup** | SQLAlchemy async requires greenlet | Run `pip install greenlet` (already included in `requirements.txt`). |
| **SSRF error when adding URL** | Target URL resolves to localhost or private IP | By design, internal network resources (e.g. `127.0.0.1`, `192.168.x.x`) are blocked for security. |
| **401 Unauthorized during Query** | `OPENAI_API_KEY` is empty or invalid | Add a valid OpenAI API key in `backend/.env`. |
| **CORS errors on frontend** | Backend `FRONTEND_ORIGIN` does not match client | Check `backend/.env` and verify `FRONTEND_ORIGIN=http://localhost:3000`. |

---

## 11. Limitations & Known Requirements

- **Synchronous Ingestion Pipeline**: Ingestion performs URL extraction and OpenAI embedding synchronously before responding. For very long web pages, request duration depends on network speed and OpenAI API latency.
- **Pure Cosine Search**: Dense vector search does not support lexical exact matches (e.g. part numbers or specific variable names). Hybrid search (BM25 + pgvector) is recommended for production.
- **Single-Tenant Scope**: The MVP assumes a single-user inbox. Multi-tenant production deployments should add JWT authentication and PostgreSQL Row-Level Security (RLS).
