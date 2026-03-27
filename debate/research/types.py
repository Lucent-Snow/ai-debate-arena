from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ResearchConfig:
    jina_api_key: str = ""
    max_research_rounds: int = 3
    max_total_evidence: int = 20
    webcontent_max_length: int = 15000
    per_round_timeout: int = 120
    total_prep_timeout: int = 300


@dataclass(slots=True)
class SearchTask:
    query: str
    purpose: str


@dataclass(slots=True)
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str


@dataclass(slots=True)
class Evidence:
    query: str
    url: str
    title: str
    summary: str
    snippet: str
