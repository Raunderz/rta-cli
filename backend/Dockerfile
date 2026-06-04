FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY . .

FROM python:3.12-slim

RUN useradd --create-home app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 7860

CMD ["uvicorn", "rta_backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
