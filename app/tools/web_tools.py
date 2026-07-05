from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import re

from langchain_core.tools import tool

USER_AGENT = "langchain-001-agent/1.0"


class _HTMLTextExtractor(HTMLParser):
    """Extract plain text content from HTML."""

    def __init__(self) -> None:
        """Initialize the text buffer."""
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collect text nodes."""
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        """Return normalized plain text."""
        return "\n".join(self.parts)


def _fetch_url(url: str) -> str:
    """Fetch raw text from a URL."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=15) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web with DuckDuckGo and return top results."""
    if not query.strip():
        return "Query must not be empty."
    if max_results <= 0:
        return "max_results must be greater than 0."

    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html = _fetch_url(search_url)
    except Exception as exc:
        return f"Web search failed: {exc}"

    matches = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not matches:
        return "No search results found."

    lines = []
    for index, (href, title) in enumerate(matches[:max_results], start=1):
        clean_title = re.sub(r"<.*?>", "", unescape(title)).strip()
        lines.append(f"{index}. {clean_title}\n{href}")
    return "\n\n".join(lines)


@tool
def fetch_webpage(url: str, max_chars: int = 4000) -> str:
    """Fetch a webpage and return extracted plain text."""
    if not url.strip():
        return "URL must not be empty."
    if max_chars <= 0:
        return "max_chars must be greater than 0."

    try:
        html = _fetch_url(url)
    except Exception as exc:
        return f"Webpage fetch failed: {exc}"

    parser = _HTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    if not text:
        return "No readable text found on the page."
    return text[:max_chars]
