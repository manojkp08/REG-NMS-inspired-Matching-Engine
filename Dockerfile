FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN mkdir -p data/wal data/snapshots

EXPOSE 8000 8080

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.engine.api.rest_server"]