from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_admin
from app.core.permissions import require_permission
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ---------------------------------------------------------
# CREATE USER
# Permission: users:create
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=UserResponse,
)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users:create")
    ),
):
    return await UserService.create_user(
        db,
        user,
    )


# ---------------------------------------------------------
# GET USERS
# Permission: users:read
# ---------------------------------------------------------

@router.get(
    "/",
    response_model=List[UserResponse],
)
async def get_users(
    name: str | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "asc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users:read")
    ),
):
    return await UserService.get_users(
        db,
        name,
        skip,
        limit,
        sort_by,
        order,
    )


# ---------------------------------------------------------
# GET ALL USERS - ADMIN ONLY
# Permission: admin role
# ---------------------------------------------------------

@router.get(
    "/admin/all",
    response_model=List[UserResponse],
)
async def get_all_users_admin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await UserService.get_users(
        db,
    )


# ---------------------------------------------------------
# GET SINGLE USER
# Permission: users:read
# ---------------------------------------------------------
@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await UserService.deactivate_user(
        db,
        user_id,
    )


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await UserService.activate_user(
        db,
        user_id,
    )

@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users:read")
    ),
):
    # Normal users can only access their own profile.
    # Admins can access any user.
    if (
        user_id != current_user.id
        and current_user.role.name != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this user",
        )

    return await UserService.get_user(
        db,
        user_id,
    )


# ---------------------------------------------------------
# UPDATE USER
# Permission: users:update
# ---------------------------------------------------------

@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users:update")
    ),
):
    return await UserService.update_user(
        db,
        user_id,
        user,
    )


# ---------------------------------------------------------
# DELETE USER
# Permission: users:delete
# ---------------------------------------------------------

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users:delete")
    ),
):
    await UserService.delete_user(
        db,
        user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )