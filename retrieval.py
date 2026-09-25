"""
Retrieval component: TF-IDF + cosine similarity over chunk text.

Why TF-IDF instead of neural embeddings: this environment can't reach
model-hosting endpoints, and TF-IDF is transparent enough to defend in a
review ("here's exactly which terms matched"). Swap in OpenAI/SBERT
embeddings by replacing `Retriever.fit` / `Retriever.query` - the rest of
the eval harness (chunking, scoring) does not need to change.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in chunks])

    def query(self, question, k=3):
        q_vec = self.vectorizer.transform([question])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked_idx = np.argsort(sims)[::-1][:k]
        return [
            {
                "chunk_id": self.chunks[i]["chunk_id"],
                "text": self.chunks[i]["text"],
                "score": float(sims[i]),
            }
            for i in ranked_idx
        ]
