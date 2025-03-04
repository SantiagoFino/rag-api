FROM ubuntu:latest
LABEL authors="sfinov"

FROM python:3.12.9-bookworm

WORKDIR /app

RUN pip install pipenv


COPY Pipfile Pipfile.lock ./


RUN pipenv install --deploy --system


COPY . .


CMD ["python", "main.py"]