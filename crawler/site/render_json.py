from crawler.config import DOCS_LATEST_JSON, DOCS_ANALYTICS_JSON
from crawler.storage.writer import write_json


def write_public_json(latest_payload: dict, analytics: dict) -> None:
    write_json(DOCS_LATEST_JSON, latest_payload)
    write_json(DOCS_ANALYTICS_JSON, analytics)
