#!/bin/bash
set -e

# Wait for Ollama service to be ready
echo "Waiting for Ollama service..."
until curl -s -f -o /dev/null "http://ollama:11434/api/version"; do
  echo "Ollama not ready yet, waiting..."
  sleep 2
done

echo "Ollama service is up!"

# Pull the model (the model name comes from the environment variable)
MODEL=${OLLAMA_MODEL:-"llama3:8b"}
echo "Pulling model: $MODEL"
curl -X POST "http://ollama:11434/api/pull" -d "{\"name\":\"$MODEL\"}"

echo "Model initialization complete. Starting the application..."
