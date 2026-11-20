# TXST Campus Assistant

TXST Campus Assistant is a modular multi-agent AI system designed to help Texas State University students access campus information through natural language. The application routes each user query to the most appropriate specialized AI agent, retrieves relevant university information using Retrieval-Augmented Generation (RAG), and generates context-aware responses using a large language model.

The project demonstrates multi-agent orchestration, semantic search, REST API development, and modern LLM application architecture.

---

## Key Features

- Multi-agent architecture with specialized AI agents
- Conversation-aware planner: one model call routes the turn, rewrites follow-ups into
  standalone search queries, and picks the tool
- Retrieval-Augmented Generation (RAG)
- Semantic search using ChromaDB vector database
- Provider-agnostic LLM integration (Groq, OpenAI, Gemini)
- Persistent conversation memory
- Session-isolated conversation history in the API and Streamlit UI
- Official source links in grounded answers when source material is available
- FastAPI backend with REST API
- Streamlit web interface
- Thumbs up/down feedback on answers, logged to SQLite
- Knowledge base generated from Texas State University resources

---

## System Architecture

```
User message + recent conversation
     │
     ▼
Planner (orchestrator.plan, one JSON-mode call)
  → agent, confidence, standalone_query, tool
     │
     ├──────────────┬────────────────┬──────────────┐
     ▼              ▼                ▼              ▼
Academics       Campus        Financial Aid      General
     │              │                │
     └──────┬───────┘                │
            ▼                        ▼
  Hybrid retrieval (ChromaDB + BM25) on the standalone query
            │                        │
            ▼                        ▼
  Grounded LLM answer        Verified source excerpts
            │                        │
            └───────────┬────────────┘
                        ▼
          FastAPI backend + Streamlit UI
```

---

## Technology Stack

| Component       | Technology           |
| --------------- | -------------------- |
| Language        | Python 3.12          |
| Backend         | FastAPI              |
| Frontend        | Streamlit            |
| Vector Database | ChromaDB             |
| Embedding Model | all-MiniLM-L6-v2     |
| LLM Provider    | Groq (`openai/gpt-oss-120b` by default, set `LLM_MODEL`) |
| Memory          | JSON Session Storage |
| Web Scraping    | BeautifulSoup        |
| API Server      | Uvicorn              |

---

## Repository Structure

```
TXST-assistant/
│
├── agents/
│   ├── academics.py
│   ├── campus.py
│   └── financial_aid.py
│
├── context/
├── llm/
├── memory/
├── rag/
│
├── api.py
├── orchestrator.py
├── scrape_context.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/0205prakriti/TXST-assistant.git
cd TXST-assistant
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=YOUR_API_KEY
# Optional
LLM_MODEL=openai/gpt-oss-120b          # writes the answers
LLM_FAST_MODEL=openai/gpt-oss-20b      # routing and passage selection (own rate-limit quota)
LLM_FAST_REASONING_EFFORT=low
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

Generate the knowledge base (also rerun these commands after pulling changes so existing indexes gain source metadata):

```bash
python scrape_context.py
python rag/embedder.py
```

To refresh only financial aid, use:

```bash
python scrape_context.py --domain financial_aid
python rag/embedder.py --domain financial_aid
```

Financial aid sources cover applications, BOSS scholarships, eligibility, verification,
SAP, disbursement, grants, loans, work-study, Bobcat Promise, and summer aid on TXST
One Stop. Source URLs and fetch times are saved in `context/financial_aid.sources.json`.
A fetch time records when the page was collected; it does not establish when a policy
took effect. Failed source downloads stop the refresh before replacing the domain's
existing text. Rebuild the index after each successful refresh.

Retrieval combines semantic search with keyword matching so specific topics such as
disbursement can outrank generic eligibility text. Financial aid replies use brief
official excerpts rather than generated paraphrases. Each excerpt must match its
attributed source text before display; invented wording or source links trigger a
fallback to official pages. This prevents added steps or requirements, though source
selection and the freshness of the university's pages still need review.

Run the backend:

```bash
uvicorn api:app --reload
```

Run the frontend:

```bash
streamlit run main.py
```

---

## API Endpoints

| Method | Endpoint   | Description                   |
| ------ | ---------- | ----------------------------- |
| GET    | `/`        | API status                    |
| POST   | `/chat`    | Send a message; returns a `session_id` |
| GET    | `/chat/stream?message=...` | Stream the reply as server-sent events (meta, token, done) |
| GET    | `/history?session_id=...` | Retrieve that session's history |
| DELETE | `/history?session_id=...` | Clear that session's history |
| GET    | `/health`  | Service health check          |

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

Send the returned `session_id` with later `/chat` requests to continue a conversation. Omitting it starts a new session. Session IDs separate local histories; they are not authentication. Add user authentication and a managed database before exposing history endpoints publicly.

---

## How It Works

1. A user submits a question through the Streamlit interface.
2. The planner reads the message with the last few turns of the conversation and, in one
   call, picks the agent, rewrites follow-ups ("what about spring?") into a standalone
   query, and chooses a tool.
3. The selected agent searches the knowledge base with that standalone query.
4. The retrieved context is combined with the user's question and sent to the configured language model.
5. The generated response is returned through the FastAPI backend and displayed to the user.

---

## Learning Outcomes

This project provided hands-on experience with:

- Multi-agent AI system design
- Retrieval-Augmented Generation (RAG)
- Semantic vector search
- Large language model integration
- FastAPI application development
- REST API design
- Web scraping and data preprocessing
- Conversation memory management
- Modular software architecture

---

## Future Work

- Authentication and user accounts
- Course recommendation system
- Voice-based interaction
- Docker support
- Cloud deployment
- Expanded university knowledge sources

## Verification

Run the offline tests (no API key needed; live model tests are skipped):

```bash
python -m pytest -q
```

### Evaluation set

`evals/golden.jsonl` holds 155 student questions across financial aid, academics and
campus, including 15 multi-turn follow-ups, personal-record questions, out-of-scope
requests and a prompt-injection attempt. Each case lists the official pages that
should support the answer, and short facts the answer must contain. A test checks
every required fact against the scraped source text, so the set cannot drift away
from the knowledge base. When a page is re-scraped and a fact changes, that test
fails and points at the case to update.

```bash
# Retrieval only: hit@1, hit@3, MRR. Offline, needs the Chroma index, no API key.
python -m scripts.run_eval --stage retrieval

# Planner: routing accuracy and follow-up rewrites (add --with-retrieval to check
# that rewritten follow-ups retrieve the right page).
python -m scripts.run_eval --stage routing --with-retrieval --interval 2

# End to end: fact recall, citation grounding, fallback rate, latency.
python -m scripts.run_eval --stage answer --interval 5
```

On Groq's free tier (8,000 tokens per minute) the answer stage hits rate limits; the
script waits 30 seconds and retries automatically. Progress is saved after every
question, so if a run stops, continue it with
`python -m scripts.run_eval --stage answer --resume evals/results/<report>.json`.

Filter with `--domain FINANCIAL_AID`, `--type follow_up` or `--limit 20`. Add gates such
as `--min-routing 0.9 --min-hit3 0.8 --min-facts 0.7` to exit with an error when quality
drops. Reports are written to `evals/results/` (git-ignored) and conversation history
goes to a temporary file, never to saved student chats.

The older eight-question check is still available:

```bash
python -m scripts.evaluate_financial_aid
```

## Author

**Prakriti Gautam**

B.S. Computer Science, Texas State University

GitHub: https://github.com/0205prakriti
