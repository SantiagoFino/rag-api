import logging
import os
import asyncio
import signal
import sys
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv

from rabbitmq.consumers.document_indexing import DocumentIndexingConsumer
from rabbitmq.consumers.ai_assistant import AIAssistantConsumer


load_dotenv()

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


executor = None


def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Received termination signal. Shutting down...")
    if executor:
        executor.shutdown(wait=False)
    sys.exit(0)


def start_document_indexing():
    """Start the document indexing consumer"""
    try:
        logger.info("Starting document indexing consumer")
        consumer = DocumentIndexingConsumer()
        consumer.consume()
    except Exception as e:
        logger.exception(f"Error in document indexing consumer: {str(e)}")


def start_ai_assistant():
    """Start the AI assistant consumer"""
    try:
        logger.info("Starting AI assistant consumer")
        consumer = AIAssistantConsumer()
        consumer.consume()
    except Exception as e:
        logger.exception(f"Error in AI assistant consumer: {str(e)}")


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting RAG API service")

    try:
        executor = ProcessPoolExecutor(max_workers=2)
        executor.submit(start_document_indexing)
        executor.submit(start_ai_assistant)

        logger.info("RAG API service started.")
        while True:
            asyncio.sleep(1)

    except Exception as e:
        logger.exception(f"Error starting RAG API service: {str(e)}")
        if executor:
            executor.shutdown(wait=False)
        sys.exit(1)