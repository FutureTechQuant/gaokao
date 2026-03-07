# scripts/generate_sources_from_seed.py
from __future__ import annotations

from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "config" / "schools_seed.generated.yaml"
OUT_DIR = ROOT / "config" / "sources" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^0-9a-z_\u4e00-\u9fa5-]", "", text)
    return text or "unknown"

def build_source(name: str, topic: str, entry: str, allow_domains: list[str], tags: list[str]):
    return {
        "name": f"{name}-{topic}",
        "enabled": True,
        "source_type": "official_candidate",
        "platform": "website",
        "topic": topic,
        "mode": "crawl",
        "trust_level": "medium",
        "verification_status": "pending",
        "entry": entry,
        "allow_domains": allow_domains,
        "must_include": [],
        "exclude_keywords": ["研究生", "博士", "硕士"] if topic == "admissions" else [],
        "tags": tags,
    }

def main():
    payload = yaml.safe_load(SEED_FILE.read_text(encoding="utf-8")) or {}
    schools = payload.get("schools", [])

    for row in schools:
        if not isinstance(row, dict):
            continue

        school_name = row.get("name", "").strip()
        if not school_name:
            continue

        tags = list(dict.fromkeys((row.get("tags") or []) + ["自动生成", "待核验"]))
        allow_domains = row.get("allow_domains") or []
        sources = []

        admissions_url = row.get("admissions_url") or ""
        info_url = row.get("info_url") or ""
        careers_url = row.get("careers_url") or ""
        budgets_url = row.get("budgets_url") or ""
        recommendation_url = row.get("recommendation_url") or ""

        if admissions_url:
            sources.append(build_source(school_name, "admissions", admissions_url, allow_domains, tags))
        if info_url:
            sources.append(build_source(school_name, "info", info_url, allow_domains, tags))
        if careers_url:
            sources.append(build_source(school_name, "careers", careers_url, allow_domains, tags))
        if budgets_url:
            sources.append(build_source(school_name, "budgets", budgets_url, allow_domains, tags))
        if recommendation_url:
            sources.append(build_source(school_name, "recommendation", recommendation_url, allow_domains, tags))

        if not sources:
            continue

        out = {"sources": sources}
        out_file = OUT_DIR / f"{slugify(school_name)}.yaml"
        out_file.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")

if __name__ == "__main__":
    main()
