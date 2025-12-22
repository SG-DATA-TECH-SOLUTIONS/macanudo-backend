FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Copy requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app /app/app

ENTRYPOINT ["fastapi", "run", "--workers", "4", "app/main.py"]