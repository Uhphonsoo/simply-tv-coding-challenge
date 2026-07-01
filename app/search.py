"""
Search implementations that operate on an already-built ImageIndex.

Three methods are exposed, all returning a ranked list of
(filename, score) tuples:

- semantic_search: natural-language text -> images, via CLIP text encoder
- similar_search:  image -> images, reusing a cached image embedding as the query
- filename_search: plain substring match on filenames (fast literal fallback)
"""

from __future__ import annotations

import numpy as np

from app.indexer import ImageIndex


def _rank(index: ImageIndex, query_vec: np.ndarray, k: int, exclude: str | None = None):
    if len(index.filenames) == 0:
        return []
    query_vec = query_vec / (np.linalg.norm(query_vec) or 1)
    scores = index.vectors @ query_vec
    order = np.argsort(-scores)
    results = []
    for i in order:
        name = index.filenames[i]
        if name == exclude:
            continue
        results.append({"filename": name, "score": float(scores[i])})
        if len(results) >= k:
            break
    return results


def semantic_search(index: ImageIndex, query: str, k: int = 24):
    query_vec = index.model.encode([query], convert_to_numpy=True)[0]
    return _rank(index, query_vec, k)


def similar_search(index: ImageIndex, filename: str, k: int = 24):
    query_vec = index.vector_for(filename)
    return _rank(index, query_vec, k, exclude=filename)


def filename_search(index: ImageIndex, query: str, k: int = 24):
    q = query.lower().strip()
    matches = [name for name in index.filenames if q in name.lower()]
    return [{"filename": name, "score": 1.0} for name in matches[:k]]
