# Build and run a single-container QuizForge web app (Express API + Vite UI + Python engine)

# 1) Build the web client
FROM node:20-bookworm-slim AS web-builder
WORKDIR /web
COPY web/package*.json ./
RUN npm ci --no-fund --no-audit
COPY web .
RUN npm run build

# 2) Runtime: Node + Python (for the orchestrator)
FROM node:20-bookworm-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUIZFORGE_SPEC_MODE=json \
    NODE_ENV=production \
    PORT=8000 \
    PYTHON_BIN=python3
ARG GIT_SHA=unknown
ARG GIT_REF=unknown
ARG BUILD_TIME=unknown
ENV BUILD_SHA=$GIT_SHA \
    BUILD_REF=$GIT_REF \
    BUILD_TIME=$BUILD_TIME
WORKDIR /app

# Install Python toolchain for the orchestrator
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create venv to avoid Debian PEP 668 protections and install deps there
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node dependencies for the API
COPY server/package*.json server/
RUN npm --prefix server ci --omit=dev --no-fund --no-audit

# Application code
COPY . .
COPY --from=web-builder /web/dist ./server/dist

EXPOSE 8000
CMD ["node", "server/index.js"]

