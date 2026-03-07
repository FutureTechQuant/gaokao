from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
AUTO_SEED_FILE = CONFIG_DIR / "schools_seed.generated.yaml"
MANUAL_SEED_FILE = CONFIG_DIR / "schools_seed.yaml"

CHSI_LIST_URL = "https://gaokao.chsi.com.cn/sch/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gaokao-bot/1.0; +https://github.com/)"
}

PROVINCES = [
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
]

BAD_HOST_KEYWORDS = [
    "chsi.com.cn",
    "gaokao.chsi.com.cn",
    "weibo.com",
    "weixin.qq.com",
    "mp.weixin.qq.com",
    "zhihu.com",
    "bilibili.com",
    "xiaohongshu.com",
]

ADMISSIONS_HINTS = ["招生", "本科招生", "招生网", "招生信息网", "录取", "zsb", "zhaosheng"]
CAREERS_HINTS = ["就业", "就业网", "job", "career", "jiuye", "就业质量"]
BUDGETS_HINTS = ["预算", "决算", "财务", "cw", "cwc"]
INFO_HINTS = ["信息公开", "xxgk"]
RECOMMEND_HINTS = ["推免", "保研", "推荐免试", "夏令营", "jwc", "教务"]


def get(url: str, **kwargs) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
    resp.raise_for_status()
    return resp


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def domain_candidates(urls: list[str]) -> list[str]:
    seen = set()
    result = []
    for url in urls:
        host = host_of(url)
        if not host:
            continue
        if host not in seen:
            seen.add(host)
            result.append(host)
    return result


def looks_like_school_name(text: str) -> bool:
    text = normalize_text(text)
    if len(text) < 2 or len(text) > 40:
        return False
    keywords = ["大学", "学院", "职业技术", "高等专科", "警察学院", "医学院", "师范"]
    return any(k in text for k in keywords)


def detect_region(text: str) -> str:
    text = normalize_text(text)
    for p in PROVINCES:
        if p in text:
            return p
    return ""


def pick_best_link(links: list[dict], hints: list[str]) -> str:
    scored = []
    for row in links:
        text = row["text"].lower()
        href = row["href"].lower()
        score = 0
        for hint in hints:
            h = hint.lower()
            if h in text:
                score += 3
            if h in href:
                score += 2
        if score > 0:
            scored.append((score, row["href"]))
    scored.sort(reverse=True)
    return scored[0][1] if scored else ""


def usable_external_link(url: str) -> bool:
    host = host_of(url)
    if not host:
        return False
    return not any(x in host for x in BAD_HOST_KEYWORDS)


def extract_external_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    rows = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a.get("href", "").strip())
        text = normalize_text(a.get_text(" ", strip=True))
        if not href.startswith("http"):
            continue
        if href in seen:
            continue
        seen.add(href)
        rows.append({"href": href, "text": text})
    return rows


def parse_school_cards_from_list(html: str, base_url: str) -> tuple[list[dict], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    next_pages = []
    seen_names = set()

    for a in soup.find_all("a", href=True):
        text = normalize_text(a.get_text(" ", strip=True))
        href = urljoin(base_url, a["href"])
        if looks_like_school_name(text) and "gaokao.chsi.com.cn" in href:
            if text not in seen_names:
                seen_names.add(text)
                block_text = normalize_text(a.parent.get_text(" ", strip=True)) if a.parent else text
                region = detect_region(block_text)
                cards.append({
                    "name": text,
                    "detail_url": href,
                    "region": region,
                })

        if "gaokao.chsi.com.cn" in href and "/sch/" in href:
            if any(token in href for token in ["page=", "start=", "sch/search", "/sch/?"]):
                next_pages.append(href)

    return cards, sorted(set(next_pages))


def parse_school_detail(detail_url: str) -> dict:
    try:
        resp = get(detail_url)
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = normalize_text(soup.get_text(" ", strip=True))
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""

    h1 = soup.find(["h1", "h2"])
    name = normalize_text(h1.get_text(" ", strip=True)) if h1 else ""
    if not looks_like_school_name(name):
        for candidate in [title, page_text[:120]]:
            m = re.search(r"([\u4e00-\u9fa5]{2,30}(大学|学院|职业技术学院|高等专科学校))", candidate)
            if m:
                name = m.group(1)
                break

    region = detect_region(page_text)

    links = extract_external_links(soup, detail_url)
    external_links = [x for x in links if usable_external_link(x["href"])]

    official_url = external_links[0]["href"] if external_links else ""
    admissions_url = pick_best_link(external_links, ADMISSIONS_HINTS)
    careers_url = pick_best_link(external_links, CAREERS_HINTS)
    budgets_url = pick_best_link(external_links, BUDGETS_HINTS)
    info_url = pick_best_link(external_links, INFO_HINTS)
    recommendation_url = pick_best_link(external_links, RECOMMEND_HINTS)

    fallback = official_url or admissions_url or info_url or careers_url or budgets_url or recommendation_url

    if not admissions_url:
        admissions_url = fallback
    if not careers_url:
        careers_url = info_url or fallback
    if not budgets_url:
        budgets_url = info_url or fallback
    if not recommendation_url:
        recommendation_url = info_url or fallback
    if not info_url:
        info_url = fallback

    allow_domains = domain_candidates([
        official_url,
        admissions_url,
        careers_url,
        budgets_url,
        recommendation_url,
        info_url,
    ])

    tags = [region] if region else []

    return {
        "name": name,
        "region": region,
        "tags": tags,
        "admissions_url": admissions_url or "",
        "info_url": info_url or "",
        "careers_url": careers_url or "",
        "recommendation_url": recommendation_url or "",
        "budgets_url": budgets_url or "",
        "allow_domains": allow_domains,
        "detail_url": detail_url,
        "official_url": official_url or "",
    }


def crawl_chsi_schools(max_pages: int = 180) -> list[dict]:
    to_visit = [CHSI_LIST_URL]
    visited = set()
    discovered = {}

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = get(url)
        except Exception:
            continue

        cards, next_pages = parse_school_cards_from_list(resp.text, url)

        for card in cards:
            key = card["name"]
            if key not in discovered:
                discovered[key] = card

        for nxt in next_pages:
            if nxt not in
