import os
from types import TracebackType
from typing import Optional, Type
from dotenv import load_dotenv

from aio_pika import connect_robust, RobustConnection

load_dotenv()


class RabbitMqConnection:
    __url = f'{os.getenv("CLOUDAMQP_URL")}?heartbeat=60'

    def __init__(self):
        self.connection: Optional[RobustConnection] = None

    async def __aenter__(self):
        await self.connect()
        await self.connection.__aenter__()

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        await self.connection.__aexit__(exc_type, exc_val, exc_tb)

    async def get_channel(self):
        await self.connect()
        channel = await self.connection.channel()
        return channel

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await connect_robust(self.__url)
