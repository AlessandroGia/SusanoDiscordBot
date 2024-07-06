FROM python:3.12-slim-bullseye

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry install --without dev

COPY src /app/src
COPY .env /app/.env

CMD ["poetry", "run", "python", "src/main.py"]