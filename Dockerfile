FROM python:3.12.9-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app


COPY . .
RUN uv sync --frozen


CMD ["uv", "run", "my_app"]