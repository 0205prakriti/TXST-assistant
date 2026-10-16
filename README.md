# TXST Campus Assistant

TXST Campus Assistant is a modular multi-agent AI system designed to help Texas State University students access campus information through natural language. The application routes each user query to the most appropriate specialized AI agent, retrieves relevant university information using Retrieval-Augmented Generation (RAG), and generates context-aware responses using a large language model.

The project demonstrates multi-agent orchestration, semantic search, REST API development, and modern LLM application architecture.

---

## Key Features

- Multi-agent architecture with specialized AI agents
- Confidence-based orchestrator for intelligent task routing
- Retrieval-Augmented Generation (RAG)
- Semantic search using ChromaDB vector database
- Provider-agnostic LLM integration (Groq, OpenAI, Gemini)
- Persistent conversation memory
- Session-isolated conversation history in the API and Streamlit UI
- Official source links in grounded answers when source material is available
- FastAPI backend with REST API
- Streamlit web interface
- Knowledge base generated from Texas State University resources

---

## System Architecture

```
User Query
     │
     ▼
Orchestrator
(Intent Classification)
     │
     ├───────────────┐
     ▼               ▼
Academic Agent   Campus Agent
                     │
                     ▼
            Financial Aid Agent
                     │
                     ▼
       ChromaDB Semantic Retrieval
                     │
                     ▼
              Large Language Model
                     │
                     ▼
          FastAPI Backend + Streamlit UI
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
| LLM Provider    | Groq (Llama 3.3-70B) |
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
2. The orchestrator analyzes the request and determines the most appropriate domain-specific agent.
3. The selected agent retrieves relevant context from the ChromaDB vector database.
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

Install `pytest` and `httpx` into your development environment, then run the offline
API and source-ingestion checks:

```bash
python -m pytest -q tests/test_api.py tests/test_sources.py tests/test_grounding.py
```

For a live check of eight financial aid questions through the API:

```bash
python -m scripts.evaluate_financial_aid
```

The live check uses your configured Groq key and may call web search. It stores its
conversations temporarily, leaving saved student chats untouched. Its citation
check detects links absent from the retrieved material; review the printed answers
against the sources to assess factual support. The existing routing tests also
make live model calls.

---

## Author

**Prakriti Gautam**

B.S. Computer Science, Texas State University

GitHub: https://github.com/0205prakriti
