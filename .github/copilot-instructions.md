# FastAPI Backend - AI Coding Agent Instructions

## Project Architecture

This is a FastAPI backend using **SQLModel** (Pydantic + SQLAlchemy) with PostgreSQL. The codebase follows a layered architecture:

- **`app/models.py`**: All SQLModel models (DB tables + Pydantic schemas combined)
  - Models use `table=True` for DB tables (e.g., `User`, `Item`)
  - Schema classes for API I/O (e.g., `UserCreate`, `UserPublic`, `ItemUpdate`)
  - UUIDs are used as primary keys (`uuid.UUID`, not integers)
  - Relationships use `Relationship()` with `cascade_delete=True` for dependent records
  
- **`app/crud.py`**: Database operations using SQLModel/SQLAlchemy patterns
  - Always use `session.exec(select(...))` for queries (not raw SQL)
  - Follow existing patterns: `model_validate()` for creation, `sqlmodel_update()` for updates

- **`app/api/routes/`**: FastAPI route handlers organized by resource
  - Use dependency injection: `SessionDep`, `CurrentUser` (see `app/api/deps.py`)
  - All endpoints require authentication except login/register
  - Superuser checks use `Depends(get_current_active_superuser)`

## Critical Patterns

### Database Sessions
```python
from app.api.deps import SessionDep, CurrentUser

@router.get("/")
def endpoint(session: SessionDep, current_user: CurrentUser):
    # SessionDep provides auto-managed session
    # Never manually create sessions in route handlers
```

### Model Validation
```python
# Creating records - use model_validate with update dict
item = Item.model_validate(item_in, update={"owner_id": current_user.id})
session.add(item)
session.commit()
session.refresh(item)  # Always refresh to get DB defaults

# Updating records - use sqlmodel_update
db_user.sqlmodel_update(user_data, update=extra_data)
session.add(db_user)
session.commit()
session.refresh(db_user)
```

### Authentication Flow
- JWT tokens with OAuth2 password bearer (see `app/core/security.py`)
- Token payload contains user ID as `sub` claim
- Password hashing uses bcrypt via passlib (pinned to `bcrypt==4.3.0`)
- `CurrentUser` dependency automatically validates token and returns active user

## Configuration & Environment

- **Settings**: `app/core/config.py` uses Pydantic Settings
  - Reads from `../.env` (parent directory relative to backend/)
  - Required vars: `POSTGRES_*`, `FIRST_SUPERUSER`, `SECRET_KEY`, `PROJECT_NAME`
  - Computed properties: `SQLALCHEMY_DATABASE_URI`, `all_cors_origins`, `emails_enabled`
  - Environment modes: `local`, `staging`, `production`

- **Private routes** (`app/api/routes/private.py`) only load when `ENVIRONMENT=local`

## Database Migrations

- **Alembic** for migrations (config: `alembic.ini`, scripts: `app/alembic/versions/`)
- Migration workflow:
  1. Modify models in `app/models.py`
  2. Generate: `alembic revision --autogenerate -m "description"`
  3. Review generated migration in `app/alembic/versions/`
  4. Apply: `alembic upgrade head`
  
- **Important**: Always include `max_length` on String/VARCHAR fields (see migration `9c0a54914c78`)
- Cascade deletes must be set on both model relationships AND database foreign keys

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
- **sqlmodel**: ORM (combines SQLAlchemy + Pydantic)
- **psycopg[binary]**: PostgreSQL adapter (v3.x, async-capable)
- **alembic**: Database migrations
- **pyjwt**: JWT token handling
- **emails**: Email sending (SMTP) with Jinja2 templates in `app/email-templates/`
- **uvicorn**: ASGI server (without httptools due to compatibility)

## Common Tasks

### Adding a New Model
1. Add model classes to `app/models.py` (Base, Create, Update, Public, DB table)
2. Import in `app/alembic/env.py` to ensure migration detection
3. Generate migration: `alembic revision --autogenerate -m "add_model_name"`
4. Add CRUD functions to `app/crud.py` if needed
5. Create routes in `app/api/routes/model_name.py`
6. Register router in `app/api/main.py`

### Adding an Endpoint
- Follow dependency injection pattern (see `app/api/routes/items.py`)
- Use type-annotated dependencies: `SessionDep`, `CurrentUser`
- Return Pydantic models (e.g., `ItemPublic`, `ItemsPublic`)
- Apply authorization checks (superuser vs. owner)

### Email Configuration
- Templates: MJML sources in `app/email-templates/src/`, compiled HTML in `build/`
- Uses Jinja2 for variable substitution
- Email functions in `app/utils.py`: `send_email()`, `generate_*_email()`
- Emails only work when `SMTP_HOST` and `EMAILS_FROM_EMAIL` are configured

## Testing Patterns

- Fixtures in `tests/conftest.py`: `db`, `client`, `superuser_token_headers`, `normal_user_token_headers`
- Test utilities: `tests/utils/user.py` for authentication helpers
- Session-scoped DB with cleanup after all tests
- Use `TestClient` from FastAPI for endpoint testing

## Sentry Integration

- Enabled when `SENTRY_DSN` set and `ENVIRONMENT != "local"`
- Configured in `app/main.py` with tracing enabled
