from bs4 import BeautifulSoup

from crawler.http.client import request_page


def scan_url(url: str) -> list[dict]:
    html = request_page(url)
    soup = BeautifulSoup(html, "lxml")
    results = []

    for a in soup.select("a[href]"):
        title = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()
        if not href:
            continue
        results.append({
            "title": title,
            "href": href,
            "source_page": url,
        })

    return results
