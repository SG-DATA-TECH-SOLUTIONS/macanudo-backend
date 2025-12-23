# FastAPI Backend - AI Coding Agent Instructions
# FastAPI Backend - Copilot Instructions (condensed)

This backend is a FastAPI service using SQLModel + PostgreSQL. Keep instructions short and concrete for fast agent onboarding.

- **Big picture**: `app/` contains the service: `app/api/` (routes + deps), `app/core/` (config, database, security), `models/` (per-resource SQLModel classes), and `crud.py` (DB helpers). Requests flow: route -> deps (`SessionDep`, `CurrentUser`) -> `crud`/models -> DB.

- **Key files to reference**: `app/api/deps.py` (session & auth DI), `app/core/config.py` (env & URIs), `app/core/security.py` (JWT/password rules), `models/` (resource models), `app/crud.py` (patterns for queries/updates), `app/main.py` (app wiring).

- **Session & model patterns**: Use `SessionDep` injected into routes (do not create sessions directly). Create with `Model.model_validate(..., update=...)`, update with `sqlmodel_update()`, then `session.add()/commit()/refresh()`.

- **Auth**: OAuth2 JWT tokens; `sub` is user id. Use `CurrentUser` dependency. Superuser checks via `get_current_active_superuser` in `app/api/deps.py`.

- **Migrations**: Alembic present under `alembic/`. Edit models in `models/` or `app/models.py` then run `alembic revision --autogenerate -m "msg"` and `alembic upgrade head`. Remember to add `max_length` to String fields when needed (see existing migration 9c0a54914c78).

- **Dev commands (project root)**:
  - Install: `uv sync` then activate venv (`.venv\Scripts\activate` on Windows).
  - Tests: `bash ./scripts/test.sh` (Pytest + fixtures in `tests/conftest.py`).
  - Format/Lint: `bash ./scripts/format.sh` / `bash ./scripts/lint.sh`.
  - Docker dev: `docker compose watch` and `docker compose exec backend bash`.

- **Project conventions**:
  - UUID primary keys across models.
  - No `print()` statements; use `logging` (ruff T201 rule enforced).
  - Keep DB cascade configured on both Relationship and FK.

- **Email templates**: MJML sources at `app/email-templates/src/`; compiled HTML in `app/email-templates/build/`. Email helpers in `app/utils.py`.

- **Testing notes**: Tests use a session-scoped DB fixture. Use `tests/utils/` helpers to create users/items and `superuser_token_headers` fixture for auth.

- **What an agent should do first**:
  1. Read `app/api/deps.py`, `app/core/config.py`, `app/core/security.py` to understand DI and auth.
  2. Run `bash ./scripts/test.sh` to verify baseline test status before edits.
  3. When changing models, update `alembic/env.py` imports if needed and generate a migration.

If any of these files or environment details are outdated or you want additional examples (sample endpoint edit, migration example, or test run), tell me which area to expand. 
item = Item.model_validate(item_in, update={"owner_id": current_user.id})
