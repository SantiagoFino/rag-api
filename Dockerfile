FROM ubuntu:latest
LABEL authors="sfinov"

FROM python:3.12.9-bookworm

WORKDIR /app

RUN pip install pipenv


COPY Pipfile Pipfile.lock ./


RUN pipenv install --deploy --system


COPY . .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]