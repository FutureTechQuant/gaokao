from collections import Counter
from datetime import datetime, timezone, timedelta

from crawler.analytics.summaries import build_analytics
from crawler.classify.category import assign_category
from crawler.classify.topic import assign_topic
from crawler.classify.tags import assign_tags
from crawler.classify.score import assign_score
from crawler.config import LATEST_JSON, HISTORY_JSON
from crawler.source_registry import build_source_registry
from crawler.adapters.website import collect_from_website
from crawler.adapters.xiaohongshu import collect_from_xiaohongshu
from crawler.pipeline.dedup import dedup_items
from crawler.pipeline.history import merge_history
from crawler.pipeline.validate import validate_item
from crawler.site.render_html import render_site
from crawler.site.render_readme import render_readme
from crawler.site.render_json import write_public_json
from crawler.storage.writer import write_json


TRUST_BONUS_MAP = {
    "high": 6,
    "medium": 3,
    "low": 0,
    "unknown": 0,
}


def collect_from_source(source: dict) -> list[dict]:
    platform = source.get("platform", "website")

    if platform == "website":
        return collect_from_website(source)

    if platform == "xiaohongshu":
        return collect_from_xiaohongshu(source)

    return []


def enrich_item(item: dict, source: dict, fetched_at: str) -> dict:
    row = dict(item)

    row["fetched_at"] = fetched_at
    row.setdefault("source", source.get("name", "unknown"))
    row.setdefault("source_url", source.get("entry", ""))
    row.setdefault("page_url", row.get("source_url", "") or row.get("url", ""))
    row.setdefault("topic", source.get("topic", "general"))
    row.setdefault("source_type", source.get("source_type", "official"))
    row.setdefault("platform", source.get("platform", "website"))
    row.setdefault("trust_level", source.get("trust_level", "medium"))
    row.setdefault("tags", [])
    row.setdefault("snippet", "")
    row.setdefault("date", "")
    row.setdefault("is_pdf", False)
    row.setdefault("score", 0)

    extra_tags = source.get("tags", []) or []
    row["tags"] = sorted(set((row.get("tags") or []) + extra_tags))

    row["category"] = assign_category(row)
    row["topic"] = assign_topic(row)
    row["tags"] = sorted(set(assign_tags(row) + row["tags"]))

    trust_bonus = TRUST_BONUS_MAP.get(row.get("trust_level", "unknown"), 0)
    row["score"] = int(row.get("score", 0)) + assign_score(row) + trust_bonus

    return row


def collect_one_source(source: dict, fetched_at: str) -> tuple[list[dict], list[dict]]:
    items = []
    errors = []

    try:
        raw_items = collect_from_source(source)

        for item in raw_items:
            enriched = enrich_item(item, source, fetched_at)
            if validate_item(enriched):
                items.append(enriched)

    except Exception as exc:
        errors.append({
            "source": source.get("name", "unknown"),
            "url": source.get("entry", ""),
            "platform": source.get("platform", "unknown"),
            "error": str(exc),
        })

    return items, errors


def _counter_to_sorted_dict(counter: Counter) -> dict:
    return dict(sorted(counter.items(), key=lambda x: (-x[1], x[0])))


def build_source_summary(sources: list[dict], items: list[dict]) -> dict:
    source_platform = Counter()
    source_topic = Counter()
    source_type = Counter()
    source_trust = Counter()

    for source in sources:
        source_platform[source.get("platform", "unknown")] += 1
        source_topic[source.get("topic", "general")] += 1
        source_type[source.get("source_type", "unknown")] += 1
        source_trust[source.get("trust_level", "unknown")] += 1

    result_platform = Counter()
    result_topic = Counter()
    result_type = Counter()
    result_trust = Counter()
    result_category = Counter()

    for item in items:
        result_platform[item.get("platform", "unknown")] += 1
        result_topic[item.get("topic", "general")] += 1
        result_type[item.get("source_type", "unknown")] += 1
        result_trust[item.get("trust_level", "unknown")] += 1
        result_category[item.get("category", "未分类")] += 1

    return {
        "total_sources": len(sources),
        "by_platform": _counter_to_sorted_dict(source_platform),
        "by_topic": _counter_to_sorted_dict(source_topic),
        "by_type": _counter_to_sorted_dict(source_type),
        "by_trust_level": _counter_to_sorted_dict(source_trust),
        "results_total": len(items),
        "results_by_platform": _counter_to_sorted_dict(result_platform),
        "results_by_topic": _counter_to_sorted_dict(result_topic),
        "results_by_source_type": _counter_to_sorted_dict(result_type),
        "results_by_trust_level": _counter_to_sorted_dict(result_trust),
        "results_by_category": _counter_to_sorted_dict(result_category),
    }


def main():
    fetched_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")

    sources = build_source_registry()
    all_items = []
    all_errors = []

    for source in sources:
        items, errors = collect_one_source(source, fetched_at)
        all_items.extend(items)
        all_errors.extend(errors)

    items = dedup_items(all_items)
    history = merge_history(items, fetched_at)
    analytics = build_analytics(items)
    source_summary = build_source_summary(sources, items)

    latest_payload = {
        "updated_at": fetched_at,
        "count": len(items),
        "errors": all_errors,
        "source_summary": source_summary,
        "items": items,
    }

    write_json(LATEST_JSON, latest_payload)
    write_json(HISTORY_JSON, history)
    render_site(latest_payload, analytics)
    render_readme(latest_payload)
    write_public_json(latest_payload, analytics)


if __name__ == "__main__":
    main()
