FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY src ./src
COPY static ./static

RUN uv pip install --system .

RUN mkdir -p /app/data

EXPOSE 8088

CMD ["uvicorn", "sql_analyst.main:app", "--host", "0.0.0.0", "--port", "8088"]