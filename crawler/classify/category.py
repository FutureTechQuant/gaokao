def assign_category(item: dict) -> str:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("source", ""),
        item.get("topic", ""),
        " ".join(item.get("tags", [])),
    ])

    topic = item.get("topic", "")

    if topic == "careers":
        return "就业质量"

    if topic == "recommendation":
        return "保研信息"

    if topic == "budgets":
        return "学校预算"

    if topic == "admissions":
        return "招生信息"

    if any(k in text for k in [
        "就业质量年度报告", "毕业生就业质量", "就业去向", "行业分布",
        "地区流向", "升学", "深造", "就业率", "月收入"
    ]):
        return "就业质量"

    if any(k in text for k in [
        "推免", "保研", "推荐免试", "推免生", "夏令营",
        "预推免", "遴选办法", "实施办法"
    ]):
        return "保研信息"

    if any(k in text for k in [
        "单位预算", "部门预算", "预算", "决算", "财务", "经费"
    ]):
        return "学校预算"

    if any(k in text for k in [
        "招生章程", "招生计划", "本科招生", "录取查询",
        "录取分数", "历年分数", "分数线", "位次", "专业介绍", "录取"
    ]):
        return "招生信息"

    if any(k in text for k in [
        "专业备案", "专业审批", "新增专业", "撤销专业"
    ]):
        return "专业趋势"

    if any(k in text for k in [
        "高考", "志愿", "查分", "成绩查询", "政策", "考试"
    ]):
        return "报考政策"

    return "未分类"
