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
            x.get("trust_level", ""),
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


def build_summary_cards(items: list[dict], errors: list[dict], source_summary: dict) -> str:
    category_count = {}
    pdf_count = 0
    official_count = 0
    platform_count = 0

    for item in items:
        category = item.get("category", "未分类")
        category_count[category] = category_count.get(category, 0) + 1
        if item.get("is_pdf"):
            pdf_count += 1
        if item.get("source_type") == "official":
            official_count += 1
        if item.get("source_type") == "platform":
            platform_count += 1

    cards = [
        ("结果总数", len(items)),
        ("PDF", pdf_count),
        ("官方结果", official_count),
        ("平台结果", platform_count),
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
    label = {
        "high": "高可信",
        "medium": "中可信",
        "low": "低可信",
    }.get(trust_level, trust_level or "未知")
    cls = {
        "high": "trust-high",
        "medium": "trust-medium",
        "low": "trust-low",
    }.get(trust_level, "trust-unknown")
    return f'<span class="trust-badge
