from pathlib import Path
import yaml

from crawler.config import CONFIG_DIR


SOURCES_DIR = CONFIG_DIR / "sources"


def _read_yaml_file(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _normalize_source(raw: dict, file_path: Path) -> dict:
    source = dict(raw)

    source.setdefault("enabled", True)
    source.setdefault("source_type", "official")
    source.setdefault("platform", "website")
    source.setdefault("topic", "general")
    source.setdefault("mode", "crawl")
    source.setdefault("trust_level", "medium")
    source.setdefault("allow_domains", [])
    source.setdefault("must_include", [])
    source.setdefault("exclude_keywords", [])
    source.setdefault("tags", [])
    source.setdefault("entry", "")

    source["_from_file"] = str(file_path.as_posix())
    return source


def load_all_sources() -> list[dict]:
    results = []

    if not SOURCES_DIR.exists():
        return results

    for path in sorted(SOURCES_DIR.rglob("*.yaml")):
        payload = _read_yaml_file(path)
        rows = payload.get("sources", [])
        if not isinstance(rows, list):
            continue

        for raw in rows:
            if not isinstance(raw, dict):
                continue
            source = _normalize_source(raw, path)
            if source.get("enabled", True):
                results.append(source)

    return results
