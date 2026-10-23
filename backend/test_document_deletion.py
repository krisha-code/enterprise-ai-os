import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.document_service import DocumentService


def test_delete_document_returns_404_when_not_owned():
    async def run_test():
        db = AsyncMock()
        user = SimpleNamespace(id=7, role=SimpleNamespace(name="user"))

        with patch(
            "app.services.document_service.DocumentRepository.get_by_id_and_user",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc:
                await DocumentService.delete_document(
                    db=db,
                    document_id=42,
                    user=user,
                )

        assert exc.value.status_code == 404
        db.commit.assert_not_awaited()

    asyncio.run(run_test())


def test_delete_document_removes_chunks_and_deactivates_document():
    async def run_test():
        db = AsyncMock()
        user = SimpleNamespace(id=7, role=SimpleNamespace(name="user"))
        document = SimpleNamespace(
            id=42,
            is_active=True,
            file_path="uploads/documents/test-document.txt",
        )

        with (
            patch(
                "app.services.document_service.DocumentRepository.get_by_id_and_user",
                new_callable=AsyncMock,
                return_value=document,
            ),
            patch(
                "app.services.document_service.DocumentChunkRepository.delete_by_document",
                new_callable=AsyncMock,
            ) as delete_chunks,
            patch.object(Path, "unlink") as unlink_file,
        ):
            await DocumentService.delete_document(
                db=db,
                document_id=42,
                user=user,
            )

        delete_chunks.assert_awaited_once_with(
            db=db,
            document_id=42,
        )
        assert document.is_active is False
        db.commit.assert_awaited_once()
        unlink_file.assert_called_once_with(missing_ok=True)

    asyncio.run(run_test())


def test_delete_document_rolls_back_when_database_cleanup_fails():
    async def run_test():
        db = AsyncMock()
        user = SimpleNamespace(id=7, role=SimpleNamespace(name="user"))
        document = SimpleNamespace(
            id=42,
            is_active=True,
            file_path="uploads/documents/test-document.txt",
        )

        with (
            patch(
                "app.services.document_service.DocumentRepository.get_by_id_and_user",
                new_callable=AsyncMock,
                return_value=document,
            ),
            patch(
                "app.services.document_service.DocumentChunkRepository.delete_by_document",
                new_callable=AsyncMock,
                side_effect=RuntimeError("database failure"),
            ),
            patch.object(Path, "unlink") as unlink_file,
        ):
            with pytest.raises(HTTPException) as exc:
                await DocumentService.delete_document(
                    db=db,
                    document_id=42,
                    user=user,
                )

        assert exc.value.status_code == 500
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()
        unlink_file.assert_not_called()

    asyncio.run(run_test())


def test_delete_document_logs_filesystem_cleanup_failure(caplog):
    async def run_test():
        db = AsyncMock()
        user = SimpleNamespace(id=7, role=SimpleNamespace(name="user"))
        document = SimpleNamespace(
            id=42,
            is_active=True,
            file_path="uploads/documents/test-document.txt",
        )

        with (
            patch(
                "app.services.document_service.DocumentRepository.get_by_id_and_user",
                new_callable=AsyncMock,
                return_value=document,
            ),
            patch(
                "app.services.document_service.DocumentChunkRepository.delete_by_document",
                new_callable=AsyncMock,
            ),
            patch.object(
                Path,
                "unlink",
                side_effect=OSError("permission denied"),
            ) as unlink_file,
            caplog.at_level(
                logging.ERROR,
                logger="app.services.document_service",
            ),
        ):
            await DocumentService.delete_document(
                db=db,
                document_id=42,
                user=user,
            )

        assert document.is_active is False
        db.commit.assert_awaited_once()
        db.rollback.assert_not_awaited()
        unlink_file.assert_called_once_with(missing_ok=True)
        assert any(
            "file could not be removed" in record.getMessage()
            for record in caplog.records
        )

    asyncio.run(run_test())
