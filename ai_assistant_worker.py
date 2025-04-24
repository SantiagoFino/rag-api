import logging

from pub_sub_consummer.ai_assistant_consumer import AiAssistantConsumer

if __name__ == "__main__":
    ai_assistant = AiAssistantConsumer()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ai_assistant.consume()