def filter_pdf_items(items: list[dict]) -> list[dict]:
    return [item for item in items if item.get("is_pdf")]
