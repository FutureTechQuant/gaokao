from dataclasses import dataclass, field
from typing import Any


@dataclass
class Source:
    name: str
    url: str
    topic: str
    allow_domains: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    title: str
    url: str
    source: str
    source_url: str
    topic: str
    category: str = ""
    tags: list[str] = field(default_factory=list)
    date: str = ""
    snippet: str = ""
    score: int = 0
    is_pdf: bool = False
    page_url: str = ""
    fetched_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "source_url": self.source_url,
            "topic": self.topic,
            "category": self.category,
            "tags": self.tags,
            "date": self.date,
            "snippet": self.snippet,
            "score": self.score,
            "is_pdf": self.is_pdf,
            "page_url": self.page_url,
            "fetched_at": self.fetched_at,
        }
