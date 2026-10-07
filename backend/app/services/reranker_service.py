from sentence_transformers import CrossEncoder

from app.models.document_chunk import DocumentChunk


class RerankerService:

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    model = CrossEncoder(MODEL_NAME)

    @staticmethod
    def rerank(
        question: str,
        chunks: list[DocumentChunk],
    ):
        pairs = []

        for chunk in chunks:
            section = (
                chunk.section_title
                if chunk.section_title
                else "Unknown section"
            )

            passage = (
                f"Section: {section}\n"
                f"Content: {chunk.content}"
            )

            pairs.append(
                (question, passage)
            )

        scores = RerankerService.model.predict(
            pairs
        )

        results = list(
            zip(chunks, scores)
        )

        results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return results