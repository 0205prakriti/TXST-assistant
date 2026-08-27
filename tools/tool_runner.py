# tools/tool_runner.py
import json
from llm.client import chat
from tools.web_search import search_web
from rag.retriever import retrieve

TOOLS = {
    "search_web": search_web,
    "search_knowledge_base": retrieve
}

def decide_tool(user_message: str, agent_type: str) -> dict:
    """Ask LLM which tool to use for this question."""
    system = """You are a tool selector for a Texas State University AI assistant.
Given a user question and agent type, decide which tool to use.
Respond with JSON only. No explanation.

Tools available:
- search_web: use for current events, real-time info, deadlines, news
- search_knowledge_base: use for general campus info already in our database

Format:
{"tool": "search_web", "query": "optimized search query here"}
or
{"tool": "search_knowledge_base", "query": "search query here"}"""

    response = chat(
        messages=[{"role": "user", "content": f"Agent: {agent_type}\nQuestion: {user_message}"}],
        system=system
    )

    try:
        return json.loads(response)
    except:
        return {"tool": "search_knowledge_base", "query": user_message}


def run_tool(user_message: str, agent_type: str) -> str:
    """Decide and execute the right tool, return result."""
    decision = decide_tool(user_message, agent_type)
    tool_name = decision.get("tool", "search_knowledge_base")
    query = decision.get("query", user_message)

    print(f"  🔧 Tool selected: {tool_name}")
    print(f"  🔍 Query: {query}")

    if tool_name == "search_web":
        return search_web(query)
    else:
        collection = agent_type.lower().replace(" ", "_")
        return retrieve(query, collection_name=collection, n_results=3)