from pydantic import AliasPath, BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    role_id: int
    role_name: str = Field(validation_alias=AliasPath("role", "name"))
    must_change_password: bool = False
    model_config = {
        "from_attributes": True,
    }
