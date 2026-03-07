import html as html_lib
import json
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


LOW_PRIORITY_HINTS = [
    "活动",
    "开笔",
    "报道",
    "纪实",
    "访谈",
    "新闻",
    "仪式",
    "典礼",
    "论坛",
    "讲座",
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
        row.setdefault("source", "")
        row.setdefault("title", "")
        row.setdefault("url", "")
        normalized.append(row)
    return normalized


def is_low_priority_news(item: dict) -> bool:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
    ])
    return any(hint in text for hint in LOW_PRIORITY_HINTS)


def sort_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda x: (
            int(x.get("score", 0)),
            x.get("date", ""),
            x.get("is_pdf", False),
            x.get("title", ""),
        ),
        reverse=True,
    )


def group_by_category(items: list[dict]) -> OrderedDict:
    grouped = OrderedDict()
    for category in CATEGORY_ORDER:
        grouped[category] = []

    for item in items:
        category = item.get("category", "未分类")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(item)

    for category in list(grouped.keys()):
        grouped[category] = sort_items(grouped[category])

    return grouped


def collect_all_tags(items: list[dict]) -> list[str]:
    tags = set()
    for item in items:
        for tag in item.get("tags", []):
            if tag:
                tags.add(tag)
    return sorted(tags)


def build_summary_cards(items: list[dict], errors: list[dict]) -> str:
    category_count = {}
    pdf_count = 0
    low_priority_count = 0

    for item in items:
        category = item.get("category", "未分类")
        category_count[category] = category_count.get(category, 0) + 1
        if item.get("is_pdf"):
            pdf_count += 1
        if is_low_priority_news(item):
            low_priority_count += 1

    cards = [
        ("总条目", len(items)),
        ("PDF条目", pdf_count),
        ("低优先级新闻", low_priority_count),
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
        f'<button class="tag filter-tag" type="button" data-tag="{safe_text(tag)}">{safe_text(tag)}</button>'
        for tag in tags[:10]
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
    tags = item.get("tags", [])
    tag_text = "|".join(tags)
    low_priority = "true" if is_low_priority_news(item) else "false"

    return f"""
    <article
      class="item-card"
      data-category="{safe_text(item.get('category', '未分类'))}"
      data-topic="{topic}"
      data-tags="{safe_text(tag_text)}"
      data-score="{safe_text(item.get('score', 0))}"
      data-low-priority="{low_priority}"
    >
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
      <div class="item-tags">{render_tags(tags)}</div>
      <div class="item-snippet">{snippet or "暂无摘要"}</div>
    </article>
    """


def render_category_section(category: str, items: list[dict]) -> str:
    if not items:
        return ""

    high_items = [item for item in items if not is_low_priority_news(item)]
    low_items = [item for item in items if is_low_priority_news(item)]

    high_html = "".join(render_item(item) for item in high_items[:80])
    low_html = "".join(render_item(item) for item in low_items[:80])

    low_block = ""
    if low_items:
        low_block = f"""
        <details class="low-priority-box">
          <summary>展开低优先级新闻（{len(low_items)} 条）</summary>
          <div class="item-grid low-priority-grid">
            {low_html}
          </div>
        </details>
        """

    return f"""
    <section class="category-section" data-category-section="{safe_text(category)}">
      <div class="section-head">
        <h2>{safe_text(category)}</h2>
        <span class="section-count">{len(items)} 条</span>
      </div>
      <div class="item-grid">
        {high_html if high_html else '<div class="empty-box">暂无高优先级内容</div>'}
      </div>
      {low_block}
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


def render_filter_bar(items: list[dict]) -> str:
    tags = collect_all_tags(items)

    tag_buttons = "".join(
        f'<button type="button" class="toolbar-btn tag-btn" data-tag-filter="{safe_text(tag)}">{safe_text(tag)}</button>'
        for tag in tags[:40]
    )

    return f"""
    <section class="toolbar-wrap">
      <div class="toolbar">
        <div class="toolbar-row">
          <span class="toolbar-label">分类</span>
          <button type="button" class="toolbar-btn active" data-category-filter="全部">全部</button>
          {''.join(
              f'<button type="button" class="toolbar-btn" data-category-filter="{safe_text(category)}">{safe_text(category)}</button>'
              for category in CATEGORY_ORDER
          )}
        </div>
        <div class="toolbar-row">
          <span class="toolbar-label">排序</span>
          <button type="button" class="toolbar-btn active" data-sort-mode="score">按评分</button>
          <button type="button" class="toolbar-btn" data-sort-mode="date">按日期</button>
          <button type="button" class="toolbar-btn" id="toggleLowPriority">隐藏低优先级新闻</button>
        </div>
        <div class="toolbar-row toolbar-tags">
          <span class="toolbar-label">标签</span>
          <button type="button" class="toolbar-btn active" data-tag-filter="全部">全部</button>
          {tag_buttons}
        </div>
      </div>
    </section>
    """


def render_site(latest_payload: dict, analytics: dict) -> None:
    items = normalize_items(latest_payload.get("items", []))
    errors = latest_payload.get("errors", [])

    grouped = group_by_category(items)
    sections = []

    for category, rows in grouped.items():
        html = render_category_section(category, rows)
        if html:
            sections.append(html)

    analytics_html = f"""
    <details class="analytics-box">
      <summary>分析摘要</summary>
      <pre>{safe_text(json.dumps(analytics, ensure_ascii=False, indent=2))}</pre>
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
      --chip: #f8fafc;
      --shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
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
      max-width: 1240px;
      margin: 0 auto;
      padding: 24px 16px 48px;
    }}

    .hero {{
      background: linear-gradient(135deg, #ffffff, #eef4ff);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
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
      box-shadow: var(--shadow);
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

    .toolbar-wrap {{
      position: sticky;
      top: 0;
      z-index: 20;
      margin-bottom: 20px;
    }}

    .toolbar {{
      background: rgba(255,255,255,0.96);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      backdrop-filter: blur(8px);
      box-shadow: var(--shadow);
    }}

    .toolbar-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}

    .toolbar-row + .toolbar-row {{
      margin-top: 10px;
    }}

    .toolbar-label {{
      color: var(--sub);
      font-size: 13px;
      min-width: 44px;
    }}

    .toolbar-btn {{
      border: 1px solid var(--line);
      background: var(--chip);
      color: var(--text);
      border-radius: 999px;
      padding: 7px 12px;
      cursor: pointer;
      font-size: 13px;
    }}

    .toolbar-btn.active {{
      background: var(--brand);
      border-color: var(--brand);
      color: white;
    }}

    .analytics-box {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
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
      font-size: 13px;
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
      box-shadow: var(--shadow);
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
      border: 0;
      border-radius: 999px;
      padding: 4px 10px;
      margin: 0 8px 8px 0;
      font-size: 12px;
      cursor: pointer;
    }}

    .tag.muted {{
      background: #f3f4f6;
      color: #6b7280;
      cursor: default;
    }}

    .item-snippet {{
      color: var(--text);
      font-size: 14px;
    }}

    .low-priority-box {{
      margin-top: 12px;
      background: #fff;
      border: 1px dashed var(--line);
      border-radius: 14px;
      padding: 12px 14px;
    }}

    .low-priority-box summary {{
      cursor: pointer;
      color: var(--sub);
      font-size: 14px;
    }}

    .low-priority-grid {{
      margin-top: 12px;
    }}

    .error-list {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px 20px 16px 36px;
      margin: 0;
      box-shadow: var(--shadow);
    }}

    .empty-box {{
      background: var(--card);
      border: 1px dashed var(--line);
      border-radius: 14px;
      padding: 18px;
      color: var(--sub);
    }}

    .footer {{
      margin-top: 32px;
      color: var(--sub);
      font-size: 13px;
      text-align: center;
    }}

    .hidden {{
      display: none !important;
    }}

    @media (max-width: 768px) {{
      .hero h1 {{
        font-size: 24px;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="hero">
      <h1>升学与专业决策信息聚合</h1>
      <p>按分类、标签和评分浏览招生、就业、保研与预算相关信息。</p>
      <div class="meta">
        最近更新：{safe_text(latest_payload.get("updated_at", ""))}；
        条目数：{safe_text(latest_payload.get("count", 0))}；
        错误数：{safe_text(len(errors))}
      </div>
    </header>

    <section class="stats">
      {build_summary_cards(items, errors)}
    </section>

    {render_filter_bar(items)}

    {analytics_html}

    <main id="contentRoot">
      {''.join(sections) if sections else '<p>暂无数据。</p>'}
    </main>

    {render_errors(errors)}

    <div class="footer">
      页面文件位于 docs/index.html
    </div>
  </div>

  <script>
    (function () {{
      const state = {{
        category: "全部",
        tag: "全部",
        sortMode: "score",
        hideLowPriority: false,
      }};

      const root = document.getElementById("contentRoot");

      function parseDate(value) {{
        if (!value) return 0;
        const t = Date.parse(value.replace(/年|月/g, "-").replace(/日/g, ""));
        return isNaN(t) ? 0 : t;
      }}

      function applySort(section) {{
        const grid = section.querySelector(".item-grid");
        if (!grid) return;

        const cards = Array.from(grid.querySelectorAll(".item-card"));
        cards.sort((a, b) => {{
          if (state.sortMode === "date") {{
            const ad = parseDate(a.querySelector(".item-meta span")?.textContent || "");
            const bd = parseDate(b.querySelector(".item-meta span")?.textContent || "");
            return bd - ad;
          }}
          const as = Number(a.dataset.score || 0);
          const bs = Number(b.dataset.score || 0);
          if (bs !== as) return bs - as;
          const at = a.querySelector(".item-title")?.textContent || "";
          const bt = b.querySelector(".item-title")?.textContent || "";
          return bt.localeCompare(at, "zh-CN");
        }});
        cards.forEach(card => grid.appendChild(card));
      }}

      function itemVisible(card) {{
        const categoryOk = state.category === "全部" || card.dataset.category === state.category;
        const tags = (card.dataset.tags || "").split("|").filter(Boolean);
        const tagOk = state.tag === "全部" || tags.includes(state.tag);
        const lowPriorityOk = !state.hideLowPriority || card.dataset.lowPriority !== "true";
        return categoryOk && tagOk && lowPriorityOk;
      }}

      function refresh() {{
        const sections = Array.from(root.querySelectorAll("[data-category-section]"));

        sections.forEach(section => {{
          const cards = Array.from(section.querySelectorAll(".item-card"));
          let visibleCount = 0;

          cards.forEach(card => {{
            const visible = itemVisible(card);
            card.classList.toggle("hidden", !visible);
            if (visible) visibleCount += 1;
          }});

          applySort(section);

          const countNode = section.querySelector(".section-count");
          if (countNode) {{
            countNode.textContent = visibleCount + " 条";
          }}

          section.classList.toggle("hidden", visibleCount === 0);
        }});

        document.querySelectorAll("[data-category-filter]").forEach(btn => {{
          btn.classList.toggle("active", btn.dataset.categoryFilter === state.category);
        }});

        document.querySelectorAll("[data-tag-filter]").forEach(btn => {{
          btn.classList.toggle("active", btn.dataset.tagFilter === state.tag);
        }});

        document.querySelectorAll("[data-sort-mode]").forEach(btn => {{
          btn.classList.toggle("active", btn.dataset.sortMode === state.sortMode);
        }});

        const lowBtn = document.getElementById("toggleLowPriority");
        if (lowBtn) {{
          lowBtn.classList.toggle("active", state.hideLowPriority);
        }}
      }}

      document.querySelectorAll("[data-category-filter]").forEach(btn => {{
        btn.addEventListener("click", () => {{
          state.category = btn.dataset.categoryFilter;
          refresh();
        }});
      }});

      document.querySelectorAll("[data-tag-filter]").forEach(btn => {{
        btn.addEventListener("click", () => {{
          state.tag = btn.dataset.tagFilter;
          refresh();
        }});
      }});

      document.querySelectorAll(".filter-tag").forEach(btn => {{
        btn.addEventListener("click", () => {{
          state.tag = btn.dataset.tag;
          refresh();
        }});
      }});

      document.querySelectorAll("[data-sort-mode]").forEach(btn => {{
        btn.addEventListener("click", () => {{
          state.sortMode = btn.dataset.sortMode;
          refresh();
        }});
      }});

      const lowBtn = document.getElementById("toggleLowPriority");
      if (lowBtn) {{
        lowBtn.addEventListener("click", () => {{
          state.hideLowPriority = !state.hideLowPriority;
          refresh();
        }});
      }}

      refresh();
    }})();
  </script>
</body>
</html>
"""
    DOCS_INDEX_HTML.write_text(page, encoding="utf-8")
