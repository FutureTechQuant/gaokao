def dedup_items(items: list[dict]) -> list[dict]:
    index = {}
    for item in items:
        key = item.get("url") or item.get("id")
        old = index.get(key)
        if not old or item.get("score", 0) > old.get("score", 0):
            index[key] = item
    return sorted(index.values(), key=lambda x: (x.get("date", ""), x.get("score", 0)), reverse=True)
