from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, DatabaseDep
from app.core import security
from app.core.config import settings
from app.models import Message, NewPassword, Token

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
async def login_access_token(
    db: DatabaseDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests"""
    user = await crud.authenticate(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            str(user.id), expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=Message)
async def test_token(current_user: CurrentUser) -> Any:
    """Test access token"""
    return Message(message="Token is valid")


@router.post("/password-recovery/{email}")
async def recover_password(email: str, db: DatabaseDep) -> Message:
    """Password Recovery"""
    user = await crud.get_user_by_email(db=db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    # TODO: Implement password recovery email
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
async def reset_password(db: DatabaseDep, body: NewPassword) -> Message:
    """Reset password"""
    # TODO: Implement password reset logic with token verification
    return Message(message="Password updated successfully")
