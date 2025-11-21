import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Recipe,
    RecipeCreate,
    RecipeIngredient,
    RecipePublic,
    RecipesPublic,
    RecipeUpdate,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=RecipesPublic)
def read_recipes(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Recipe)
        count = session.exec(count_statement).one()
        statement = select(Recipe).offset(skip).limit(limit)
        recipes = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Recipe)
            .where(Recipe.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Recipe)
            .where(Recipe.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        recipes = session.exec(statement).all()

    return RecipesPublic(data=recipes, count=count)


@router.post("/", response_model=RecipePublic)
def create_recipe(
    *, session: SessionDep, current_user: CurrentUser, recipe_in: RecipeCreate
) -> Any:
    # Create recipe
    recipe = Recipe.model_validate(
        recipe_in, update={"owner_id": current_user.id}, exclude={"ingredients"}
    )
    session.add(recipe)
    session.commit()
    session.refresh(recipe)

    # Create ingredients
    for ing in recipe_in.ingredients:
        recipe_ing = RecipeIngredient(
            recipe_id=recipe.id, product_id=ing.product_id, quantity=ing.quantity
        )
        session.add(recipe_ing)
    
    session.commit()
    session.refresh(recipe)
    return recipe


@router.delete("/{id}")
def delete_recipe(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    recipe = session.get(Recipe, id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not current_user.is_superuser and (recipe.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(recipe)
    session.commit()
    return Message(message="Recipe deleted successfully")