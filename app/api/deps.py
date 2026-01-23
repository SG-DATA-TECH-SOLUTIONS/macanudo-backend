from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from google.cloud.firestore import Client as FirestoreClient
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.core.database import get_database
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> FirestoreClient:
    """Dependency to get Firestore client instance."""
    return get_database()


DatabaseDep = Annotated[FirestoreClient, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(db: DatabaseDep, token: TokenDep) -> User:
    """Get current authenticated user."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if not token_data.sub:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user from Firestore
    user_ref = db.collection("users").document(token_data.sub)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = user_doc.to_dict()
    user_dict["id"] = user_doc.id
    user = User(**user_dict)
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    """Dependency to verify current user is superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
