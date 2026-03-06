from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
CONFIG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

SEED_FILE = CONFIG_DIR / "seed_urls.json"
APPROVED_FILE = CONFIG_DIR / "approved_sources.json"
CANDIDATES_FILE = DATA_DIR / "discovered_candidates.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

POSITIVE = [
    "高考", "普通高考", "招生", "本科招生", "考试院", "招办",
    "志愿填报", "录取", "分数线", "查分", "阳光高考"
]

NEGATIVE = [
    "考研", "研究生", "博士", "硕士", "成考", "自考",
    "留学", "四六级", "就业", "培训"
]

PATH_HINTS = ["gaokao", "zsb", "zs", "bkzs", "admission", "recruit"]
DOMAIN_HINTS = [".gov.cn", ".edu.cn", "chsi.com.cn"]

DEFAULT_SEEDS = [
    "https://gaokao.chsi.com.cn/"
]

def load_json(path: Path, default):
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()

def normalize_url(base: str, href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return ""
    return urljoin(base, href)

def get_host(url: str) -> str:
    return urlparse(url).netloc.lower()

def score_candidate(url: str, title: str, context: str) -> int:
    host = get_host(url)
    text = f"{url} {title} {context}".lower()

    score = 0

    for d in DOMAIN_HINTS:
        if host.endswith(d):
            score += 3

    for k in POSITIVE:
        if k.lower() in text:
            score += 2

    for k in NEGATIVE:
        if k.lower() in text:
            score -= 3

    for p in PATH_HINTS:
        if p in text:
            score += 2

    if "招生网" in title or "考试院" in title:
        score += 3

    return score

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text

def extract_links(page_url: str, html: str):
    soup = BeautifulSoup(html, "lxml")
    out = []

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        full = normalize_url(page_url, href)
        if not full.startswith("http"):
            continue

        title = clean_text(a.get_text(" ", strip=True))
        parent_text = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
        context = f"{title} | {parent_text}"[:300]

        if len(title) < 2:
            continue

        out.append({
            "url": full,
            "title": title,
            "context": context,
            "from": page_url,
        })

    return out

def discover(max_pages=30, max_depth=2):
    seed_urls = load_json(SEED_FILE, DEFAULT_SEEDS)
    approved = load_json(APPROVED_FILE, [])

    approved_urls = {x["url"] for x in approved if "url" in x}
    visited = set()
    queue = deque([(u, 0) for u in seed_urls])

    candidates = {}

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            html = fetch(url)
        except Exception:
            continue

        for link in extract_links(url, html):
            score = score_candidate(link["url"], link["title"], link["context"])
            if score < 4:
                continue

            key = link["url"]
            old = candidates.get(key)
            item = {
                "url": link["url"],
                "title": link["title"],
                "context": link["context"],
                "from": link["from"],
                "host": get_host(link["url"]),
                "score": score,
                "approved": key in approved_urls,
            }

            if (not old) or item["score"] > old["score"]:
                candidates[key] = item

            if depth + 1 <= max_depth and score >= 7:
                queue.append((link["url"], depth + 1))

    items = sorted(candidates.values(), key=lambda x: (x["approved"], x["score"]), reverse=True)
    save_json(CANDIDATES_FILE, items)
    return items

def auto_promote(threshold=10):
    candidates = load_json(CANDIDATES_FILE, [])
    approved = load_json(APPROVED_FILE, [])

    known = {x["url"] for x in approved if "url" in x}

    for c in candidates:
        if c["url"] in known:
            continue
        if c["score"] >= threshold:
            approved.append({
                "name": c["title"][:60],
                "url": c["url"],
                "must_include": ["高考", "招生", "录取", "志愿", "报名", "查分", "分数线"],
                "exclude_keywords": ["考研", "研究生", "成考", "自考", "留学"],
                "auto_discovered": True,
                "score": c["score"],
                "from": c["from"],
            })

    save_json(APPROVED_FILE, approved)

if __name__ == "__main__":
    discover()
    auto_promote()
