def build_industry_chain_summary(items: list[dict]) -> dict:
    industry_items = [i for i in items if i.get("topic") == "industry"]
    return {
        "count": len(industry_items),
        "message": "后续这里会接入产业链节点、对应专业与岗位映射。",
    }
