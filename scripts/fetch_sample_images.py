"""
One-time helper to populate data/images/ with a diverse sample set for the demo.

Uses Lorem Picsum (https://picsum.photos), which serves real Unsplash photos at
stable `picsum.photos/id/{id}/{w}/{h}` URLs -- no API key required. A spread of
IDs is used to get a visually/semantically varied set (people, animals, nature,
food, architecture, objects, etc.) for a meaningful semantic search demo.

Usage: python scripts/fetch_sample_images.py
"""

import sys
from pathlib import Path

import requests

IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "images"
WIDTH, HEIGHT = 640, 480

# A spread of Picsum photo IDs, chosen to get varied subject matter.
PHOTO_IDS = [
    10, 15, 20, 24, 28, 33, 37, 40, 42, 48,
    54, 58, 62, 65, 69, 76, 82, 88, 91, 96,
    103, 110, 119, 128, 137, 145, 152, 160, 168, 177,
    184, 193, 201, 209, 217, 225, 233, 241, 249, 257,
]


def fetch_image(photo_id: int) -> bool:
    dest = IMAGES_DIR / f"picsum_{photo_id}.jpg"
    if dest.exists():
        return True
    url = f"https://picsum.photos/id/{photo_id}/{WIDTH}/{HEIGHT}.jpg"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except requests.RequestException as exc:
        print(f"  ! failed to fetch id={photo_id}: {exc}", file=sys.stderr)
        return False


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fetching {len(PHOTO_IDS)} sample images into {IMAGES_DIR} ...")
    ok = 0
    for photo_id in PHOTO_IDS:
        if fetch_image(photo_id):
            ok += 1
            print(f"  ok  id={photo_id}")
    print(f"Done: {ok}/{len(PHOTO_IDS)} images available.")


if __name__ == "__main__":
    main()
