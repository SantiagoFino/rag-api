import logging

from pub_sub_consummer.document_indexing_consumer import DocumentIndexingConsumer

if __name__ == "__main__":
    document_indexer = DocumentIndexingConsumer()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    document_indexer.consume()
