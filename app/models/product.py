from typing import Annotated, List
from pydantic import Field
from .base import PyObjectId, TimestampModel

# --- Product Models ---

class ProductBase(TimestampModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    price: float = Field(gt=0)
    cost: float | None = Field(default=None, ge=0)
    stock_quantity: int = Field(ge=0, default=0)
    unit: str = Field(max_length=50, default="unit")
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(TimestampModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, gt=0)
    cost: float | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None

class ProductPublic(ProductBase):
    id: Annotated[PyObjectId, Field(alias="_id")]

class ProductsPublic(TimestampModel):
    data: list[ProductPublic]
    count: int

class Product(ProductBase):
    pass