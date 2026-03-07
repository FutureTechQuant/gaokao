import html as html_lib

from crawler.config import DOCS_INDEX_HTML


def group_items(items: list[dict]) -> dict:
    grouped = {}
    for item in items:
        key = item.get("category", "未分类")
        grouped.setdefault(key, []).append(item)
    return grouped


def render_site(latest_payload: dict, analytics: dict) -> None:
    items = latest_payload.get("items", [])
    grouped = group_items(items)

    sections = []
    for category, rows in grouped.items():
        lis = []
        for item in rows[:50]:
            title = html_lib.escape(item.get("title", ""))
            url = html_lib.escape(item.get("url", ""))
            source = html_lib.escape(item.get("source", ""))
            tags = "、".join(item.get("tags", []))
            lis.append(f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a> <small>来源：{source}；标签：{html_lib.escape(tags)}</small></li>')
        sections.append(f"<section><h2>{html_lib.escape(category)}</h2><ul>{''.join(lis) or '<li>暂无数据</li>'}</ul></section>")

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>升学与专业决策信息聚合</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 24px auto; padding: 0 16px; line-height: 1.6; }}
    h1, h2 {{ color: #222; }}
    small {{ color: #666; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 8px 0; }}
    .meta {{ color: #666; margin-bottom: 16px; }}
    .card {{ background:#f7f7f7; padding:12px 16px; border-radius:8px; margin-bottom:16px; }}
  </style>
</head>
<body>
  <h1>升学与专业决策信息聚合</h1>
  <div class="meta">最近更新：{html_lib.escape(latest_payload.get("updated_at", ""))}；条目数：{latest_payload.get("count", 0)}</div>
  <div class="card"><pre>{html_lib.escape(str(analytics))}</pre></div>
  {''.join(sections) or '<p>暂无数据。</p>'}
</body>
</html>"""
    DOCS_INDEX_HTML.write_text(html, encoding="utf-8")
