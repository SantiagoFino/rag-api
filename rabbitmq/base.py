import asyncio
import json
from abc import ABC, abstractmethod

from aio_pika import IncomingMessage

from rabbitmq.connect import RabbitMqConnection


class MessageConsumer(ABC):
    __consumption_exchange__ = None
    __consumption_queue__ = None
    consumer_connection = RabbitMqConnection()
    MAX_WORKERS = 12

    def __init__(self):
        self.channel = None
        self.semaphore = asyncio.Semaphore(self.MAX_WORKERS)

    @abstractmethod
    async def __call__(self, message: dict):
        return NotImplemented

    def reconnect(self):
        self.channel = self.consumer_connection.get_channel()

    async def on_message(self, message: IncomingMessage):
        async with self.semaphore:
            body = json.loads(message.body)
            print(f" [x] {self.__consumption_exchange__} | Received {body}\n")
            await message.ack()
            await self(body)
            print(f" [x] {self.__consumption_exchange__} | Job finished!\n")

    async def start_consuming(self):
        async with self.consumer_connection:
            self.channel = await self.consumer_connection.get_channel()
            exchange = await self.channel.declare_exchange(name=self.__consumption_exchange__, type="direct",
                                                           durable=True)
            queue = await self.channel.declare_queue(name=self.__consumption_queue__, durable=True)
            await queue.bind(exchange)

            await queue.consume(self.on_message)

            print(f" [*] {self.__consumption_exchange__} | Waiting for messages. To exit press CTRL+C \n")

            await asyncio.Future()

    def consume(self):
        asyncio.run(self.start_consuming())
