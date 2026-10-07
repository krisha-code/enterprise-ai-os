from pydantic import BaseModel

from app.schemas.citation import Citation


class RAGRequest(BaseModel):
    question: str


class RAGResponse(BaseModel):
    answer: str
    citations: list[Citation]