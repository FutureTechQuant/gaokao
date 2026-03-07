from datetime import datetime, timezone, timedelta

from crawler.config import DISCOVERED_JSON
from crawler.discover.seeds import load_seed_urls
from crawler.discover.scanner import scan_url
from crawler.discover.matcher import match_topics
from crawler.discover.promote import promote_candidates
from crawler.storage.writer import write_json


def main():
    fetched_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    candidates = []

    for seed in load_seed_urls():
        try:
            results = scan_url(seed)
            for row in results:
                row["topics"] = match_topics(row.get("title", ""))
                candidates.append(row)
        except Exception as exc:
            candidates.append({
                "title": "",
                "href": "",
                "source_page": seed,
                "topics": [],
                "error": str(exc),
            })

    promoted = promote_candidates(candidates)

    payload = {
        "updated_at": fetched_at,
        "count": len(promoted),
        "items": promoted,
    }
    write_json(DISCOVERED_JSON, payload)


if __name__ == "__main__":
    main()
