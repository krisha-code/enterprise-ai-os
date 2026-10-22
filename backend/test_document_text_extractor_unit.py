import pytest
from docx import Document as DocxDocument
from fastapi import HTTPException
from pypdf import PdfWriter

from app.services.document_text_extractor import DocumentTextExtractor


DOCX_TYPE = (
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document"
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("MODULE 1 - DRONE TECHNOLOGY", "MODULE 1 - DRONE TECHNOLOGY"),
        ("module 2: UAV fundamentals", "module 2: UAV fundamentals"),
        ("1. Fixed-Wing UAV", "1. Fixed-Wing UAV"),
        ("2. Multi-Rotor UAV", "2. Multi-Rotor UAV"),
        ("Definition of UAV", None),
        ("", None),
        ("   ", None),
        ("GROUND CONTROL STATION (GCS)", None),
    ],
)
def test_detect_section_title(text, expected):
    assert DocumentTextExtractor.detect_section_title(text) == expected


def test_missing_file_raises_404(tmp_path):
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(HTTPException) as exc_info:
        DocumentTextExtractor.extract(str(missing_file), "text/plain")

    assert exc_info.value.status_code == 404


def test_unsupported_content_type_raises_400(tmp_path):
    path = tmp_path / "file.bin"
    path.write_bytes(b"test")

    with pytest.raises(HTTPException) as exc_info:
        DocumentTextExtractor.extract(str(path), "application/octet-stream")

    assert exc_info.value.status_code == 400


def test_extract_text_file(tmp_path):
    path = tmp_path / "policy.txt"
    path.write_text("  First line.\nSecond line.  ", encoding="utf-8")

    blocks = DocumentTextExtractor.extract(str(path), "text/plain")

    assert len(blocks) == 1
    assert blocks[0].content == "First line.\nSecond line."
    assert blocks[0].section_title is None
    assert blocks[0].page_number is None


def test_empty_text_file_returns_no_blocks(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("   \n ", encoding="utf-8")

    assert DocumentTextExtractor.extract(str(path), "text/plain") == []


def test_extract_docx_preserves_section_metadata(tmp_path):
    path = tmp_path / "policy.docx"
    document = DocxDocument()
    document.add_paragraph("MODULE 1 - FUNDAMENTALS")
    document.add_paragraph("Introduction to UAVs")
    document.add_paragraph("1. Fixed-Wing UAV")
    document.add_paragraph("Long endurance and efficient flight.")
    document.add_paragraph("   ")
    document.save(path)

    blocks = DocumentTextExtractor.extract(str(path), DOCX_TYPE)

    assert [block.content for block in blocks] == [
        "MODULE 1 - FUNDAMENTALS",
        "Introduction to UAVs",
        "1. Fixed-Wing UAV",
        "Long endurance and efficient flight.",
    ]
    assert [block.section_title for block in blocks] == [
        "MODULE 1 - FUNDAMENTALS",
        "MODULE 1 - FUNDAMENTALS",
        "1. Fixed-Wing UAV",
        "1. Fixed-Wing UAV",
    ]
    assert all(block.page_number is None for block in blocks)


def test_extract_pdf_preserves_page_numbers(tmp_path):
    path = tmp_path / "policy.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.add_blank_page(width=300, height=300)
    with path.open("wb") as file:
        writer.write(file)

    blocks = DocumentTextExtractor.extract(str(path), "application/pdf")

    # Blank PDF pages have no extractable text, so no blocks are expected.
    assert blocks == []

def test_extract_pdf_text_and_page_numbers(tmp_path):
    from unittest.mock import MagicMock, patch

    path = tmp_path / "policy.pdf"
    path.write_bytes(b"mock PDF fixture")

    page_one = MagicMock()
    page_one.extract_text.return_value = "  First page text.  "

    page_two = MagicMock()
    page_two.extract_text.return_value = "Second page text."

    page_three = MagicMock()
    page_three.extract_text.return_value = None

    reader = MagicMock()
    reader.pages = [page_one, page_two, page_three]

    with patch(
        "app.services.document_text_extractor.PdfReader",
        return_value=reader,
    ):
        blocks = DocumentTextExtractor.extract(
            str(path),
            "application/pdf",
        )

    assert len(blocks) == 2
    assert blocks[0].content == "First page text."
    assert blocks[0].page_number == 1
    assert blocks[1].content == "Second page text."
    assert blocks[1].page_number == 2
