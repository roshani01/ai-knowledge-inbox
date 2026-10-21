# TRADEOFFS.md — Architectural Tradeoffs & Engineering Decisions

This document evaluates the key architectural tradeoffs, component choices, retrieval limitations, scaling characteristics, and future production enhancements for **AI Knowledge Inbox**.

---

## 1. Technology Selection Rationale

### A. PostgreSQL + pgvector vs Dedicated Vector Databases (Pinecone, Qdrant, Milvus)
* **Choice**: PostgreSQL with `pgvector` extension.
* **Why**:
  - **Single Source of Truth**: Eliminates the distributed dual-write consistency problem where metadata lives in a relational DB and vectors live in a separate vector service. In PostgreSQL, chunks, parent documents, indexing statuses, and embeddings live in the same ACID transaction.
  - **Relational Joins**: When retrieving top chunks, we execute a single SQL query with an inner join to fetch chunk content, parent item titles, source types, and URLs simultaneously, avoiding N+1 HTTP calls.
  - **Cost & Operational Simplicity**: Avoids recurring SaaS fees or managing separate vector database clusters for a developer assessment or early-stage product.
* **Tradeoff**: Specialized vector engines (such as Qdrant or Milvus) offer advanced HNSW filtering features and cluster auto-sharding out-of-the-box. For PostgreSQL, scaling to tens of millions of vectors requires fine-tuning `work_mem`, `maintenance_work_mem`, and table partitioning.

### B. Chunking Strategy: Recursive Character Splitting (~500 tokens / 80 overlap)
* **Choice**: Recursive semantic boundary chunker approximating ~500 tokens (~2,000 characters) with ~80 tokens (~320 characters) overlap.
* **Why**:
  - **Boundary Preservation**: Splitting by paragraphs (`\n\n`), sentences (`. `), and words prevents mid-sentence fragmentation that degrades embedding quality.
  - **Optimal Context Window vs Granularity**: 500 tokens is long enough to preserve sufficient context around a concept while remaining granular enough that top-5 retrieval fits comfortably within small context windows without overwhelming LLM attention.
  - **Overlap Cushion**: 80 tokens of overlap prevents key ideas spanning chunk boundaries from being lost during semantic search.
* **Tradeoff**: Fixed-size chunking does not understand hierarchical document structure (e.g., markdown tables, nested JSON, code blocks). Advanced production chunking would benefit from layout-aware AST parsers.

### C. AI Models: `text-embedding-3-small` & `gpt-4o-mini`
* **Choice**:
  - Embeddings: OpenAI `text-embedding-3-small` (1536 dimensions).
  - Completion: OpenAI `gpt-4o-mini`.
* **Why**:
  - `text-embedding-3-small` offers state-of-the-art multilingual semantic performance at a fraction of the cost of previous models (`text-embedding-ada-002`), with low latency.
  - `gpt-4o-mini` is extremely cost-effective, fast, and adheres reliably to system instructions regarding negative constraints ("answer only from context, declare insufficient information").
* **Tradeoff**: Dependency on proprietary APIs. For strict on-premise compliance, open-source models (e.g., `bge-small-en-v1.5` and `llama-3.2-3b`) could be run locally via Ollama or vLLM.

---

## 2. Limitations of Cosine Similarity Retrieval

Pure cosine similarity on dense embeddings has well-documented limitations:
1. **Keyword & Exact Match Blind Spots**: Dense embeddings excel at semantic similarity ("onboarding procedures" matches "new hire orientation"), but struggle with exact alphanumeric strings, serial numbers, specific error codes, or function names.
2. **Loss of Global Document Context**: Each chunk is evaluated independently; the vector similarity score does not capture where the chunk was situated within a multi-page document or section outline.
3. **Threshold Ambiguity**: Cosine similarity values fluctuate based on query length and vocabulary density. A fixed similarity threshold can either exclude valid answers or permit irrelevant noise.
4. **Resolution Strategy in Production**: Implement **Hybrid Search** (combining PostgreSQL full-text search `tsvector`/`tsquery` via BM25 with `pgvector` dense search using Reciprocal Rank Fusion) followed by a Cross-Encoder Re-ranker (e.g., Cohere Rerank or BGE Reranker).

---

## 3. Scalability & Growth Profile

| Metric | Current Behavior (MVP) | Behavior at 100K Items | Production Scaling Strategy |
| :--- | :--- | :--- | :--- |
| **Ingestion Latency** | Synchronous (wait for HTTP fetch + OpenAI embeddings) | Thread exhaustion if many simultaneous large URLs | Async task queues (Celery/ARQ with Redis) & Webhooks |
| **Vector Search** | In-memory HNSW index via pgvector (`<=>`) | Sub-10ms latency with index | Partitioning tables by user/workspace + tuned `hnsw.ef_search` |
| **Storage Footprint** | ~6 KB per chunk (1536 floats * 4 bytes + text) | ~600 MB for 100,000 chunks | Half-precision (`halfvec`) or vector quantization (IVFFlat/scalar quantization) |
| **Database Connections** | SQLAlchemy async pool (pool_size=5) | Connection starvation | PgBouncer connection pooler in transaction mode |

---

## 4. Production Improvements Roadmap

If transitioning this MVP into an enterprise production deployment, the following enhancements should be prioritized:

1. **Background Job Workers (Asynchronous Ingestion)**:
   - Offload URL fetching, BeautifulSoup parsing, and batch embedding generation to background workers (e.g., Celery, Temporal, or ARQ).
   - Ingestion API immediately returns a 202 Accepted status with a job ID, and the client polls or listens to WebSocket/Server-Sent Events (SSE) for completion.

2. **Retry Mechanisms & Exponential Backoff**:
   - Implement exponential backoff with jitter on HTTP page fetches and OpenAI API calls to survive transient network partitions and rate limits.

3. **Multi-Tenancy & Authentication**:
   - Add user authentication (OAuth2 / JWT via Supabase Auth, Clerk, or FastAPI Users).
   - Enforce Row-Level Security (RLS) in PostgreSQL so users can never search or view each other's knowledge items.

4. **Semantic Caching**:
   - Cache frequently asked questions and high-confidence answers using Redis to avoid repeated LLM completion costs.

5. **Observability & Evaluation**:
   - Integrate OpenTelemetry tracing and structured metrics (Prometheus/Grafana).
   - Use RAG evaluation frameworks (RAGAS or TruLens) to continuously evaluate Faithfulness, Answer Relevance, and Context Recall.

---

## 5. Deliberate Exclusions for the MVP

To maintain a clean, high-quality, understandable implementation realistic for a 6–12 hour technical assessment without overengineering:
- **No Heavy Distributed Orchestration**: Kept API ingestion straightforward and atomic with explicit transactions and status states rather than spinning up Redis, Celery, and message queues.
- **No Unnecessary State Libraries**: Used standard React hooks (`useState`, `useEffect`, `useCallback`) in Next.js instead of Redux or Zustand, keeping frontend state predictable and lightweight.
- **Unified Backend Monolith**: Packaged the API, extraction, vector search, and RAG into a clean modular service structure rather than microservices.
- **Dialect Abstraction**: Implemented an automated SQLite fallback type in addition to first-class PostgreSQL + pgvector so tests can run instantly and reliably in any local developer environment.
