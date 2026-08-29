from __future__ import annotations

from crawler.adapters.bs4_parser import BeautifulSoupParser


def test_beautifulsoup_parser_extracts_title_and_text() -> None:
    parser = BeautifulSoupParser()
    html = "<html><head><title>Peacock</title></head><body><p>Hello</p></body></html>"
    assert parser.extract_title(html) == "Peacock"
    assert "Hello" in parser.extract_text(html)
