# Unified Multi-Tenant Agentic RAG Gateway

This repository contains the production-grade **Unified Multi-Tenant Agentic RAG (Retrieval-Augmented Generation) Gateway**. Built using **FastAPI**, **LangGraph**, **PostgreSQL (pgvector + BM25 Hybrid)**, and a **Vite + React Frontend Suite**, it provides a single unified serving API for 4 distinct enterprise portals (Customer Support, Sales, HR, and IT Helpdesk) with strict tenant-level boundaries, zero-shot LLM intent routing, automatic model failovers, real-time token streaming, and an executive dual-theme UI (Light Porcelain & Dark Obsidian).

---

## 🏗️ System Architecture

The following diagram illustrates the flow of a multi-tenant query through the security gateway, zero-shot intent classifier node, hybrid retriever, agentic self-correction loop, and real-time SSE streaming pipeline:

```mermaid
graph TD
    %% Portals and Security Gateway
    Portal["Enterprise Client Portals<br/>(HR / IT / Support / Sales)"] -->|"Post Message + Bearer JWT"| API["FastAPI security.py Gateway"]
    API -->|"Verify Signature & Claims"| Context["Authorize UserContext<br/>scope: hr / role: employee"]
    
    %% Graph State & Intent Classifier Node
    Context -->|"Initialize State & thread_id"| State["AgentState Graph State"]
    State -->|"Entry Point"| IntentClassifier["Zero-Shot Intent Classifier Node<br/>ChatGroq.with_structured_output(QueryIntent)"]
    
    %% Intent Routing Branching
    IntentClassifier -->|"conversational: 'hi', 'who are you'"| Generator["Generate Node<br/>Fast LLM Response (< 0.4s)"]
    IntentClassifier -->|"domain_query: 'PTO Policy'"| RetrieveNode["Execute Hybrid Retrieve Node<br/>app/db/hybrid_retriever.py"]
    
    %% Scoped Hybrid Retrieval
    RetrieveNode -->|"Keyword Search"| BM25["Local Sparse BM25 Index"]
    RetrieveNode -->|"Dense Search"| PgVector["pgvector Cosine Similarity"]
    
    BM25 -->|"Candidate Chunks"| RRF["Reciprocal Rank Fusion (RRF)"]
    PgVector -->|"Candidate Chunks"| RRF
    RRF -->|"Rank Fusion & Scope Normalization"| RetDocs["Top 5 Scoped Documents"]
    
    %% Self-Correction & Grading
    RetDocs -->|"Grade Context Relevance"| Grader["Relevance Grader Node<br/>Groq Llama-3.1 Fallback Chain"]
    Grader -->|"Relevant / One-Pass Optimization"| Generator
    
    %% Hallucination & Self-Correction
    Generator -->|"Synthesize Final Text"| HGrader["Hallucination Grader Node"]
    HGrader -->|"Grounded"| FinalResponse["Final Structured Response"]
    HGrader -->|"Not Grounded: Self-Correct"| Generator
    
    %% SSE Streaming Output
    FinalResponse -->|"Yield Tokens Chunks"| Stream["SSE Event Stream<br/>/api/chat/stream"]
    Stream -->|"Close Stream"| Client["Stream Completed"]
    
    %% Checkpointer Memory Loop
    FinalResponse -->|"Persist Thread History"| Memory["MemorySaver Checkpointer"]
```

---

## 📂 Directory Structure

```
multi-tenant_rag/
├── .gitignore                            # Excludes credentials (.env), venv, node_modules
├── README.md                             # System architecture & setup guide
├── backend/
│   └── enterprise-ai-engine/
│       ├── app/
│       │   ├── api/
│       │   │   ├── dependencies.py       # JWT scope validation dependency
│       │   │   └── router.py             # Chat & SSE Streaming API endpoints
│       │   ├── core/
│       │   │   ├── config.py             # Settings & environment variables
│       │   │   ├── embeddings.py         # OpenRouter embedding client + httpx pooling & cache
│       │   │   └── security.py           # JWT generation/decoding module
│       │   ├── db/
│       │   │   ├── hybrid_retriever.py   # BM25 + pgvector RRF hybrid retriever + timeout fallback
│       │   │   └── pgvector_client.py    # PostgreSQL connection pooler (pre-warmed)
│       │   ├── graph/
│       │   │   ├── nodes.py              # Zero-shot intent classifier & LangGraph nodes
│       │   │   ├── state.py              # State schema definitions (intent, messages)
│       │   │   ├── tools.py              # Dynamic, scope-authorized tools
│       │   │   └── workflow.py           # StateGraph compilation & intent routing edges
│       │   └── main.py                   # FastAPI server entry point
│       ├── documents/                    # Enterprise document PDFs
│       ├── scripts/
│       │   └── ingest_documents.py       # Batch vector/BM25 ingestion pipeline
│       └── Requirements.txt              # Backend package list
└── frontend/                             # Standalone 4-Portal Executive React Suite (Vite + React Router)
    ├── src/
    │   ├── components/                   # Header, ChatInterface, CitationCards (Dual Theme)
    │   ├── pages/                        # LaunchpadPage, HR, IT, Support, Sales
    │   ├── config/                       # Portal definitions & pre-signed JWT tokens
    │   └── index.css                     # Porcelain Light & Obsidian Dark executive design system
    └── package.json                      # Frontend dependencies
```

---

## 🛡️ Core Features

1. **JWT-Scoped Context Scoping:** A centralized security gateway decodes JSON Web Tokens to inject tenant `scope` and `role` claims, ensuring strict isolation and preventing cross-tenant data leakage.
2. **Zero-Shot LLM Intent Routing:** Classifies user intent prior to search. Conversational queries bypass document vector retrieval entirely, executing direct responses in **< 0.4s**.
3. **Automatic Model Failover Chain:** Built-in Groq model fallback (`llama-3.1-8b-instant` $\rightarrow$ `llama3-8b-8192`) handles rate limits (HTTP 429) automatically with zero downtime.
4. **Hybrid RRF Retrieval & BM25 Fallback:** Fuses sparse (BM25) and dense (`openai/text-embedding-3-small` / OpenRouter) retrieval scoring using Reciprocal Rank Fusion. Includes a 1.2s timeout fallback to local BM25.
5. **Self-Correcting Agentic Loop:** Enforces document relevance grading and hallucination detection to eliminate unsupported LLM claims before streaming.
6. **Executive Dual Theme UI:** Features an executive Porcelain Light (`#f8f6f0`) and Deep Obsidian Dark theme with rounded pill buttons, curved chat bubbles, and persistent `localStorage` theme toggling.
7. **Native Event Streaming:** Leverages FastAPI's `StreamingResponse` and SSE events to stream real-time tokens directly to the client UI.

---

## 🚀 Setup & Execution

### 1. Configure the Environment
Navigate to the engine directory and configure the `.env` file:
```bash
cd backend/enterprise-ai-engine
```

Add your credentials inside `.env`:
```env
# Server Configuration
APP_NAME="Enterprise AI Engine"

# PostgreSQL Database (Supabase pooler URL)
DATABASE_URL="postgresql://postgres.your_user:your_password@your_host.supabase.com:5432/postgres"

# API Keys
OPENROUTER_API_KEY="sk-or-v1-your-openrouter-api-key-here"
GROQ_API_KEY="gsk_your_groq_api_key_here"

# Model Configuration
EMBEDDING_MODEL="openai/text-embedding-3-small"
EMBEDDING_DIMENSION=1536
GROQ_MODEL="llama-3.1-8b-instant"
JWT_SECRET_KEY="ApexTech-RAG-Serving-SecretKey-For-JWTokens"
```

### 2. Install Dependencies & Run Backend
Activate your Python virtual environment and launch FastAPI:
```bash
..\venv\Scripts\activate
pip install -r Requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Run Frontend Client
In a separate terminal, navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) to access the portal suite!

---

## 🧪 API Endpoints

### 1. Real-Time Streaming Chat Endpoint
* **Endpoint:** `POST /api/chat/stream`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Payload:**
  ```json
  {
    "message": "What is the PTO policy?",
    "thread_id": "thread-hr-1024"
  }
  ```
* **Response:** Server-Sent Events (`text/event-stream`). Streams JSON tokens `{"token": "..."}` and emits retrieved source citations in the final frame `{"references": [...]}`.
