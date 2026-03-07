from crawler.analytics.budget_metrics import build_budget_metrics
from crawler.analytics.major_changes import build_major_change_metrics
from crawler.analytics.civil_service_ratio import build_civil_service_ratio
from crawler.analytics.industry_chain import build_industry_chain_summary


def build_analytics(items: list[dict]) -> dict:
    return {
        "budget_metrics": build_budget_metrics(items),
        "major_changes": build_major_change_metrics(items),
        "civil_service_ratio": build_civil_service_ratio(items),
        "industry_chain": build_industry_chain_summary(items),
    }
