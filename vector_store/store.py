from typing import List, Dict, Any, Optional, Union
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging
from pathlib import Path
import pickle

from vector_store.chunking import chunk_document

logger = logging.getLogger(__name__)


class VectorStore:
    """
    A vector store for document embedding and retrieval using FAISS.
    Implements the Singleton pattern to ensure only one instance is used.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of VectorStore"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the vector store with model and index"""
        logger.info("Initializing VectorStore")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks: List[Dict[str, Any]] = []
        self.document_chunks: Dict[str, List[str]] = {}  # document_id -> list of chunk_ids
        self.document_count = 0
        self.chunk_count = 0
        self.data_dir = Path("data/vector_store")
        self.initialize_storage()

    def initialize_storage(self):
        """Initialize storage directories"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def add_document(self, document_id: Union[str, int], document_text: str,
                     chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Add a document to the vector store by chunking it and generating embeddings.

        Parameters:
            document_id: Unique identifier for the document
            document_text: The text content of the document
            chunk_size: The target size for each chunk
            chunk_overlap: The number of characters to overlap between chunks

        Returns:
            List of chunk IDs created
        """
        document_id = str(document_id)

        # chunks the document
        document = {'document_id': document_id, 'document_text': document_text}
        chunks = chunk_document(document, chunk_size, chunk_overlap)

        if not chunks:
            logger.warning(f"No chunks created for document {document_id}")
            return []

        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)

            faiss.normalize_L2(embeddings)
            self.index.add(np.array(embeddings).astype('float32'))

            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = chunk['chunk_id']
                chunk_ids.append(chunk_id)

                # Add global index reference
                chunk['index'] = self.chunk_count + i

                # Store chunk
                self.chunks.append(chunk)

            # Update document mapping
            self.document_chunks[document_id] = chunk_ids

            # Update counts
            self.document_count += 1
            self.chunk_count += len(chunks)

            logger.info(f"Added document {document_id} with {len(chunks)} chunks")
            self.save()

            return chunk_ids

        except Exception as e:
            logger.error(f"Error generating embeddings for document {document_id}: {str(e)}")
            return []

    def similarity_search(self, query: str, k: int = 4, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for chunks similar to the query.

        Parameters:
            query: The search query
            k: Number of results to return
            document_id: Optional filter to search only within a specific document

        Returns:
            List of chunk dictionaries with similarity metadata
        """
        if self.chunk_count == 0:
            logger.warning("Vector store is empty - no results for similarity search")
            return []

        try:
            query_embedding = self.model.encode([query], show_progress_bar=False)
            faiss.normalize_L2(query_embedding)

            # searches in the index
            distances, indices = self.index.search(np.array(query_embedding).astype('float32'),
                                                   k=min(k * 2, self.chunk_count))

            results = []
            seen_documents = set()

            for idx in indices[0]:
                if len(results) >= k:
                    break

                if idx < 0 or idx >= len(self.chunks):
                    continue

                chunk = self.chunks[idx]

                if document_id and chunk['document_id'] != document_id:
                    continue

                # maximum 2 chunks per doc
                if chunk['document_id'] in seen_documents and len(seen_documents) >= 2:
                    continue

                seen_documents.add(chunk['document_id'])

                distance = distances[0][list(indices[0]).index(idx)]
                similarity_score = 1.0 - (distance / 2.0)  # converts L2 distance to similarity score

                # Create result with metadata
                result = chunk.copy()
                result['similarity'] = max(0.0, min(1.0, similarity_score))

                results.append(result)

            logger.info(f"Found {len(results)} chunks similar to query")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def save(self):
        """Save the vector store index and metadata to disk"""
        try:
            index_path = self.data_dir / "faiss_index.bin"
            faiss.write_index(self.index, str(index_path))

            # Save chunks metadata
            chunks_path = self.data_dir / "chunks.pkl"
            with open(chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)

            docs_path = self.data_dir / "documents.json"
            with open(docs_path, 'w') as f:
                json.dump(self.document_chunks, f)

            logger.info(f"Saved vector store with {self.document_count} documents and {self.chunk_count} chunks")
            return True

        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            return False

    def load(self):
        """Load the vector store index and metadata from disk"""
        index_path = self.data_dir / "faiss_index.bin"
        chunks_path = self.data_dir / "chunks.pkl"
        docs_path = self.data_dir / "documents.json"

        if not index_path.exists() or not chunks_path.exists() or not docs_path.exists():
            logger.info("No existing vector store found - starting with empty store")
            return False

        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))

            # Load chunks metadata
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)

            # Load document mapping
            with open(docs_path, 'r') as f:
                self.document_chunks = json.load(f)

            # Update counts
            self.document_count = len(self.document_chunks)
            self.chunk_count = len(self.chunks)

            logger.info(f"Loaded vector store with {self.document_count} documents and {self.chunk_count} chunks")
            return True

        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            # Reset to empty store
            self.index = faiss.IndexFlatL2(self.dimension)
            self.chunks = []
            self.document_chunks = {}
            self.document_count = 0
            self.chunk_count = 0
            return False


def get_vector_store():
    """Get the singleton instance of VectorStore"""
    return VectorStore.get_instance()