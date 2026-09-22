"""Key near-white/near-black plates; boost crystal + energy glow. Fast numpy path."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

SRC = Path(
    r"C:\Users\c.barbosa.CELLAIRIS\.cursor\projects"
    r"\c-Users-c-barbosa-CELLAIRIS-Downloads-Luiz-Projetos-retornatus"
    r"\assets\seedcore-float-v2.png"
)
REPO = Path(__file__).resolve().parents[1]
OUTS = [
    REPO / "docs/assets/retornatus-mascot-seedcore.png",
    REPO / "docs/assets/retornatus-mascot.png",
    REPO / ".assets/retornatus-mascot.png",
    REPO / ".assets/retornatus-mascot-seedcore.png",
]


def key_background(arr: np.ndarray) -> np.ndarray:
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3].astype(np.int16)
    bright = (r.astype(np.int16) + g.astype(np.int16) + b.astype(np.int16)) / 3
    # near-white plate
    hard_w = (r > 242) & (g > 242) & (b > 242)
    soft_w = (r > 220) & (g > 220) & (b > 220) & ~hard_w
    # near-black plate (some generators bake black)
    hard_k = (r < 12) & (g < 12) & (b < 12)
    soft_k = (r < 28) & (g < 28) & (b < 28) & ~hard_k
    a = a.copy()
    a[hard_w | hard_k] = 0
    a[soft_w] = np.clip((255 - bright[soft_w]) * 12, 0, 255).astype(np.int16)
    a[soft_k] = np.clip(bright[soft_k] * 12, 0, 255).astype(np.int16)
    out = arr.copy()
    out[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return out


def energy_glow(arr: np.ndarray) -> Image.Image:
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    gp = np.zeros_like(arr)
    amber = (r > 175) & (g > 110) & (b < 150) & (r > b + 35) & (a > 15)
    teal = (g > 145) & (b > 145) & (r < 145) & (a > 60)
    gp[amber, 0] = 255
    gp[amber, 1] = np.minimum(255, g[amber].astype(np.int16) + 50)
    gp[amber, 2] = 40
    gp[amber, 3] = np.minimum(200, a[amber] // 2 + 55)
    gp[teal, 0] = 60
    gp[teal, 1] = 255
    gp[teal, 2] = 230
    gp[teal, 3] = np.minimum(160, a[teal] // 3 + 40)
    glow = Image.fromarray(gp, "RGBA").filter(ImageFilter.GaussianBlur(radius=8))
    base = Image.fromarray(arr, "RGBA")
    return Image.alpha_composite(base, glow)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    raw = np.asarray(Image.open(SRC).convert("RGBA"))
    keyed = key_background(raw)
    out = energy_glow(keyed)
    out = ImageEnhance.Contrast(out).enhance(1.1)
    out = ImageEnhance.Brightness(out).enhance(1.05)
    for p in OUTS:
        p.parent.mkdir(parents=True, exist_ok=True)
        out.save(p, "PNG", optimize=True)
        print("wrote", p)
    c = out.getpixel((5, 5))
    print("corner", c, "mode", out.mode, "size", out.size)
    # sample mid for non-zero alpha somewhere
    mid = out.getpixel((out.size[0] // 2, out.size[1] // 2))
    print("center", mid)


if __name__ == "__main__":
    main()
