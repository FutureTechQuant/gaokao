from crawler.pipeline.dedup import dedup_items


def test_dedup_items():
    items = [
        {"id": "1", "url": "https://a.com/1", "score": 1},
        {"id": "2", "url": "https://a.com/1", "score": 5},
    ]
    result = dedup_items(items)
    assert len(result) == 1
    assert result[0]["score"] == 5
