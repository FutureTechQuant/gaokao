from crawler.extractors.generic import extract_generic_items


def test_extract_generic_items():
    source = {
        "name": "demo",
        "url": "https://example.com",
        "topic": "admissions",
        "allow_domains": ["example.com"],
        "must_include": ["招生"],
        "exclude_keywords": [],
    }
    html = '<a href="/a.html">本科招生章程</a>'
    items = extract_generic_items(source, html)
    assert len(items) == 1
