# tools/web_search.py
from duckduckgo_search import DDGS
from urllib.parse import urlparse

def search_web(query: str, max_results: int = 3) -> str:
    """Search the web and return combined results as text."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No results found."

        combined = ""
        for r in results:
            url = r.get("href", "")
            host = urlparse(url).hostname or ""
            if not url.startswith("https://") or not any(
                host == domain or host.endswith("." + domain)
                for domain in ("txst.edu", "txstate.edu")
            ):
                continue
            combined += f"Title: {r['title']}\n"
            combined += f"Source: {url}\n"
            combined += f"Summary: {r['body']}\n\n"
        
        return combined.strip() or "No official Texas State results found."

    except Exception as e:
        return f"Search failed: {e}"


if __name__ == "__main__":
    result = search_web("Texas State University FAFSA deadline 2026")
    print(result)
