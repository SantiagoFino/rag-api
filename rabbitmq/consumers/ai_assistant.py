import logging
import json
import time
from typing import Dict, Any, List, Optional

from rabbitmq.base import MessageConsumer
from llm.ollama_client import get_llm_client
from llm.retrieval import get_document_retriever

logger = logging.getLogger(__name__)


class AIAssistantConsumer(MessageConsumer):
    """
    Consumer for the AI assistant queue. Processes messages, retrieves relevant documents, and generates responses.
    """
    __consumption_exchange__ = "ai-assistant-exchange"
    __consumption_queue__ = "ai-assistant-queue"

    def __init__(self):
        """Initialize the consumer with LLM client and document retriever"""
        super().__init__()
        self.llm = get_llm_client()
        self.retriever = get_document_retriever()
        logger.info("AI assistant consumer initialized")

    async def __call__(self, message: Dict[str, Any]):
        """
        Process a message and generate a response.

        Args:
            message: A dictionary containing 'messages' list
        """
        try:
            messages = message.get("messages", [])

            if not messages:
                logger.error("Invalid message: missing or empty messages list")
                return

            # Get the last message (the user's question)
            last_message = messages[-1]
            query_text = last_message.get("text", "")

            if not query_text:
                logger.error("Invalid message: last message has no text")
                return

            logger.info(f"Processing query: {query_text}")

            # Retrieve relevant documents
            relevant_docs = await self.retriever.retrieve_documents(query_text, top_k=3)

            # Prepare context from retrieved documents
            context = self._prepare_context(relevant_docs)

            # Generate response using LLM
            response_text = await self.llm.generate_response(messages, context)

            # Create response message
            response_message = self._create_response_message(response_text)

            # Add response to messages list
            messages.append(response_message)

            # Update message with the new messages with the llm response
            message["messages"] = messages

            logger.info(f"Generated response: {response_text[:100]}...")

        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")

            # Add an error response if possible
            try:
                error_message = self._create_response_message(
                    "I'm sorry, I encountered an error while processing your request."
                )

                if isinstance(message.get("messages"), list):
                    message["messages"].append(error_message)

            except Exception as e:
                logger.exception("Error creating error response")

    def _create_response_message(self, text: str) -> Dict[str, Any]:
        """
        Create a response message dictionary.

        Parameters:
            text: The response text

        Returns:
            A message dictionary
        """
        current_time = time.time()
        return {
            "id": f"msg{current_time}",
            "timestamp": current_time,
            "sender": "assistant",
            "text": text
        }

    def _prepare_context(self, documents: List[Dict[str, Any]]) -> Optional[str]:
        """
        Prepare context from retrieved documents.

        Parameters:
            documents: List of document dictionaries

        Returns:
            Context string or None if no documents
        """
        if not documents:
            return None

        context_parts = []

        for i, doc in enumerate(documents, 1):
            doc_text = doc.get("text", "")

            if not doc_text:
                continue

            # Limit text length to avoid context overload
            if len(doc_text) > 1500:
                doc_text = doc_text[:1500] + "..."

            doc_name = doc.get("name", f"Document {doc.get('id', i)}")
            similarity = doc.get("similarity", 0.0)

            # Add document to context
            context_parts.append(f"--- {doc_name} (Relevance: {similarity:.2f}) ---\n{doc_text}\n")

        if not context_parts:
            return None

        return "\n".join(context_parts)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Start the consumer
    ai_assistant = AIAssistantConsumer()
    ai_assistant.consume()