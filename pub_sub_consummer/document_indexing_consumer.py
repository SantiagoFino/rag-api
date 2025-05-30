from typing import Dict, Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from db.connector import get_db_connector
from pub_sub_consummer.pub_sub_consumer import PubSubConsumer
from vector_store.chunking import chunk_text


class DocumentIndexingConsumer(PubSubConsumer):
    """
    Consumer for the document indexing queue.
    Processes documents, generates embeddings, and updates the database.
    """
    __subscription_id__ = "DocumentIndexing-sub"

    def __init__(self):
        """Initialize the consumer with the embedding model and database connector"""
        super().__init__()
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.db = get_db_connector()
        self.logger.info("Document indexing consumer initialized")

    async def callback(self, message: Dict[str, Any]):
        """
        Process a document indexing message

        Parameters:
            message: A dictionary containing 'document_id' and 'document_text'
        """
        try:
            document_id = message.get("document_id")
            document_text = message.get("document_text")

            if not document_id:
                self.logger.error("Invalid message: missing document_id")
                return

            if not document_text:
                self.logger.error(f"Invalid message for document {document_id}: missing document_text")
                return

            self.logger.info(f"Processing document {document_id} with {len(document_text)} characters")

            embedding = self._generate_document_embedding(document_text)

            if embedding is not None:
                success = self.db.update_document_embedding(document_id, embedding)

                if success:
                    self.logger.info(f"Successfully indexed document {document_id}")
                else:
                    self.logger.error(f"Failed to update document {document_id} in the database")

        except Exception as e:
            self.logger.exception(f"Error processing document {message.get('document_id', 'unknown')}: {str(e)}")

    def _generate_document_embedding(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> Optional[
        np.ndarray]:
        """
        Generate a document embedding by chunking the text and averaging chunk embeddings.

        Args:
            text: The document text
            chunk_size: The target size for each chunk
            chunk_overlap: The number of characters to overlap between chunks

        Returns:
            The document embedding as a numpy array, or None if an error occurs
        """
        try:
            chunks = chunk_text(text, chunk_size, chunk_overlap)

            if not chunks:
                self.logger.warning("No chunks generated from document text")
                # If no chunks, just encode the first 512 characters
                chunks = [text[:512]]

            embeddings = self.model.encode(chunks, show_progress_bar=False)
            avg_embedding = np.mean(embeddings, axis=0)

            norm = np.linalg.norm(avg_embedding)
            if norm > 0:
                avg_embedding = avg_embedding / norm

            self.logger.info(f"Generated embedding from {len(chunks)} chunks")
            return avg_embedding

        except Exception as e:
            self.logger.error(f"Error generating document embedding: {str(e)}")
            return None
