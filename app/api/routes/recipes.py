import uuid
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DatabaseDep
from app.models import (
    Message,
    Recipe,
    RecipeCreate,
    RecipePublic,
    RecipesPublic,
    RecipeUpdate,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=RecipesPublic)
async def read_recipes(
    db: DatabaseDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve recipes."""
    count = await db.recipes.count_documents({})
    cursor = db.recipes.find().skip(skip).limit(limit)
    recipes = [Recipe(**recipe_dict) async for recipe_dict in cursor]

    return RecipesPublic(data=recipes, count=count)


@router.get("/{id}", response_model=RecipePublic)
async def read_recipe(db: DatabaseDep, current_user: CurrentUser, id: str) -> Any:
    """Get recipe by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe_dict = await db.recipes.find_one({"_id": ObjectId(id)})
    if not recipe_dict:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return Recipe(**recipe_dict)


@router.post("/", response_model=RecipePublic)
async def create_recipe(
    *, db: DatabaseDep, current_user: CurrentUser, recipe_in: RecipeCreate
) -> Any:
    """Create new recipe."""
    # Verify product exists
    product_dict = await db.products.find_one({"_id": recipe_in.product_id})
    if not product_dict:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify all ingredients exist
    for ingredient in recipe_in.ingredients:
        item_dict = await db.items.find_one({"_id": ingredient.item_id})
        if not item_dict:
            raise HTTPException(
                status_code=404, detail=f"Item {ingredient.item_id} not found"
            )

    recipe_dict = recipe_in.model_dump()
    result = await db.recipes.insert_one(recipe_dict)
    recipe_dict["_id"] = result.inserted_id

    return Recipe(**recipe_dict)


@router.put("/{id}", response_model=RecipePublic)
async def update_recipe(
    *, db: DatabaseDep, current_user: CurrentUser, id: str, recipe_in: RecipeUpdate
) -> Any:
    """Update a recipe."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe_dict = await db.recipes.find_one({"_id": ObjectId(id)})
    if not recipe_dict:
        raise HTTPException(status_code=404, detail="Recipe not found")

    update_data = recipe_in.model_dump(exclude_unset=True)

    # Verify product exists if being updated
    if recipe_in.product_id:
        product_dict = await db.products.find_one({"_id": recipe_in.product_id})
        if not product_dict:
            raise HTTPException(status_code=404, detail="Product not found")

    # Verify all ingredients exist if being updated
    if recipe_in.ingredients:
        for ingredient in recipe_in.ingredients:
            item_dict = await db.items.find_one({"_id": ingredient.item_id})
            if not item_dict:
                raise HTTPException(
                    status_code=404, detail=f"Item {ingredient.item_id} not found"
                )

    if update_data:
        await db.recipes.update_one({"_id": ObjectId(id)}, {"$set": update_data})

    updated_recipe_dict = await db.recipes.find_one({"_id": ObjectId(id)})
    return Recipe(**updated_recipe_dict)


@router.delete("/{id}")
async def delete_recipe(db: DatabaseDep, current_user: CurrentUser, id: str) -> Message:
    """Delete a recipe."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID")

    recipe_dict = await db.recipes.find_one({"_id": ObjectId(id)})
    if not recipe_dict:
        raise HTTPException(status_code=404, detail="Recipe not found")

    await db.recipes.delete_one({"_id": ObjectId(id)})
    return Message(message="Recipe deleted successfully")