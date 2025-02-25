import aiohttp
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OllamaService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the Ollama service configuration"""
        logger.info("Initializing Ollama Service")

        # Get configuration from environment variables with defaults
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3:8b")

        # System prompt for RAG
        self.system_prompt = """You are a helpful assistant that answers questions based on the provided documents. 
        If the answer cannot be determined from the context, say so instead of making up information."""

        logger.info(f"Ollama service configured with model: {self.model_name}")

    async def generate_response(self, conversation_history: List[Dict[str, str]], document_context: List[str],
            temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate a response using Ollama API"""
        try:
            messages = self._format_messages(conversation_history, document_context)

            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            # Log the request (for debugging)
            logger.debug(f"Sending request to Ollama: {self.ollama_base_url}/api/chat")

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_base_url}/api/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.exception(f"Ollama API error: {response.status}, {error_text}")
                        return "I'm sorry, I encountered an error while processing your request."

        except Exception as e:
            logger.exception(f"Error generating response with Ollama: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."

    def _format_messages(self, conversation_history: List[Dict[str, str]], document_context: List[str]) -> List[
        Dict[str, str]]:
        """Format messages for the Ollama API"""
        # Create context string from document chunks
        context_text = "\n\n".join(document_context)

        # Start with system message including context
        messages = [{
            "role": "system",
            "content": f"{self.system_prompt}\n\nDocument Context:\n{context_text}"
        }]

        # Add conversation history
        for message in conversation_history:
            # Skip system messages as we've already set our system message
            if message["role"] != "system":
                messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })

        return messages


def get_ollama_service():
    return OllamaService.get_instance()