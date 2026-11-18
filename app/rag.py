"""Mini-RAG: chunk pages, embed, keep only the chunks most relevant to the sub-task."""
import numpy as np
from .llm import client
from .config import EMBED_MODEL


def chunk(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out


def embed(texts: list[str]) -> np.ndarray:
    vecs = []
    for i in range(0, len(texts), 256):
        r = client.embeddings.create(model=EMBED_MODEL, input=texts[i : i + 256])
        vecs += [d.embedding for d in r.data]
    m = np.array(vecs, dtype=np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def select(query: str, docs: list[str], k: int = 4) -> list[list[str]]:
    """For each doc, return its top-k chunks by cosine similarity to the query."""
    chunks, owner = [], []
    for i, d in enumerate(docs):
        for c in chunk(d):
            chunks.append(c)
            owner.append(i)
    if not chunks:
        return [[] for _ in docs]
    vecs = embed([query] + chunks)
    sims = vecs[1:] @ vecs[0]
    out = []
    for i in range(len(docs)):
        idx = sorted((j for j, o in enumerate(owner) if o == i), key=lambda j: -sims[j])
        out.append([chunks[j] for j in idx[:k]])
    return out
