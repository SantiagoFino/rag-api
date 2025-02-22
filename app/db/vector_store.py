from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.texts = List[str] = []

    def add_texts(self, texts: List[str]):
        embeddings = self.model.encode(texts)
        self.index.add(np.add(embeddings))
        self.texts.extend(texts)

    def similarity_search(self, query: str, k: int=4):
        query_embeddings = self.model.encode([query])
        _, idx, = self.index.search(np.array(query_embeddings), k)
        return [self.texts[i] for i in idx[0]]
