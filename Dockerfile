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

# uv Cache mode (still useful even without BuildKit mounts)
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
