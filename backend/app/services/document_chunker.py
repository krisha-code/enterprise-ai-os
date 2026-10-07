import re

from app.schemas.document_chunk import DocumentChunkData


class DocumentChunker:

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_OVERLAP_SENTENCES = 1

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    @staticmethod
    def chunk_text(
        blocks: list[DocumentChunkData],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap_sentences: int = DEFAULT_OVERLAP_SENTENCES,
    ) -> list[DocumentChunkData]:

        if not blocks:
            return []

        if overlap_sentences < 0:
            raise ValueError(
                "overlap_sentences cannot be negative"
            )

        chunks = []

        current_sentences = []
        current_page_number = None
        current_section_title = None

        for block in blocks:

            # -------------------------------------------------
            # Hard section boundary
            # -------------------------------------------------
            if (
                current_sentences
                and block.section_title != current_section_title
            ):
                chunks.append(
                    DocumentChunkData(
                        content=" ".join(current_sentences),
                        section_title=current_section_title,
                        page_number=current_page_number,
                    )
                )

                # Do NOT carry sentence overlap across sections.
                current_sentences = []

                current_page_number = block.page_number
                current_section_title = block.section_title

            # -------------------------------------------------
            # Initialize metadata for the first block
            # -------------------------------------------------
            if not current_sentences:
                current_page_number = block.page_number
                current_section_title = block.section_title

            sentences = DocumentChunker.split_sentences(
                block.content
            )

            for sentence in sentences:

                candidate_sentences = (
                    current_sentences + [sentence]
                )

                candidate = " ".join(
                    candidate_sentences
                )

                # -------------------------------------------------
                # Normal chunk-size boundary
                # -------------------------------------------------
                if (
                    current_sentences
                    and len(candidate) > chunk_size
                ):
                    chunks.append(
                        DocumentChunkData(
                            content=" ".join(
                                current_sentences
                            ),
                            section_title=current_section_title,
                            page_number=current_page_number,
                        )
                    )

                    # Sentence overlap stays within the
                    # same section only.
                    current_sentences = (
                        current_sentences[
                            -overlap_sentences:
                        ]
                    )

                    current_page_number = (
                        block.page_number
                    )

                    current_section_title = (
                        block.section_title
                    )

                current_sentences.append(sentence)

        # -------------------------------------------------
        # Final chunk
        # -------------------------------------------------
        if current_sentences:
            chunks.append(
                DocumentChunkData(
                    content=" ".join(current_sentences),
                    section_title=current_section_title,
                    page_number=current_page_number,
                )
            )

        return chunks