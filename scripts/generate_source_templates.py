from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[1]
AUTO_SEED_FILE = ROOT / "config" / "schools_seed.generated.yaml"
MANUAL_SEED_FILE = ROOT / "config" / "schools_seed.yaml"
OUTPUT_DIR = ROOT / "config" / "sources" / "generated"


ADMISSIONS_MUST = [
    "本科招生", "招生章程", "招生计划", "录取", "录取查询", "历年分数", "分数线", "位次"
]
ADMISSIONS_EXCLUDE = [
    "研究生", "博士", "硕士", "继续教育", "留学生"
]

CAREERS_MUST = [
    "就业质量年度报告", "毕业生就业质量", "就业质量", "就业去向", "行业分布", "升学", "深造"
]
CAREERS_EXCLUDE = [
    "采购", "研究生招生", "招标"
]

RECOMMENDATION_MUST = [
    "推免", "保研", "推荐免试", "推免生", "夏令营", "预推免", "遴选办法", "实施办法"
]
RECOMMENDATION_EXCLUDE = [
    "博士后", "留学生", "成人教育"
]

BUDGETS_MUST = [
    "单位预算", "部门预算", "预算", "决算", "财务", "经费"
]
BUDGETS_EXCLUDE = [
    "采购", "招标", "中标", "成交公告"
]


def load_seed() -> list[dict]:
    seed_file = AUTO_SEED_FILE if AUTO_SEED_FILE.exists() else MANUAL_SEED_FILE
    payload = yaml.safe_load(seed_file.read_text(encoding="utf-8")) or {}
    schools = payload.get("schools", [])
    return [row for row in schools if isinstance(row, dict)]


def base_tags(school: dict, extra: list[str]) -> list[str]:
    tags = []
    for x in school.get("tags", []):
        if x and x not in tags:
            tags.append(x)
    for x in extra:
        if x and x not in tags:
            tags.append(x)
    return tags


def make_admissions(school: dict) -> dict | None:
    url = school.get("admissions_url", "").strip()
    if not url:
        return None
    return {
        "name": f"{school['name']}本科招生",
        "enabled": True,
        "source_type": "official",
        "platform": "website",
        "topic": "admissions",
        "mode": "crawl",
        "trust_level": "high",
        "entry": url,
        "allow_domains": school.get("allow_domains", []),
        "must_include": ADMISSIONS_MUST,
        "exclude_keywords": ADMISSIONS_EXCLUDE,
        "tags": base_tags(school, ["招生"]),
    }


def make_careers(school: dict) -> dict | None:
    url = school.get("careers_url", "").strip()
    if not url:
        return None
    return {
        "name": f"{school['name']}就业质量",
        "enabled": True,
        "source_type": "official",
        "platform": "website",
        "topic": "careers",
        "mode": "crawl",
        "trust_level": "high",
        "entry": url,
        "allow_domains": school.get("allow_domains", []),
        "must_include": CAREERS_MUST,
        "exclude_keywords": CAREERS_EXCLUDE,
        "tags": base_tags(school, ["就业", "就业质量报告"]),
    }


def make_recommendation(school: dict) -> dict | None:
    url = school.get("recommendation_url", "").strip()
    if not url:
        return None
    return {
        "name": f"{school['name']}保研推免",
        "enabled": True,
        "source_type": "official",
        "platform": "website",
        "topic": "recommendation",
        "mode": "crawl",
        "trust_level": "high",
        "entry": url,
        "allow_domains": school.get("allow_domains", []),
        "must_include": RECOMMENDATION_MUST,
        "exclude_keywords": RECOMMENDATION_EXCLUDE,
        "tags": base_tags(school, ["保研"]),
    }


def make_budgets(school: dict) -> dict | None:
    url = school.get("budgets_url", "").strip()
    if not url:
        return None
    return {
        "name": f"{school['name']}预算公开",
        "enabled": True,
        "source_type": "official",
        "platform": "website",
        "topic": "budgets",
        "mode": "crawl",
        "trust_level": "high",
        "entry": url,
        "allow_domains": school.get("allow_domains", []),
        "must_include": BUDGETS_MUST,
        "exclude_keywords": BUDGETS_EXCLUDE,
        "tags": base_tags(school, ["预算"]),
    }


def dump_yaml(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sources": rows}
    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(text, encoding="utf-8")


def main():
    schools = load_seed()

    admissions = []
    careers = []
    recommendation = []
    budgets = []

    for school in schools:
        row = make_admissions(school)
        if row:
            admissions.append(row)

        row = make_careers(school)
        if row:
            careers.append(row)

        row = make_recommendation(school)
        if row:
            recommendation.append(row)

        row = make_budgets(school)
        if row:
            budgets.append(row)

    dump_yaml(OUTPUT_DIR / "admissions.generated.yaml", admissions)
    dump_yaml(OUTPUT_DIR / "careers.generated.yaml", careers)
    dump_yaml(OUTPUT_DIR / "recommendation.generated.yaml", recommendation)
    dump_yaml(OUTPUT_DIR / "budgets.generated.yaml", budgets)

    print(f"generated schools={len(schools)}")
    print(f"admissions={len(admissions)}")
    print(f"careers={len(careers)}")
    print(f"recommendation={len(recommendation)}")
    print(f"budgets={len(budgets)}")


if __name__ == "__main__":
    main()
