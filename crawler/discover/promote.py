def promote_candidates(candidates: list[dict]) -> list[dict]:
    promoted = []
    for item in candidates:
        if item.get("topics"):
            promoted.append(item)
    return promoted
