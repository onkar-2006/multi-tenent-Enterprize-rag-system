# Unified Multi-Tenant Agentic RAG Gateway

This repository contains the production-grade **Unified Multi-Tenant Agentic RAG (Retrieval-Augmented Generation) Gateway**. Built using **FastAPI**, **LangGraph**, and **PostgreSQL (pgvector + BM25 Hybrid)**, it provides a single unified serving API for 4 distinct enterprise portals (Customer Support, Sales, HR, and IT Helpdesk) with strict tenant-level boundaries, real-time token streaming, and conversation memory.

---

## 🏗️ System Architecture

The following diagram illustrates the flow of a multi-tenant query through the security gateway, hybrid retriever, agentic routing loop, and SSE streaming pipeline:

```mermaid
graph TD
    %% Portals and Security Gateway
    Portal["Enterprise Portals<br/>HR / IT / Support / Sales"] -->|"Post Message + JWT"| API["FastAPI security.py Gateway"]
    API -->|"Verify Signature & Claims"| Context["Authorize UserContext<br/>scope: hr / role: employee"]
    
    %% Graph State Initialization
    Context -->|"Initialize State & thread_id"| State["AgentState Graph State"]
    
    %% LangGraph Routing Engine
    State -->|"astream stream_mode='messages'"| RetrieveNode["Execute Retrieve Node<br/>nodes.py"]
    
    %% Scoped Hybrid Retrieval
    RetrieveNode -->|"Keyword Search"| BM25["Local Sparse BM25 Index"]
    RetrieveNode -->|"Dense Search"| PgVector["pgvector Cosine Similarity"]
    
    BM25 -->|"Candidate Docs"| RRF["Reciprocal Rank Fusion RRF"]
    PgVector -->|"Candidate Docs"| RRF
    RRF -->|"Rank Fusion & Filter"| RetDocs["Top 5 Scoped Documents"]
    
    %% Grading & Generation
    RetDocs -->|"Grade Context Relevance"| Grader["Relevance Grader<br/>Groq Llama-3.3"]
    Grader -->|"Relevant: Skip Rewriter"| Generator["Generate Node<br/>Dynamic Tools & Memory Saver Checkpointer"]
    Grader -->|"Irrelevant: One-pass Search Bypass"| Generator
    
    %% Dynamic Tool Execution
    Generator -->|"Determine Action"| Actions["LLM Decision"]
    Actions -->|"Call Tool: e.g. request_pto"| ToolNode["Tool Node<br/>tools.py"]
    ToolNode -->|"ToolMessage Output"| Generator
    
    %% Hallucination & Self-Correction
    Actions -->|"Synthesize Final Text"| HGrader["Hallucination Grader"]
    HGrader -->|"Grounded"| FinalResponse["Final Structured Response"]
    HGrader -->|"Not Grounded: Self-Correct"| Generator
    
    %% SSE Streaming Output
    FinalResponse -->|"Yield Tokens Chunks"| Stream["SSE Event Stream<br/>/api/chat/stream"]
    Stream -->|"Close Stream"| Client["Stream Completed"]
    
    %% Checkpointer Memory Loop
    FinalResponse -->|"Persist Thread History"| Memory["MemorySaver Checkpointer"]
```

### 📂 Directory Structure
```
multi-tenant_rag/
├── .gitignore                            # Excludes credentials (.env), venv, node_modules
├── README.md                             # Comprehensive system architecture documentation
├── backend/
│   └── enterprise-ai-engine/
│       ├── app/
│       │   ├── api/
│       │   │   ├── dependencies.py       # JWT scope validation dependency
│       │   │   └── router.py             # Chat & SSE Streaming API endpoints
│       │   ├── core/
│       │   │   ├── config.py             # Pydantic Settings management
│       │   │   ├── embeddings.py         # OpenRouter Qwen3 Embedding client
│       │   │   └── security.py           # JWT generation/decoding module
│       │   ├── db/
│       │   │   ├── hybrid_retriever.py   # BM25 + pgvector RRF hybrid retriever
│       │   │   └── pgvector_client.py    # PostgreSQL connection pooler (pre-warmed)
│       │   ├── graph/
│       │   │   ├── nodes.py              # LangGraph workflow nodes
│       │   │   ├── state.py              # State schema definitions
│       │   │   ├── tools.py              # Dynamic, scope-authorized tools
│       │   │   └── workflow.py           # StateGraph workflow compilation
│       │   └── main.py                   # FastAPI server entry point
│       ├── documents/                    # Enterprise document PDFs
│       ├── scripts/
│       │   └── ingest_documents.py       # Batch vector/BM25 ingestion pipeline
│       └── Requirements.txt              # Backend package list
└── frontend/                             # Standalone 4-Portal React Suite (Vite + React Router)
    ├── src/
    │   ├── components/                   # Header, ChatInterface, CitationCards
    │   ├── pages/                        # LaunchpadPage, HR, IT, Support, Sales
    │   └── config/                       # Portal definitions & tokens
    └── package.json                      # Frontend dependencies
```

---

## 🛡️ Core Features

1. **JWT-Scoped Context Injection:** A centralized gateway decodes secure JSON Web Tokens to inject tenant `scope` and `role` claims, restricting data access to authorized boundaries.
2. **Double-Decker Hybrid Retrieval:** Fuses sparse (BM25) and dense (pgvector Cosine distance) retrieval scoring using Reciprocal Rank Fusion (RRF).
3. **One-Pass Query & Bypass Routing:** Prevents infinite loop latency by enforcing a maximum of one search query execution per request, routing simple conversational greetings directly to generation nodes.
4. **Self-Correcting Hallucination Loop:** Integrates reflection nodes checking LLM generations against retrieved facts, prompting dynamic correction loops before releasing outputs.
5. **Connection Pool Pre-Warming:** Bypasses PgBouncer transaction-mode prepared statement blocks by pre-registering pgvector OIDs (`SELECT '[0.0]'::vector;`) during pool setup.
6. **Thread-Level Isolated Memory:** Compiles states with LangGraph's `MemorySaver` checkpointer, persisting dialogue boundaries per `thread_id`.
7. **Native Event Streaming:** Leverages FastAPI's `StreamingResponse` and LangGraph's `stream_mode="messages"` to stream token chunks in real-time.

---

## 🚀 Setup & Execution

### 1. Configure the Environment
Navigate to the engine directory and create a `.env` file:
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
EMBEDDING_MODEL="qwen/qwen-vl-plus:free"
EMBEDDING_DIMENSION=1536
GROQ_MODEL="llama-3.3-70b-versatile"
JWT_SECRET_KEY="ApexTech-RAG-Serving-SecretKey-For-JWTokens"
```

### 2. Install Dependencies
Ensure your python virtual environment is active:
```bash
..\venv\Scripts\activate
pip install -r Requirements.txt
```

### 3. Ingest Documents
Batch upload pdfs into your Supabase Postgres vector store:
```bash
python scripts/ingest_documents.py
```

### 4. Run the FastAPI Server
Start the Uvicorn serving engine:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
On boot, the server logs pre-signed developer JWT tokens for each of the 4 portal roles (HR, IT, Support, Sales) to ease local validation.

---

## 🧪 API Validation & Streaming Verification

### Chat Endpoint
* **Endpoint:** `POST /api/chat`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Payload:**
  ```json
  {
    "message": "What is the PTO policy?",
    "thread_id": "thread-alice-123"
  }
  ```

### Real-Time Streaming Endpoint
* **Endpoint:** `POST /api/chat/stream`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Payload:**
  ```json
  {
    "message": "What is the PTO policy?",
    "thread_id": "thread-alice-123"
  }
  ```
* **Response Format:** Server-Sent Events (`text/event-stream`). Streams text tokens matching `data: {"token": "..."}` and returns sources in the final block matching `data: {"references": [...]}`.
