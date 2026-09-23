"""Key near-black (or near-white) plate from a mascot PNG; write transparent assets."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SRC = REPO / ".assets/preview/candidates-2026-09/SELECTED-ember.png"
DEFAULT_OUTS = [
    REPO / ".assets/retornatus-mascot.png",
    REPO / ".assets/retornatus-mascot-ember.png",
    REPO / "docs/assets/retornatus-mascot.png",
    REPO / "docs/assets/retornatus-mascot-ember.png",
]


def key_plate(arr: np.ndarray) -> np.ndarray:
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3].astype(np.int16)
    bright = (r.astype(np.int16) + g.astype(np.int16) + b.astype(np.int16)) / 3.0
    hard_w = (r > 248) & (g > 248) & (b > 248)
    soft_w = (r > 235) & (g > 235) & (b > 235) & ~hard_w
    hard_k = (r < 10) & (g < 10) & (b < 10)
    soft_k = (r < 28) & (g < 28) & (b < 28) & ~hard_k
    fringe = (bright < 42) & ~hard_k & (r < 50) & (g < 50) & (b < 50)
    not_body = fringe & ~((g > 80) | (b > 80) | ((r > 120) & (g > 60)))
    a2 = a.copy()
    a2[hard_w | hard_k] = 0
    a2[soft_w] = np.clip((255 - bright[soft_w]) * 14, 0, 255).astype(np.int16)
    a2[soft_k] = np.clip(bright[soft_k] * 14, 0, 255).astype(np.int16)
    a2[not_body] = np.clip(bright[not_body] * 6, 0, a2[not_body]).astype(np.int16)
    out = arr.copy()
    out[..., 3] = np.clip(a2, 0, 255).astype(np.uint8)
    return out


def crop_content(im: Image.Image, pad: int = 28) -> Image.Image:
    arr = np.asarray(im)
    ys, xs = np.where(arr[..., 3] > 8)
    if len(xs) == 0:
        return im
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(arr.shape[0], int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(arr.shape[1], int(xs.max()) + pad + 1)
    return im.crop((x0, y0, x1, y1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, action="append", default=None)
    args = parser.parse_args()
    outs = args.out or DEFAULT_OUTS
    raw = np.asarray(Image.open(args.src).convert("RGBA"))
    keyed = Image.fromarray(key_plate(raw), "RGBA")
    cropped = crop_content(keyed)
    for path in outs:
        path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(path, "PNG", optimize=True)
        print("wrote", path, cropped.size, "corner", cropped.getpixel((3, 3)))


if __name__ == "__main__":
    main()
