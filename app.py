from datetime import datetime, timezone
from urllib.parse import urlparse
import time

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

DEFAULT_URLS = [
    "https://example.com",
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/503",
]


def check_url(url: str) -> dict:
    """Check one public HTTP/HTTPS endpoint and return a small result record."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "url": url,
            "status": "Invalid URL",
            "status_code": "—",
            "latency_ms": "—",
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "error": "Enter a valid URL starting with http:// or https://",
        }

    started = time.perf_counter()
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        latency_ms = round((time.perf_counter() - started) * 1000)
        ok = 200 <= response.status_code < 400
        return {
            "url": url,
            "status": "Online" if ok else "Issue",
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "error": "" if ok else f"HTTP {response.status_code}",
        }
    except requests.RequestException as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "url": url,
            "status": "Offline / unreachable",
            "status_code": "—",
            "latency_ms": latency_ms,
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "error": str(exc),
        }


@app.route("/", methods=["GET", "POST"])
def index():
    raw_urls = request.form.get("urls", "\n".join(DEFAULT_URLS))
    results = []
    if request.method == "POST":
        urls = [line.strip() for line in raw_urls.splitlines() if line.strip()]
        urls = urls[:10]
        results = [check_url(url) for url in urls]

    online_count = sum(result["status"] == "Online" for result in results)
    issue_count = len(results) - online_count
    return render_template(
        "index.html",
        urls=raw_urls,
        results=results,
        online_count=online_count,
        issue_count=issue_count,
        checked_count=len(results),
    )


if __name__ == "__main__":
    app.run(debug=True)
