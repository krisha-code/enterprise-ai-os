from pathlib import Path
from uuid import uuid4
import logging

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.user import User
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentUploadResponse
from app.services.document_chunker import DocumentChunker
from app.services.document_text_extractor import (
    DocumentTextExtractor,
)
from app.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class DocumentService:
    UPLOAD_DIR = Path("uploads/documents")

    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    @staticmethod
    async def save_document(
        db: AsyncSession,
        file: UploadFile,
        user: User,
    ) -> DocumentUploadResponse:
        file_path = None
        document = None

        try:
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Filename is required",
                )

            if file.content_type not in DocumentService.ALLOWED_CONTENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type",
                )

            # Read no more than the limit plus one byte.
            # This prevents an oversized upload from being read entirely
            # into memory before the size check.
            contents = await file.read(
                DocumentService.MAX_FILE_SIZE + 1
            )

            if not contents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty",
                )

            if len(contents) > DocumentService.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds 10 MB limit",
                )

            original_filename = Path(file.filename).name
            file_extension = Path(original_filename).suffix.lower()

            if file_extension not in {".pdf", ".docx", ".txt"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file extension",
                )

            DocumentService.UPLOAD_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            storage_filename = f"{uuid4()}{file_extension}"
            file_path = DocumentService.UPLOAD_DIR / storage_filename
            file_path.write_bytes(contents)

            document = Document(
                user_id=user.id,
                organization_id=user.organization_id,
                filename=original_filename,
                file_path=str(file_path),
                content_type=file.content_type,
                processing_status="processing",
                processing_error=None,
            )

            db.add(document)
            await db.commit()
            await db.refresh(document)

            extracted_blocks = DocumentTextExtractor.extract(
                file_path=str(file_path),
                content_type=file.content_type,
            )

            extracted_text = "\n\n".join(
                block.content for block in extracted_blocks
            )

            if not extracted_text.strip():
                raise ValueError(
                    "Could not extract usable text from document"
                )

            chunks = DocumentChunker.chunk_text(extracted_blocks)

            if not chunks:
                raise ValueError(
                    "Could not create usable chunks from document"
                )

            chunk_contents = [chunk.content for chunk in chunks]
            section_titles = [chunk.section_title for chunk in chunks]
            page_numbers = [chunk.page_number for chunk in chunks]

            embeddings = EmbeddingService.generate_embeddings(
                chunk_contents
            )

            if len(embeddings) != len(chunk_contents):
                raise ValueError(
                    "Embedding count does not match chunk count"
                )

            await DocumentChunkRepository.create_many(
                db=db,
                document_id=document.id,
                chunks=chunk_contents,
                embeddings=embeddings,
                section_titles=section_titles,
                page_numbers=page_numbers,
            )

            document.extracted_text = extracted_text
            document.processing_status = "completed"
            document.processing_error = None

            await db.commit()
            await db.refresh(document)

            return DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                status=document.processing_status,
            )

        except HTTPException:
            await db.rollback()

            if document is not None:
                await DocumentService._mark_failed(
                    db,
                    document.id,
                    "Document upload or processing failed",
                )
            elif file_path is not None:
                try:
                    file_path.unlink(missing_ok=True)
                except OSError:
                    logger.exception(
                        "Could not remove file after upload failure"
                    )

            raise

        except Exception as exc:
            await db.rollback()

            logger.exception("Document processing failed")

            if document is not None:
                await DocumentService._mark_failed(
                    db,
                    document.id,
                    "Document processing failed. Please retry the upload.",
                )
            elif file_path is not None:
                try:
                    file_path.unlink(missing_ok=True)
                except OSError:
                    logger.exception(
                        "Could not remove file after processing failure"
                    )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document processing failed. Please retry the upload.",
            ) from exc

    @staticmethod
    async def _mark_failed(
        db: AsyncSession,
        document_id: int,
        error_message: str,
    ) -> None:
        try:
            await db.rollback()

            document = await db.get(Document, document_id)

            if document is None:
                return

            await DocumentChunkRepository.delete_by_document(
                db=db,
                document_id=document_id,
            )

            document.processing_status = "failed"
            document.processing_error = error_message
            stored_path = document.file_path

            await db.commit()

            # Keep the failed database record for diagnostics.
            # Remove the physical file only after commit succeeds.
            try:
                Path(stored_path).unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Could not remove file for failed document %s",
                    document_id,
                )

        except Exception:
            await db.rollback()
            logger.exception(
                "Could not record failure for document %s",
                document_id,
            )

    @staticmethod
    async def get_user_documents(
        db: AsyncSession,
        user: User,
    ) -> list[Document]:
        return await DocumentRepository.get_by_user(
            db=db,
            organization_id=user.organization_id,
        )

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document_id: int,
        user: User,
    ) -> None:
        if user.role.name == "admin":
            document = await DocumentRepository.get_by_id_and_organization(
                db=db,
                document_id=document_id,
                organization_id=user.organization_id,
            )
        else:
            document = await DocumentRepository.get_by_id_and_user(
                db=db,
                document_id=document_id,
                user_id=user.id,
            )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        stored_path = document.file_path

        try:
            await DocumentChunkRepository.delete_by_document(
                db=db,
                document_id=document.id,
            )

            document.is_active = False
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception(
                "Could not delete document %s",
                document_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete document",
            ) from None

        # Database changes are committed; now remove the stored file.
        # A filesystem cleanup error must not imply the DB rollback succeeded.
        try:
            Path(stored_path).unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Document %s was deactivated, but its file could not be removed",
                document_id,
            )
