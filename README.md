# Macanudo Backend

API REST construida con **FastAPI** y **MongoDB** para gestión de inventario, productos, recetas y ventas.

## Stack Tecnológico

- **FastAPI** - Framework web async
- **MongoDB** + **Motor** - Base de datos y driver async
- **Pydantic** - Validación de datos
- **JWT** - Autenticación con tokens
- **Alembic** - Migraciones (legacy, proyecto migrado a MongoDB)

## Requisitos

- Python 3.11+
- MongoDB 6.0+
- [uv](https://github.com/astral-sh/uv) (recomendado) o pip

## Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd macanudo-backend

# O con pip
pip install -r requirements.txt

# Activar entorno virtual
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

Estructura del proyecto:

```
app/
├── api/
│   ├── deps.py          # Dependencias (SessionDep, CurrentUser)
│   ├── main.py          # Agregador de routers
│   └── routes/          # Endpoints por recurso
├── core/
│   ├── config.py        # Settings (Pydantic)
│   ├── database.py      # Conexión MongoDB
│   └── security.py      # JWT y hashing
├── models/              # Modelos Pydantic por recurso
├── crud.py              # Operaciones de base de datos
├── utils.py             # Helpers (email, etc.)
└── main.py              # Entry point FastAPI
tests/
├── conftest.py          # Fixtures de pytest
├── api/routes/          # Tests de endpoints
└── utils/               # Helpers para tests
```