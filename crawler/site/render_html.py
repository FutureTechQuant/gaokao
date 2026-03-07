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

SOURCE_TYPE_ORDER = [
    "official",
    "platform",
    "community",
    "unknown",
]

SOURCE_TYPE_LABELS = {
    "official": "官方",
    "platform": "平台",
    "community": "社区",
    "unknown": "未知",
    "全部": "全部",
}

TRUST_LABELS = {
    "high": "高可信",
    "medium": "中可信",
    "low": "低可信",
    "unknown": "未知",
}

LOW_PRIORITY_HINTS = [
    "活动",
    "开笔",
    "报道",
    "纪实",
    "新闻",
    "仪式",
    "典礼",
    "论坛",
    "讲座",
    "采访",
    "交流会",
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
        row.setdefault("platform", "website")
        row.setdefault("source_type", "unknown")
        row.setdefault("trust_level", "unknown")
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


def build_summary_cards(items: list[dict], errors: list[dict], source_summary: dict) -> str:
    category_count = {}
    pdf_count = 0
    official_count = 0
    platform_count = 0
    community_count = 0

    for item in items:
        category = item.get("category", "未分类")
        category_count[category] = category_count.get(category, 0) + 1
        if item.get("is_pdf"):
            pdf_count += 1
        if item.get("source_type") == "official":
            official_count += 1
        if item.get("source_type") == "platform":
            platform_count += 1
        if item.get("source_type") == "community":
            community_count += 1

    cards = [
        ("结果总数", len(items)),
        ("PDF", pdf_count),
        ("官方结果", official_count),
        ("平台结果", platform_count),
        ("社区结果", community_count),
        ("抓取错误", len(errors)),
        ("信源总数", source_summary.get("total_sources", 0)),
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


def trust_badge(trust_level: str) -> str:
    label = TRUST_LABELS.get(trust_level, trust_level or "未知")
    cls = {
        "high": "trust-high",
        "medium": "trust-medium",
        "low": "trust-low",
    }.get(trust_level, "trust-unknown")
    return f'<span class="trust-badge {cls}">{safe_text(label)}</span>'


def source_type_label(source_type: str) -> str:
    return SOURCE_TYPE_LABELS.get(source_type, source_type or "未知")


def render_item(item: dict) -> str:
    title = safe_text(item.get("title"))
    url = safe_text(item.get("url"))
    source = safe_text(item.get("source"))
    date = safe_text(item.get("date") or "未知日期")
    topic = safe_text(item.get("topic") or "综合信息")
    snippet = safe_text(item.get("snippet"))
    score = safe_text(item.get("score", 0))
    item_type = "PDF" if item.get("is_pdf") else "网页"
    platform = safe_text(item.get("platform", "website"))
    source_type = safe_text(source_type_label(item.get("source_type", "unknown")))
    trust = item.get("trust_level", "unknown")
    trust_label = TRUST_LABELS.get(trust, trust or "未知")
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
      data-source-type="{safe_text(item.get('source_type', 'unknown'))}"
      data-platform="{platform}"
      data-trust-level="{safe_text(trust)}"
      data-date="{date}"
    >
      <div class="item-header">
        <a class="item-title" href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
        <div class="item-badges">
          <span class="meta-badge">{source_type}</span>
          <span class="meta-badge">{platform}</span>
          {trust_badge(trust)}
        </div>
      </div>
      <div class="item-meta">
        <span>日期：{date}</span>
        <span>来源：{source}</span>
        <span>专题：{topic}</span>
        <span>类型：{item_type}</span>
        <span>可信度：{safe_text(trust_label)}</span>
        <span>评分：{score}</span>
      </div>
      <div class="item-tags">{render_tags(tags)}</div>
      <div class="item-snippet">{snippet or "暂无摘要"}</div>
    </article>
    """


def render_category_section(category: str, items: list[dict]) -> str:
    if not items:
        return ""

    groups = OrderedDict()
    for key in SOURCE_TYPE_ORDER:
        groups[key] = []
    for item in items:
        source_type = item.get("source_type", "unknown")
        if source_type not in groups:
            groups[source_type] = []
        groups[source_type].append(item)

    blocks = []
    for source_type, rows in groups.items():
        if not rows:
            continue

        high_items = [item for item in rows if not is_low_priority_news(item)]
        low_items = [item for item in rows if is_low_priority_news(item)]

        high_html = "".join(render_item(item) for item in high_items[:120])
        low_html = "".join(render_item(item) for item in low_items[:120])

        low_block = ""
        if low_items:
            low_block = f"""
            <details class="low-priority-box">
              <summary>展开低优先级内容（{len(low_items)} 条）</summary>
              <div class="item-grid low-priority-grid">
                {low_html}
              </div>
            </details>
            """

        blocks.append(
            f"""
            <div class="source-type-block" data-source-type-block="{safe_text(source_type)}">
              <div class="sub-head">
                <h3>{safe_text(source_type_label(source_type))}</h3>
                <span class="section-count">{len(rows)} 条</span>
              </div>
              <div class="item-grid">
                {high_html if high_html else '<div class="empty-box">暂无高优先级内容</div>'}
              </div>
              {low_block}
            </div>
            """
        )

    return f"""
    <section class="category-section" data-category-section="{safe_text(category)}">
      <div class="section-head">
        <h2>{safe_text(category)}</h2>
        <span class="section-count total-category-count">{len(items)} 条</span>
      </div>
      {''.join(blocks)}
    </section>
    """


def render_errors(errors: list[dict]) -> str:
    if not errors:
        return ""

    items = []
    for err in errors[:20]:
        items.append(
            f"<li>{safe_text(err.get('source'))} | {safe_text(err.get('platform'))} | {safe_text(err.get('url'))} | {safe_text(err.get('error'))}</li>"
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


def render_top_tabs() -> str:
    return f"""
    <section class="tabbar-wrap">
      <div class="tabbar" role="tablist" aria-label="信源类型切换">
        <button type="button" class="top-tab active" role="tab" aria-selected="true" data-source-type-filter="全部">{safe_text(SOURCE_TYPE_LABELS['全部'])}</button>
        <button type="button" class="top-tab" role="tab" aria-selected="false" data-source-type-filter="official">{safe_text(SOURCE_TYPE_LABELS['official'])}</button>
        <button type="button" class="top-tab" role="tab" aria-selected="false" data-source-type-filter="platform">{safe_text(SOURCE_TYPE_LABELS['platform'])}</button>
        <button type="button" class="top-tab" role="tab" aria-selected="false" data-source-type-filter="community">{safe_text(SOURCE_TYPE_LABELS['community'])}</button>
      </div>
    </section>
    """


def render_filter_bar(items: list[dict]) -> str:
    tags = collect_all_tags(items)
    tag_buttons = "".join(
        f'<button type="button" class="toolbar-btn" data-tag-filter="{safe_text(tag)}">{safe_text(tag)}</button>'
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
          <button type="button" class="toolbar-btn" id="toggleLowPriority">隐藏低优先级</button>
          <button type="button" class="toolbar-btn danger-btn" id="clearAllFilters">清空联动筛选</button>
        </div>
        <div class="toolbar-row toolbar-tags">
          <span class="toolbar-label">标签</span>
          <button type="button" class="toolbar-btn active" data-tag-filter="全部">全部</button>
          {tag_buttons}
        </div>
      </div>
    </section>
    """


def render_active_filters_bar() -> str:
    return """
    <section class="active-filters-panel" id="activeFiltersPanel">
      <div class="active-filters-head">
        <div class="active-filters-title">当前联动筛选</div>
        <button type="button" class="toolbar-btn danger-btn small-btn" id="clearAllFiltersInline">清空</button>
      </div>
      <div class="active-filter-chips" id="activeFilterChips"></div>
    </section>
    """


def render_kv_cards(title: str, data: dict, action_key: str | None = None, empty_text: str = "暂无数据") -> str:
    if not data:
        return f"""
        <div class="summary-group">
          <div class="summary-group-title">{safe_text(title)}</div>
          <div class="summary-empty">{safe_text(empty_text)}</div>
        </div>
        """

    cards = []
    for name, value in data.items():
        action_attrs = ""
        clickable_cls = " clickable-card" if action_key else ""
        if action_key:
            action_attrs = (
                f' data-action-key="{safe_text(action_key)}"'
                f' data-action-value="{safe_text(name)}"'
                f' role="button" tabindex="0"'
            )

        cards.append(
            f"""
            <div class="mini-stat-card{clickable_cls}"{action_attrs}>
              <div class="mini-stat-name">{safe_text(name)}</div>
              <div class="mini-stat-value">{safe_text(value)}</div>
            </div>
            """
        )

    return f"""
    <div class="summary-group">
      <div class="summary-group-title">{safe_text(title)}</div>
      <div class="mini-stat-grid">
        {''.join(cards)}
      </div>
    </div>
    """


def render_source_summary(source_summary: dict) -> str:
    if not source_summary:
        return """
        <section class="summary-panel">
          <div class="section-head">
            <h2>信源摘要</h2>
            <span class="section-count">暂无数据</span>
          </div>
          <div class="empty-box">暂无信源摘要</div>
        </section>
        """

    top_cards = f"""
    <div class="summary-top-grid">
      <div class="stat-card">
        <div class="stat-name">信源总数</div>
        <div class="stat-value">{safe_text(source_summary.get('total_sources', 0))}</div>
      </div>
      <div class="stat-card">
        <div class="stat-name">结果总数</div>
        <div class="stat-value">{safe_text(source_summary.get('results_total', 0))}</div>
      </div>
    </div>
    """

    groups = [
        render_kv_cards("信源-按类型", source_summary.get("by_type", {}), "sourceType"),
        render_kv_cards("信源-按平台", source_summary.get("by_platform", {}), "platform"),
        render_kv_cards("信源-按专题", source_summary.get("by_topic", {}), "topic"),
        render_kv_cards("信源-按可信度", source_summary.get("by_trust_level", {}), "trustLevel"),
        render_kv_cards("结果-按类型", source_summary.get("results_by_source_type", {}), "sourceType"),
        render_kv_cards("结果-按平台", source_summary.get("results_by_platform", {}), "platform"),
        render_kv_cards("结果-按专题", source_summary.get("results_by_topic", {}), "topic"),
        render_kv_cards("结果-按可信度", source_summary.get("results_by_trust_level", {}), "trustLevel"),
        render_kv_cards("结果-按分类", source_summary.get("results_by_category", {}), "category"),
    ]

    return f"""
    <section class="summary-panel">
      <div class="section-head">
        <h2>信源摘要</h2>
        <span class="section-count">点击卡片可联动过滤</span>
      </div>
      {top_cards}
      <div class="summary-groups">
        {''.join(groups)}
      </div>
    </section>
    """


def render_site(latest_payload: dict, analytics: dict) -> None:
    items = normalize_items(latest_payload.get("items", []))
    errors = latest_payload.get("errors", [])
    source_summary = latest_payload.get("source_summary", {})

    grouped = group_by_category(items)
    sections = []

    for category, rows in grouped.items():
        html = render_category_section(category, rows)
        if html:
            sections.append(html)

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
      --brand-2: #1d4ed8;
      --tag: #eef2ff;
      --chip: #f8fafc;
      --shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    }}

    * {{ box-sizing: border-box; }}

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
      margin-bottom: 16px;
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

    .tabbar-wrap {{
      margin-bottom: 14px;
    }}

    .tabbar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      background: rgba(255,255,255,0.96);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px;
      box-shadow: var(--shadow);
    }}

    .top-tab {{
      border: 1px solid var(--line);
      background: var(--chip);
      color: var(--text);
      border-radius: 999px;
      padding: 9px 14px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      min-height: 42px;
    }}

    .top-tab.active {{
      background: var(--brand);
      border-color: var(--brand);
      color: #fff;
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

    .summary-panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
    }}

    .summary-top-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}

    .summary-groups {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
    }}

    .summary-group {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      background: #fcfdff;
    }}

    .summary-group-title {{
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 10px;
      color: var(--text);
    }}

    .mini-stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      gap: 10px;
    }}

    .mini-stat-card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
    }}

    .mini-stat-card.clickable-card {{
      cursor: pointer;
    }}

    .mini-stat-card.clickable-card:hover {{
      transform: translateY(-1px);
      box-shadow: var(--shadow);
      border-color: #c7d2fe;
    }}

    .mini-stat-card.active {{
      border-color: var(--brand);
      background: #eff6ff;
    }}

    .mini-stat-name {{
      font-size: 12px;
      color: var(--sub);
      margin-bottom: 4px;
      word-break: break-word;
    }}

    .mini-stat-value {{
      font-size: 20px;
      font-weight: 700;
      color: var(--brand);
    }}

    .summary-empty {{
      color: var(--sub);
      font-size: 13px;
    }}

    .toolbar-wrap {{
      position: sticky;
      top: 0;
      z-index: 20;
      margin-bottom: 16px;
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

    .danger-btn {{
      color: #b91c1c;
    }}

    .small-btn {{
      padding: 5px 10px;
      font-size: 12px;
    }}

    .active-filters-panel {{
      display: none;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      margin-bottom: 18px;
      box-shadow: var(--shadow);
    }}

    .active-filters-panel.show {{
      display: block;
    }}

    .active-filters-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }}

    .active-filters-title {{
      font-size: 14px;
      font-weight: 700;
    }}

    .active-filter-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .active-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #eef2ff;
      color: #3730a3;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
    }}

    .chip-x {{
      border: 0;
      background: transparent;
      color: inherit;
      cursor: pointer;
      font-size: 12px;
      padding: 0;
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

    .section-head h2, .sub-head h3 {{
      margin: 0;
    }}

    .sub-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 12px 0 10px;
    }}

    .section-count {{
      color: var(--sub);
      font-size: 14px;
    }}

    .source-type-block {{
      margin-bottom: 16px;
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

    .item-header {{
      display: flex;
      gap: 12px;
      align-items: flex-start;
      justify-content: space-between;
    }}

    .item-title {{
      color: var(--brand);
      text-decoration: none;
      font-size: 18px;
      font-weight: 600;
      flex: 1;
    }}

    .item-title:hover {{
      text-decoration: underline;
    }}

    .item-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: flex-end;
    }}

    .meta-badge, .trust-badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      white-space: nowrap;
    }}

    .meta-badge {{
      background: #eef2ff;
      color: #3730a3;
    }}

    .trust-high {{
      background: #dcfce7;
      color: #166534;
    }}

    .trust-medium {{
      background: #fef3c7;
      color: #92400e;
    }}

    .trust-low, .trust-unknown {{
      background: #f3f4f6;
      color: #4b5563;
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

      .item-header {{
        flex-direction: column;
      }}

      .item-badges {{
        justify-content: flex-start;
      }}

      .summary-groups {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="hero">
      <h1>升学与专业决策信息聚合</h1>
      <p>按分类、标签、信源类型与可信度浏览招生、就业、保研与预算相关信息。</p>
      <div class="meta">
        最近更新：{safe_text(latest_payload.get("updated_at", ""))}；
        结果数：{safe_text(latest_payload.get("count", 0))}；
        错误数：{safe_text(len(errors))}
      </div>
    </header>

    {render_top_tabs()}

    <section class="stats">
      {build_summary_cards(items, errors, source_summary)}
    </section>

    {render_source_summary(source_summary)}

    {render_filter_bar(items)}

    {render_active_filters_bar()}

    <details class="analytics-box">
      <summary>分析摘要</summary>
      <pre>{safe_text(json.dumps(analytics, ensure_ascii=False, indent=2))}</pre>
    </details>

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
        sourceType: "全部",
        platform: "全部",
        trustLevel: "全部",
        topic: "全部",
        sortMode: "score",
        hideLowPriority: false,
      }};

      const root = document.getElementById("contentRoot");
      const activeFiltersPanel = document.getElementById("activeFiltersPanel");
      const activeFilterChips = document.getElementById("activeFilterChips");

      function parseDate(value) {{
        if (!value) return 0;
        const t = Date.parse(value);
        return isNaN(t) ? 0 : t;
      }}

      function itemVisible(card) {{
        const categoryOk = state.category === "全部" || card.dataset.category === state.category;
        const sourceTypeOk = state.sourceType === "全部" || card.dataset.sourceType === state.sourceType;
        const platformOk = state.platform === "全部" || card.dataset.platform === state.platform;
        const trustOk = state.trustLevel === "全部" || card.dataset.trustLevel === state.trustLevel;
        const topicOk = state.topic === "全部" || card.dataset.topic === state.topic;
        const tags = (card.dataset.tags || "").split("|").filter(Boolean);
        const tagOk = state.tag === "全部" || tags.includes(state.tag);
        const lowPriorityOk = !state.hideLowPriority || card.dataset.lowPriority !== "true";
        return categoryOk && sourceTypeOk && platformOk && trustOk && topicOk && tagOk && lowPriorityOk;
      }}

      function sortCards(cards) {{
        return cards.sort((a, b) => {{
          if (state.sortMode === "date") {{
            return parseDate(b.dataset.date) - parseDate(a.dataset.date);
          }}
          const bs = Number(b.dataset.score || 0);
          const as = Number(a.dataset.score || 0);
          if (bs !== as) return bs - as;
          return (b.dataset.date || "").localeCompare(a.dataset.date || "", "zh-CN");
        }});
      }}

      function syncTopTabs() {{
        document.querySelectorAll(".top-tab").forEach(btn => {{
          const active = btn.dataset.sourceTypeFilter === state.sourceType;
          btn.classList.toggle("active", active);
          btn.setAttribute("aria-selected", active ? "true" : "false");
        }});
      }}

      function syncToolbarButtons() {{
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

      function syncSummaryCards() {{
        document.querySelectorAll(".mini-stat-card[data-action-key]").forEach(card => {{
          const key = card.dataset.actionKey;
          const value = card.dataset.actionValue;
          const active = state[key] === value;
          card.classList.toggle("active", active);
        }});
      }}

      function renderActiveFilterChips() {{
        const labels = {{
          category: "分类",
          tag: "标签",
          sourceType: "来源",
          platform: "平台",
          trustLevel: "可信度",
          topic: "专题",
        }};

        const valueLabels = {{
          sourceType: {{
            "official": "官方",
            "platform": "平台",
            "community": "社区",
            "unknown": "未知",
            "全部": "全部"
          }},
          trustLevel: {{
            "high": "高可信",
            "medium": "中可信",
            "low": "低可信",
            "unknown": "未知",
            "全部": "全部"
          }}
        }};

        const rows = [];
        ["sourceType", "category", "platform", "trustLevel", "topic", "tag"].forEach(key => {{
          if (state[key] && state[key] !== "全部") {{
            const label = labels[key] || key;
            const pretty = (valueLabels[key] && valueLabels[key][state[key]]) || state[key];
            rows.push(
              '<span class="active-chip">' +
              label + '：' + pretty +
              ' <button type="button" class="chip-x" data-clear-key="' + key + '">×</button>' +
              '</span>'
            );
          }}
        }});

        activeFilterChips.innerHTML = rows.join("");
        activeFiltersPanel.classList.toggle("show", rows.length > 0);

        document.querySelectorAll("[data-clear-key]").forEach(btn => {{
          btn.addEventListener("click", () => {{
            state[btn.dataset.clearKey] = "全部";
            refresh();
          }});
        }});
      }}

      function sortAllVisibleGrids() {{
        document.querySelectorAll(".item-grid").forEach(grid => {{
          const cards = Array.from(grid.querySelectorAll(":scope > .item-card"));
          const sorted = sortCards(cards);
          sorted.forEach(card => grid.appendChild(card));
        }});
      }}

      function refresh() {{
        const sections = Array.from(root.querySelectorAll("[data-category-section]"));

        sections.forEach(section => {{
          let categoryVisibleCount = 0;

          const sourceTypeBlocks = Array.from(section.querySelectorAll("[data-source-type-block]"));
          sourceTypeBlocks.forEach(block => {{
            const cards = Array.from(block.querySelectorAll(".item-card"));

            cards.forEach(card => {{
              const visible = itemVisible(card);
              card.classList.toggle("hidden", !visible);
              if (visible) categoryVisibleCount += 1;
            }});

            const visibleCards = cards.filter(card => !card.classList.contains("hidden")).length;
            block.classList.toggle("hidden", visibleCards === 0);

            const countNode = block.querySelector(".section-count");
            if (countNode) {{
              countNode.textContent = visibleCards + " 条";
            }}
          }});

          const totalNode = section.querySelector(".total-category-count");
          if (totalNode) {{
            totalNode.textContent = categoryVisibleCount + " 条";
          }}

          section.classList.toggle("hidden", categoryVisibleCount === 0);
        }});

        sortAllVisibleGrids();
        syncTopTabs();
        syncToolbarButtons();
        syncSummaryCards();
        renderActiveFilterChips();
      }}

      document.querySelectorAll(".top-tab").forEach(btn => {{
        btn.addEventListener("click", () => {{
          state.sourceType = btn.dataset.sourceTypeFilter;
          refresh();
        }});
      }});

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

      document.querySelectorAll(".mini-stat-card[data-action-key]").forEach(card => {{
        const applyCardAction = () => {{
          const key = card.dataset.actionKey;
          const value = card.dataset.actionValue;
          state[key] = state[key] === value ? "全部" : value;
          refresh();
        }};

        card.addEventListener("click", applyCardAction);
        card.addEventListener("keydown", (event) => {{
          if (event.key === "Enter" || event.key === " ") {{
            event.preventDefault();
            applyCardAction();
          }}
        }});
      }});

      const lowBtn = document.getElementById("toggleLowPriority");
      if (lowBtn) {{
        lowBtn.addEventListener("click", () => {{
          state.hideLowPriority = !state.hideLowPriority;
          refresh();
        }});
      }}

      function clearAllFilters() {{
        state.category = "全部";
        state.tag = "全部";
        state.sourceType = "全部";
        state.platform = "全部";
        state.trustLevel = "全部";
        state.topic = "全部";
        state.sortMode = "score";
        state.hideLowPriority = false;
        refresh();
      }}

      const clearBtn = document.getElementById("clearAllFilters");
      if (clearBtn) {{
        clearBtn.addEventListener("click", clearAllFilters);
      }}

      const clearBtnInline = document.getElementById("clearAllFiltersInline");
      if (clearBtnInline) {{
        clearBtnInline.addEventListener("click", clearAllFilters);
      }}

      refresh();
    }})();
  </script>
</body>
</html>
"""
    DOCS_INDEX_HTML.write_text(page, encoding="utf-8")
