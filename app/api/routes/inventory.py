from typing import Any
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DatabaseDep
from app.models import (
    InventoryAdjustment,
    InventoryAdjustmentCreate,
    InventoryAdjustmentPublic,
    InventoryAdjustmentsPublic,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/adjustments", response_model=InventoryAdjustmentsPublic)
async def read_adjustments(
    db: DatabaseDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve inventory adjustments."""
    count = await db.inventory_adjustments.count_documents({})
    cursor = db.inventory_adjustments.find().sort("created_at", -1).skip(skip).limit(limit)
    adjustments = [
        InventoryAdjustment(**adj_dict) async for adj_dict in cursor
    ]
    
    return InventoryAdjustmentsPublic(data=adjustments, count=count)


@router.post("/adjustments", response_model=InventoryAdjustmentPublic)
async def create_adjustment(
    *, db: DatabaseDep, current_user: CurrentUser, adjustment_in: InventoryAdjustmentCreate
) -> Any:
    """Create inventory adjustment."""
    # Get current item
    item_dict = await db.items.find_one({"_id": adjustment_in.item_id})
    if not item_dict:
        raise HTTPException(status_code=404, detail="Item not found")
    
    previous_quantity = item_dict.get("stock_quantity", 0)
    
    # Calculate new quantity based on adjustment type
    if adjustment_in.adjustment_type == "add":
        new_quantity = previous_quantity + adjustment_in.quantity
    elif adjustment_in.adjustment_type == "remove":
        new_quantity = previous_quantity - adjustment_in.quantity
        if new_quantity < 0:
            raise HTTPException(
                status_code=400,
                detail="Adjustment would result in negative stock"
            )
    else:  # set
        new_quantity = adjustment_in.quantity
    
    # Update item stock
    await db.items.update_one(
        {"_id": adjustment_in.item_id},
        {"$set": {"stock_quantity": new_quantity}}
    )
    
    # Create adjustment record
    adjustment_dict = {
        **adjustment_in.model_dump(),
        "user_id": current_user.id,
        "previous_quantity": previous_quantity,
        "new_quantity": new_quantity,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    result = await db.inventory_adjustments.insert_one(adjustment_dict)
    adjustment_dict["_id"] = result.inserted_id
    
    return InventoryAdjustment(**adjustment_dict)