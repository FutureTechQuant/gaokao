import json
from pathlib import Path

from crawler.config import ROOT


PUBLIC_DATA_DIR = Path(ROOT) / "docs" / "data"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _safe_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _normalize_tags(value) -> list[str]:
    tags = []
    seen = set()
    for tag in _safe_list(value):
        text = _safe_str(tag)
        if not text:
            continue
        if text not in seen:
            seen.add(text)
            tags.append(text)
    return tags


def _normalize_item(item: dict) -> dict:
    row = dict(item or {})

    return {
        "id": _safe_str(row.get("id")),
        "title": _safe_str(row.get("title")),
        "url": _safe_str(row.get("url")),
        "source": _safe_str(row.get("source")),
        "source_url": _safe_str(row.get("source_url")),
        "page_url": _safe_str(row.get("page_url")),
        "topic": _safe_str(row.get("topic"), "general"),
        "category": _safe_str(row.get("category"), "未分类"),
        "date": _safe_str(row.get("date")),
        "snippet": _safe_str(row.get("snippet")),
        "is_pdf": _safe_bool(row.get("is_pdf")),
        "score": _safe_int(row.get("score"), 0),
        "fetched_at": _safe_str(row.get("fetched_at")),
        "source_type": _safe_str(row.get("source_type"), "unknown"),
        "platform": _safe_str(row.get("platform"), "website"),
        "trust_level": _safe_str(row.get("trust_level"), "unknown"),
        "tags": _normalize_tags(row.get("tags")),
    }


def _normalize_source_summary(source_summary: dict) -> dict:
    source_summary = source_summary or {}

    def _normalize_count_map(value) -> dict:
        if not isinstance(value, dict):
            return {}
        result = {}
        for k, v in value.items():
            key = _safe_str(k)
            if not key:
                continue
            result[key] = _safe_int(v, 0)
        return dict(sorted(result.items(), key=lambda x: (-x[1], x[0])))

    return {
        "total_sources": _safe_int(source_summary.get("total_sources"), 0),
        "by_platform": _normalize_count_map(source_summary.get("by_platform")),
        "by_topic": _normalize_count_map(source_summary.get("by_topic")),
        "by_type": _normalize_count_map(source_summary.get("by_type")),
        "by_trust_level": _normalize_count_map(source_summary.get("by_trust_level")),
        "results_total": _safe_int(source_summary.get("results_total"), 0),
        "results_by_platform": _normalize_count_map(source_summary.get("results_by_platform")),
        "results_by_topic": _normalize_count_map(source_summary.get("results_by_topic")),
        "results_by_source_type": _normalize_count_map(source_summary.get("results_by_source_type")),
        "results_by_trust_level": _normalize_count_map(source_summary.get("results_by_trust_level")),
        "results_by_category": _normalize_count_map(source_summary.get("results_by_category")),
    }

def _normalize_errors(errors) -> list[dict]:
    result = []
    for err in _safe_list(errors):
        if not isinstance(err, dict):
            continue
        result.append({
            "source": _safe_str(err.get("source")),
            "platform": _safe_str(err.get("platform")),
            "url": _safe_str(err.get("url")),
            "error": _safe_str(err.get("error")),
        })
    return result


def _write_json(path: Path, payload: dict | list) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_public_payload(latest_payload: dict, analytics: dict) -> dict:
    items = [_normalize_item(item) for item in _safe_list(latest_payload.get("items"))]
    items = sorted(
        items,
        key=lambda x: (x.get("score", 0), x.get("date", ""), x.get("title", "")),
        reverse=True,
    )

    errors = _normalize_errors(latest_payload.get("errors"))
    source_summary = _normalize_source_summary(latest_payload.get("source_summary"))

    return {
        "updated_at": _safe_str(latest_payload.get("updated_at")),
        "count": len(items),
        "errors": errors,
        "source_summary": source_summary,
        "items": items,
        "analytics": analytics or {},
    }


def write_public_json(latest_payload: dict, analytics: dict) -> None:
    _ensure_dir(PUBLIC_DATA_DIR)

    public_payload = build_public_payload(latest_payload, analytics)

    _write_json(PUBLIC_DATA_DIR / "latest.json", public_payload)
    _write_json(PUBLIC_DATA_DIR / "items.json", public_payload["items"])
    _write_json(PUBLIC_DATA_DIR / "analytics.json", public_payload["analytics"])
    _write_json(PUBLIC_DATA_DIR / "source_summary.json", public_payload["source_summary"])

