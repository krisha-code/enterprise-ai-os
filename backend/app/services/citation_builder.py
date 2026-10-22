
import re

from app.models.document_chunk import DocumentChunk
from app.schemas.citation import Citation


class CitationBuilder:
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been",
        "by", "for", "from", "had", "has", "have", "in",
        "into", "is", "it", "its", "of", "on", "or", "that",
        "the", "their", "this", "to", "was", "were", "with",
        "what", "why", "how", "does", "do", "did", "can",
        "could", "would", "should", "which", "who", "when",
        "where", "about", "include", "includes", "including",
    }

    @classmethod
    def _content_words(cls, text: str) -> set[str]:
        words = re.findall(r"\b[a-z0-9-]+\b", text.lower())
        return {
            word
            for word in words
            if word not in cls.STOP_WORDS and len(word) > 2
        }

    @staticmethod
    def _make_citation(
        chunk: DocumentChunk,
        source_id: int,
    ) -> Citation:
        filename = (
            chunk.document.filename
            if chunk.document
            else "Unknown document"
        )

        return Citation(
            source_id=source_id,
            document_id=chunk.document_id,
            chunk_id=chunk.id,
            filename=filename,
            section_title=chunk.section_title,
            page_number=chunk.page_number,
        )

    @classmethod
    def build(
        cls,
        chunks: list[DocumentChunk],
    ) -> list[Citation]:
        return [
            cls._make_citation(chunk, source_id)
            for source_id, chunk in enumerate(chunks, start=1)
        ]

    @classmethod
    def build_relevant(
        cls,
        chunks: list[DocumentChunk],
        answer: str,
        min_overlap_ratio: float = 0.20,
        question: str | None = None,
    ) -> list[Citation]:
        """
        Select likely supporting chunks while preserving original source IDs.

        Lexical overlap is only a heuristic; it does not prove that a source
        supports every claim in the answer.
        """
        if not chunks:
            return []

        answer_words = cls._content_words(answer)
        question_words = cls._content_words(question or "")

        if not answer_words:
            return []

        # Retain the original source positions used by the prompt's
        # [Source N] labels. Never renumber after filtering.
        scored_chunks = []

        for source_id, chunk in enumerate(chunks, start=1):
            content = chunk.content or ""
            section = chunk.section_title or ""
            source_words = cls._content_words(
                f"{section} {content}"
            )

            answer_overlap = (
                len(answer_words & source_words) / len(answer_words)
            )

            question_overlap = (
                len(question_words & source_words) / len(question_words)
                if question_words
                else 0.0
            )

            # Strongly prefer chunks matching the subject of the question.
            combined_score = (
                0.70 * answer_overlap
                + 0.30 * question_overlap
            )

            if (
                answer_overlap >= min_overlap_ratio
                or (
                    question_words
                    and question_overlap >= 0.50
                    and answer_overlap >= 0.10
                )
            ):
                scored_chunks.append(
                    (combined_score, source_id, chunk)
                )

        # Do not attach unrelated citations merely to avoid an empty list.
        if not scored_chunks:
            return []

        scored_chunks.sort(key=lambda item: item[0], reverse=True)

        # Keep only sources close to the strongest matching source.
        best_score = scored_chunks[0][0]
        selected = [
            item
            for item in scored_chunks
            if item[0] >= max(0.10, best_score * 0.60)
        ]

        # Return citations in the original context order.
        selected.sort(key=lambda item: item[1])

        return [
            cls._make_citation(chunk, source_id)
            for _, source_id, chunk in selected
        ]
