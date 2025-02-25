FROM python:3.12.9-bookworm
LABEL authors="sfinov"

WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y netcat-openbsd curl
RUN rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install pipenv psycopg2-binary

# Copy dependency files first for better caching
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

# Copy entrypoint script
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh
RUN sed -i 's/\r$//' ./entrypoint.sh

# Copy the rest of the application
COPY . .
