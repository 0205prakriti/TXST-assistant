# api.py
import json
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from groq import RateLimitError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from chat_service import answer, answer_stream
from memory.memory import load_history, clear_history

app = FastAPI(
    title="TXST Campus Assistant API",
    description="Multi-agent AI assistant for Texas State University",
    version="1.0.0"
)

# allow Streamlit and future React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# request/response models
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    agent: str
    confidence: float
    session_id: str

# endpoints
@app.get("/")
def root():
    return {"status": "running", "app": "TXST Campus Assistant"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return ChatResponse(**answer(request.message, request.session_id))
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="The assistant is temporarily busy. Please try again in a minute.") from exc

@app.get("/chat/stream")
def chat_stream(message: str = Query(min_length=1, max_length=4000), session_id: str | None = None):
    """Server-sent events: a meta event, then one token event per chunk, then done."""
    def event_gen():
        try:
            meta, tokens = answer_stream(message, session_id)
        except RateLimitError:
            yield f"data: {json.dumps({'type': 'error', 'detail': 'The assistant is temporarily busy. Please try again in a minute.'})}\n\n"
            return
        yield f"data: {json.dumps({'type': 'meta', **meta})}\n\n"
        try:
            for token in tokens:
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except RateLimitError:
            yield f"data: {json.dumps({'type': 'error', 'detail': 'The assistant is temporarily busy. Please try again in a minute.'})}\n\n"
            return
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(event_gen(), media_type="text/event-stream")

@app.get("/history")
def get_history(session_id: str = Query(...)):
    return {"history": load_history(session_id)}

@app.delete("/history")
def delete_history(session_id: str = Query(...)):
    clear_history(session_id)
    return {"status": "cleared"}

@app.get("/health")
def health():
    return {"status": "healthy"}
