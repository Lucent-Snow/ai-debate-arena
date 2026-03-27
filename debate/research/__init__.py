from .reader import fetch_page
from .search import web_search
from .types import Evidence, ResearchConfig, SearchResult, SearchTask

__all__ = [
    "Evidence",
    "ResearchConfig",
    "SearchResult",
    "SearchTask",
    "fetch_page",
    "web_search",
]
