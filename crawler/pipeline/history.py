from crawler.config import HISTORY_JSON
from crawler.storage.reader import read_json


def merge_history(items: list[dict], fetched_at: str) -> dict:
    history = read_json(HISTORY_JSON, {"updated_at": "", "items": []})
    index = {item["id"]: item for item in history.get("items", []) if item.get("id")}

    for item in items:
        if item["id"] in index:
            old = index[item["id"]]
            old["last_seen_at"] = fetched_at
            old["seen_count"] = int(old.get("seen_count", 1)) + 1
            old.update(item)
        else:
            index[item["id"]] = {
                **item,
                "first_seen_at": fetched_at,
                "last_seen_at": fetched_at,
                "seen_count": 1,
            }

    return {
        "updated_at": fetched_at,
        "items": list(index.values()),
    }
