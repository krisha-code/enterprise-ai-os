from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.chat_service import ChatService


router = APIRouter(
    prefix="/conversations/{conversation_id}",
    tags=["Chat"],
)


@router.post(
    "/chat",
    response_model=RAGResponse,
)
async def chat(
    conversation_id: int,
    request: RAGRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChatService.chat(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        question=request.question,
        limit=2,
    )