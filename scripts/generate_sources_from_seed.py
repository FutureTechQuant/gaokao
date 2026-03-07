from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "config" / "schools_seed.generated.yaml"
OUT_DIR = ROOT / "config" / "sources" / "generated"
OUT_FILE = OUT_DIR / "official_candidates.generated.yaml"

OUT_DIR.mkdir(parents=True, exist_ok=True)

TOPIC_RULES = {
    "admissions": {
        "must_include": ["招生", "本科招生", "招生章程", "招生计划", "录取"],
        "exclude_keywords": ["研究生", "博士", "硕士", "继续教育"],
    },
    "info": {
        "must_include": ["信息公开", "本科教学质量", "就业质量", "预算", "决算"],
        "exclude_keywords": [],
    },
    "careers": {
        "must_include": ["就业", "就业质量", "毕业生", "就业去向", "升学"],
        "exclude_keywords": ["研究生招生", "采购"],
    },
    "budgets": {
        "must_include": ["预算", "决算", "财务", "信息公开"],
        "exclude_keywords": ["采购", "招标"],
    },
    "recommendation": {
        "must_include": ["推免", "保研", "推荐免试", "教务"],
        "exclude_keywords": ["研究生招生"],
    },
}


def normalize_text(text: str) -> str:
    return (text or "").strip()


def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_source(
    school_name: str,
    topic: str,
    entry: str,
    allow_domains: list[str],
    tags: list[str],
    region: str,
) -> dict:
    rules = TOPIC_RULES[topic]
    all_tags = unique_keep_order(([region] if region else []) + tags + ["自动生成", "待核验"])

    return {
        "name": f"{school_name}{topic_name(topic)}",
        "enabled": True,
        "source_type": "official",
        "platform": "website",
        "topic": topic,
        "mode": "crawl",
        "trust_level": "medium",
        "verification_status": "pending",
        "source_origin": "zhangshanggaokao",
        "entry": entry,
        "allow_domains": unique_keep_order(allow_domains + [host_of(entry)]),
        "must_include": rules["must_include"],
        "exclude_keywords": rules["exclude_keywords"],
        "tags": all_tags,
    }


def topic_name(topic: str) -> str:
    mapping = {
        "admissions": "本科招生",
        "info": "信息公开",
        "careers": "就业质量",
        "budgets": "预算公开",
        "recommendation": "保研推免",
    }
    return mapping.get(topic, topic)


def main():
    if not SEED_FILE.exists():
        raise FileNotFoundError(f"seed file not found: {SEED_FILE}")

    payload = yaml.safe_load(SEED_FILE.read_text(encoding="utf-8")) or {}
    schools = payload.get("schools", [])

    generated_sources = []
    seen = set()

    for row in schools:
        if not isinstance(row, dict):
            continue

        school_name = normalize_text(row.get("name", ""))
        if not school_name:
            continue

        region = normalize_text(row.get("region", ""))
        tags = row.get("tags") or []
        allow_domains = row.get("allow_domains") or []

        topic_to_url = {
            "admissions": normalize_text(row.get("admissions_url", "")),
            "info": normalize_text(row.get("info_url", "")),
            "careers": normalize_text(row.get("careers_url", "")),
            "budgets": normalize_text(row.get("budgets_url", "")),
            "recommendation": normalize_text(row.get("recommendation_url", "")),
        }

        for topic, entry in topic_to_url.items():
            if not entry or not entry.startswith("http"):
                continue

            key = (school_name, topic, entry)
            if key in seen:
                continue
            seen.add(key)

            generated_sources.append(
                build_source(
                    school_name=school_name,
                    topic=topic,
                    entry=entry,
                    allow_domains=allow_domains,
                    tags=tags,
                    region=region,
                )
            )

    generated_sources.sort(key=lambda x: (str(x.get("name", "")), str(x.get("entry", ""))))

    out = {"sources": generated_sources}
    OUT_FILE.write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    print(f"generated source candidates: {OUT_FILE}")
    print(f"sources: {len(generated_sources)}")


if __name__ == "__main__":
    main()
