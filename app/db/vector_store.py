from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.texts: List[str] = []

    def add_texts(self, content: List[str]):
        embeddings = self.model.encode(content)
        self.index.add(np.array(embeddings))
        self.texts.extend(content)

    def similarity_search(self, query: str, k: int=4):
        query_embeddings = self.model.encode([query])
        _, idx, = self.index.search(np.array(query_embeddings), k)
        return [self.texts[i] for i in idx[0]]
