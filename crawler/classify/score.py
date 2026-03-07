def assign_score(item: dict) -> int:
    text = " ".join([item.get("title", ""), item.get("snippet", "")])

    score = 0
    if item.get("is_pdf"):
        score += 3
    if item.get("date"):
        score += 2

    keywords = [
        "就业质量年度报告", "招生计划", "招生章程", "录取分数",
        "推荐免试", "单位预算", "重点实验室", "选调生", "撤销专业"
    ]
    score += sum(2 for word in keywords if word in text)
    return score
