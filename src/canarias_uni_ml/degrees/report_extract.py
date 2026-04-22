from __future__ import annotations

import io
import re

import requests
import urllib3
from pypdf import PdfReader


def extract_report_text(pdf_bytes: bytes, max_pages: int = 6) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join((reader.pages[index].extract_text() or "") for index in range(min(max_pages, len(reader.pages))))
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def build_description_from_report_text(text: str, max_chars: int = 4000) -> str | None:
    if not text:
        return None
    match = re.search(r"MOTIVACIÓN(.*?)(RECOMENDACIONES|En Madrid, a)", text, re.S | re.I)
    snippet = match.group(1) if match else text
    snippet = re.sub(r"\s+", " ", snippet).strip()
    if not snippet:
        return None
    return snippet[:max_chars]


def fetch_and_extract_report_description(
    report_url: str,
    *,
    timeout: int = 60,
    verify_ssl: bool = False,
) -> str | None:
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(report_url, timeout=timeout, verify=verify_ssl)
    response.raise_for_status()
    text = extract_report_text(response.content)
    return build_description_from_report_text(text)
