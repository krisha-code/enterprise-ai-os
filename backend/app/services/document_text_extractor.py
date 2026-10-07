from pathlib import Path
import re

from fastapi import HTTPException, status
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.schemas.document_chunk import DocumentChunkData


class DocumentTextExtractor:

    @staticmethod
    def extract(
        file_path: str,
        content_type: str,
    ) -> list[DocumentChunkData]:

        path = Path(file_path)

        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored document file not found",
            )

        # ----------------------------------------
        # PDF
        # ----------------------------------------

        if content_type == "application/pdf":

            reader = PdfReader(str(path))

            blocks = []

            for page_number, page in enumerate(
                reader.pages,
                start=1,
            ):
                text = page.extract_text()

                if text:
                    blocks.append(
                        DocumentChunkData(
                            content=text.strip(),
                            page_number=page_number,
                        )
                    )

            return blocks

        # ----------------------------------------
        # DOCX
        # ----------------------------------------

                # ----------------------------------------
        # DOCX
        # ----------------------------------------

        if content_type == (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        ):

            document = DocxDocument(str(path))

            blocks = []
            current_section_title = None

            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if not text:
                    continue

                detected_section = (
                    DocumentTextExtractor.detect_section_title(text)
                )

                if detected_section:
                    current_section_title = detected_section

                blocks.append(
                    DocumentChunkData(
                        content=text,
                        section_title=current_section_title,
                    )
                )

            return blocks

        # ----------------------------------------
        # TXT
        # ----------------------------------------

        if content_type == "text/plain":

            text = path.read_text(
                encoding="utf-8"
            )

            if not text.strip():
                return []

            return [
                DocumentChunkData(
                    content=text.strip()
                )
            ]

        # ----------------------------------------
        # Unsupported type
        # ----------------------------------------

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document type",
        )

    # ----------------------------------------
    # Section title detection
    # ----------------------------------------

    @staticmethod
    def detect_section_title(
        text: str,
    ) -> str | None:

        text = text.strip()

        if not text:
            return None

        # Major module headings
        #
        # Example:
        # MODULE 1 – FUNDAMENTALS OF DRONE TECHNOLOGY
        #
        if re.match(
            r"^MODULE\s+\d+\b",
            text,
            re.IGNORECASE,
        ):
            return text

        # Numbered section headings
        #
        # Examples:
        # 1. Fixed-Wing UAV
        # 2. Multi-Rotor UAV
        #
        if re.match(
            r"^\d+\.\s+[A-Z]",
            text,
        ):
            return text

        return None