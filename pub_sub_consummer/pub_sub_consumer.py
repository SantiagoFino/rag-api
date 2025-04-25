import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

load_dotenv()


class PubSubConsumer(ABC):
    __subscription_id__ = None

    def __init__(self):
        self.subscription_id = self.__subscription_id__
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.subscriber = pubsub_v1.SubscriberClient()
        self.logger = logging.getLogger(__name__)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.subscription_path = self.subscriber.subscription_path(
            self.project_id, self.subscription_id
        )

    @abstractmethod
    async def callback(self, message: dict):
        return NotImplemented

    def wrapped_callback(self, message: Message):
        self.logger.info(f" [x] {self.subscription_id} | Received {message.data}\n")
        try:
            body = json.loads(message.data)
            asyncio.run_coroutine_threadsafe(self.callback(body), self.loop)
            message.ack()
        except Exception as e:
            self.logger.exception(f"Error in callback: {str(e)}")
            message.nack()

    def consume(self):
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.wrapped_callback,
        )

        self.logger.info(f"Listening for messages on {self.subscription_id}...\n")

        try:
            self.loop.run_forever()
        except Exception as e:
            self.logger.exception(f"Error: {e}")
        finally:
            streaming_pull_future.cancel()
            self.subscriber.close()
