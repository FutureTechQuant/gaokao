def build_major_change_metrics(items: list[dict]) -> dict:
    added = [i for i in items if "新增专业" in i.get("title", "")]
    removed = [i for i in items if "撤销专业" in i.get("title", "")]
    return {
        "added_count": len(added),
        "removed_count": len(removed),
    }
