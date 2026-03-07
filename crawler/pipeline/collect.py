from crawler.source_registry import build_source_registry
from crawler.adapters.website import collect_from_website
from crawler.adapters.xiaohongshu import collect_from_xiaohongshu


def collect_from_source(source: dict) -> list[dict]:
    platform = source.get("platform", "website")
    if platform == "website":
        return collect_from_website(source)
    if platform == "xiaohongshu":
        return collect_from_xiaohongshu(source)
    return []
