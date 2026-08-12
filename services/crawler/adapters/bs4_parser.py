from __future__ import annotations

from bs4 import BeautifulSoup

from crawler.ports import HtmlParser


class BeautifulSoupParser:
    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)

    def extract_title(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None


_: HtmlParser = BeautifulSoupParser()
