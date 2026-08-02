# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator import route
from agents import academics, campus, financial_aid
from memory.memory import load_history, save_history, clear_history

app = FastAPI(
    title="TXST Campus Assistant API",
    description="Multi-agent AI assistant for Texas State University",
    version="1.0.0"
)

# allow Streamlit and future React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# request/response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    agent: str
    confidence: float

# endpoints
@app.get("/")
def root():
    return {"status": "running", "app": "TXST Campus Assistant"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = load_history()
    
    result = route(request.message)
    agent = result["agent"]
    confidence = result["confidence"]

    if confidence < 0.6:
        response = "Could you clarify — are you asking about academics, campus life, or financial aid?"
    elif agent == "ACADEMICS":
        response = academics.run(request.message, history)
    elif agent == "FINANCIAL_AID":
        response = financial_aid.run(request.message, history)
    else:
        response = campus.run(request.message, history)

    # save to memory
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response})
    save_history(history)

    return ChatResponse(response=response, agent=agent, confidence=confidence)

@app.get("/history")
def get_history():
    return {"history": load_history()}

@app.delete("/history")
def delete_history():
    clear_history()
    return {"status": "cleared"}

@app.get("/health")
def health():
    return {"status": "healthy"}