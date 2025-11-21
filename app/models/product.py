# ...existing code...
from typing import List, Optional
import uuid
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

# --- Product Models ---

class ProductBase(SQLModel):
    name: str
    unit: str
    current_stock: float
    min_stock: float
    cost: float
    category: str  # 'ingredient' | 'final-product'

class Product(ProductBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    
    # Relationships
    recipe_ingredients: List["RecipeIngredient"] = Relationship(back_populates="product", cascade_delete=True)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(SQLModel):
    name: str | None = None
    unit: str | None = None
    current_stock: float | None = None
    min_stock: float | None = None
    cost: float | None = None
    category: str | None = None

class ProductPublic(ProductBase):
    id: uuid.UUID
    owner_id: uuid.UUID

class ProductsPublic(SQLModel):
    data: List[ProductPublic]
    count: int