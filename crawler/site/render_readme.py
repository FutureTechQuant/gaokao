from pathlib import Path

from crawler.config import ROOT


def render_readme(latest_payload: dict) -> None:
    readme = Path(ROOT / "README.md")
    lines = [
        "# gaokao",
        "",
        "面向高考、专业、就业与升学决策的信息聚合项目。",
        "",
        f"- 最近更新：{latest_payload.get('updated_at', '')}",
        f"- 条目数：{latest_payload.get('count', 0)}",
        f"- 错误数：{len(latest_payload.get('errors', []))}",
        "",
        "## 当前分类",
        "",
        "- 报考政策",
        "- 招生信息",
        "- 专业趋势",
        "- 就业质量",
        "- 保研信息",
        "- 学校预算",
        "- 国企要求",
        "- 选调生政策",
        "- 国家重点实验室",
        "- 产业链分析",
        "- 消失专业",
        "- 公务员岗位适配度",
    ]
    readme.write_text("\n".join(lines), encoding="utf-8")
