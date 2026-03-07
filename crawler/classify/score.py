def assign_score(item: dict) -> int:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("source", ""),
        item.get("url", ""),
        item.get("topic", ""),
        item.get("category", ""),
        " ".join(item.get("tags", [])),
    ])

    score = 0

    title = item.get("title", "")
    url = item.get("url", "")

    def add_if_contains(keyword: str, points: int):
        nonlocal score
        if keyword in text:
            score += points

    if item.get("date"):
        score += 2

    if item.get("is_pdf"):
        score += 3

    if "陕西" in text or any(k in text.lower() for k in ["snnu", "nwu", "xaut", "xupt", "xust"]):
        score += 3

    career_rules = {
        "就业质量年度报告": 12,
        "毕业生就业质量年度报告": 12,
        "就业质量报告": 10,
        "毕业生就业质量": 9,
        "就业去向": 5,
        "行业分布": 5,
        "地区流向": 5,
        "就业率": 4,
        "升学": 4,
        "深造": 4,
        "月收入": 4,
    }

    recommendation_rules = {
        "推荐免试": 12,
        "推免生": 10,
        "推免": 9,
        "保研": 9,
        "夏令营": 6,
        "预推免": 6,
        "接收推荐免试研究生": 10,
        "实施办法": 5,
        "遴选办法": 5,
    }

    budget_rules = {
        "单位预算": 12,
        "部门预算": 10,
        "预算公开": 9,
        "预算说明": 8,
        "决算": 7,
        "财务": 2,
        "经费": 2,
    }

    admission_rules = {
        "招生计划": 10,
        "本科招生计划": 10,
        "招生章程": 9,
        "本科招生章程": 9,
        "录取查询": 9,
        "录取结果查询": 8,
        "历年分数": 8,
        "录取分数": 8,
        "分数线": 7,
        "位次": 6,
        "录取通知书": 5,
        "专业介绍": 4,
        "本科招生": 4,
    }

    for rules in [career_rules, recommendation_rules, budget_rules, admission_rules]:
        for keyword, points in rules.items():
            add_if_contains(keyword, points)

    if url.lower().endswith(".pdf"):
        score += 2

    if any(word in text for word in ["采购", "招标", "中标", "成交公告"]):
        score -= 8

    if any(word in text for word in ["新闻网", "新闻网", "校园新闻", "综合新闻"]):
        score -= 4

    if any(word in title for word in ["开笔", "活动", "报道", "纪实", "访谈", "新闻"]):
        score -= 5

    if item.get("category") == "招生信息":
        score += 2
    if item.get("category") == "就业质量":
        score += 3
    if item.get("category") == "保研信息":
        score += 3
    if item.get("category") == "学校预算":
        score += 3

    tags = item.get("tags", [])
    if "陕西" in tags:
        score += 2
    if "PDF" in tags:
        score += 1
    if "就业质量报告" in tags:
        score += 4
    if "保研" in tags:
        score += 3
    if "学校预算" in tags:
        score += 3
    if "招生计划" in tags:
        score += 3

    return max(score, 0)
