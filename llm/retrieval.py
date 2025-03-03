import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from db.connector import get_db_connector

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """
    Retrieves relevant documents from the database based on query embeddings. Implements the Singleton pattern.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of DocumentRetriever"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the document retriever"""
        logger.info("Initializing Document Retriever")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.db = get_db_connector()
        logger.info("Document retriever initialized")

    async def retrieve_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Parameters:
            query: The search query
            top_k: Number of most relevant documents to retrieve

        Returns:
            List of document dictionaries with text and metadata
        """
        try:
            query_embedding = self.model.encode(query, show_progress_bar=False)
            norm = np.linalg.norm(query_embedding)
            if norm > 0:
                query_embedding = query_embedding / norm

            # Get all documents with embeddings from the database
            documents = self.db.query_documents_by_embedding(query_embedding, top_k)
            return documents

        except Exception as e:
            logger.exception(f"Error retrieving documents: {str(e)}")
            return []

    async def _get_documents_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        Get all documents with embeddings from the database.

        Returns:
            List of document dictionaries
        """
        connection = None
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor(dictionary=True)

            # Get documents with embeddings
            query = """
            SELECT id, name, text, embedding, account_id
            FROM documents
            WHERE embedding IS NOT NULL
            """

            cursor.execute(query)
            documents = cursor.fetchall()

            # Parse embeddings
            for doc in documents:
                if doc.get('embedding'):
                    try:
                        doc['embedding'] = json.loads(doc['embedding'])
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse embedding for document {doc.get('id')}")
                        doc['embedding'] = None

            return documents

        except Exception as e:
            logger.error(f"Error getting documents with embeddings: {str(e)}")
            return []

        finally:
            if connection:
                connection.close()


def get_document_retriever():
    """Get the singleton instance of DocumentRetriever"""
    return DocumentRetriever.get_instance()