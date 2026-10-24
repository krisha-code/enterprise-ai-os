from typing import Literal

from pydantic import BaseModel

from app.schemas.citation import Citation


class RAGRequest(BaseModel):
    question: str
    document_id: int | None = None
    mode: Literal["answer", "passage_summary", "document_summary"] = "answer"


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation]
