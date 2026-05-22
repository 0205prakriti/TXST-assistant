import json
import os

MEMORY_FILE = "memory/sessions.json"

def load_history():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        data = json.load(f)
    return data.get("history", [])

def save_history(history: list):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"history": history}, f, indent=2)

def clear_history():
    save_history([])