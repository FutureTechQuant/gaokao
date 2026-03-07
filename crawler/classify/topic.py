TOPIC_NAME_MAP = {
    "admissions": "本科招生",
    "careers": "就业质量报告",
    "recommendation": "保研推免",
    "budgets": "高校预算",
    "state_owned": "国企要求",
    "civil_service": "公务员与选调生",
    "labs": "国家重点实验室",
    "industry": "产业链分析",
    "majors": "专业调整",
}


def assign_topic(item: dict) -> str:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("source", ""),
        item.get("url", ""),
    ])

    if any(k in text for k in [
        "就业质量年度报告", "毕业生就业质量", "就业去向",
        "行业分布", "地区流向", "就业率", "月收入", "升学", "深造"
    ]):
        return "就业质量报告"

    if any(k in text for k in [
        "推免", "保研", "推荐免试", "推免生", "夏令营", "预推免", "遴选办法"
    ]):
        return "保研推免"

    if any(k in text for k in [
        "单位预算", "部门预算", "预算", "决算"
    ]):
        return "高校预算"

    if any(k in text for k in [
        "招生章程", "招生计划", "本科招生", "录取查询",
        "录取分数", "历年分数", "分数线", "位次", "专业介绍"
    ]):
        return "本科招生"

    if any(k in text for k in [
        "新增专业", "撤销专业", "专业备案", "专业审批"
    ]):
        return "专业调整"

    raw_topic = item.get("topic", "")
    if raw_topic in TOPIC_NAME_MAP:
        return TOPIC_NAME_MAP[raw_topic]

    return "综合信息"
