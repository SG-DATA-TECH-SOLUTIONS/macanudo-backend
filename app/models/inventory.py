# ...existing code...
from typing import List, Optional
import uuid
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

# --- Inventory Models ---

class InventoryAdjustmentBase(SQLModel):
    product_id: uuid.UUID = Field(foreign_key="product.id", nullable=False)
    quantity: float
    type: str # 'waste' | 'additional-use' | 'manual-correction'
    reason: str
    timestamp: int
    user_name: str

class InventoryAdjustment(InventoryAdjustmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")

class InventoryAdjustmentCreate(InventoryAdjustmentBase):
    pass

class InventoryAdjustmentPublic(InventoryAdjustmentBase):
    id: uuid.UUID
    owner_id: uuid.UUID

class InventoryAdjustmentsPublic(SQLModel):
    data: List[InventoryAdjustmentPublic]
    count: int