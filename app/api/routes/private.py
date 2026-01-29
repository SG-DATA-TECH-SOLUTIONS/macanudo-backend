from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import (
    CurrentUser,
    DatabaseDep,
    get_current_active_superuser,
)
from app.core.security import get_password_hash
from app.models import UserCreate, UserPublic

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str


@router.post("/users/")
async def create_user(*, db: DatabaseDep, user_in: PrivateUserCreate) -> Any:
    """Create new user."""
    user_dict = user_in.model_dump(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_in.password)
    
    doc_ref = db.collection("users").document()
    doc_ref.set(user_dict)

    return user_dict
