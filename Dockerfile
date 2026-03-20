# ============================================================
# Stage 1: Build frontend (Vue 3 + Vite)
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /build/webui
COPY webui/package.json webui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY webui/ ./
RUN npm run build

# ============================================================
# Stage 2: Python runtime
# ============================================================
FROM python:3.12-slim AS runtime

LABEL maintainer="taiko-ratingpro"
LABEL description="太鼓达人谱面多维难度评定系统"

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

# api.py resolves WEBUI_DIST via __file__ relative path:
#   Path(__file__).parent.parent.parent / "webui" / "dist"
# With PYTHONPATH=/app/src, __file__ = /app/src/taiko_rating/api.py
# → parent³ = /app → /app/webui/dist ✓
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir numpy flask gunicorn

COPY src/ src/
COPY --from=frontend-build /build/webui/dist webui/dist
COPY examples/ examples/

ENV PYTHONPATH=/app/src

RUN chown -R app:app /app
USER app

EXPOSE 5000

ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:5000 --workers=2 --timeout=120 --access-logfile=- --error-logfile=-"

CMD ["gunicorn", "taiko_rating.api:app"]
