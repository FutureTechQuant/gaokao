def assign_tags(item: dict) -> list[str]:
    text = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        item.get("source", ""),
        item.get("url", ""),
        item.get("source_url", ""),
        item.get("topic", ""),
        item.get("category", ""),
    ]).lower()

    tags = []

    def hit(*keywords: str) -> bool:
        return any(keyword.lower() in text for keyword in keywords)

    if hit("陕西", "snnu", "nwu", "xaut", "xupt", "xust", "shaanxi", "xisu", "nwafu"):
        tags.append("陕西")

    if item.get("is_pdf") or hit(".pdf", "pdf"):
        tags.append("PDF")

    if hit("就业质量年度报告", "毕业生就业质量年度报告", "就业质量报告", "毕业生就业质量"):
        tags.append("就业质量报告")

    if hit("就业去向", "行业分布", "地区流向", "就业率", "升学", "深造", "月收入"):
        tags.append("就业分析")

    if hit("推免", "保研", "推荐免试", "推免生", "预推免", "夏令营"):
        tags.append("保研")

    if hit("接收推荐免试研究生", "接收推免生", "接收优秀应届本科毕业生"):
        tags.append("接收推免")

    if hit("单位预算", "部门预算", "预算公开", "预算说明"):
        tags.append("学校预算")

    if hit("决算", "决算公开"):
        tags.append("学校决算")

    if hit("招生计划", "本科招生计划", "分省分专业招生计划", "招生专业目录"):
        tags.append("招生计划")

    if hit("招生章程", "本科招生章程"):
        tags.append("招生章程")

    if hit("录取查询", "录取结果查询", "录取通知书"):
        tags.append("录取")

    if hit("历年分数", "录取分数", "分数线", "位次", "投档线"):
        tags.append("分数线")

    if hit("专业介绍", "专业解读", "本科专业", "招生专业"):
        tags.append("专业信息")

    if hit("新增专业", "专业备案", "专业审批"):
        tags.append("新增专业")

    if hit("撤销专业", "停招专业"):
        tags.append("撤销专业")

    if hit("公务员", "职位表", "专业目录"):
        tags.append("公务员")

    if hit("选调生", "定向选调"):
        tags.append("选调生")

    if hit("国企", "国资", "校招", "引才"):
        tags.append("国企")

    if hit("国家重点实验室", "教育部重点实验室", "实验室年度报告"):
        tags.append("重点实验室")

    if hit("产业链", "战略性新兴产业", "新兴产业"):
        tags.append("产业链")

    topic = item.get("topic", "")
    if topic == "admissions":
        tags.append("招生")
    elif topic == "careers":
        tags.append("就业")
    elif topic == "recommendation":
        tags.append("推免")
    elif topic == "budgets":
        tags.append("预算")

    category = item.get("category", "")
    if category:
        tags.append(category)

    return sorted(set(tags))
