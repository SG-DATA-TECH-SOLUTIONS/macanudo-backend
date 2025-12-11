FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

COPY ./scripts /app/scripts

COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/

COPY ./app /app/app
COPY ./tests /app/tests

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
ENV UV_LINK_MODE=copy

# -----------------------------
# 1) Install dependencies (no BuildKit)
# -----------------------------

# Copy only dependency metadata first → better cache reuse
COPY ./pyproject.toml ./uv.lock /app/

# Create cache dir (optional) and install deps without the project
RUN mkdir -p /root/.cache/uv && \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

# -----------------------------
# 2) Copy project files
# -----------------------------
COPY ./scripts /app/scripts
COPY ./alembic.ini /app/
COPY ./app /app/app
COPY ./tests /app/tests

# Sync the project environment (installs your package in editable mode, etc.)
RUN uv sync

# -----------------------------
# 3) Run the app
# -----------------------------
CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
