def validate_item(item: dict) -> bool:
    required = ["id", "title", "url", "source", "topic"]
    return all(item.get(key) for key in required)
