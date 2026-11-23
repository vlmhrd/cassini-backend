FROM ghcr.io/astral-sh/uv:0.13.7-python3.12-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
ENV DB_PATH=/data/data.sqlite3 SIGNING_KEY_PATH=/data/keys/signing.key
VOLUME /data
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "cassini_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
