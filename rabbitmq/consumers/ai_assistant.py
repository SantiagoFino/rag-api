from rabbitmq.base import MessageConsumer


class AIAssistantConsumer(MessageConsumer):
    __consumption_exchange__ = "ai-assistant-exchange"
    __consumption_queue__ = "ai-assistant-queue"
    async def __call__(self, message: dict):
        print(message)



if __name__ == "__main__":
    ai_assistant = AIAssistantConsumer()
    ai_assistant.consume()