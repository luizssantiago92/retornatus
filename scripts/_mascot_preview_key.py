"""Preview only: remove near-white/near-black plate. Do NOT boost glow."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path(
    r"C:\Users\c.barbosa.CELLAIRIS\.cursor\projects"
    r"\c-Users-c-barbosa-CELLAIRIS-Downloads-Luiz-Projetos-retornatus"
    r"\assets\seedcore-preview-v3.png"
)
REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ".assets/preview/seedcore-preview-v3-alpha.png"
# also key the original d903278 if present (cleaner baseline)
SRC_OLD = REPO / ".assets/preview/seedcore-from-d903278.png"
OUT_OLD = REPO / ".assets/preview/seedcore-d903278-alpha.png"


def key_plate(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im).copy()
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3].astype(np.int16)
    bright = (r.astype(np.int16) + g.astype(np.int16) + b.astype(np.int16)) / 3.0
    hard_w = (r > 248) & (g > 248) & (b > 248)
    soft_w = (r > 235) & (g > 235) & (b > 235) & ~hard_w
    hard_k = (r < 8) & (g < 8) & (b < 8) & (bright < 10)
    soft_k = (r < 22) & (g < 22) & (b < 22) & ~hard_k
    a = a.copy()
    a[hard_w | hard_k] = 0
    a[soft_w] = np.clip((255 - bright[soft_w]) * 14, 0, 255).astype(np.int16)
    a[soft_k] = np.clip(bright[soft_k] * 14, 0, 255).astype(np.int16)
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = key_plate(SRC)
    out.save(OUT, "PNG", optimize=True)
    print("preview", OUT, out.mode, out.size, "corner", out.getpixel((5, 5)))
    if SRC_OLD.exists() and SRC_OLD.stat().st_size > 1000:
        try:
            old = key_plate(SRC_OLD)
            old.save(OUT_OLD, "PNG", optimize=True)
            print("old", OUT_OLD, old.mode, old.size, "corner", old.getpixel((5, 5)))
        except Exception as exc:  # noqa: BLE001
            print("old skip", exc)


if __name__ == "__main__":
    main()
