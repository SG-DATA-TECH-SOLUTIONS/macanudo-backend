FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app /app/app

# Expose the port (documentation purposes, Cloud Run ignores this)
EXPOSE 8080

ENTRYPOINT ["fastapi", "run", "--workers", "4", "--host", "0.0.0.0", "--port", "8080", "app/main.py"]