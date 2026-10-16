# Manual smoke script (needs GROQ_API_KEY). Lives in scripts/ so pytest does not collect it.
from llm.client import chat

reply = chat(
    messages=[{"role": "user", "content": "Say hello from TXST assistant"}],
    system="You are a helpful campus assistant for Texas State University."
)
print(reply)