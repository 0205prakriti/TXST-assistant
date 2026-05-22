from orchestrator import route

questions = [
    "When is the last day to drop a class?",
    "Where is the dining hall?",
    "How do I appeal a grade?",
    "What are the library hours?",
    "When does registration open?",
]

for q in questions:
    print(f"Q: {q}")
    print(f"→ {route(q)}\n")