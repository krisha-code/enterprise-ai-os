from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.citation_builder import CitationBuilder


def make_chunk(
    chunk_id: int,
    content: str,
    section_title: str | None = None,
    page_number: int | None = None,
    filename: str = "guide.pdf",
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
    chunk = make_chunk(
        chunk_id=42,
        content="A UAV is an unmanned aerial vehicle.",
        section_title="Introduction",
        page_number=3,
        filename="uav-guide.pdf",
    )

    citations = CitationBuilder.build([chunk])

    assert len(citations) == 1
    citation = citations[0]
    assert citation.source_id == 1
    assert citation.document_id == 10
    assert citation.chunk_id == 42
    assert citation.filename == "uav-guide.pdf"
    assert citation.section_title == "Introduction"
    assert citation.page_number == 3


def test_build_relevant_preserves_original_source_ids():
    chunks = [
        make_chunk(1, "UAV means unmanned aerial vehicle."),
        make_chunk(2, "Quarterly office parking allocation."),
        make_chunk(3, "UAVs can be remotely piloted aircraft."),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="A UAV is an unmanned aerial vehicle that can be remotely piloted.",
        min_overlap_ratio=0.20,
        question="What is a UAV?",
    )

    assert citations
    assert all(c.source_id in {1, 3} for c in citations)
    assert 2 not in {c.source_id for c in citations}


def test_build_relevant_returns_empty_for_unrelated_chunks():
    chunks = [
        make_chunk(1, "Office parking allocation and cafeteria schedules."),
        make_chunk(2, "Quarterly office seating arrangements."),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="A UAV is an unmanned aerial vehicle.",
        question="What is a UAV?",
    )

    assert citations == []


def test_build_relevant_keeps_original_ids_after_filtering():
    chunks = [
        make_chunk(1, "Unrelated office cafeteria schedule."),
        make_chunk(2, "A UAV is an unmanned aerial vehicle."),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="A UAV is an unmanned aerial vehicle.",
        question="What is a UAV?",
    )

    assert len(citations) == 1
    assert citations[0].source_id == 2


def test_build_relevant_rejects_weak_overlap():
    chunks = [
        make_chunk(
            1,
            "The UAV fleet maintenance schedule is updated every Friday.",
        ),
        make_chunk(
            2,
            "UAV means unmanned aerial vehicle used for aerial surveying.",
        ),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="A UAV is an unmanned aerial vehicle used for aerial surveying.",
        question="What is a UAV?",
    )

    source_ids = {citation.source_id for citation in citations}
    assert 2 in source_ids
    assert 1 not in source_ids


def test_build_relevant_returns_empty_when_answer_has_no_content_words():
    chunks = [
        make_chunk(1, "Office parking allocation and cafeteria schedules."),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="is it a or the",
        question="What is a UAV?",
    )

    assert citations == []


def test_build_relevant_preserves_context_order():
    chunks = [
        make_chunk(1, "UAV means unmanned aerial vehicle."),
        make_chunk(2, "Quarterly office parking allocation."),
        make_chunk(
            3,
            "Unmanned aerial vehicles are used for aerial surveying.",
        ),
    ]

    citations = CitationBuilder.build_relevant(
        chunks,
        answer="A UAV is an unmanned aerial vehicle used for aerial surveying.",
        question="What is a UAV?",
    )

    source_ids = [citation.source_id for citation in citations]
    assert source_ids == sorted(source_ids)
    assert 2 not in source_ids
