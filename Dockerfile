FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app /app/app

# Cloud Run provides PORT env variable, default to 8080 if not set
ENV PORT=8080

# Expose the port (documentation purposes, Cloud Run ignores this)
EXPOSE 8080

ENTRYPOINT ["fastapi", "run", "app/main.py"]
CMD [ "--workers", "4", "--host", "0.0.0.0", "--port", "8080"]