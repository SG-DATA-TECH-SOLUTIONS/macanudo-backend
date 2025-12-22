from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import (
    CurrentUser,
    DatabaseDep,
    get_current_active_superuser,
)
from app.core.security import get_password_hash
from app.models import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
async def create_user(*, db: DatabaseDep, user_in: PrivateUserCreate) -> Any:
    """Create new user."""
    user_dict = user_in.model_dump(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_in.password)

    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id

    return User(**user_dict)
