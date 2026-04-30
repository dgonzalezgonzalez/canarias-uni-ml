from pathlib import Path

import requests

from src.canarias_uni_ml.degrees.program_page_resolver import (
    extract_program_description_from_html,
    resolve_program_page_description,
)


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("http error")


def test_extract_program_description_from_html_reads_description_section():
    html = Path("tests/fixtures/program_page_samples/program_page_detail.html").read_text(encoding="utf-8")
    text = extract_program_description_from_html(html)
    assert text is not None
    assert "formación avanzada" in text


def test_resolve_program_page_description_uses_index_and_detail(monkeypatch):
    index_html = Path("tests/fixtures/program_page_samples/program_index.html").read_text(encoding="utf-8")
    detail_html = Path("tests/fixtures/program_page_samples/program_page_detail.html").read_text(encoding="utf-8")

    def fake_get(url, timeout=20):
        if "grado-ingenieria-informatica" in url:
            return _FakeResponse(detail_html)
        return _FakeResponse(index_html)

    monkeypatch.setattr("src.canarias_uni_ml.degrees.program_page_resolver.requests.get", fake_get)

    result = resolve_program_page_description("ull", "Grado en Ingeniería Informática")
    assert result.status == "ok"
    assert result.source_url is not None
    assert "grado-ingenieria-informatica" in result.source_url
    assert result.description is not None


def test_resolve_program_page_description_handles_unknown_university():
    result = resolve_program_page_description("unknown", "Titulo")
    assert result.status == "missing"
    assert result.error == "no_program_page_resolver"
