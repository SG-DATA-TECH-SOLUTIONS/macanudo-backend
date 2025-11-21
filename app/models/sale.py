# ...existing code...
from typing import List, Optional
import uuid
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

# --- Sale Models ---

class SaleItem(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sale_id: uuid.UUID = Field(foreign_key="sale.id", nullable=False, ondelete="CASCADE")
    name: str
    quantity: float
    price: float
    product_id: uuid.UUID | None = Field(default=None, foreign_key="product.id") # Optional link

class SaleBase(SQLModel):
    total: float
    payment_method: str
    timestamp: int # Unix timestamp
    waiter_name: str
    event: str | None = None
    other_error_reason: str | None = None
    other_error_notes: str | None = None
    general_notes: str | None = None
    
    # Complex JSON fields
    errors: dict = Field(default={}, sa_column=Column(JSON))
    return_data: dict | None = Field(default=None, sa_column=Column(JSON))

class Sale(SaleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    
    items: List[SaleItem] = Relationship(back_populates="sale", cascade_delete=True)

class SaleItemCreate(SQLModel):
    name: str
    quantity: float
    price: float
    product_id: uuid.UUID | None = None

class SaleCreate(SaleBase):
    items: List[SaleItemCreate]

class SalePublic(SaleBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    items: List[SaleItemCreate]

class SalesPublic(SQLModel):
    data: List[SalePublic]
    count: int