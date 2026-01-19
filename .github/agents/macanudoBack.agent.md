---
description: 'Describe what this custom agent does and when to use it.'
tools: ['runCommands', 'runTasks', 'edit', 'runNotebooks', 'search', 'new', 'MCP_DOCKER/*', 'pylance mcp server/*', 'extensions', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'todos', 'runSubagent', 'runTests']
---

# FastAPI Backend - AI Coding Agent Instructions

## Project Architecture

This is a FastAPI backend using **MongoDB** (NoSQL) with Motor (async MongoDB driver) and Pydantic for data validation. The codebase follows a layered architecture optimized for document-based storage:

- **`app/models/`**: Pydantic models for document schemas and API validation
  - Each domain has its own file: `user.py`, `product.py`, `recipe.py`, `sale.py`, `inventory.py`, `item.py`
  - **Document models** inherit from `BaseModel` (Pydantic v2) for MongoDB collections
  - Schema classes for API I/O (e.g., `ProductCreate`, `ProductPublic`, `ProductUpdate`, `ProductsPublic` for lists)
  - **ObjectId strings are used as primary keys** (`str` type with MongoDB ObjectId validation)
  - Use `Field(default_factory=lambda: str(ObjectId()))` for auto-generated IDs
  - All exports centralized in `app/models/__init__.py` - import models from here, not individual files
  - **Embedded documents** for one-to-many relationships (e.g., `Recipe.ingredients: List[RecipeIngredient]`)
  - **Reference fields** (`product_id: str`) for many-to-one relationships that need to be queried separately
  - Complex nested structures use Pydantic models directly (see `Sale.items`, `Sale.errors`, `Sale.return_data`)
  
- **`app/crud.py`**: Database operations using Motor async patterns
  - Always use async/await: `await collection.find_one()`, `await collection.insert_one()`, etc.
  - Use Pydantic's `model_dump()` to convert to dicts for MongoDB: `await collection.insert_one(model.model_dump())`
  - Parse results with `model_validate()`: `Product.model_validate(doc)` or `Product(**doc)`
  - Aggregation pipelines for complex queries (joins, grouping)
  - Index creation for performance on frequently queried fields

- **`app/api/routes/`**: FastAPI route handlers organized by resource (products, recipes, sales, inventory, etc.)
  - **ALL endpoints must be async def** to work with Motor
  - Use dependency injection: `DatabaseDep`, `CurrentUser` (see `app/api/deps.py`)
  - All endpoints require authentication except login/register
  - Superuser checks use `Depends(get_current_active_superuser)`
  - Standard CRUD pattern: list (with pagination), get by ID, create, update, delete
  - **Owner-based filtering**: non-superusers only see their own records via MongoDB queries

## Domain Model: Business Logic

This backend manages a restaurant/inventory system with:

- **Products**: Ingredients and final products with stock tracking (`category: 'ingredient' | 'final-product'`)
- **Recipes**: Multi-ingredient recipes with **embedded** `RecipeIngredient` subdocuments
- **Sales**: Transactional records with **embedded** `SaleItem` subdocuments, complex error/return tracking
- **Inventory**: Stock adjustment records referencing product IDs
- **Users**: Multi-tenant with owner-based data isolation (all documents have `owner_id` field)

### Document Design Patterns

**Embedded Documents** (store child data within parent):
```python
# Recipe model with embedded ingredients
class RecipeIngredient(BaseModel):
    product_id: str  # Reference to Product
    quantity: float

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    owner_id: str
    name: str
    preparation_time: int
    price: float
    category: str
    ingredients: List[RecipeIngredient] = []  # Embedded array
```

**Reference Pattern** (link to other collections):
```python
class InventoryAdjustment(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    owner_id: str
    product_id: str  # Reference to products collection
    quantity: float
    type: str
    reason: str
    timestamp: int
```

### Creating Documents with Embedded Data

MongoDB stores nested structures naturally. No separate inserts needed:

```python
@router.post("/", response_model=RecipePublic)
async def create_recipe(
    db: DatabaseDep, current_user: CurrentUser, recipe_in: RecipeCreate
) -> Any:
    # Convert Pydantic model to dict, add owner_id
    recipe_dict = recipe_in.model_dump()
    recipe_dict["owner_id"] = current_user.id
    recipe_dict["id"] = str(ObjectId())
    
    # Single insert includes embedded ingredients
    result = await db["recipes"].insert_one(recipe_dict)
    
    # Retrieve and return
    doc = await db["recipes"].find_one({"_id": result.inserted_id})
    return Recipe.model_validate(doc)
```

See `app/api/routes/recipes.py` and `app/api/routes/sales.py` for complete examples.

## Critical Patterns

### Database Access (Motor Async)
```python
from app.api.deps import DatabaseDep, CurrentUser

@router.get("/")
async def endpoint(db: DatabaseDep, current_user: CurrentUser):
    # DatabaseDep provides MongoDB database instance
    # Access collections: db["collection_name"]
    # ALL database operations must use await
```

### CRUD Operations (MongoDB)
```python
# Create - insert document
doc_dict = model.model_dump()
doc_dict["owner_id"] = current_user.id
doc_dict["id"] = str(ObjectId())
result = await db["products"].insert_one(doc_dict)

# Read - find one
doc = await db["products"].find_one({"_id": ObjectId(id), "owner_id": owner_id})
if doc:
    product = Product.model_validate(doc)

# Read - find many with pagination
cursor = db["products"].find({"owner_id": owner_id}).skip(skip).limit(limit)
products = [Product.model_validate(doc) async for doc in cursor]

# Update - update document
await db["products"].update_one(
    {"_id": ObjectId(id)},
    {"$set": update_dict}
)

# Delete - remove document
await db["products"].delete_one({"_id": ObjectId(id)})

# Count documents
count = await db["products"].count_documents({"owner_id": owner_id})
```

### Owner-Based Filtering (Multi-tenant)
```python
# Superusers see all documents
if current_user.is_superuser:
    query = {}
else:
    query = {"owner_id": current_user.id}

cursor = db["products"].find(query).skip(skip).limit(limit)
products = [Product.model_validate(doc) async for doc in cursor]
```

### Authentication Flow
- JWT tokens with OAuth2 password bearer (see `app/core/security.py`)
- Token payload contains user ID as `sub` claim
- Password hashing uses bcrypt via passlib (pinned to `bcrypt==4.3.0`)
- `CurrentUser` dependency automatically validates token and returns active user

## Configuration & Environment

- **Settings**: `app/core/config.py` uses Pydantic Settings
  - Reads from `../.env` (parent directory relative to backend/)
  - Required vars: `MONGODB_URL`, `MONGODB_DATABASE`, `FIRST_SUPERUSER`, `SECRET_KEY`, `PROJECT_NAME`
  - Computed properties: `all_cors_origins`, `emails_enabled`
  - Environment modes: `local`, `staging`, `production`

- **Private routes** (`app/api/routes/private.py`) only load when `ENVIRONMENT=local`

## Database Schema Management

- **MongoDB** is schemaless but use Pydantic models for validation
- **Indexes** should be created for:
  - `owner_id` on all collections (multi-tenant queries)
  - `email` on users collection (unique index)
  - Foreign key references like `product_id`, `recipe_id`, `sale_id`
  - Timestamp fields for time-based queries
  
- Index creation typically done in `app/core/db.py` or migration scripts:
```python
# Create indexes on application startup
await db["products"].create_index([("owner_id", 1)])
await db["users"].create_index([("email", 1)], unique=True)
await db["sales"].create_index([("owner_id", 1), ("timestamp", -1)])
```

- No migrations needed for schema changes - just update Pydantic models
- For data migrations, create standalone scripts in `app/migrations/`

## Development Workflow

### Local Setup (uv package manager)
```bash
# From backend/ directory
uv sync                          # Install dependencies
source .venv/bin/activate        # Activate venv (or `.venv\Scripts\activate` on Windows)
```

### Running Tests
```bash
bash ./scripts/test.sh           # Run full test suite with Pytest
# Tests use fixtures from tests/conftest.py (session-scoped DB)
# Test utilities in tests/utils/ for creating test users/items
```

### Docker Development
```bash
docker compose watch             # Hot-reload development mode
docker compose exec backend bash # Enter container for debugging
# Inside container: fastapi run --reload app/main.py
```

### Code Quality
```bash
bash ./scripts/format.sh         # Format with ruff
bash ./scripts/lint.sh           # Lint with ruff + mypy
```

- Ruff config in `pyproject.toml`: enforces isort, pyflakes, pycodestyle, flake8-bugbear
- **No print statements allowed** (T201 rule) - use `logging` instead
- MyPy in strict mode (exclude alembic/)

## API Structure

- Base path: `/api/v1` (configured in `app/core/config.py`)
- OpenAPI docs: `/api/v1/openapi.json`
- Route organization: `app/api/main.py` aggregates routers from `app/api/routes/`
- Custom OpenAPI ID generation: uses `{tag}-{route_name}` format

## Key Dependencies

- **fastapi[standard]**: Web framework (v0.114.2)
- **motor**: Async MongoDB driver (integrates with asyncio)
- **pymongo**: MongoDB client (used by Motor)
- **pydantic**: Data validation and settings management (v2.x)
- **pyjwt**: JWT token handling
- **emails**: Email sending (SMTP) with Jinja2 templates in `app/email-templates/`
- **uvicorn**: ASGI server (without httptools due to compatibility)
- **passlib[bcrypt]**: Password hashing (pinned to `bcrypt==4.3.0`)

## Common Tasks

### Adding a New Model
1. Add model classes to `app/models/<domain>.py` (Base, Create, Update, Public classes using Pydantic `BaseModel`)
2. Export from `app/models/__init__.py` - add to `__all__` list
3. Add CRUD functions to `app/crud.py` if needed (using Motor async patterns)
4. Create routes in `app/api/routes/model_name.py` (all endpoints must be `async def`)
5. Register router in `app/api/main.py`
6. Create indexes in `app/core/db.py` for frequently queried fields

### Adding an Endpoint
- Follow dependency injection pattern (see `app/api/routes/items.py` or `app/api/routes/products.py`)
- **All endpoints must be `async def`** to work with Motor
- Use type-annotated dependencies: `DatabaseDep`, `CurrentUser`
- Return Pydantic models (e.g., `ItemPublic`, `ItemsPublic`)
- Apply authorization checks (superuser vs. owner)
- Owner-based filtering pattern:
  ```python
  if current_user.is_superuser:
      query = {}
  else:
      query = {"owner_id": current_user.id}
  
  cursor = db["products"].find(query).skip(skip).limit(limit)
  products = [Product.model_validate(doc) async for doc in cursor]
  count = await db["products"].count_documents(query)
  ```

### Email Configuration
- Templates: MJML sources in `app/email-templates/src/`, compiled HTML in `build/`
- Uses Jinja2 for variable substitution
- Email functions in `app/utils.py`: `send_email()`, `generate_*_email()`
- Emails only work when `SMTP_HOST` and `EMAILS_FROM_EMAIL` are configured

## Testing Patterns

- Fixtures in `tests/conftest.py`: `db`, `client`, `superuser_token_headers`, `normal_user_token_headers`
- Test utilities: `tests/utils/user.py` for authentication helpers
- Session-scoped DB with cleanup after all tests (MongoDB test database)
- Use `TestClient` from FastAPI for endpoint testing
- Async test functions when testing database operations directly

## Sentry Integration

- Enabled when `SENTRY_DSN` set and `ENVIRONMENT != "local"`
- Configured in `app/main.py` with tracing enabled
