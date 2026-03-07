from crawler.http.client import request_page
from crawler.extractors.admissions import extract_items as extract_admissions
from crawler.extractors.careers import extract_items as extract_careers
from crawler.extractors.recommendation import extract_items as extract_recommendation
from crawler.extractors.budgets import extract_items as extract_budgets
from crawler.extractors.generic import extract_generic_items


WEBSITE_EXTRACTOR_MAP = {
    "admissions": extract_admissions,
    "careers": extract_careers,
    "recommendation": extract_recommendation,
    "budgets": extract_budgets,
}


def choose_website_extractor(topic: str):
    return WEBSITE_EXTRACTOR_MAP.get(topic, extract_generic_items)


def build_runtime_source(source: dict) -> dict:
    return {
        "name": source.get("name", ""),
        "url": source.get("entry", ""),
        "topic": source.get("topic", "general"),
        "allow_domains": source.get("allow_domains", []),
        "must_include": source.get("must_include", []),
        "exclude_keywords": source.get("exclude_keywords", []),
        "source_type": source.get("source_type", "official"),
        "platform": source.get("platform", "website"),
        "trust_level": source.get("trust_level", "medium"),
        "extra_tags": source.get("tags", []),
    }


def collect_from_website(source: dict) -> list[dict]:
    runtime_source = build_runtime_source(source)
    url = runtime_source["url"]
    if not url:
        return []

    html = request_page(url)
    extractor = choose_website_extractor(runtime_source.get("topic", "general"))
    items = extractor(runtime_source, html)

    extra_tags = runtime_source.get("extra_tags", [])
    for item in items:
        item["source_type"] = runtime_source.get("source_type", "official")
        item["platform"] = runtime_source.get("platform", "website")
        item["trust_level"] = runtime_source.get("trust_level", "medium")
        item.setdefault("tags", [])
        item["tags"] = sorted(set(item["tags"] + extra_tags))

    return items
