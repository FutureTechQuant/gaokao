from __future__ import annotations

from urllib.parse import urlparse

POSITIVE = [
    "高考", "普通高考", "阳光高考", "招生", "本科招生", "招生网",
    "招生办", "招办", "考试院", "教育考试院", "招考", "录取",
    "志愿", "志愿填报", "查分", "分数线", "报名", "招生章程"
]

NEGATIVE = [
    "考研", "研究生", "硕士", "博士", "留学", "成人高考",
    "成考", "自考", "就业", "培训", "四六级", "专升本培训"
]

PATH_HINTS = [
    "gaokao", "zsb", "zs", "bkzs", "admission", "recruit",
    "notice", "news", "list", "article"
]

SOURCE_HINTS = [
    "招生网", "本科招生", "考试院", "教育考试院", "阳光高考", "招考"
]

LIST_HINTS = [
    "通知", "公告", "动态", "新闻", "政策", "资讯", "专栏", "专栏", "栏目"
]

BAD_HOST_HINTS = [
    "weibo.com", "zhihu.com", "csdn.net", "bilibili.com",
    "toutiao.com", "sohu.com", "163.com", "baidu.com"
]


def is_officialish_host(host: str) -> bool:
    host = (host or "").lower()
    return (
        host.endswith(".gov.cn")
        or host.endswith(".edu.cn")
        or host.endswith("chsi.com.cn")
    )


def get_host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def score_candidate(url: str, title: str, context: str) -> tuple[int, list[str]]:
    host = get_host(url)
    text = f"{url} {title} {context}".lower()

    score = 0
    reasons = []

    if is_officialish_host(host):
        score += 6
        reasons.append("official_host")

    for bad in BAD_HOST_HINTS:
        if host.endswith(bad):
            score -= 6
            reasons.append("bad_host")
            break

    pos_hits = 0
    for k in POSITIVE:
        if k.lower() in text:
            pos_hits += 1
    if pos_hits:
        score += min(pos_hits, 5) * 2
        reasons.append(f"positive_hits:{pos_hits}")

    neg_hits = 0
    for k in NEGATIVE:
        if k.lower() in text:
            neg_hits += 1
    if neg_hits:
        score -= min(neg_hits, 4) * 3
        reasons.append(f"negative_hits:{neg_hits}")

    path_hits = 0
    for p in PATH_HINTS:
        if p in text:
            path_hits += 1
    if path_hits:
        score += min(path_hits, 3) * 2
        reasons.append(f"path_hits:{path_hits}")

    source_hits = 0
    for s in SOURCE_HINTS:
        if s.lower() in title.lower():
            source_hits += 1
    if source_hits:
        score += source_hits * 3
        reasons.append(f"source_hits:{source_hits}")

    list_hits = 0
    for s in LIST_HINTS:
        if s.lower() in text:
            list_hits += 1
    if list_hits:
        score += min(list_hits, 2) * 2
        reasons.append(f"list_hits:{list_hits}")

    if host and host.count(".") <= 1 and is_officialish_host(host):
        score += 1
        reasons.append("top_level_official")

    return score, reasons
