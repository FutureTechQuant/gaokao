from __future__ import annotations

import json
import re
import hashlib
import html as html_lib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from .sources import SOURCES
except ImportError:
    from sources import SOURCES


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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

DEFAULT_MUST_INCLUDE = [
    "高考", "普通高考", "志愿", "录取", "招生", "报名", "查分", "分数线", "考试"
]
DEFAULT_EXCLUDE = [
    "考研", "研究生", "博士", "硕士", "自考", "成考", "四六级", "留学"
]

DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/年\.](\d{1,2})[-/月\.](\d{1,2})日?"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
]


def clean_text(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = re.sub(r"[\u200b\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(base_url: str, href: str) -> str:
    href = (href or "").strip()
    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
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
    allow_domains = [d.lower() for d in allow_domains]
    return any(host == d or host.endswith("." + d) for d in allow_domains)


def contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


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


def request_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


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


def collect_from_source(source: dict) -> list[dict]:
    base_url = source["url"]
    html = request_page(base_url)
    soup = BeautifulSoup(html, "lxml")

    must_include = source.get("must_include") or DEFAULT_MUST_INCLUDE
    exclude_keywords = source.get("exclude_keywords") or DEFAULT_EXCLUDE
    allow_domains = source.get("allow_domains") or []
    source_name = source["name"]

    collected = []
    seen = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        full_url = normalize_url(base_url, href)
        if not full_url:
            continue
        if not domain_allowed(full_url, allow_domains):
            continue

        title = clean_text(a.get_text(" ", strip=True))
        context = anchor_context(a)
        haystack = clean_text(" ".join([title, context, href, full_url]))

        if not title or len(title) < 4:
            continue
        if not contains_any(haystack, must_include):
            continue
        if contains_any(haystack, exclude_keywords):
            continue

        uid = sha1_text(source_name + "|" + full_url + "|" + title)
        if uid in seen:
            continue
        seen.add(uid)

        item = {
            "id": uid,
            "source": source_name,
            "source_url": base_url,
            "title": title,
            "url": full_url,
            "date": extract_date(context) or extract_date(title) or "",
            "snippet": context[:240],
            "fetched_at": FETCHED_AT,
        }
        collected.append(item)

    return collected


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
        else:
            index[key] = {
                **item,
                "first_seen_at": FETCHED_AT,
                "last_seen_at": FETCHED_AT,
                "seen_count": 1,
            }

    merged = list(index.values())
    merged.sort(
        key=lambda x: ((x.get("date") or ""), (x.get("last_seen_at") or "")),
        reverse=True
    )
    return {
        "updated_at": FETCHED_AT,
        "items": merged
    }


def sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda x: (x.get("date") or "", x.get("title") or ""),
        reverse=True
    )


def render_readme(items: list[dict], errors: list[dict]) -> str:
    top = items[:80]
    lines = []
    lines.append("# 高考信息自动汇总\n")
    lines.append(f"- 最近更新：{FETCHED_AT}\n")
    lines.append(f"- 本次抓取条目：{len(items)}\n")
    lines.append(f"- 错误数：{len(errors)}\n")
    lines.append("")
    lines.append("## 最新信息\n")

    if not top:
        lines.append("暂无数据，请检查 `crawler/sources.py` 中的页面地址是否正确。\n")
    else:
        for item in top:
            date_str = item["date"] or "未知日期"
            lines.append(f"- [{item['title']}]({item['url']}) | {item['source']} | {date_str}")

    if errors:
        lines.append("")
        lines.append("## 抓取错误\n")
        for e in errors[:20]:
            lines.append(f"- {e['source']} | {e['url']} | {e['error']}")

    lines.append("")
    lines.append("## 说明\n")
    lines.append("- 数据由 GitHub Actions 定时抓取生成。")
    lines.append("- 建议只添加官方来源页面。")
    lines.append("- 站点结构变化后，可能需要调整来源列表或过滤关键词。")
    lines.append("")
    return "\n".join(lines)


def render_html(items: list[dict], errors: list[dict]) -> str:
    rows = []
    for item in items[:200]:
        title = html_lib.escape(item["title"])
        url = html_lib.escape(item["url"])
        source = html_lib.escape(item["source"])
        date_str = html_lib.escape(item["date"] or "")
        snippet = html_lib.escape(item["snippet"] or "")
        rows.append(
            f"""
            <tr>
              <td>{date_str}</td>
              <td><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a><div class="snippet">{snippet}</div></td>
              <td>{source}</td>
            </tr>
            """
        )

    error_html = ""
    if errors:
        lis = []
        for e in errors[:20]:
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
      max-width: 1100px;
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
      </tr>
    </thead>
    <tbody>
      {''.join(rows) if rows else '<tr><td colspan="3">暂无数据，请检查来源配置。</td></tr>'}
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

        old_score = len(old.get("snippet", "")) + (5 if old.get("date") else 0)
        new_score = len(item.get("snippet", "")) + (5 if item.get("date") else 0)
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
