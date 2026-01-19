from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DatabaseDep
from app.models import (
    Message,
    Product,
    ProductCreate,
    ProductPublic,
    ProductsPublic,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductsPublic)
async def read_products(
    db: DatabaseDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve products."""
    count = await db.products.count_documents({})
    cursor = db.products.find().skip(skip).limit(limit)
    products = [Product(**product_dict) async for product_dict in cursor]

    return ProductsPublic(data=products, count=count)


@router.get("/{id}", response_model=ProductPublic)
async def read_product(db: DatabaseDep, current_user: CurrentUser, id: str) -> Any:
    """Get product by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product_dict = await db.products.find_one({"_id": ObjectId(id)})
    if not product_dict:
        raise HTTPException(status_code=404, detail="Product not found")

    return Product(**product_dict)


@router.post("/", response_model=ProductPublic)
async def create_product(
    *, db: DatabaseDep, current_user: CurrentUser, product_in: ProductCreate
) -> Any:
    """Create new product."""
    product_dict = product_in.model_dump()

    result = await db.products.insert_one(product_dict)
    product_dict["_id"] = result.inserted_id

    return Product(**product_dict)


@router.put("/{id}", response_model=ProductPublic)
async def update_product(
    *, db: DatabaseDep, current_user: CurrentUser, id: str, product_in: ProductUpdate
) -> Any:
    """Update a product."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product_dict = await db.products.find_one({"_id": ObjectId(id)})
    if not product_dict:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    if update_data:
        await db.products.update_one({"_id": ObjectId(id)}, {"$set": update_data})

    updated_product_dict = await db.products.find_one({"_id": ObjectId(id)})
    return Product(**updated_product_dict)


@router.delete("/{id}")
async def delete_product(
    db: DatabaseDep, current_user: CurrentUser, id: str
) -> Message:
    """Delete a product."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product_dict = await db.products.find_one({"_id": ObjectId(id)})
    if not product_dict:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if product is used in recipes
    recipe_count = await db.recipes.count_documents({"product_id": ObjectId(id)})
    if recipe_count > 0:
        raise HTTPException(
            status_code=400, detail="Cannot delete product that is used in recipes"
        )

    await db.products.delete_one({"_id": ObjectId(id)})
    return Message(message="Product deleted successfully")