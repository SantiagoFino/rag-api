import os
import json
import logging
import mysql.connector
from mysql.connector import pooling
from typing import Dict, Any, List, Optional
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
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="db_pool",
                pool_size=5,
                **db_config
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {str(e)}")
            raise

    def get_connection(self):
        """
        Get a connection from the pool
        """
        try:
            return self.connection_pool.get_connection()
        except Exception as e:
            logger.error(f"Error getting database connection: {str(e)}")
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

        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

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

        except Exception as e:
            logger.error(f"Error updating document {document_id} embedding: {str(e)}")
            if connection:
                connection.rollback()
            return False

        finally:
            if connection:
                connection.close()

    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Gets a document from the database

        Args:
            document_id: The ID of the document

        Returns:
            The document as a dictionary, or None if not found
        """
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)

            query = """
            SELECT id, name, text, embedding, account_id
            FROM documents
            WHERE id = %s
            """

            cursor.execute(query, (document_id,))
            document = cursor.fetchone()

            if not document:
                logger.warning(f"Document {document_id} not found in the database")
                return None

            if document.get('embedding'):
                try:
                    document['embedding'] = json.loads(document['embedding'])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse embedding for document {document_id}")
                    document['embedding'] = None

            return document

        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            return None

        finally:
            if connection:
                connection.close()


def get_db_connector():
    """Get the singleton instance of DatabaseConnector"""
    return DatabaseConnector.get_instance()
