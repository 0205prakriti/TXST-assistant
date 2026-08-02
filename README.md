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

Generate the knowledge base:

```bash
python scrape_context.py
python rag/embedder.py
```

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
| POST   | `/chat`    | Send a user query             |
| GET    | `/history` | Retrieve conversation history |
| DELETE | `/history` | Clear conversation history    |
| GET    | `/health`  | Service health check          |

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

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

---

## Author

**Prakriti Gautam**

B.S. Computer Science, Texas State University

GitHub: https://github.com/0205prakriti
