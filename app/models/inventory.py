from typing import Annotated, List, Literal
from pydantic import Field
from .base import TimestampModel

# --- Inventory Models ---

class InventoryAdjustmentBase(TimestampModel):
    item_id: str
    adjustment_type: Literal["add", "remove", "set"]
    quantity: float = Field(gt=0)
    reason: str | None = Field(default=None, max_length=500)
    reference: str | None = Field(default=None, max_length=255)

class InventoryAdjustmentCreate(InventoryAdjustmentBase):
    pass

class InventoryAdjustmentPublic(InventoryAdjustmentBase):
    id: Annotated[str, Field(alias="_id")]
    user_id: str
    previous_quantity: float
    new_quantity: float

class InventoryAdjustmentsPublic(TimestampModel):
    data: list[InventoryAdjustmentPublic]
    count: int

class InventoryAdjustment(InventoryAdjustmentBase):
    user_id: str
    previous_quantity: float
    new_quantity: float
