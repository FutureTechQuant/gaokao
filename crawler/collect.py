from __future__ import annotations

import json
import re
import time
import socket
import hashlib
import html as html_lib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import requests.packages.urllib3.util.connection as urllib3_cn
from bs4 import BeautifulSoup

try:
    from .sources import SOURCES
except ImportError:
    from sources import SOURCES


def allowed_gai_family():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "docs"
README_FILE = ROOT / "README.md"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)

LATEST_JSON = DATA_DIR / "latest.json"
HISTORY_JSON = DATA_DIR / "history.json"
README_MD = README_FILE
SITE_HTML = SITE_DIR / "index.html"

CN_TZ = timezone(timedelta(hours=8))
FETCHED_AT = datetime.now(CN_TZ).isoformat(timespec="seconds")

DEFAULT_MUST_INCLUDE = [
    "高考", "普通高考", "本科招生", "招生", "录取", "录取查询", "招生计划",
    "招生章程", "招生简章", "历年分数", "专业", "专业介绍", "专业备案", "专业审批",
    "新增专业", "撤销专业", "就业质量年度报告", "就业质量", "毕业生就业",
    "就业去向", "行业分布", "地区流向", "升学", "月收入", "薪酬", "就业率",
    "位次", "分数线", "成绩查询"
]

DEFAULT_EXCLUDE = [
    "考研", "研究生", "博士", "硕士", "继续教育", "成人教育",
    "自考", "成考", "四六级", "教师资格", "党务", "工会"
]

HIGH_VALUE_HINTS = [
    "就业质量年度报告", "毕业生就业质量年度报告", "就业质量报告",
    "本科专业备案", "本科专业审批", "专业备案和审批结果",
    "招生章程", "招生计划", "历年分数", "录取分数", "录取查询",
    "专业介绍", "专业目录", "新增专业", "撤销专业"
]

CAREER_HINTS = [
    "就业", "就业率", "就业去向", "行业分布", "地区流向",
    "升学", "深造", "签约", "单位性质", "月收入", "薪酬"
]

ADMISSION_HINTS = [
    "高考", "本科招生", "招生", "录取", "录取查询",
    "招生计划", "招生章程", "分数线", "位次", "专业"
]

DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/年\.](\d{1,2})[-/月\.](\d{1,2})日?"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
]


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
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return ""
    return urljoin(base_url, href)


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def get_path(url: str) -> str:
    try:
        return urlparse(url).path.lower()
    except Exception:
        return ""


def is_pdf(url: str) -> bool:
    path = get_path(url)
    return path.endswith(".pdf")


def domain_allowed(url: str, allow_domains: list[str]) -> bool:
    if not allow_domains:
        return True
    host = get_domain(url)
    allow_domains = [d.lower() for d in allow_domains]
    return any(host == d or host.endswith("." + d) for d in allow_domains)


def contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def count_hits(text: str, keywords: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for k in keywords if k.lower() in t)


def extract_date(text: str) -> str:
    if not text:
        return ""
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        y, mth, d = m.groups()
        try:
            dt = datetime(int(y), int(mth), int(d))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def build_header_sets() -> list[dict]:
    return [
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.baidu.com/",
        },
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Safari/605.1.15"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.baidu.com/",
        },
    ]


def request_page(url: str) -> str:
    last_error = None
    for headers in build_header_sets():
        for _ in range(3):
            try:
                session = requests.Session()
                session.headers.update(headers)
                resp = session.get(url, timeout=25, allow_redirects=True)
                resp.raise_for_status()
                if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except Exception as e:
                last_error = e
                time.sleep(2)
    raise last_error


def anchor_context(anchor) -> str:
    texts = []
    if anchor:
        texts.append(anchor.get_text(" ", strip=True))
        p = anchor.parent
        depth = 0
        while p is not None and depth < 3:
            texts.append(p.get_text(" ", strip=True))
            p = p.parent
            depth += 1
    return clean_text(" | ".join([x for x in texts if x]))


def score_link(title: str, context: str, url: str, source: dict) -> int:
    text = clean_text(" ".join([title, context, url]))
    must_include = source.get("must_include") or DEFAULT_MUST_INCLUDE
    exclude_keywords = source.get("exclude_keywords") or DEFAULT_EXCLUDE

    score = 0

    if len(title) >= 4:
        score += 1

    score += count_hits(text, must_include) * 2
    score += count_hits(text, HIGH_VALUE_HINTS) * 4
    score += count_hits(text, CAREER_HINTS) * 3
    score += count_hits(text, ADMISSION_HINTS) * 2
    score -= count_hits(text, exclude_keywords) * 5

    if is_pdf(url):
        score += 4

    path = get_path(url)
    for hint in ["info", "article", "detail", "content", "notice", "news", "list", "pdf"]:
        if hint in path:
            score += 1

    if extract_date(context) or extract_date(title) or extract_date(url):
        score += 2

    return score


def extract_links_from_html(page_url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    links = []

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        full_url = normalize_url(page_url, href)
        if not full_url.startswith("http"):
            continue

        title = clean_text(a.get_text(" ", strip=True))
        context = anchor_context(a)
        if not title and not context:
            continue

        links.append({
            "title": title,
            "context": context,
            "url": full_url,
            "page_url": page_url,
        })

    return links


def candidate_to_item(source: dict, candidate: dict) -> dict:
    title = candidate["title"] or candidate["context"][:80] or candidate["url"]
    context = clean_text(candidate["context"])
    return {
        "id": sha1_text(source["name"] + "|" + candidate["url"] + "|" + title),
        "source": source["name"],
        "source_url": source["url"],
        "title": title,
        "url": candidate["url"],
        "date": extract_date(context) or extract_date(title) or extract_date(candidate["url"]) or "",
        "snippet": context[:240],
        "fetched_at": FETCHED_AT,
        "page_url": candidate["page_url"],
        "is_pdf": is_pdf(candidate["url"]),
        "score": candidate["score"],
    }


def extract_items_from_page(source: dict, page_url: str, html: str) -> tuple[list[dict], list[str]]:
    allow_domains = source.get("allow_domains") or []
    must_include = source.get("must_include") or DEFAULT_MUST_INCLUDE
    exclude_keywords = source.get("exclude_keywords") or DEFAULT_EXCLUDE

    items = []
    follow_urls = []
    seen_links = set()

    for link in extract_links_from_html(page_url, html):
        url = link["url"]
        if url in seen_links:
            continue
        seen_links.add(url)

        if not domain_allowed(url, allow_domains):
            continue

        title = link["title"]
        context = link["context"]
        haystack = clean_text(" ".join([title, context, url]))

        if contains_any(haystack, exclude_keywords):
            continue

        score = score_link(title, context, url, source)
        link["score"] = score

        if (contains_any(haystack, must_include) or score >= 7) and len(title + context) >= 4:
            items.append(candidate_to_item(source, link))

        if score >= 9 and not is_pdf(url):
            follow_urls.append(url)

    follow_urls = sorted(set(follow_urls))[:8]
    return items, follow_urls


def collect_from_source(source: dict) -> list[dict]:
    base_url = source["url"]
    base_html = request_page(base_url)

    collected = []
    visited = set()

    base_items, follow_urls = extract_items_from_page(source, base_url, base_html)
    collected.extend(base_items)
    visited.add(base_url)

    for sub_url in follow_urls:
        if sub_url in visited:
            continue
        visited.add(sub_url)
        try:
            sub_html = request_page(sub_url)
            sub_items, _ = extract_items_from_page(source, sub_url, sub_html)
            collected.extend(sub_items)
            time.sleep(0.5)
        except Exception:
            continue

    dedup = {}
    for item in collected:
        key = item["url"]
        old = dedup.get(key)
        if not old:
            dedup[key] = item
            continue
        old_score = int(old.get("score", 0)) + len(old.get("snippet", ""))
        new_score = int(item.get("score", 0)) + len(item.get("snippet", ""))
        if new_score > old_score:
            dedup[key] = item

    return list(dedup.values())


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def merge_history(items: list[dict]) -> dict:
    history = load_json(HISTORY_JSON, {"updated_at": "", "items": []})
    index = {}

    for old in history.get("items", []):
        key = old.get("id") or sha1_text(
            old.get("source", "") + "|" + old.get("url", "") + "|" + old.get("title", "")
        )
        index[key] = old

    for item in items:
        key = item["id"]
        if key in index:
            old = index[key]
            old["last_seen_at"] = FETCHED_AT
            old["seen_count"] = int(old.get("seen_count", 1)) + 1
            old["title"] = item["title"]
            old["url"] = item["url"]
            old["source"] = item["source"]
            old["source_url"] = item["source_url"]
            old["date"] = item["date"] or old.get("date", "")
            old["snippet"] = item["snippet"]
            old["score"] = item.get("score", old.get("score", 0))
            old["is_pdf"] = item.get("is_pdf", old.get("is_pdf", False))
            old["page_url"] = item.get("page_url", old.get("page_url", ""))
        else:
            index[key] = {
                **item,
                "first_seen_at": FETCHED_AT,
                "last_seen_at": FETCHED_AT,
                "seen_count": 1,
            }

    merged = list(index.values())
    merged.sort(
        key=lambda x: (
            x.get("date") or "",
            int(x.get("score", 0)),
            x.get("last_seen_at") or ""
        ),
        reverse=True
    )
    return {
        "updated_at": FETCHED_AT,
        "items": merged
    }


def sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda x: (
            x.get("date") or "",
            int(x.get("score", 0)),
            x.get("source") or "",
            x.get("title") or ""
        ),
        reverse=True
    )


def render_readme(items: list[dict], errors: list[dict]) -> str:
    top = items[:120]
    lines = []
    lines.append("# 高考信息自动汇总\n")
    lines.append(f"- 最近更新：{FETCHED_AT}\n")
    lines.append(f"- 本次抓取条目：{len(items)}\n")
    lines.append(f"- 错误数：{len(errors)}\n")
    lines.append("")
    lines.append("## 最新信息\n")

    if not top:
        lines.append("暂无数据，请检查 `crawler/sources.py` 的来源网址、网络可达性或关键词配置。\n")
    else:
        for item in top:
            date_str = item["date"] or "未知日期"
            tag = "PDF" if item.get("is_pdf") else "网页"
            lines.append(
                f"- [{item['title']}]({item['url']}) | {item['source']} | {date_str} | {tag}"
            )

    if errors:
        lines.append("")
        lines.append("## 抓取错误\n")
        for e in errors[:30]:
            lines.append(f"- {e['source']} | {e['url']} | {e['error']}")

    lines.append("")
    lines.append("## 说明\n")
    lines.append("- 本版本增强了专业趋势、招生信息、就业质量报告关键词识别。")
    lines.append("- 页面文件输出到 `docs/index.html`，可直接用于 GitHub Pages。")
    lines.append("- 结构化数据输出到 `data/latest.json` 和 `data/history.json`。")
    lines.append("")
    return "\n".join(lines)


def render_html(items: list[dict], errors: list[dict]) -> str:
    rows = []
    for item in items[:300]:
        title = html_lib.escape(item["title"])
        url = html_lib.escape(item["url"])
        source = html_lib.escape(item["source"])
        date_str = html_lib.escape(item["date"] or "")
        snippet = html_lib.escape(item["snippet"] or "")
        item_type = "PDF" if item.get("is_pdf") else "网页"
        score = int(item.get("score", 0))

        rows.append(
            f"""
            <tr>
              <td>{date_str}</td>
              <td>
                <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
                <div class="snippet">{snippet}</div>
              </td>
              <td>{source}</td>
              <td>{item_type}</td>
              <td>{score}</td>
            </tr>
            """
        )

    error_html = ""
    if errors:
        lis = []
        for e in errors[:30]:
            lis.append(
                f"<li>{html_lib.escape(e['source'])} | "
                f"{html_lib.escape(e['url'])} | "
                f"{html_lib.escape(e['error'])}</li>"
            )
        error_html = "<h2>抓取错误</h2><ul>" + "".join(lis) + "</ul>"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>高考信息自动汇总</title>
  <style>
    body {{
      font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif;
      margin: 24px auto;
      max-width: 1180px;
      padding: 0 16px;
      line-height: 1.6;
      color: #222;
    }}
    h1 {{ margin-bottom: 8px; }}
    .meta {{ color: #666; margin-bottom: 20px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      border-bottom: 1px solid #eee;
      padding: 12px 8px;
      vertical-align: top;
      text-align: left;
      word-break: break-word;
    }}
    th:nth-child(1), td:nth-child(1) {{ width: 120px; }}
    th:nth-child(3), td:nth-child(3) {{ width: 180px; }}
    th:nth-child(4), td:nth-child(4) {{ width: 80px; }}
    th:nth-child(5), td:nth-child(5) {{ width: 70px; }}
    a {{ color: #0b57d0; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .snippet {{ color: #666; font-size: 13px; margin-top: 4px; }}
  </style>
</head>
<body>
  <h1>高考信息自动汇总</h1>
  <div class="meta">最近更新：{html_lib.escape(FETCHED_AT)}；本次抓取：{len(items)} 条；错误数：{len(errors)}</div>
  <table>
    <thead>
      <tr>
        <th>日期</th>
        <th>标题</th>
        <th>来源</th>
        <th>类型</th>
        <th>评分</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows) if rows else '<tr><td colspan="5">暂无数据，请检查来源配置或网络可达性。</td></tr>'}
    </tbody>
  </table>
  {error_html}
</body>
</html>
"""


def main():
    all_items = []
    errors = []

    for source in SOURCES:
        try:
            items = collect_from_source(source)
            all_items.extend(items)
        except Exception as e:
            errors.append({
                "source": source.get("name", "unknown"),
                "url": source.get("url", ""),
                "error": str(e),
            })

    dedup = {}
    for item in all_items:
        key = item["url"] or item["id"]
        old = dedup.get(key)
        if not old:
            dedup[key] = item
            continue

        old_score = int(old.get("score", 0)) + len(old.get("snippet", "")) + (5 if old.get("date") else 0)
        new_score = int(item.get("score", 0)) + len(item.get("snippet", "")) + (5 if item.get("date") else 0)
        if new_score > old_score:
            dedup[key] = item

    items = sort_items(list(dedup.values()))
    history = merge_history(items)

    latest_payload = {
        "updated_at": FETCHED_AT,
        "count": len(items),
        "errors": errors,
        "items": items,
    }

    LATEST_JSON.write_text(
        json.dumps(latest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    HISTORY_JSON.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    README_MD.write_text(render_readme(items, errors), encoding="utf-8")
    SITE_HTML.write_text(render_html(items, errors), encoding="utf-8")


if __name__ == "__main__":
    main()
