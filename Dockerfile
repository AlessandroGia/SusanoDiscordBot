FROM python:3.12-slim-bullseye

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml /app/


RUN poetry install --without dev

COPY src ./src
COPY main.py .
COPY config.py .
COPY .env .

CMD ["poetry", "run", "python", "-u", "main.py"]