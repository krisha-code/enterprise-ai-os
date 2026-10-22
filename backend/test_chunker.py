from app.schemas.document_chunk import DocumentChunkData
from app.services.document_chunker import DocumentChunker


blocks = [
    DocumentChunkData(
        content="Employees receive a monthly transportation allowance. "
        "Employees can use the allowance for approved commuting expenses.",
        section_title="Transportation Policy",
        page_number=1,
    ),
    DocumentChunkData(
        content="Employees receive 20 days of annual leave every year. "
        "Employees must submit leave requests to their manager.",
        section_title="Leave Policy",
        page_number=2,
    ),
]


def test_chunk_text_preserves_section_boundaries():
    chunks = DocumentChunker.chunk_text(
        blocks=blocks,
        chunk_size=120,
        overlap_sentences=1,
    )

    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(
        chunk.section_title in {
            "Transportation Policy",
            "Leave Policy",
        }
        for chunk in chunks
    )

    assert all(
        not (
            "Transportation Policy" in chunk.section_title
            and "Leave Policy" in chunk.section_title
        )
        for chunk in chunks
    )

    assert any(
        chunk.section_title == "Transportation Policy"
        for chunk in chunks
    )
    assert any(
        chunk.section_title == "Leave Policy"
        for chunk in chunks
    )

def test_chunk_text_preserves_page_metadata():
    source_blocks = [
        DocumentChunkData(
            content="First sentence. Second sentence.",
            section_title="Leave Policy",
            page_number=3,
        ),
        DocumentChunkData(
            content="Third sentence.",
            section_title="Leave Policy",
            page_number=4,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=25,
        overlap_sentences=0,
    )

    assert chunks
    assert all(chunk.section_title == "Leave Policy" for chunk in chunks)
    assert all(chunk.page_number in {3, 4} for chunk in chunks)


def test_chunk_text_does_not_overlap_across_sections():
    source_blocks = [
        DocumentChunkData(
            content="Alpha sentence. Beta sentence.",
            section_title="Section A",
            page_number=1,
        ),
        DocumentChunkData(
            content="Gamma sentence.",
            section_title="Section B",
            page_number=2,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=20,
        overlap_sentences=1,
    )

    section_b_chunks = [
        chunk for chunk in chunks
        if chunk.section_title == "Section B"
    ]

    assert section_b_chunks
    assert all("Alpha sentence" not in chunk.content for chunk in section_b_chunks)
    assert all("Beta sentence" not in chunk.content for chunk in section_b_chunks)


def test_chunk_text_keeps_single_oversized_sentence_intact():
    long_sentence = "word " * 30
    source_blocks = [
        DocumentChunkData(
            content=long_sentence.strip() + ".",
            section_title="Long Text",
            page_number=1,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=10,
        overlap_sentences=0,
    )

    assert len(chunks) == 1
    assert chunks[0].content == long_sentence.strip() + "."
    assert chunks[0].section_title == "Long Text"
    assert chunks[0].page_number == 1

def test_chunk_text_preserves_page_metadata():
    source_blocks = [
        DocumentChunkData(
            content="First sentence. Second sentence.",
            section_title="Leave Policy",
            page_number=3,
        ),
        DocumentChunkData(
            content="Third sentence.",
            section_title="Leave Policy",
            page_number=4,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=25,
        overlap_sentences=0,
    )

    assert chunks
    assert all(chunk.section_title == "Leave Policy" for chunk in chunks)
    assert all(chunk.page_number in {3, 4} for chunk in chunks)


def test_chunk_text_does_not_overlap_across_sections():
    source_blocks = [
        DocumentChunkData(
            content="Alpha sentence. Beta sentence.",
            section_title="Section A",
            page_number=1,
        ),
        DocumentChunkData(
            content="Gamma sentence.",
            section_title="Section B",
            page_number=2,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=20,
        overlap_sentences=1,
    )

    section_b_chunks = [
        chunk for chunk in chunks
        if chunk.section_title == "Section B"
    ]

    assert section_b_chunks
    assert all("Alpha sentence" not in chunk.content for chunk in section_b_chunks)
    assert all("Beta sentence" not in chunk.content for chunk in section_b_chunks)


def test_chunk_text_keeps_single_oversized_sentence_intact():
    long_sentence = "word " * 30
    source_blocks = [
        DocumentChunkData(
            content=long_sentence.strip() + ".",
            section_title="Long Text",
            page_number=1,
        ),
    ]

    chunks = DocumentChunker.chunk_text(
        blocks=source_blocks,
        chunk_size=10,
        overlap_sentences=0,
    )

    assert len(chunks) == 1
    assert chunks[0].content == long_sentence.strip() + "."
    assert chunks[0].section_title == "Long Text"
    assert chunks[0].page_number == 1
