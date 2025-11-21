# ...existing code...
from typing import List, Optional
import uuid
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models import Product


# --- Recipe Models ---

class RecipeBase(SQLModel):
    name: str
    preparation_time: int
    price: float
    category: str

class Recipe(RecipeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    
    ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe", cascade_delete=True)

class RecipeIngredient(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    recipe_id: uuid.UUID = Field(foreign_key="recipe.id", nullable=False, ondelete="CASCADE")
    product_id: uuid.UUID = Field(foreign_key="product.id", nullable=False)
    quantity: float

    recipe: Recipe = Relationship(back_populates="ingredients")
    product: Product = Relationship(back_populates="recipe_ingredients")

class RecipeIngredientCreate(SQLModel):
    product_id: uuid.UUID
    quantity: float

class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate]

class RecipeUpdate(SQLModel):
    name: str | None = None
    preparation_time: int | None = None
    price: float | None = None
    category: str | None = None

class RecipePublic(RecipeBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    ingredients: List[RecipeIngredientCreate]

class RecipesPublic(SQLModel):
    data: List[RecipePublic]
    count: int