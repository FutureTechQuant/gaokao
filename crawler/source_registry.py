from collections import defaultdict

from crawler.source_loader import load_all_sources


def build_source_registry() -> list[dict]:
    return load_all_sources()


def group_sources_by_platform(sources: list[dict]) -> dict:
    grouped = defaultdict(list)
    for source in sources:
        grouped[source.get("platform", "unknown")].append(source)
    return dict(grouped)


def group_sources_by_topic(sources: list[dict]) -> dict:
    grouped = defaultdict(list)
    for source in sources:
        grouped[source.get("topic", "general")].append(source)
    return dict(grouped)
