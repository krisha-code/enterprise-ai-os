from fastapi import APIRouter, Depends, File, Response, UploadFile, status
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
    document_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await DocumentSearchService.search(
        db=db,
        query=query,
        organization_id=current_user.organization_id,
        limit=limit,
        document_id=document_id,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await DocumentService.delete_document(
        db=db,
        document_id=document_id,
        user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
