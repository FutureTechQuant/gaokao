from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"

APP_YAML = CONFIG_DIR / "app.yaml"
CATEGORIES_YAML = CONFIG_DIR / "categories.yaml"
TAGS_YAML = CONFIG_DIR / "tags.yaml"
TRUSTED_DOMAINS_TXT = CONFIG_DIR / "trusted_domains.txt"
SEED_URLS_TXT = CONFIG_DIR / "seed_urls.txt"
TOPIC_RULES_YAML = CONFIG_DIR / "topic_rules.yaml"

LATEST_JSON = DATA_DIR / "latest.json"
HISTORY_JSON = DATA_DIR / "history.json"
DISCOVERED_JSON = DATA_DIR / "discovered_sources.json"
ANALYTICS_JSON = DATA_DIR / "analytics.json"

DOCS_INDEX_HTML = DOCS_DIR / "index.html"
DOCS_LATEST_JSON = DOCS_DIR / "latest.json"
DOCS_ANALYTICS_JSON = DOCS_DIR / "analytics.json"

for path in [DATA_DIR, DOCS_DIR]:
    path.mkdir(parents=True, exist_ok=True)
