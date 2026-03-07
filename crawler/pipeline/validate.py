import hashlib
import re
from urllib.parse import urlparse


ALLOWED_SOURCE_TYPES = {"official", "platform", "community", "unknown"}
ALLOWED_TRUST_LEVELS = {"high", "medium", "low", "unknown"}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def _normalize_tags(tags) -> list[str]:
    if tags is None:
        return []

    if isinstance(tags, str):
        raw = [tags]
    elif isinstance(tags, (list, tuple, set)):
        raw = list(tags)
    else:
        return []

    result = []
    seen = set()
    for tag in raw:
        text = _safe_str(tag)
        if not text:
            continue
        if text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _normalize_url(url: str) -> str:
    url = _safe_str(url)
    if not url:
        return ""

    lowered = url.lower()
    if lowered.startswith(("javascript:", "mailto:", "#")):
        return ""

    return url


def _is_valid_http_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _normalize_date(value: str) -> str:
    value = _safe_str(value)
    if not value:
        return ""
    if DATE_PATTERN.match(value):
        return value
    return ""


def _infer_source_type(item: dict) -> str:
    source_type = _safe_str(item.get("source_type"), "unknown").lower()
    if source_type in ALLOWED_SOURCE_TYPES:
        return source_type

    platform = _safe_str(item.get("platform")).lower()
    if platform in {"website", "gov", "edu"}:
        return "official"
    if platform in {"xiaohongshu", "wechat", "bilibili", "zhihu", "weibo"}:
        return "platform"
    return "unknown"


def _infer_platform(item: dict) -> str:
    platform = _safe_str(item.get("platform"), "").lower()
    if platform:
        return platform

    url = _safe_str(item.get("url")).lower()
    source_url = _safe_str(item.get("source_url")).lower()
    text = f"{url} {source_url}"

    if "xiaohongshu.com" in text:
        return "xiaohongshu"
    if "weixin.qq.com" in text or "mp.weixin.qq.com" in text:
        return "wechat"
    if "bilibili.com" in text:
        return "bilibili"
    if "zhihu.com" in text:
        return "zhihu"
    if "weibo.com" in text:
        return "weibo"
    return "website"


def _infer_trust_level(item: dict) -> str:
    trust_level = _safe_str(item.get("trust_level"), "unknown").lower()
    if trust_level in ALLOWED_TRUST_LEVELS:
        return trust_level

    source_type = _infer_source_type(item)
    if source_type == "official":
        return "high"
    if source_type == "platform":
        return "medium"
    if source_type == "community":
        return "low"
    return "unknown"


def _build_fallback_id(item: dict) -> str:
    text = "|".join([
        _safe_str(item.get("source")),
        _safe_str(item.get("title")),
        _safe_str(item.get("url")),
        _safe_str(item.get("topic")),
    ])
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def normalize_item(item: dict) -> dict:
    row = dict(item or {})

    row["title"] = _safe_str(row.get("title"))
    row["url"] = _normalize_url(row.get("url"))
    row["source"] = _safe_str(row.get("source"))
    row["source_url"] = _normalize_url(row.get("source_url"))
    row["page_url"] = _normalize_url(row.get("page_url"))
    row["snippet"] = _safe_str(row.get("snippet"))
    row["topic"] = _safe_str(row.get("topic"), "general")
    row["category"] = _safe_str(row.get("category"), "未分类")
    row["date"] = _normalize_date(row.get("date"))
    row["fetched_at"] = _safe_str(row.get("fetched_at"))
    row["is_pdf"] = _safe_bool(row.get("is_pdf"))
    row["score"] = _safe_int(row.get("score"), 0)
    row["tags"] = _normalize_tags(row.get("tags"))
    row["platform"] = _infer_platform(row)
    row["source_type"] = _infer_source_type(row)
    row["trust_level"] = _infer_trust_level(row)

    if not row["source_url"]:
        row["source_url"] = row["url"]
    if not row["page_url"]:
        row["page_url"] = row["source_url"] or row["url"]

    row["id"] = _safe_str(row.get("id")) or _build_fallback_id(row)

    return row


def validate_item(item: dict) -> bool:
    row = normalize_item(item)

    required_fields = ["id", "title", "url", "source", "topic"]
    for field in required_fields:
        if not _safe_str(row.get(field)):
            return False

    if not _is_valid_http_url(row["url"]):
        return False

    if row["source_url"] and not _is_valid_http_url(row["source_url"]):
        row["source_url"] = row["url"]

    if row["page_url"] and not _is_valid_http_url(row["page_url"]):
        row["page_url"] = row["source_url"] or row["url"]

    if row["score"] < 0:
        row["score"] = 0

    if not row["title"].strip():
        return False

    item.clear()
    item.update(row)
    return True
