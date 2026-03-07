from datetime import datetime, timezone, timedelta

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


def choose_extractor(topic: str):
    return EXTRACTOR_MAP.get(topic, extract_generic_items)


def main():
    fetched_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    all_items = []
    errors = []

    for source in build_source_registry():
        try:
            html = request_page(source["url"])
            extractor = choose_extractor(source.get("topic", ""))
            items = extractor(source, html)

            for item in items:
                item["fetched_at"] = fetched_at
                item["category"] = assign_category(item)
                item["topic"] = assign_topic(item)
                item["tags"] = assign_tags(item)
                item["score"] = item.get("score", 0) + assign_score(item)
                if validate_item(item):
                    all_items.append(item)

        except Exception as exc:
            errors.append({
                "source": source["name"],
                "url": source["url"],
                "error": str(exc),
            })

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
