from crawler.sources.admissions import SOURCES as ADMISSION_SOURCES
from crawler.sources.careers import SOURCES as CAREER_SOURCES
from crawler.sources.budgets import SOURCES as BUDGET_SOURCES
from crawler.sources.recommendation import SOURCES as RECOMMENDATION_SOURCES
from crawler.sources.state_owned import SOURCES as STATE_OWNED_SOURCES
from crawler.sources.civil_service import SOURCES as CIVIL_SERVICE_SOURCES
from crawler.sources.labs import SOURCES as LAB_SOURCES
from crawler.sources.industry import SOURCES as INDUSTRY_SOURCES
from crawler.sources.majors import SOURCES as MAJOR_SOURCES


def build_source_registry() -> list[dict]:
    return (
        ADMISSION_SOURCES
        + CAREER_SOURCES
        + BUDGET_SOURCES
        + RECOMMENDATION_SOURCES
        + STATE_OWNED_SOURCES
        + CIVIL_SERVICE_SOURCES
        + LAB_SOURCES
        + INDUSTRY_SOURCES
        + MAJOR_SOURCES
    )
