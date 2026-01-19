from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import (
    CurrentUser,
    DatabaseDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(db: DatabaseDep, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve users."""
    count = await db.users.count_documents({})

    cursor = db.users.find().skip(skip).limit(limit)
    users = [User(**user_dict) async for user_dict in cursor]

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, db: DatabaseDep, user_in: UserCreate) -> Any:
    """Create new user."""
    user = await crud.get_user_by_email(db=db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = await crud.create_user(db=db, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    *, db: DatabaseDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""
    if user_in.email:
        existing_user = await crud.get_user_by_email(db=db, email=user_in.email)
        if existing_user and str(existing_user.id) != str(current_user.id):
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    update_data = user_in.model_dump(exclude_unset=True)
    if update_data:
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": update_data},
        )

    updated_user = await crud.get_user_by_id(db, str(current_user.id))
    return updated_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, db: DatabaseDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )

    hashed_password = get_password_hash(body.new_password)
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"hashed_password": hashed_password}},
    )

    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    """Get current user."""
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(db: DatabaseDep, current_user: CurrentUser) -> Any:
    """Delete own user."""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )

    await db.users.delete_one({"_id": current_user.id})
    await db.items.delete_many({"owner_id": current_user.id})

    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(db: DatabaseDep, user_in: UserRegister) -> Any:
    """Create new user without the need to be logged in."""
    user = await crud.get_user_by_email(db=db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    user_create = UserCreate.model_validate(user_in)
    user = await crud.create_user(db=db, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: str, db: DatabaseDep, current_user: CurrentUser
) -> Any:
    """Get a specific user by id."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(user.id) == str(current_user.id):
        return user

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    db: DatabaseDep,
    user_id: str,
    user_in: UserUpdate,
) -> Any:
    """Update a user."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    db_user = await crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )

    if user_in.email:
        existing_user = await crud.get_user_by_email(db=db, email=user_in.email)
        if existing_user and str(existing_user.id) != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    updated_user = await crud.update_user(db=db, user_id=user_id, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    db: DatabaseDep, current_user: CurrentUser, user_id: str
) -> Message:
    """Delete a user."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )

    await db.items.delete_many({"owner_id": ObjectId(user_id)})
    await db.users.delete_one({"_id": ObjectId(user_id)})

    return Message(message="User deleted successfully")
