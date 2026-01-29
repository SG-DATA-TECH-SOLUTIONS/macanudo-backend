from typing import TYPE_CHECKING, Annotated
from pydantic import Field
from .base import TimestampModel

if TYPE_CHECKING:
    from .user import User


# Shared properties
class ItemBase(TimestampModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item update
class ItemUpdate(TimestampModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    description: str | None = Field(default=None, max_length=255)


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: Annotated[str, Field(alias="_id")]
    owner_id: str


class ItemsPublic(TimestampModel):
    data: list[ItemPublic]
    count: int


# Database model, database table inferred from class name
class Item(ItemBase):
    owner_id: str

    class Config:
        collection = "items"
