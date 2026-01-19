from typing import Annotated
from pydantic import EmailStr, Field
from .base import PyObjectId, TimestampModel


class UserBase(TimestampModel):
    email: EmailStr = Field(unique=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


class UserCreate(TimestampModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserRegister(TimestampModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(TimestampModel):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserUpdateMe(TimestampModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(TimestampModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UserPublic(TimestampModel):
    id: Annotated[PyObjectId, Field(alias="_id")]
    email: EmailStr
    is_active: bool
    is_superuser: bool
    full_name: str | None = None


class UsersPublic(TimestampModel):
    data: list[UserPublic]
    count: int


class User(UserBase):
    hashed_password: str
