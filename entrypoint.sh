#!/bin/bash
set -e

# Wait for Ollama service to be ready with a timeout
echo "Waiting for Ollama service..."
TIMEOUT=120
ELAPSED=0
while ! curl -s -f -o /dev/null "http://ollama:11434/api/version"; do
  echo "Ollama not ready yet, waiting..."
  sleep 5
  ELAPSED=$((ELAPSED+5))
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "Timed out waiting for Ollama after ${TIMEOUT} seconds"
    exit 1
  fi
done

echo "Ollama service is up!"

# Pull the model (the model name comes from the environment variable)
MODEL=${OLLAMA_MODEL:-"llama3:8b"}
echo "Pulling model: $MODEL"
curl -X POST "http://ollama:11434/api/pull" -d "{\"name\":\"$MODEL\"}"

echo "Model initialization complete. Starting the application..."

# Wait for database to be ready
echo "Waiting for PostgreSQL database..."
ELAPSED=0
MAX_TIMEOUT=60

# First check if we can reach the database port
while ! nc -z db 5432; do
  echo "Database port not reachable yet, waiting..."
  sleep 2
  ELAPSED=$((ELAPSED+2))
  if [ $ELAPSED -ge $MAX_TIMEOUT ]; then
    echo "Timed out waiting for database port after $MAX_TIMEOUT seconds"
    exit 1
  fi
done

# Now verify database connection with Python
python -c "
import sys
import time
import psycopg2
start_time = time.time()
while True:
    try:
        conn = psycopg2.connect(
            dbname='ragdb',
            user='postgres',
            password='yourpassword',
            host='db',
            port='5432'
        )
        conn.close()
        print('Database connection successful!')
        break
    except psycopg2.OperationalError as e:
        elapsed = time.time() - start_time
        if elapsed > $MAX_TIMEOUT:
            print(f'Failed to connect to database after {$MAX_TIMEOUT} seconds: {e}')
            sys.exit(1)
        print('Database not ready for connections yet, waiting...')
        time.sleep(2)
"

echo "Database is ready!"

# Start your application
# Use exec to ensure signals are properly passed to your application

# Find the correct main file
if [ -f "main.py" ]; then
    echo "Found main.py in root directory"
    MODULE_PATH="main:app"
elif [ -f "app/main.py" ]; then
    echo "Found main.py in app directory"
    MODULE_PATH="app.main:app"
elif [ -f "src/main.py" ]; then
    echo "Found main.py in src directory"
    MODULE_PATH="src.main:app"
else
    echo "Looking for any Python file with 'app' definition..."
    # Find all Python files
    PYTHON_FILES=$(find . -name "*.py" | grep -v "__pycache__" | sort)

    # Look for a file containing an 'app' definition
    for FILE in $PYTHON_FILES; do
        if grep -q "app\s*=" "$FILE"; then
            # Get the module path from the file path
            MODULE_PATH=$(echo "$FILE" | sed 's/^\.\///' | sed 's/\.py$//' | tr '/' '.')
            echo "Found potential app in $FILE, using module path: $MODULE_PATH:app"
            break
        fi
    done

    if [ -z "$MODULE_PATH" ]; then
        echo "Could not find main application file. Please check your project structure."
        echo "Available Python files:"
        echo "$PYTHON_FILES"
        exit 1
    fi
fi

echo "Starting application with module path: $MODULE_PATH"
exec uvicorn "$MODULE_PATH" --host 0.0.0.0 --port 8000
