# Multi-stage build for QuizForge (newspec-enabled)

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUIZFORGE_SPEC_MODE=json

WORKDIR /app

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Copy application code
COPY . .

# Default entrypoint: run CLI wrapper
ENTRYPOINT ["python", "run_quizforge.py"]

