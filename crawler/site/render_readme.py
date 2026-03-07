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


def top_counts(values, limit=10):
    counter = Counter(v for v in values if v)
    return counter.most_common(limit)


def render_list(lines: list[str], rows: list[tuple[str, int]], empty_text: str):
    if not rows:
        lines.append(empty_text)
        return
    for name, count in rows:
        lines.append(f"- {name}：{count}")


def render_readme(latest_payload: dict) -> None:
    readme = Path(ROOT / "README.md")
    items = latest_payload.get("items", [])
    errors = latest_payload.get("errors", [])

    category_counts = Counter(item.get("category", "未分类") for item in items)
    topic_counts = Counter(item.get("topic", "综合信息") for item in items)

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
        "## 分类摘要",
        "",
    ]

    for category in CATEGORY_ORDER:
        count = category_counts.get(category, 0)
        if count:
            lines.append(f"- {category}：{count}")

    if not any(category_counts.values()):
        lines.append("- 暂无分类数据")

    lines.extend([
        "",
        "## 专题摘要",
        "",
    ])
    render_list(lines, top_counts(topic_counts.elements() if False else list(topic_counts.keys())), "- 暂无专题数据")
