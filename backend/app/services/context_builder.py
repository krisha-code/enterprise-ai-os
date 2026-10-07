from app.models.document_chunk import DocumentChunk


class ContextBuilder:

    @staticmethod
    def build(
        chunks: list[DocumentChunk],
    ) -> str:

        context_parts = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            filename = (
                chunk.document.filename
                if chunk.document
                else "Unknown document"
            )

            section = (
                chunk.section_title
                if chunk.section_title
                else "Unknown section"
            )

            page = (
                str(chunk.page_number)
                if chunk.page_number is not None
                else "N/A"
            )

            context_parts.append(
                f"[Source {index}]\n"
                f"Document: {filename}\n"
                f"Section: {section}\n"
                f"Page: {page}\n"
                f"Content:\n"
                f"{chunk.content}"
            )

        return "\n\n".join(context_parts)