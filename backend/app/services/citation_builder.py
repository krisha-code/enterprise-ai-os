from app.models.document_chunk import DocumentChunk
from app.schemas.citation import Citation


class CitationBuilder:

    @staticmethod
    def build(
        chunks: list[DocumentChunk],
    ) -> list[Citation]:

        citations = []

        for source_id, chunk in enumerate(
            chunks,
            start=1,
        ):

            filename = (
                chunk.document.filename
                if chunk.document
                else "Unknown document"
            )

            citations.append(
                Citation(
                    source_id=source_id,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    filename=filename,
                    section_title=chunk.section_title,
                    page_number=chunk.page_number,
                )
            )

        return citations