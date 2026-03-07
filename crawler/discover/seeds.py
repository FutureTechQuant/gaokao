from crawler.config import SEED_URLS_TXT


def load_seed_urls() -> list[str]:
    if not SEED_URLS_TXT.exists():
        return []
    return [line.strip() for line in SEED_URLS_TXT.read_text(encoding="utf-8").splitlines() if line.strip()]
