import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.services.document_service import DocumentService


def test_processing_failure_marks_document_failed_and_removes_file(tmp_path):
    async def run_test():
        db = AsyncMock()
        db.add = Mock()
        user = SimpleNamespace(id=7, organization_id=1)
        upload_dir = tmp_path / "documents"
        document = SimpleNamespace(
            id=42,
            filename="test.txt",
            file_path=None,
            content_type="text/plain",
            processing_status="processing",
            processing_error=None,
            extracted_text=None,
        )

        def refresh_document(_document):
            _document.file_path = str(next(upload_dir.glob("*.txt")))

        db.refresh.side_effect = refresh_document

        upload = UploadFile(
            filename="test.txt",
            file=BytesIO(b"Some document content"),
            headers={"content-type": "text/plain"},
        )

        with (
            patch.object(DocumentService, "UPLOAD_DIR", upload_dir),
            patch(
                "app.services.document_service.Document",
                return_value=document,
            ),
            patch(
                "app.services.document_service.DocumentTextExtractor.extract",
                side_effect=ValueError("simulated extraction failure"),
            ),
            patch(
                "app.services.document_service.DocumentChunkRepository.delete_by_document",
                new_callable=AsyncMock,
            ),
        ):
            db.get = AsyncMock(return_value=document)

            with pytest.raises(HTTPException) as exc:
                await DocumentService.save_document(
                    db=db,
                    file=upload,
                    user=user,
                )

        assert exc.value.status_code == 500
        assert document.processing_status == "failed"
        assert document.processing_error is not None
        assert db.commit.await_count >= 1
        assert list(upload_dir.glob("*.txt")) == []

    asyncio.run(run_test())
