def assign_topic(item: dict) -> str:
    text = " ".join([item.get("title", ""), item.get("snippet", "")])

    rules = {
        "保研信息": ["推免", "保研", "推荐免试", "夏令营"],
        "学校预算": ["预算", "决算", "单位预算"],
        "国企要求": ["国企", "校招", "引才", "专业要求"],
        "选调生政策": ["选调生", "定向选调", "报考条件"],
        "国家重点实验室": ["国家重点实验室", "教育部重点实验室", "实验室年度报告"],
        "产业链分析": ["产业链", "产业", "新兴产业"],
        "消失专业": ["撤销专业", "停招专业"],
        "公务员岗位适配度": ["公务员", "职位表", "专业目录"],
    }

    for topic, keywords in rules.items():
        if any(word in text for word in keywords):
            return topic

    return item.get("topic", "general")
