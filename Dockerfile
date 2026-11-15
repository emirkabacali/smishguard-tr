# syntax=docker/dockerfile:1

# ---- Stage 1: build a virtual environment with pinned dependencies ----------------------
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Dependencies first: this layer is cached until requirements-lock.txt changes.
COPY requirements-lock.txt .
RUN pip install -r requirements-lock.txt

# Then the package itself (without re-resolving dependencies).
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-deps .

# ---- Stage 2: slim runtime image ---------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SMISHGUARD_ROOT=/app

# Run as an unprivileged user: a compromised process cannot modify the system.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

# The trained model is NOT baked into the image (the training data is licensed for academic
# use only). Mount it at runtime:  -v "$(pwd)/models:/app/models:ro"
RUN mkdir -p /app/models && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

CMD ["uvicorn", "smishguard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
