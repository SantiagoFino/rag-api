import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from rabbitmq.consumers.document_indexing import DocumentIndexingConsumer
from rabbitmq.consumers.ai_assistant import AIAssistantConsumer

logger = logging.getLogger(__name__)


def start_document_indexing():
    consumer = DocumentIndexingConsumer()
    consumer.consume()


def start_ai_assistant():
    consumer = AIAssistantConsumer()
    consumer.consume()


if __name__ == "__main__":
    logger.info("Starting RAG API service")

    # Use process pool to run consumers in separate processes
    with ProcessPoolExecutor(max_workers=2) as executor:
        executor.submit(start_document_indexing)
        executor.submit(start_ai_assistant)