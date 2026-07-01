"""
Builds and caches the CLIP embedding index for images in data/images/.

Embeddings and thumbnails are computed once per image and cached to disk
(data/embeddings.npz + data/thumbs/), so subsequent app restarts load
instantly instead of re-running the model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "data" / "images"
THUMBS_DIR = BASE_DIR / "data" / "thumbs"
EMBEDDINGS_PATH = BASE_DIR / "data" / "embeddings.npz"
THUMB_SIZE = (320, 320)
MODEL_NAME = "clip-ViT-B-32"
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class ImageIndex:
    model: SentenceTransformer
    filenames: list[str]
    vectors: np.ndarray  # shape (n, dim), L2-normalized

    def vector_for(self, filename: str) -> np.ndarray:
        i = self.filenames.index(filename)
        return self.vectors[i]


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=-1, keepdims=True)
    norms[norms == 0] = 1
    return vecs / norms


def _ensure_thumbnail(src: Path) -> None:
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMBS_DIR / src.name
    if dest.exists():
        return
    with Image.open(src) as img:
        img = img.convert("RGB")
        img.thumbnail(THUMB_SIZE)
        img.save(dest, "JPEG", quality=82)


def build_or_load_index() -> ImageIndex:
    print(f"[indexer] loading CLIP model '{MODEL_NAME}' ...")
    model = SentenceTransformer(MODEL_NAME)

    image_paths = sorted(
        p for p in IMAGES_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTS
    )
    filenames = [p.name for p in image_paths]

    cached_filenames: list[str] = []
    cached_vectors = np.zeros((0, 0), dtype=np.float32)
    if EMBEDDINGS_PATH.exists():
        cache = np.load(EMBEDDINGS_PATH, allow_pickle=True)
        cached_filenames = list(cache["filenames"])
        cached_vectors = cache["vectors"]

    cached_lookup = dict(zip(cached_filenames, cached_vectors))
    new_paths = [p for p in image_paths if p.name not in cached_lookup]

    if new_paths:
        print(f"[indexer] embedding {len(new_paths)} new image(s) ...")
        pil_images = []
        for p in new_paths:
            _ensure_thumbnail(p)
            pil_images.append(Image.open(p).convert("RGB"))
        new_vectors = model.encode(pil_images, convert_to_numpy=True, show_progress_bar=False)
        new_vectors = _normalize(new_vectors)
        for p, vec in zip(new_paths, new_vectors):
            cached_lookup[p.name] = vec
    else:
        # still make sure thumbnails exist even if embeddings were already cached
        for p in image_paths:
            _ensure_thumbnail(p)

    vectors = np.stack([cached_lookup[name] for name in filenames]) if filenames else np.zeros((0, 512))
    np.savez(
        EMBEDDINGS_PATH,
        filenames=np.array(filenames, dtype=object),
        vectors=vectors.astype(np.float32),
    )

    print(f"[indexer] index ready: {len(filenames)} image(s).")
    return ImageIndex(model=model, filenames=filenames, vectors=vectors.astype(np.float32))
