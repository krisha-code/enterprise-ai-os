from pathlib import Path
from uuid import uuid4

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

        # ----------------------------------------
        # Validate filename
        # ----------------------------------------

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # ----------------------------------------
        # Validate content type
        # ----------------------------------------

        if file.content_type not in DocumentService.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )

        # ----------------------------------------
        # Read file
        # ----------------------------------------

        contents = await file.read()

        # ----------------------------------------
        # Validate file size
        # ----------------------------------------

        if len(contents) > DocumentService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10 MB limit",
            )

        # ----------------------------------------
        # Create upload directory
        # ----------------------------------------

        DocumentService.UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------
        # Generate safe storage filename
        # ----------------------------------------

        original_filename = Path(file.filename).name

        file_extension = Path(
            original_filename
        ).suffix.lower()

        storage_filename = f"{uuid4()}{file_extension}"

        file_path = (
            DocumentService.UPLOAD_DIR
            / storage_filename
        )

        # ----------------------------------------
        # Save physical file
        # ----------------------------------------

        file_path.write_bytes(contents)

        # ----------------------------------------
        # Extract document blocks
        # ----------------------------------------

        extracted_blocks = DocumentTextExtractor.extract(
            file_path=str(file_path),
            content_type=file.content_type,
        )

        # ----------------------------------------
        # Create combined extracted text
        # ----------------------------------------

        extracted_text = "\n\n".join(
            block.content
            for block in extracted_blocks
        )

        # ----------------------------------------
        # Validate extracted text
        # ----------------------------------------

        if not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract usable text from document",
            )

        # ----------------------------------------
        # Create document database record
        # ----------------------------------------

        document = Document(
            user_id=user.id,
            filename=original_filename,
            file_path=str(file_path),
            content_type=file.content_type,
            extracted_text=extracted_text,
        )

        db.add(document)

        await db.commit()
        await db.refresh(document)

        # ----------------------------------------
        # Chunk document
        # ----------------------------------------

        chunks = DocumentChunker.chunk_text(
            extracted_blocks,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create usable chunks from document",
            )

        # ----------------------------------------
        # Extract chunk content
        # ----------------------------------------

        chunk_contents = [
            chunk.content
            for chunk in chunks
        ]

        # ----------------------------------------
        # Extract chunk metadata
        # ----------------------------------------

        section_titles = [
            chunk.section_title
            for chunk in chunks
        ]

        page_numbers = [
            chunk.page_number
            for chunk in chunks
        ]

        # ----------------------------------------
        # Generate embeddings
        # ----------------------------------------

        embeddings = EmbeddingService.generate_embeddings(
            chunk_contents
        )

        # ----------------------------------------
        # Store chunks
        # ----------------------------------------

        await DocumentChunkRepository.create_many(
            db=db,
            document_id=document.id,
            chunks=chunk_contents,
            embeddings=embeddings,
            section_titles=section_titles,
            page_numbers=page_numbers,
        )

        # ----------------------------------------
        # Return response
        # ----------------------------------------

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status="uploaded",
        )

    @staticmethod
    async def get_user_documents(
        db: AsyncSession,
        user: User,
    ) -> list[Document]:

        return await DocumentRepository.get_by_user(
            db=db,
            user_id=user.id,
        )