from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.context_builder import ContextBuilder


def make_chunk(
    chunk_id: int,
    content: str,
    filename: str = "guide.pdf",
    section_title: str | None = "Introduction",
    page_number: int | None = 1,
) -> DocumentChunk:
    document = Document(
        id=10,
        filename=filename,
    )

    chunk = DocumentChunk(
        id=chunk_id,
        document_id=10,
        chunk_index=chunk_id,
        content=content,
        section_title=section_title,
        page_number=page_number,
    )
    chunk.document = document
    return chunk


def test_build_includes_source_and_document_metadata():
    context = ContextBuilder.build([
        make_chunk(
            1,
            "A UAV is an unmanned aerial vehicle.",
            filename="uav-guide.pdf",
            section_title="Definition",
            page_number=3,
        )
    ])

    assert "[Source 1]" in context
    assert "Document: uav-guide.pdf" in context
    assert "Section: Definition" in context
    assert "Page: 3" in context
    assert "A UAV is an unmanned aerial vehicle." in context


def test_build_numbers_sources_in_input_order():
    chunks = [
        make_chunk(1, "First chunk."),
        make_chunk(2, "Second chunk.", filename="second.pdf"),
    ]

    context = ContextBuilder.build(chunks)

    assert context.index("[Source 1]") < context.index("[Source 2]")
    assert "Content:\nFirst chunk." in context
    assert "Content:\nSecond chunk." in context


def test_build_uses_fallbacks_for_missing_metadata():
    chunk = make_chunk(
        1,
        "Content without section or page metadata.",
        section_title=None,
        page_number=None,
    )
    chunk.document = None

    context = ContextBuilder.build([chunk])

    assert "Document: Unknown document" in context
    assert "Section: Unknown section" in context
    assert "Page: N/A" in context


def test_build_returns_empty_string_for_no_chunks():
    assert ContextBuilder.build([]) == ""
