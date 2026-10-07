from dataclasses import dataclass


@dataclass
class DocumentChunkData:
    content: str
    section_title: str | None = None
    page_number: int | None = None