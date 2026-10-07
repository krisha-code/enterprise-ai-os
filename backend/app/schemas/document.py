from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSearchResult(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str

    class Config:
        from_attributes = True