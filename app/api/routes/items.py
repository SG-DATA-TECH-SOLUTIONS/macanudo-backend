from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DatabaseDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
async def read_items(
    db: DatabaseDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve items."""
    if current_user.is_superuser:
        count = await db.items.count_documents({})
        cursor = db.items.find().skip(skip).limit(limit)
        items = [Item(**item_dict) async for item_dict in cursor]
    else:
        query = {"owner_id": current_user.id}
        count = await db.items.count_documents(query)
        cursor = db.items.find(query).skip(skip).limit(limit)
        items = [Item(**item_dict) async for item_dict in cursor]

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
async def read_item(db: DatabaseDep, current_user: CurrentUser, id: str) -> Any:
    """Get item by ID."""
    item_dict = await db.items.find_one({"_id": id})
    if not item_dict:
        raise HTTPException(status_code=404, detail="Item not found")

    item = Item(**item_dict)
    if not current_user.is_superuser and str(item.owner_id) != str(current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return item


@router.post("/", response_model=ItemPublic)
async def create_item(
    *, db: DatabaseDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """Create new item."""
    item_dict = item_in.model_dump()
    item_dict["owner_id"] = current_user.id

    result = await db.items.insert_one(item_dict)
    item_dict["_id"] = result.inserted_id

    return Item(**item_dict)


@router.put("/{id}", response_model=ItemPublic)
async def update_item(
    *, db: DatabaseDep, current_user: CurrentUser, id: str, item_in: ItemUpdate
) -> Any:
    """Update an item."""
    item_dict = await db.items.find_one({"_id": id})
    if not item_dict:
        raise HTTPException(status_code=404, detail="Item not found")

    item = Item(**item_dict)
    if not current_user.is_superuser and str(item.owner_id) != str(current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    update_data = item_in.model_dump(exclude_unset=True)
    if update_data:
        await db.items.update_one({"_id": id}, {"$set": update_data})

    updated_item_dict = await db.items.find_one({"_id": id})
    return Item(**updated_item_dict)


@router.delete("/{id}")
async def delete_item(db: DatabaseDep, current_user: CurrentUser, id: str) -> Message:
    """Delete an item."""
    item_dict = await db.items.find_one({"_id": id})
    if not item_dict:
        raise HTTPException(status_code=404, detail="Item not found")

    item = Item(**item_dict)
    if not current_user.is_superuser and str(item.owner_id) != str(current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    await db.items.delete_one({"_id": id})
    return Message(message="Item deleted successfully")
