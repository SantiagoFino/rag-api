FROM python:3.12.9-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY .python-version .
COPY uv.lock .
COPY pyproject.toml .

RUN uv venv .venv
RUN uv sync --frozen

COPY . .

COPY rag-service-account.json rag-service-account.json


CMD ["uv", "run" , "document_indexing_worker.py"]