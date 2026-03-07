import socket
import time
import requests
import requests.packages.urllib3.util.connection as urllib3_cn

from crawler.http.headers import build_header_sets


def allowed_gai_family():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family


def request_page(url: str, timeout: int = 25) -> str:
    last_error = None

    for headers in build_header_sets():
        for _ in range(3):
            try:
                session = requests.Session()
                session.headers.update(headers)
                response = session.get(url, timeout=timeout, allow_redirects=True)
                response.raise_for_status()
                if not response.encoding or response.encoding.lower() == "iso-8859-1":
                    response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            except Exception as exc:
                last_error = exc
                time.sleep(2)

    raise last_error
