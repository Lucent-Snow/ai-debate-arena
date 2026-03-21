FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY debate ./debate
COPY web ./web
COPY examples ./examples

RUN pip install --no-cache-dir .

ENTRYPOINT ["debate"]
