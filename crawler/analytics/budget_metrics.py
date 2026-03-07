def build_budget_metrics(items: list[dict]) -> dict:
    budget_items = [i for i in items if i.get("topic") == "budgets" or "预算" in i.get("tags", [])]
    return {
        "count": len(budget_items),
        "latest_titles": [i["title"] for i in budget_items[:10]],
    }
