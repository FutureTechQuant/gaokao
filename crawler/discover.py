from __future__ import annotations

from collections import deque
from pathlib import Path

from bs4 import BeautifulSoup

from crawler.scoring import is_officialish_host, score_candidate
from crawler.utils import (
    CONFIG_DIR,
    DATA_DIR,
    README_FILE,
    clean_text,
    get_host,
    load_json,
    normalize_url,
    now_cn_iso,
    request_html,
    save_json,
    shorten,
    strip_url,
)

SEED_FILE = CONFIG_DIR / "seed_urls.json"
APPROVED_FILE = CONFIG_DIR / "approved_sources.json"
DISCOVERED_FILE = DATA_DIR / "discovered_candidates.json"
DISCOVER_META_FILE = DATA_DIR / "discover_meta.json"

DEFAULT_SEEDS = [
    "https://gaokao.chsi.com.cn/"
]

AUTO_APPROVE_THRESHOLD = 14
CANDIDATE_THRESHOLD = 6
MAX_PAGES = 40
MAX_DEPTH = 2
MAX_FOLLOW_PER_PAGE = 15


def infer_source_name(title: str, host: str) -> str:
    title = clean_text(title)
    if title:
        return title[:80]
    return host


def candidate_allow_domains(url: str) -> list[str]:
    host = get_host(url)
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2:] in (["gov", "cn"], ["edu", "cn"]):
        return [".".join(parts[-3:]), host]
    return [host] if host else []


def extract_links(page_url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []

    for a in soup.select("a[href]"):
        full = normalize_url(page_url, a.get("href", ""))
        if not full.startswith("http"):
            continue

        title = clean_text(a.get_text(" ", strip=True))
        if len(title) < 2:
            continue

        parent_text = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
        context = shorten(f"{title} | {parent_text}", 300)

        score, reasons = score_candidate(full, title, context)
        items.append({
            "url": strip_url(full),
            "title": title,
            "context": context,
            "from": page_url,
            "host": get_host(full),
            "score": score,
            "reasons": reasons,
        })

    return items


def select_follow_links(items: list[dict]) -> list[dict]:
    items = [x for x in items if x["score"] >= 10]
    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:MAX_FOLLOW_PER_PAGE]


def auto_approve_candidates(candidates: list[dict], approved: list[dict]) -> list[dict]:
    known = {x["url"] for x in approved if "url" in x}

    for c in candidates:
        if c["url"] in known:
            continue
        host = c["host"]
        title = c["title"]
        score = c["score"]

        if score < AUTO_APPROVE_THRESHOLD:
            continue
        if not is_officialish_host(host):
            continue

        approved.append({
            "name": infer_source_name(title, host),
            "url": c["url"],
            "allow_domains": candidate_allow_domains(c["url"]),
            "must_include": ["高考", "招生", "录取", "志愿", "报名", "查分", "分数线"],
            "exclude_keywords": ["考研", "研究生", "成考", "自考", "留学", "就业"],
            "auto_discovered": True,
            "score": score,
            "from": c["from"],
            "enabled": True,
        })
        known.add(c["url"])

    approved.sort(key=lambda x: (int(x.get("score", 0)), x.get("name", "")), reverse=True)
    return approved


def render_discover_summary(candidates: list[dict], approved: list[dict], updated_at: str) -> str:
    lines = []
    lines.append("# 高考信息自动汇总\n")
    lines.append(f"- 最近发现时间：{updated_at}")
    lines.append(f"- 候选来源数：{len(candidates)}")
    lines.append(f"- 已批准来源数：{len(approved)}")
    lines.append("")
    lines.append("## 自动发现的高分候选\n")

    top = [x for x in candidates if x["score"] >= 10][:30]
    if not top:
        lines.append("- 暂无高分候选")
    else:
        for item in top:
            lines.append(
                f"- [{item['title']}]({item['url']}) | host={item['host']} | score={item['score']}"
            )

    lines.append("")
    lines.append("## 说明\n")
    lines.append("- `discover` 会从种子页面出发自动扩展候选站点。")
    lines.append("- 只有高分且看起来像官方域名的候选才会自动入库。")
    lines.append("- 正式抓取由 `collect` 工作流读取 `config/approved_sources.json` 执行。")
    lines.append("")
    return "\n".join(lines)


def main():
    updated_at = now_cn_iso()
    seed_urls = load_json(SEED_FILE, DEFAULT_SEEDS)
    approved = load_json(APPROVED_FILE, [])

    visited = set()
    queue = deque((url, 0) for url in seed_urls)
    candidates = {}

    while queue and len(visited) < MAX_PAGES:
        current_url, depth = queue.popleft()
        if current_url in visited or depth > MAX_DEPTH:
            continue
        visited.add(current_url)

        try:
            html = request_html(current_url)
        except Exception:
            continue

        links = extract_links(current_url, html)

        for link in links:
            if link["score"] < CANDIDATE_THRESHOLD:
                continue

            key = link["url"]
            old = candidates.get(key)
            if old is None or link["score"] > old["score"]:
                candidates[key] = link

        if depth < MAX_DEPTH:
            for item in select_follow_links(links):
                if item["url"] not in visited:
                    queue.append((item["url"], depth + 1))

    candidate_list = sorted(
        candidates.values(),
        key=lambda x: (x["score"], x["host"], x["title"]),
        reverse=True
    )

    approved = auto_approve_candidates(candidate_list, approved)

    save_json(DISCOVERED_FILE, {
        "updated_at": updated_at,
        "count": len(candidate_list),
        "items": candidate_list,
    })
    save_json(APPROVED_FILE, approved)
    save_json(DISCOVER_META_FILE, {
        "updated_at": updated_at,
        "visited_pages": len(visited),
        "approved_count": len(approved),
        "candidate_count": len(candidate_list),
    })

    README_FILE.write_text(
        render_discover_summary(candidate_list, approved, updated_at),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
