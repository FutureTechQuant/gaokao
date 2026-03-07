KEYWORDS = {
    "recommendation": ["推免", "保研", "推荐免试", "夏令营"],
    "budgets": ["预算", "决算", "单位预算"],
    "state_owned": ["国企", "校招", "引才"],
    "civil_service": ["公务员", "选调生", "职位表"],
    "labs": ["重点实验室", "年度报告", "科研平台"],
    "majors": ["新增专业", "撤销专业", "专业备案", "专业审批"],
}


def match_topics(title: str) -> list[str]:
    text = (title or "").lower()
    matched = []
    for topic, words in KEYWORDS.items():
        if any(word.lower() in text for word in words):
            matched.append(topic)
    return matched
