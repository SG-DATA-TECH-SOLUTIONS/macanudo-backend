from typing import Annotated, Literal
from pydantic import BaseModel, Field
from .base import PyObjectId, TimestampModel


class SaleItemCreate(BaseModel):
    product_id: PyObjectId
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount: float = Field(ge=0, default=0)


class SaleItem(SaleItemCreate):
    subtotal: float = Field(ge=0)


class SaleCreate(TimestampModel):
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)
    payment_method: Literal["cash", "card", "transfer", "other"]
    items: list[SaleItemCreate]
    notes: str | None = Field(default=None, max_length=1000)


class SalePublic(TimestampModel):
    id: Annotated[PyObjectId, Field(alias="_id")]
    sale_number: str
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None
    payment_method: str
    items: list[SaleItem]
    subtotal: float
    tax: float
    discount: float
    total: float
    status: str
    user_id: PyObjectId
    notes: str | None


class SalesPublic(TimestampModel):
    data: list[SalePublic]
    count: int


class Sale(TimestampModel):
    sale_number: str = Field(unique=True, max_length=50)
    customer_name: str | None = Field(default=None, max_length=255)
    customer_email: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)
    payment_method: Literal["cash", "card", "transfer", "other"]
    items: list[SaleItem] = Field(default_factory=list)
    subtotal: float = Field(ge=0)
    tax: float = Field(ge=0, default=0)
    discount: float = Field(ge=0, default=0)
    total: float = Field(ge=0)
    status: Literal["pending", "completed", "cancelled"] = "completed"
    user_id: PyObjectId
    notes: str | None = Field(default=None, max_length=1000)
