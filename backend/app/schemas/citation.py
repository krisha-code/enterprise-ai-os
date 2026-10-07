from pydantic import BaseModel


class Citation(BaseModel):
    source_id: int
    document_id: int
    chunk_id: int
    filename: str
    section_title: str | None = None
    page_number: int | None = None