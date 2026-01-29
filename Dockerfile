FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app /app/app

COPY ./.env /app/.env
COPY ./macanudo-credentials.json /app/macanudo-credentials.json


ENV PORT=8080

# Expose the port (documentation purposes, Cloud Run ignores this)
EXPOSE 8080:8080

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
