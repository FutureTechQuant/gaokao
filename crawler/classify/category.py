def assign_category(item: dict) -> str:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("topic", ""),
    ])

    if any(k in text for k in ["就业质量", "就业去向", "行业分布", "升学"]):
        return "就业质量"
    if any(k in text for k in ["专业备案", "专业审批", "新增专业", "撤销专业"]):
        return "专业趋势"
    if any(k in text for k in ["招生", "录取", "招生计划", "分数", "章程"]):
        return "招生信息"
    return "报考政策"
