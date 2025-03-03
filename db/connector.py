import os
import json
import logging
from psycopg_pool import ConnectionPool
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    A connector for the MySQL database.
    Implements the Singleton pattern.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of DatabaseConnector"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """
        Initialize the database connection pool
        """
        logger.info("Initializing Database Connector")
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'rag_db'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'use_pure': True,
        }

        try:
            self.connection_pool = ConnectionPool(
                f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}",
                min_size=1, max_size=5)
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {str(e)}")
            raise

    def update_document_embedding(self, document_id: int, embedding: np.ndarray) -> bool:
        """
        Update a document's embedding in the database

        Parameters:
            document_id: The ID of the document
            embedding: The embedding vector (numpy array)

        Returns:
            True if successful, False otherwise
        """
        embedding_json = json.dumps(embedding.tolist())

        with self.connection_pool.connection() as connection:
            with connection.cursor() as cursor:
                # Update the document embedding
                update_query = """
                UPDATE documents
                SET embedding = %s
                WHERE id = %s
                """

                cursor.execute(update_query, (embedding_json, document_id))
                connection.commit()

                if cursor.rowcount == 0:
                    logger.warning(f"Document {document_id} not found in the database")
                    return False

                logger.info(f"Updated embedding for document {document_id}")
                return True

    def query_documents_by_embedding(self, query_embedding, top_k=5):
        query = '''
        SELECT id, name, text, embedding, account_id, documents.embedding <=> %s AS distance
        FROM documents
        ORDER BY distance ASC
        LIMIT %s
        '''

        embedding_json = json.dumps(query_embedding.tolist())
        with self.connection_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (embedding_json, top_k))
                raw_docs = cursor.fetchall()
                documents = [{
                    "id": doc[0],
                    "name": doc[1],
                    "text": doc[2],
                    "embedding": doc[3],
                    "account_id": doc[4]
                } for doc in raw_docs]
                return documents


    def add_message_to_chat(self, chat_id: int, message: Dict[str, Any]):
        add_message_query = '''
        UPDATE chats
        SET messages       = messages || %s::jsonb,
            unread_messages= true
        WHERE id = %s
        RETURNING *;
        '''

        with self.connection_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(add_message_query, (json.dumps(message), chat_id))
                connection.commit()



def get_db_connector():
    """Get the singleton instance of DatabaseConnector"""
    return DatabaseConnector.get_instance()
