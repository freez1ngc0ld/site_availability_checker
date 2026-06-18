FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY . .

CMD ["uv", "run", "python", "-m", "src.main"]