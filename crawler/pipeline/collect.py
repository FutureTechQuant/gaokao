from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from crawler.analytics.summaries import build_analytics
from crawler.classify.category import assign_category
from crawler.classify.topic import assign_topic
from crawler.classify.tags import assign_tags
from crawler.classify.score import assign_score
from crawler.config import LATEST_JSON, HISTORY_JSON
from crawler.http.client import request_page
from crawler.registry import build_source_registry
from crawler.extractors.admissions import extract_items as extract_admission_items
from crawler.extractors.careers import extract_items as extract_career_items
from crawler.extractors.recommendation import extract_items as extract_recommendation_items
from crawler.extractors.budgets import extract_items as extract_budget_items
from crawler.extractors.generic import extract_generic_items
from crawler.pipeline.dedup import dedup_items
from crawler.pipeline.history import merge_history
from crawler.pipeline.validate import validate_item
from crawler.site.render_html import render_site
from crawler.site.render_readme import render_readme
from crawler.site.render_json import write_public_json
from crawler.storage.writer import write_json


EXTRACTOR_MAP = {
    "admissions": extract_admission_items,
    "careers": extract_career_items,
    "recommendation": extract_recommendation_items,
    "budgets": extract_budget_items,
}

MAX_SECOND_HOP_PER_SOURCE = 8


def choose_extractor(topic: str):
    return EXTRACTOR_MAP.get(topic, extract_generic_items)


def get_host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def is_same_or_allowed_domain(url: str, allow_domains: list[str]) -> bool:
    host = get_host(url)
    if not host:
        return False
    if not allow_domains:
        return True
    for domain in allow_domains:
        domain = domain.lower()
        if host == domain or host.endswith("." + domain):
            return True
    return False


def should_follow_item(item: dict, source: dict) -> bool:
    url = item.get("url", "")
    if not url.startswith("http"):
        return False
    if item.get("is_pdf"):
        return False
    if not is_same_or_allowed_domain(url, source.get("allow_domains", [])):
        return False

    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("topic", ""),
        item.get("category", ""),
        " ".join(item.get("tags", [])),
    ])

    strong_keywords = [
        "招生章程", "招生计划", "录取查询", "历年分数", "分数线", "位次",
        "就业质量年度报告", "就业质量", "毕业生就业质量",
        "推免", "保研", "推荐免试", "夏令营",
        "单位预算", "部门预算", "预算", "决算"
    ]

    score = int(item.get("score", 0))
    if score >= 10:
        return True
    if any(k in text for k in strong_keywords):
        return True

    return False


def enrich_item(item: dict, fetched_at: str) -> dict:
    item["fetched_at"] = fetched_at
    item["category"] = assign_category(item)
    item["topic"] = assign_topic(item)
    item["tags"] = assign_tags(item)
    item["score"] = int(item.get("score", 0)) + assign_score(item)
    return item


def extract_for_source(source: dict, html: str) -> list[dict]:
    extractor = choose_extractor(source.get("topic", ""))
    return extractor(source, html)


def collect_one_source(source: dict, fetched_at: str) -> tuple[list[dict], list[dict]]:
    items = []
    local_errors = []
    visited = set()

    try:
        root_html = request_page(source["url"])
        first_items = extract_for_source(source, root_html)
        for item in first_items:
            enrich_item(item, fetched_at)
            if validate_item(item):
                items.append(item)

        visited.add(source["url"])

        follow_candidates = []
        for item in first_items:
            enrich_item(item, fetched_at)
            if should_follow_item(item, source):
                follow_candidates.append(item)

        follow_candidates = sorted(
            follow_candidates,
            key=lambda x: (int(x.get("score", 0)), x.get("date", ""), x.get("title", "")),
            reverse=True,
        )

        picked_urls = []
        for item in follow_candidates:
            url = item.get("url", "")
            if not url or url in visited:
                continue
            picked_urls.append(url)
            visited.add(url)
            if len(picked_urls) >= MAX_SECOND_HOP_PER_SOURCE:
                break

        for url in picked_urls:
            try:
                sub_html = request_page(url)
                second_source = dict(source)
                second_source["url"] = url
                second_items = extract_for_source(second_source, sub_html)

                for item in second_items:
                    enrich_item(item, fetched_at)
                    if validate_item(item):
                        items.append(item)

            except Exception as exc:
                local_errors.append({
                    "source": source["name"],
                    "url": url,
                    "error": f"second-hop: {exc}",
                })

    except Exception as exc:
        local_errors.append({
            "source": source["name"],
            "url": source["url"],
            "error": str(exc),
        })

    return items, local_errors


def main():
    fetched_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    all_items = []
    errors = []

    for source in build_source_registry():
        source_items, source_errors = collect_one_source(source, fetched_at)
        all_items.extend(source_items)
        errors.extend(source_errors)

    items = dedup_items(all_items)
    history = merge_history(items, fetched_at)
    analytics = build_analytics(items)

    latest_payload = {
        "updated_at": fetched_at,
        "count": len(items),
        "errors": errors,
        "items": items,
    }

    write_json(LATEST_JSON, latest_payload)
    write_json(HISTORY_JSON, history)
    render_site(latest_payload, analytics)
    render_readme(latest_payload)
    write_public_json(latest_payload, analytics)


if __name__ == "__main__":
    main()
