from rabbitmq.base import MessageConsumer


class DocumentIndexingConsumer(MessageConsumer):
    __consumption_exchange__ = "document-indexing-exchange"
    __consumption_queue__ = "document-indexing-queue"
    async def __call__(self, message: dict):
        print(message)



if __name__ == "__main__":
    document_indexer = DocumentIndexingConsumer()
    document_indexer.consume()