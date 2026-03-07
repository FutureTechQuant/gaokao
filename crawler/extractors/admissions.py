import hashlib
import html as html_lib
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/年\.](\d{1,2})[-/月\.](\d{1,2})日?"),
]


def clean_text(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_url(base_url: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return ""
    return urljoin(base_url, href)


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def domain_allowed(url: str, allow_domains: list[str]) -> bool:
    if not allow_domains:
        return True
    host = get_domain(url)
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in allow_domains)


def extract_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text or "")
        if match:
            y, m, d = match.groups()
            try:
                return datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d")
            except Exception:
                return ""
    return ""


def score_admission_text(text: str, url: str) -> int:
    score = 0
    keywords = {
        "招生章程": 5,
        "招生计划": 5,
        "录取查询": 5,
        "历年分数": 4,
        "录取分数": 4,
        "分数线": 4,
        "专业介绍": 3,
        "本科招生": 3,
        "录取": 2,
        "陕西": 2,
        "位次": 2,
    }
    for k, v in keywords.items():
        if k in text:
            score += v

    if url.lower().endswith(".pdf"):
        score += 2
    return score


def extract_items(source: dict, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []

    for a in soup.select("a[href]"):
        title = clean_text(a.get_text(" ", strip=True))
        href = normalize_url(source["url"], a.get("href", ""))
        if not href:
            continue
        if not domain_allowed(href, source.get("allow_domains", [])):
            continue

        text = f"{title} {href}"
        if source.get("exclude_keywords") and any(k in text for k in source["exclude_keywords"]):
            continue

        score = score_admission_text(text, href)
        if source.get("must_include") and not any(k in text for k in source["must_include"]) and score < 4:
            continue

        items.append({
            "id": hashlib.sha1(f'{source["name"]}|{href}|{title}'.encode("utf-8")).hexdigest(),
            "title": title or href,
            "url": href,
            "source": source["name"],
            "source_url": source["url"],
            "topic": source["topic"],
            "date": extract_date(title) or extract_date(href),
            "snippet": title[:220],
            "page_url": source["url"],
            "is_pdf": href.lower().endswith(".pdf"),
            "score": score,
        })

    return items
