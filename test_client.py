from llm.client import chat

reply = chat(
    messages=[{"role": "user", "content": "Say hello from TXST assistant"}],
    system="You are a helpful campus assistant for Texas State University."
)
print(reply)