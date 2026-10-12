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
