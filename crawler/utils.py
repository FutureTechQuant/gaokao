from __future__ import annotations

import html as html_lib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
README_FILE = ROOT / "README.md"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

CN_TZ = timezone(timedelta(hours=8))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/年\.](\d{1,2})[-/月\.](\d{1,2})日?"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
]


def now_cn_iso() -> str:
    return datetime.now(CN_TZ).isoformat(timespec="seconds")


def load_json(path: Path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_text(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[\u200b\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(base_url: str, href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("#"):
        return ""
    if href.lower().startswith("javascript:"):
        return ""
    full = urljoin(base_url, href)
    return strip_url(full)


def strip_url(url: str) -> str:
    try:
        p = urlparse(url)
        p = p._replace(fragment="", query="")
        return urlunparse(p)
    except Exception:
        return url


def get_host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def get_path(url: str) -> str:
    try:
        return urlparse(url).path.lower()
    except Exception:
        return ""


def domain_allowed(url: str, allow_domains: list[str] | None) -> bool:
    if not allow_domains:
        return True
    host = get_host(url)
    for d in allow_domains:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def same_host(url1: str, url2: str) -> bool:
    return get_host(url1) == get_host(url2)


def request_html(url: str, timeout: int = 20) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def extract_date(text: str) -> str:
    text = text or ""
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        y, mm, dd = m.groups()
        try:
            dt = datetime(int(y), int(mm), int(dd))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""


def best_nonempty(*values: str) -> str:
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def shorten(text: str, limit: int = 220) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def unique_keep_best(items: list[dict], key_fn, score_fn):
    out = {}
    for item in items:
        key = key_fn(item)
        old = out.get(key)
        if old is None or score_fn(item) > score_fn(old):
            out[key] = item
    return list(out.values())
