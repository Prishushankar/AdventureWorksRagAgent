# AdventureWorks2022 RAG Agent

A production-grade **Text-to-SQL** conversational agent that lets you query Microsoft's AdventureWorks2022 database using plain English — or even Hinglish. Ask business questions in a Streamlit chat interface, and the agent writes the SQL, executes it, fetches the data, and explains the results in your preferred language.

---

## Features

- **Natural language to SQL** — Ask questions like *"Which bikes are basically dead stock?"* and get executable T-SQL + results.
- **Multilingual explanations** — Results are described in English, Hindi, Gujarati, or Marathi using Unicode Devanagari/Gujarati scripts.
- **Hinglish support** — Intent clarification translates Hinglish (Hindi + English mix) queries into clear English before SQL generation.
- **Self-healing retry loop** — If the generated SQL fails or returns empty results, the agent retries up to 4 times with error feedback.
- **Schema-aware retrieval** — ChromaDB vector store with query expansion, CrossEncoder reranking, and LLM escalation for low-confidence matches.
- **Live schema verification** — Pulls actual column names from the database at runtime to prevent hallucinated column references.
- **Hard schema-lock rules** — 14 enforced rules that prevent common SQL generation mistakes (wrong joins, missing filters, non-existent columns).
- **Regex fast-path templates** — Deterministic SQL templates for common queries (department headcount, leave, salary, dead stock) that bypass the LLM entirely.
- **SQL sanitization** — Strips markdown fences, hardcoded years, and dangerous `USE`/`SET NOCOUNT` statements.
- **Security blocklist** — Blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `ALTER`, `CREATE`, `EXEC` keywords.

---

## How It Works

```
User Question (any language)
        │
        ▼
┌─────────────────────┐
│  Intent Clarifier    │  LLM translates Hinglish → English
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Schema Retriever    │  ChromaDB vector search + query expansion
│                      │  + CrossEncoder reranking
│                      │  + LLM escalation on low confidence
│                      │  + Live column verification from DB
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  SQL Generator       │  Template matcher (fast path) OR
│                      │  Groq LLM with schema-lock rules
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  SQL Sanitizer       │  Strip markdown, remove hardcoded years
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  SQL Executor        │  pyodbc → SQL Server (read-only)
│                      │  Retries up to 4x with error feedback
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Result Explainer    │  LLM writes 2-3 sentence business summary
│                      │  in selected language (EN/HI/GU/MR)
└─────────┬───────────┘
          │
          ▼
   Data Table + SQL + Explanation (in Streamlit UI)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | [Groq](https://console.groq.com) — Llama 3.1 8B (SQL gen) + Llama 3.3 70B (explanations) |
| Embeddings | `BAAI/bge-base-en-v1.5` via Sentence Transformers |
| Vector Store | ChromaDB (persistent, local) |
| Reranker | CrossEncoder (same model as embeddings) |
| Database | Microsoft SQL Server (AdventureWorks2022) via `pyodbc` + ODBC Driver 17 |
| Frontend | Streamlit chat interface |
| Schema Registry | YAML config + Python data modules (900+ lines of table/relationship metadata) |

---

## Prerequisites

- **Python 3.10+**
- **Microsoft SQL Server** with the `AdventureWorks2022` database restored
- **ODBC Driver 17 for SQL Server** ([install guide](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server))
- **Groq API key** — free tier available at [console.groq.com](https://console.groq.com)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Prishushankar/AdventureWorksRagAgent.git
cd AdventureWorksRagAgent

# Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

1. Copy the example environment file and fill in your values:

```bash
copy .env.example .env
```

2. Edit `.env` with your settings:

```env
# REQUIRED
GROQ_API_KEY=your_groq_api_key_here

# DATABASE
DB_SERVER=localhost
DB_DATABASE=AdventureWorks2022
DB_TRUSTED_CONNECTION=yes
DB_ENCRYPT=no

# PATHS
SCHEMA_YAML_PATH=config/schema_adventureworks.yaml
CHROMA_DB_PATH=./chroma_db

# MODEL CONFIGURATION
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
LLM_MODEL=llama-3.1-8b-instant
EXPLANATION_MODEL=llama-3.3-70b-versatile

# RETRIEVAL TUNING
RETRIEVAL_TOP_K=10
ESCALATION_DISTANCE_THRESHOLD=0.65
RERANK_TOP_K=5
QUERY_EXPANSION_COUNT=3

# LOGGING
LOG_LEVEL=INFO
```

---

## Usage

### 1. Ingest the schema into ChromaDB

This embeds all table descriptions, business logic rules, view descriptions, and YAML supplements into the vector store. Run once (or whenever the schema changes):

```bash
python scripts/ingest.py
```

### 2. Launch the Streamlit app

```bash
streamlit run src/main.py
```

The app opens at **http://localhost:8501**. Select your preferred explanation language, then start asking questions.

### Example queries

| Query | What it does |
|---|---|
| `How many employees are in the Engineering department?` | Counts employees via `EmployeeDepartmentHistory` + `Department` |
| `Sabse zyada vacation hours kiske paas hai?` | Hinglish → finds employee with most vacation hours |
| `Which bikes are dead stock?` | Products in inventory with no sales in the last year |
| `Show me total revenue from shipped orders` | Aggregates `TotalDue` from `SalesOrderHeader` with status filter |
| `What is the salary of the highest paid employee?` | Uses `EmployeePayHistory` with `CROSS APPLY` for current rate |

---

## Project Structure

```
AdventureWorks2022-RAG/
├── config/
│   └── schema_adventureworks.yaml    # Full schema registry (tables, columns, FKs, business logic)
├── data/
│   └── schema_data.py                # Embedded schema: TABLE_DESCRIPTIONS, FOREIGN_KEYS, BUSINESS_LOGIC, VIEWS
├── scripts/
│   ├── ingest.py                     # 4-pass ChromaDB ingestion (tables → rules → views → YAML supplements)
│   └── run_eval.py                   # Retrieval evaluation suite
├── src/
│   ├── main.py                       # Streamlit UI entry point
│   ├── pipeline.py                   # Orchestrator: intent → retrieve → generate → execute (retry loop)
│   ├── config.py                     # Frozen dataclass config (all env vars centralized)
│   ├── intent.py                     # Hinglish → English intent clarification via LLM
│   ├── retrieval.py                  # Vector search + LLM escalation fallback
│   ├── vector_store.py               # ChromaDB wrapper: query expansion, reranking, lazy init
│   ├── generation.py                 # SQL generation with 14 hard schema-lock rules
│   ├── templates.py                  # Regex fast-path SQL templates (dept, leave, pay, dead stock)
│   ├── sanitizer.py                  # Strip markdown fences, hardcoded years
│   ├── executor.py                   # Forbidden keyword blocklist + pyodbc execution
│   ├── explanation.py                # Multilingual result explanation with script validation
│   ├── database.py                   # Lazy pyodbc connection, live schema introspection, temporal anchor
│   ├── llm_client.py                 # Groq client with retry, rate-limit backoff, token tracking
│   └── logger.py                     # Centralized structured logging
├── tests/
│   └── eval_suite.json               # 25 retrieval evaluation test cases
├── .env.example                      # Environment variable template
├── .gitignore
├── pyproject.toml                    # Build config, ruff, mypy, pytest settings
└── requirements.txt                  # Python dependencies
```

---

## Evaluation

Run the retrieval evaluation suite to measure how accurately the vector store retrieves the correct tables for each query:

```bash
python scripts/run_eval.py
```

This runs 25 test queries, checks if the expected tables are retrieved, and outputs:

- **Accuracy score** (e.g., `Eval Score: 88.0% (22/25 passed)`)
- **Per-query details** with expected vs retrieved tables and missed tables
- Full report saved to `eval_report.json`

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Groq over OpenAI** | Free tier, fast inference, no data leaves to OpenAI — API key stays local |
| **ChromaDB over Pinecone/Qdrant** | Fully local, no cloud dependency, persistent storage, zero cost |
| **Frozen dataclass config** | Immutable singleton — no accidental mutation, all config in one place |
| **Schema-lock rules in prompt** | 14 hard-coded rules prevent the most common SQL generation failures for AdventureWorks2022 |
| **Regex templates before LLM** | Deterministic fast path for known query patterns — faster, cheaper, zero hallucination |
| **Retry with error feedback** | Self-healing: the agent sees the SQL Server error and rewrites the query up to 4 times |
| **Live column verification** | At runtime, actual `INFORMATION_SCHEMA.COLUMNS` are appended to the prompt as ground truth |
| **Multilingual explanations** | Script validation ensures Hindi/Marathi output is in Devanagari, not Romanized — with fallback |

---

## Author

**Priyanshu Shankar** — [GitHub](https://github.com/Prishushankar)

---

## License

This project is open source. See the repository for license details.
