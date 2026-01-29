from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DatabaseDep
from app.models import Message, Sale, SaleCreate, SalePublic, SalesPublic

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/", response_model=SalesPublic)
async def read_sales(
    db: DatabaseDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve sales."""
    count = await db.sales.count_documents({})
    cursor = db.sales.find().sort("created_at", -1).skip(skip).limit(limit)
    sales = [Sale(**sale_dict) async for sale_dict in cursor]
    
    return SalesPublic(data=sales, count=count)


@router.get("/{id}", response_model=SalePublic)
async def read_sale(db: DatabaseDep, current_user: CurrentUser, id: str) -> Any:
    """Get sale by ID."""
    sale_dict = await db.sales.find_one({"_id": id})
    if not sale_dict:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    return Sale(**sale_dict)


@router.post("/", response_model=SalePublic)
async def create_sale(
    *, db: DatabaseDep, current_user: CurrentUser, sale_in: SaleCreate
) -> Any:
    """Create new sale."""
    # Calculate totals
    subtotal = 0.0
    items_with_subtotal = []
    
    for item in sale_in.items:
        # Verify product exists
        product_dict = await db.products.find_one({"_id": item.product_id})
        if not product_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )
        
        item_subtotal = (item.unit_price * item.quantity) - item.discount
        subtotal += item_subtotal
        
        items_with_subtotal.append({
            **item.model_dump(),
            "subtotal": item_subtotal
        })
    
    # Generate sale number
    count = await db.sales.count_documents({})
    sale_number = f"SALE-{count + 1:06d}"
    
    # Calculate tax and total (example: 10% tax)
    tax = subtotal * 0.1
    total = subtotal + tax
    
    sale_dict = {
        "sale_number": sale_number,
        "customer_name": sale_in.customer_name,
        "customer_email": sale_in.customer_email,
        "customer_phone": sale_in.customer_phone,
        "payment_method": sale_in.payment_method,
        "items": items_with_subtotal,
        "subtotal": subtotal,
        "tax": tax,
        "discount": 0,
        "total": total,
        "status": "completed",
        "user_id": current_user.id,
        "notes": sale_in.notes,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    result = await db.sales.insert_one(sale_dict)
    sale_dict["_id"] = result.inserted_id
    
    # Update product stock
    for item in sale_in.items:
        await db.products.update_one(
            {"_id": item.product_id},
            {"$inc": {"stock_quantity": -item.quantity}}
        )
    
    return Sale(**sale_dict)


@router.delete("/{id}")
async def delete_sale(db: DatabaseDep, current_user: CurrentUser, id: str) -> Message:
    """Delete a sale (cancel)."""
    sale_dict = await db.sales.find_one({"_id": id})
    if not sale_dict:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    sale = Sale(**sale_dict)
    if sale.status == "cancelled":
        raise HTTPException(status_code=400, detail="Sale already cancelled")
    
    # Restore product stock
    for item in sale.items:
        await db.products.update_one(
            {"_id": item.product_id},
            {"$inc": {"stock_quantity": item.quantity}}
        )
    
    # Mark as cancelled instead of deleting
    await db.sales.update_one(
        {"_id": id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}}
    )
    
    return Message(message="Sale cancelled successfully")
