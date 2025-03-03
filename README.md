# RAG API Service

A Retrieval-Augmented Generation (RAG) API service that consumes RabbitMQ messages for document indexing and question answering.

## Overview

This service consists of two main components:

1. **Document Indexing Consumer**: Processes documents sent via RabbitMQ, generates embeddings using sentence-transformers, and stores them in a MySQL database.

2. **AI Assistant Consumer**: Processes chat messages, retrieves relevant documents based on the query, and generates responses using a local LLM (Ollama).

## Requirements

- Python 3.10+
- RabbitMQ server
- MySQL database
- Ollama (for the LLM)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rag-api
   ```

2. **Create a virtual environment**:
   ```bash
   pip install pipenv
   ```

3. **Install dependencies**:
   ```bash
   pipenv shell
   ```

4 **Pull the Ollama model**:
   ```bash
   ollama pull phi
   ```

## Running the Service

### Using Python directly

```bash
python main.py
```

### Using Docker Compose

```bash
docker-compose up -d
```

This will start:
- The RAG API service
- Ollama with the phi model

## Message Formats

### Document Indexing

```json
{
  "document_id": 123,
  "document_text": "Document content goes here...",
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

### AI Assistant Message

```json
{
  "messages": [
    {
      "id": "msg0",
      "timestamp": "2023-01-01T12:00:00Z",
      "sender": "user",
      "text": "Hello, can you help me with something?"
    },
    {
      "id": "msg1",
      "timestamp": "2023-01-01T12:01:00Z",
      "sender": "assistant",
      "text": "Of course! What can I help you with?"
    },
    {
      "id": "msg2",
      "timestamp": "2023-01-01T12:02:00Z",
      "sender": "user",
      "text": "Tell me about document X."
    }
  ]
}
```

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ Go API      │─────────▶ RabbitMQ    │─────────▶ RAG API     │
│             │         │ Queue       │         │ (Python)    │
└─────────────┘         └─────────────┘         └──────┬──────┘
      ▲                                                 │
      │                                                 │
      │                                                 ▼
┌─────┴─────────────────────────────────┐     ┌─────────────────┐
│ MySQL Database                        │◀────│ Ollama LLM      │
└───────────────────────────────────────┘     └─────────────────┘
```

## Models

By default, the service uses:
- **Embeddings**: SentenceTransformers "all-MiniLM-L6-v2" (384-dimensional)
- **LLM**: Ollama with phi model 

## License

[MIT License](LICENSE)

