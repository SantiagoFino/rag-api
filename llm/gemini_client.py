import os
from typing import List, Dict, Optional

import google.generativeai as genai


class GeminiClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.api_key)
        self.gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_ID"))

    @staticmethod
    def to_genai_message(message):
        """Converts a message to a Gemini AI content format."""
        role = "user" if message["sender"] != "assistant" else "model"
        return {"role": role, "parts": [message["text"]]}

    async def generate_response(self, messages: List[Dict[str, str]], context: Optional[str] = None) -> str:
        """Sends a chat session to Gemini AI and retrieves the response."""
        chat_session = self.gemini_model.start_chat()

        # Convert chat history (excluding the last message) to AI format

        ai_messages = [self.to_genai_message(msg) for msg in messages[:-1] if msg["text"]]
        if context:
            context_message = {"role": "user", "parts": [context]} if context else None
            ai_messages += [context_message]

        # Assign the history to the session
        chat_session.history = ai_messages

        # Send the last user message to Gemini
        response = chat_session.send_message(messages[-1]["text"])

        # Extract the first candidate's response
        text = ""
        if response.candidates:
            for candidate in response.candidates[:1]:
                for part in candidate.content.parts:
                    text += part.text  # Direct string since Python handles text differently

        return text
