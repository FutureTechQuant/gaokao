from collections import Counter
from pathlib import Path

from crawler.config import ROOT


CATEGORY_ORDER = [
    "招生信息",
    "就业质量",
    "保研信息",
    "学校预算",
    "专业趋势",
    "报考政策",
    "未分类",
]


def render_count_block(lines: list[str], rows: list[tuple[str, int]], empty_text: str):
    if not rows:
        lines.append(empty_text)
        return
    for name, count in rows:
        lines.append(f"- {name}：{count}")


def render_source_summary(lines: list[str], source_summary: dict):
    if not source_summary:
        lines.append("- 暂无信源摘要")
        return

    lines.append(f"- 信源总数：{source_summary.get('total_sources', 0)}")

    by_type = source_summary.get("by_type", {})
    if by_type:
        lines.append("- 按信源类型：")
        for name, count in sorted(by_type.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {name}：{count}")

    by_platform = source_summary.get("by_platform", {})
    if by_platform:
        lines.append("- 按平台：")
        for name, count in sorted(by_platform.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {name}：{count}")

    by_topic = source_summary.get("by_topic", {})
    if by_topic:
        lines.append("- 按专题：")
        for name, count in sorted(by_topic.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {name}：{count}")


def render_readme(latest_payload: dict) -> None:
    readme = Path(ROOT / "README.md")
    items = latest_payload.get("items", [])
    errors = latest_payload.get("errors", [])
    source_summary = latest_payload.get("source_summary", {})

    category_counts = Counter(item.get("category", "未分类") for item in items)
    topic_counts = Counter(item.get("topic", "综合信息") for item in items)
    platform_counts = Counter(item.get("platform", "unknown") for item in items)
    source_type_counts = Counter(item.get("source_type", "unknown") for item in items)
    trust_counts = Counter(item.get("trust_level", "unknown") for item in items)

    tag_values = []
    for item in items:
        tag_values.extend(item.get("tags", []))
    tag_counts = Counter(tag_values)

    top_items = sorted(
        items,
        key=lambda x: (
            int(x.get("score", 0)),
            x.get("date", ""),
            x.get("title", ""),
        ),
        reverse=True,
    )[:20]

    lines = [
        "# gaokao",
        "",
        "面向高考、专业、就业与升学决策的信息聚合项目。",
        "",
        "## 运行概况",
        "",
        f"- 最近更新：{latest_payload.get('updated_at', '')}",
        f"- 条目数：{latest_payload.get('count', 0)}",
        f"- 错误数：{len(errors)}",
        "",
        "## 信源摘要",
        "",
    ]

    render_source_summary(lines, source_summary)

    lines.extend([
        "",
        "## 分类摘要",
        "",
    ])

    has_category = False
    for category in CATEGORY_ORDER:
        count
