FROM python:3.12.9-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY .python-version .
COPY uv.lock .
COPY pyproject.toml .

RUN uv venv .venv
RUN uv sync --frozen

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . .

COPY rag-service-account.json rag-service-account.json


CMD ["uv", "run", "ai_assistant_worker.py"]
