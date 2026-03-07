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
    row.setdefault("page_url", row.get("source_url", ""))
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
    row["tags"] = sorted(set(row["tags"] + extra_tags))

    row["category"] = assign_category(row)
    row["topic"] = assign_topic(row)
    row["tags"] = sorted(set(assign_tags(row) + row["tags"]))

    trust_bonus_map = {
        "high": 6,
        "medium": 3,
        "low": 0,
    }
    row["score"] = int(row.get("score", 0)) + assign_score(row) + trust_bonus_map.get(
        row.get("trust_level", "medium"), 0
    )

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


def build_source_summary(sources: list[dict]) -> dict:
    by_platform = {}
    by_topic = {}
    by_type = {}

    for source in sources:
        platform = source.get("platform", "unknown")
        topic = source.get("topic", "general")
        source_type = source.get("source_type", "unknown")

        by_platform[platform] = by_platform.get(platform, 0) + 1
        by_topic[topic] = by_topic.get(topic, 0) + 1
        by_type[source_type] = by_type.get(source_type, 0) + 1

    return {
        "total_sources": len(sources),
        "by_platform": by_platform,
        "by_topic": by_topic,
        "by_type": by_type,
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
    source_summary = build_source_summary(sources)

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
