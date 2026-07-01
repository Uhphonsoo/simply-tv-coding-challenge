"""
FastAPI app: serves the search API, the image/thumbnail files, and the
static frontend, all from a single process (`uvicorn app.main:app`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.indexer import BASE_DIR, IMAGES_DIR, THUMBS_DIR, build_or_load_index
from app.search import filename_search, semantic_search, similar_search

STATIC_DIR = BASE_DIR / "static"

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["index"] = build_or_load_index()
    yield


app = FastAPI(title="Image Semantic Search", lifespan=lifespan)


def _results_payload(results: list[dict]) -> list[dict]:
    return [
        {
            "filename": r["filename"],
            "score": r.get("score"),
            "thumb_url": f"/thumbs/{r['filename']}",
            "image_url": f"/images/{r['filename']}",
        }
        for r in results
    ]


@app.get("/api/images")
def list_images():
    index = _state["index"]
    return _results_payload([{"filename": name} for name in index.filenames])


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, max_length=500),
    method: Literal["semantic", "filename"] = "semantic",
    k: int = Query(48, ge=1, le=200),
):
    index = _state["index"]
    if method == "filename":
        results = filename_search(index, q, k)
    else:
        results = semantic_search(index, q, k)
    return _results_payload(results)


@app.get("/api/similar/{filename}")
def similar(filename: str, k: int = Query(24, ge=1, le=200)):
    index = _state["index"]
    if filename not in index.filenames:
        raise HTTPException(status_code=404, detail="image not found")
    results = similar_search(index, filename, k)
    return _results_payload(results)


# Static file mounts: thumbnails/originals get long-lived cache headers since
# filenames are stable content -- this keeps repeat/gallery loads cheap and fast.
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
app.mount("/thumbs", StaticFiles(directory=THUMBS_DIR), name="thumbs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index_page():
    return FileResponse(STATIC_DIR / "index.html")
