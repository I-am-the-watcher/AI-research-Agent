"""Tools the Researcher can call."""
from urllib.parse import urlparse
from tavily import TavilyClient
from .config import TAVILY_API_KEY

_client = None
TRUSTED = (".gov", ".edu", "arxiv.org", "nature.com", "who.int", "nih.gov", "ieee.org", "acm.org", "oecd.org")
LOW_TRUST = ("reddit.com", "quora.com", "medium.com", "pinterest.com", "facebook.com")


def web_search(query: str, max_results: int = 5) -> list[dict]:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    res = _client.search(
        query=query, max_results=max_results, search_depth="advanced", include_raw_content=True
    )
    return res.get("results", [])


def credibility(url: str, search_score: float = 0.5) -> float:
    """Cheap heuristic: domain reputation blended with the search engine's relevance score."""
    host = urlparse(url).netloc.lower()
    base = 0.5
    if any(t in host for t in TRUSTED):
        base = 0.9
    elif any(t in host for t in LOW_TRUST):
        base = 0.3
    return round(0.7 * base + 0.3 * min(max(search_score, 0), 1), 2)
