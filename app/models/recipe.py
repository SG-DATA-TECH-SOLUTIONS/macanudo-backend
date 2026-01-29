from typing import Annotated, List, Optional
import uuid
from pydantic import BaseModel, Field
from app.models import Product
from .base import TimestampModel


# --- Recipe Models ---

class RecipeIngredientCreate(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    unit: str = Field(max_length=50)


class RecipeIngredient(RecipeIngredientCreate):
    pass


class RecipeBase(TimestampModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    product_id: str
    yield_quantity: float = Field(gt=0, default=1.0)
    yield_unit: str = Field(max_length=50, default="unit")
    instructions: str | None = Field(default=None, max_length=2000)
    is_active: bool = True


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientCreate]


class RecipeUpdate(TimestampModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    product_id: str | None = None
    yield_quantity: float | None = Field(default=None, gt=0)
    yield_unit: str | None = Field(default=None, max_length=50)
    instructions: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    ingredients: list[RecipeIngredientCreate] | None = None


class RecipePublic(RecipeBase):
    id: Annotated[str, Field(alias="_id")]
    ingredients: list[RecipeIngredient]


class RecipesPublic(TimestampModel):
    data: list[RecipePublic]
    count: int


class Recipe(RecipeBase):
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
