import html as html_lib
from collections import OrderedDict

from crawler.config import DOCS_INDEX_HTML


CATEGORY_ORDER = [
    "招生信息",
    "就业质量",
    "保研信息",
    "学校预算",
    "专业趋势",
    "报考政策",
    "未分类",
]


def safe_text(value) -> str:
    return html_lib.escape(str(value or ""))


def normalize_items(items: list[dict]) -> list[dict]:
    normalized = []
    for item in items:
        row = dict(item)
        row.setdefault("category", "未分类")
        row.setdefault("topic", "综合信息")
        row.setdefault("tags", [])
        row.setdefault("date", "")
        row.setdefault("snippet", "")
        row.setdefault("score", 0)
        row.setdefault("is_pdf", False)
        normalized.append(row)
    return normalized


def group_by_category(items: list[dict]) -> OrderedDict:
    grouped = OrderedDict()
    for category in CATEGORY_ORDER:
        grouped[category] = []

    for item in items:
        category = item.get("category", "未分类")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(item)

    return grouped


def build_summary_cards(items: list[dict], errors: list[dict]) -> str:
    category_count = {}
    pdf_count = 0

    for item in items:
        category = item.get("category", "未分类")
        category_count[category] = category_count.get(category, 0) + 1
        if item.get("is_pdf"):
            pdf_count += 1

    cards = [
        ("总条目", len(items)),
        ("PDF条目", pdf_count),
        ("错误数", len(errors)),
    ]

    for category in CATEGORY_ORDER:
        if category_count.get(category):
            cards.append((category, category_count[category]))

    html = []
    for name, value in cards:
        html.append(
            f"""
            <div class="stat-card">
              <div class="stat-name">{safe_text(name)}</div>
              <div class="stat-value">{safe_text(value)}</div>
            </div>
            """
        )
    return "".join(html)


def render_tags(tags: list[str]) -> str:
    if not tags:
        return '<span class="tag muted">无标签</span>'
    return "".join(
        f'<span class="tag">{safe_text(tag)}</span>'
        for tag in tags[:8]
    )


def render_item(item: dict) -> str:
    title = safe_text(item.get("title"))
    url = safe_text(item.get("url"))
    source = safe_text(item.get("source"))
    date = safe_text(item.get("date") or "未知日期")
    topic = safe_text(item.get("topic") or "综合信息")
    snippet = safe_text(item.get("snippet"))
    score = safe_text(item.get("score", 0))
    item_type = "PDF" if item.get("is_pdf") else "网页"

    return f"""
    <article class="item-card">
      <div class="item-header">
        <a class="item-title" href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
      </div>
      <div class="item-meta">
        <span>日期：{date}</span>
        <span>来源：{source}</span>
        <span>专题：{topic}</span>
        <span>类型：{item_type}</span>
        <span>评分：{score}</span>
      </div>
      <div class="item-tags">{render_tags(item.get("tags", []))}</div>
      <div class="item-snippet">{snippet or "暂无摘要"}</div>
    </article>
    """


def render_category_section(category: str, items: list[dict]) -> str:
    if not items:
        return ""

    rows = "".join(render_item(item) for item in items[:80])
    return f"""
    <section class="category-section">
      <div class="section-head">
        <h2>{safe_text(category)}</h2>
        <span class="section-count">{len(items)} 条</span>
      </div>
      <div class="item-grid">
        {rows}
      </div>
    </section>
    """


def render_errors(errors: list[dict]) -> str:
    if not errors:
        return ""

    items = []
    for err in errors[:20]:
        items.append(
            f"<li>{safe_text(err.get('source'))} | {safe_text(err.get('url'))} | {safe_text(err.get('error'))}</li>"
        )

    return f"""
    <section class="category-section">
      <div class="section-head">
        <h2>抓取错误</h2>
        <span class="section-count">{len(errors)} 条</span>
      </div>
      <ul class="error-list">
        {''.join(items)}
      </ul>
    </section>
    """


def render_site(latest_payload: dict, analytics: dict) -> None:
    items = normalize_items(latest_payload.get("items", []))
    errors = latest_payload.get("errors", [])

    items = sorted(
        items,
        key=lambda x: (
            x.get("category", ""),
            x.get("date", ""),
            int(x.get("score", 0)),
            x.get("title", ""),
        ),
        reverse=True,
    )

    grouped = group_by_category(items)

    sections = []
    for category, rows in grouped.items():
        html = render_category_section(category, rows)
        if html:
            sections.append(html)

    analytics_html = f"""
    <details class="analytics-box">
      <summary>分析摘要</summary>
      <pre>{safe_text(analytics)}</pre>
    </details>
    """

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>升学与专业决策信息聚合</title>
  <style>
    :root {{
      --bg: #f6f8fb;
      --card: #ffffff;
      --text: #1f2328;
      --sub: #59636e;
      --line: #e5e7eb;
      --brand: #2563eb;
      --brand-soft: #dbeafe;
      --tag: #eef2ff;
      --ok: #0f766e;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC",
        "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
      line-height: 1.6;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px 16px 48px;
    }}

    .hero {{
      background: linear-gradient(135deg, #ffffff, #eef4ff);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      margin-bottom: 20px;
    }}

    .hero h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.2;
    }}

    .hero p {{
      margin: 0;
      color: var(--sub);
    }}

    .meta {{
      margin-top: 12px;
      color: var(--sub);
      font-size: 14px;
    }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}

    .stat-card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
    }}

    .stat-name {{
      color: var(--sub);
      font-size: 13px;
      margin-bottom: 6px;
    }}

    .stat-value {{
      font-size: 26px;
      font-weight: 700;
      color: var(--brand);
    }}

    .analytics-box {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
      margin-bottom: 20px;
    }}

    .analytics-box summary {{
      cursor: pointer;
      font-weight: 600;
    }}

    .analytics-box pre {{
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--sub);
      margin-top: 12px;
    }}

    .category-section {{
      margin-bottom: 24px;
    }}

    .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }}

    .section-head h2 {{
      margin: 0;
      font-size: 22px;
    }}

    .section-count {{
      color: var(--sub);
      font-size: 14px;
    }}

    .item-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }}

    .item-card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
    }}

    .item-title {{
      color: var(--brand);
      text-decoration: none;
      font-size: 18px;
      font-weight: 600;
    }}

    .item-title:hover {{
      text-decoration: underline;
    }}

    .item-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      margin: 8px 0 10px;
      color: var(--sub);
      font-size: 13px;
    }}

    .item-tags {{
      margin-bottom: 10px;
    }}

    .tag {{
      display: inline-block;
      background: var(--tag);
      color: #3730a3;
      border-radius: 999px;
      padding: 4px 10px;
      margin: 0 8px 8px 0;
      font-size: 12px;
    }}

    .tag.muted {{
      background: #f3f4f6;
      color: #6b7280;
    }}

    .item-snippet {{
      color: var(--text);
      font-size: 14px;
    }}

    .error-list {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px 20px 16px 36px;
      margin: 0;
    }}

    .footer {{
      margin-top: 32px;
      color: var(--sub);
      font-size: 13px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="hero">
      <h1>升学与专业决策信息聚合</h1>
      <p>按分类展示招生、就业、保研与预算相关信息，方便快速浏览与后续扩展。</p>
      <div class="meta">
        最近更新：{safe_text(latest_payload.get("updated_at", ""))}；
        条目数：{safe_text(latest_payload.get("count", 0))}；
        错误数：{safe_text(len(errors))}
      </div>
    </header>

    <section class="stats">
      {build_summary_cards(items, errors)}
    </section>

    {analytics_html}

    {''.join(sections) if sections else '<p>暂无数据。</p>'}

    {render_errors(errors)}

    <div class="footer">
      页面文件位于 docs/index.html
    </div>
  </div>
</body>
</html>
"""
    DOCS_INDEX_HTML.write_text(page, encoding="utf-8")
