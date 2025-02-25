from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Created new VectorStore instance")
        return cls._instance

    def __init__(self):
        logger.info("Initializing VectorStore")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts: List[str] = []

    def add_texts(self, content: List[str]):
        if not content:
            logger.warning("Attempted to add empty content to VectorStore")
            return

        try:
            embeddings = self.model.encode(content)
            self.index.add(np.array(embeddings).astype('float32'))
            self.texts.extend(content)
            logger.info(f"Added {len(content)} texts to VectorStore. Total: {len(self.texts)}")
        except Exception as e:
            logger.error(f"Error adding texts to VectorStore: {str(e)}")

    def similarity_search(self, query: str, k: int = 4) -> List[str]:
        if not self.texts:
            logger.warning("VectorStore is empty - no results for similarity search")
            return []

        try:
            query_embeddings = self.model.encode([query])
            distances, indices = self.index.search(np.array(query_embeddings).astype('float32'), k)

            results = []
            for i in indices[0]:
                if 0 <= i < len(self.texts):
                    results.append(self.texts[i])

            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []


def get_vector_store():
    return VectorStore.get_instance()
