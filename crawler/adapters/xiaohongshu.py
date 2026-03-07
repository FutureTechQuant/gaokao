import hashlib
from datetime import datetime


def build_xiaohongshu_search_url(keyword: str) -> str:
    keyword = (keyword or "").strip()
    return f"https://www.xiaohongshu.com/search_result?keyword={keyword}"


def collect_from_xiaohongshu(source: dict) -> list[dict]:
    keyword = source.get("entry", "").strip()
    if not keyword:
        return []

    now = datetime.now().strftime("%Y-%m-%d")
    url = build_xiaohongshu_search_url(keyword)

    item = {
        "id": hashlib.sha1(f"xiaohongshu|{keyword}|{url}".encode("utf-8")).hexdigest(),
        "title": f"小红书搜索：{keyword}",
        "url": url,
        "source": source.get("name", "小红书"),
        "source_url": url,
        "topic": source.get("topic", "general"),
        "date": now,
        "snippet": f"平台搜索入口：{keyword}",
        "page_url": url,
        "is_pdf": False,
        "score": 3,
        "source_type": source.get("source_type", "platform"),
        "platform": source.get("platform", "xiaohongshu"),
        "trust_level": source.get("trust_level", "medium"),
        "tags": sorted(set((source.get("tags") or []) + ["小红书", "平台内容"])),
    }
    return [item]
