from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentSearchResult,
    DocumentUploadResponse,
)
from app.services.document_search_service import (
    DocumentSearchService,
)
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DocumentService.save_document(
        db=db,
        file=file,
        user=current_user,
    )


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
async def get_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DocumentService.get_user_documents(
        db=db,
        user=current_user,
    )


@router.get(
    "/search",
    response_model=list[DocumentSearchResult],
)
async def search_documents(
    query: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DocumentSearchService.search(
        db=db,
        query=query,
        user_id=current_user.id,
        limit=limit,
    )