import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.services.document_service import DocumentService


MAX_SIZE = DocumentService.MAX_FILE_SIZE


def make_upload(size: int) -> UploadFile:
    return UploadFile(
        filename="boundary-test.txt",
        file=BytesIO(b"x" * size),
        headers={"content-type": "text/plain"},
    )


def test_upload_exactly_at_size_limit_passes_size_check():
    async def run_test():
        upload = make_upload(MAX_SIZE)

        contents = await upload.read(MAX_SIZE + 1)

        assert len(contents) == MAX_SIZE

    asyncio.run(run_test())


def test_upload_one_byte_over_limit_is_rejected():
    async def run_test():
        db = AsyncMock()
        user = SimpleNamespace(id=7)
        upload = make_upload(MAX_SIZE + 1)

        with patch.object(DocumentService, "UPLOAD_DIR") as upload_dir:
            with pytest.raises(HTTPException) as exc:
                await DocumentService.save_document(
                    db=db,
                    file=upload,
                    user=user,
                )

        assert exc.value.status_code == 413
        assert exc.value.detail == "File size exceeds 10 MB limit"
        db.add.assert_not_called()
        db.commit.assert_not_awaited()
        upload_dir.mkdir.assert_not_called()

    asyncio.run(run_test())

