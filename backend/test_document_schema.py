from datetime import datetime, timezone

from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
)


def test_document_response_includes_processing_status():
    document = DocumentResponse(
        id=1,
        filename="policy.pdf",
        file_path="uploads/documents/policy.pdf",
        content_type="application/pdf",
        created_at=datetime.now(timezone.utc),
        processing_status="completed",
        processing_error=None,
    )

    assert document.processing_status == "completed"
    assert document.processing_error is None


def test_document_response_includes_processing_error():
    document = DocumentResponse(
        id=2,
        filename="broken.pdf",
        file_path="uploads/documents/broken.pdf",
        content_type="application/pdf",
        created_at=datetime.now(timezone.utc),
        processing_status="failed",
        processing_error="Could not extract usable text",
    )

    assert document.processing_status == "failed"
    assert document.processing_error == "Could not extract usable text"


def test_upload_response_reports_processing_status():
    response = DocumentUploadResponse(
        id=3,
        filename="policy.docx",
        status="completed",
    )

    assert response.status == "completed"