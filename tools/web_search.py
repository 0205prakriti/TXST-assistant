# tools/web_search.py
from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 3) -> str:
    """Search the web and return combined results as text."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No results found."

        combined = ""
        for r in results:
            combined += f"Title: {r['title']}\n"
            combined += f"Summary: {r['body']}\n\n"
        
        return combined.strip()

    except Exception as e:
        return f"Search failed: {e}"


if __name__ == "__main__":
    result = search_web("Texas State University FAFSA deadline 2026")
    print(result)