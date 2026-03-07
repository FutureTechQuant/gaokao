def assign_tags(item: dict) -> list[str]:
    text = " ".join([item.get("title", ""), item.get("snippet", ""), item.get("url", "")])
    tags = []

    rules = {
        "陕西": ["陕西", "snnu", "nwu", "xaut", "xupt"],
        "PDF报告": [".pdf", "年度报告"],
        "预算": ["预算", "决算"],
        "保研": ["推免", "保研"],
        "国企": ["国企", "国资"],
        "选调生": ["选调生", "定向选调"],
        "重点实验室": ["重点实验室"],
        "公务员": ["公务员", "职位表"],
        "专业调整": ["新增专业", "撤销专业", "专业备案"],
    }

    for tag, keywords in rules.items():
        if any(word.lower() in text.lower() for word in keywords):
            tags.append(tag)

    return sorted(set(tags))
