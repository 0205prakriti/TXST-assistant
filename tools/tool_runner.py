"""Run the tool chosen by the planner. No model call happens here."""
import logging

from rag.retriever import retrieve
from tools.web_search import search_web

logger = logging.getLogger(__name__)


def run_tool(query: str, agent_type: str, tool: str = "search_knowledge_base") -> str:
    logger.info("tool=%s agent=%s query=%r", tool, agent_type, query)
    if tool == "search_web":
        return search_web(f"site:txst.edu OR site:txstate.edu {query}")
    if tool == "none":
        return ""
    collection = agent_type.lower().replace(" ", "_")
    return retrieve(query, collection_name=collection, n_results=3)
