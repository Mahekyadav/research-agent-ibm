FROM python:3.11-slim

LABEL maintainer="ResearchMind Agent"
LABEL description="IBM WatsonX-powered Intelligent Research Companion"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY main.py .
COPY langflow/ ./langflow/

RUN mkdir -p data/documents data/vector_store data/processed static

# Copy built frontend if it exists (optional — built via docker-compose profile)
COPY static/ ./static/ 2>/dev/null || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
