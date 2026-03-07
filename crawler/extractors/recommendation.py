from crawler.extractors.generic import extract_generic_items

def extract_items(source: dict, html: str) -> list[dict]:
    return extract_generic_items(source, html)
