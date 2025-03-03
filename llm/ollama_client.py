import os
import logging
import aiohttp
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama API . Implements the Singleton pattern.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of OllamaClient"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the Ollama client"""
        logger.info("Initializing Ollama Client")
        self.api_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api')
        self.model = os.getenv('OLLAMA_MODEL', 'phi')  # Default to phi-2 model
        self.temperature = float(os.getenv('OLLAMA_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('OLLAMA_MAX_TOKENS', '2048'))

        logger.info(f"Ollama client configured with model: {self.model}")

    async def generate_response(self, messages: List[Dict[str, str]], context: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.

        Parameters:
            messages: List of message dictionaries with 'role' and 'content' keys
            context: Optional, context from document retrieval

        Returns:
            The generated response text
        """
        try:
            system_prompt = "You are a helpful assistant."
            if context:
                system_prompt = f"""You are a helpful assistant answering questions based  on the following context: 
                    {context}

                    Answer the question based only on the information in the context. If you don't know the answer, 
                    say so."""

            ollama_messages = [{"role": "system", "content": system_prompt}]

            # Add user messages
            for msg in messages:
                role = "assistant" if msg.get("sender") == "assistant" else "user"
                ollama_messages.append({
                    "role": role,
                    "content": msg.get("text", "")
                })

            # ollama request
            data = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }

            # Make request to Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base}/chat", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return "I'm sorry, I'm having trouble processing your request right now."

                    result = await response.json()
                    return result.get("message", {}).get("content", "")

        except Exception as e:
            logger.exception(f"Error generating response from Ollama: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."


def get_llm_client():
    """Get the singleton instance of OllamaClient"""
    return OllamaClient.get_instance()