#!/usr/bin/env python3
"""Turn green-screen animal illustrations into transparent PNGs for the Animais category.

The illustrations come from Kairogen (model z-image-turbo) with a prompt that asks for a flat green background.
Background = green-hued pixels connected to the image border, so the ground shadow under a figure goes too,
while green pixels inside the figure stay. The white sticker outline separates the figure from the background.

Usage:
  build_animal_art.py RAW_DIR OUT_DIR MAPPING.json
  MAPPING.json maps raw file stems to person ids, e.g. {"leao-green": "leao"}; output is OUT_DIR/<id>.png.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUTPUT_SIZE = 512
MARGIN = 0.04  # fraction of the figure size kept around it


def key_out_background(rgb: np.ndarray) -> np.ndarray:
    """Alpha channel (0 = transparent) for an RGB array: green background connected to the border is removed."""
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    greenish = (g > r + 25) & (g > b + 15)
    labels, _ = ndimage.label(greenish)
    border_labels = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, border_labels[border_labels != 0])
    alpha = np.where(background, 0.0, 1.0)
    # soft fringe: pixels next to the background that are only slightly green keep partial opacity
    fringe = ndimage.binary_dilation(background) & ~background
    greenness = np.clip((g - np.maximum(r, b)) / 60.0, 0.0, 1.0)
    alpha = np.where(fringe, 1.0 - greenness, alpha)
    return alpha


def despill(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Remove green tint from semi-transparent edge pixels, so the fringe does not look green."""
    out = rgb.astype(np.int16).copy()
    edge = (alpha > 0) & (alpha < 1)
    limit = np.maximum(out[..., 0], out[..., 2]) + 10
    out[..., 1] = np.where(edge, np.minimum(out[..., 1], limit), out[..., 1])
    return np.clip(out, 0, 255).astype(np.uint8)


def to_transparent_square(source: Path, target: Path) -> None:
    image = Image.open(source).convert("RGB")
    rgb = np.asarray(image)
    alpha = key_out_background(rgb)
    rgb = despill(rgb, alpha)
    rgba = np.dstack([rgb, (alpha * 255).astype(np.uint8)])

    ys, xs = np.where(alpha > 0.05)
    if len(xs) == 0:
        raise SystemExit(f"nenhum pixel do personagem em {source}")
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    side = max(x1 - x0, y1 - y0)
    pad = int(side * MARGIN)
    side += 2 * pad
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    canvas = np.zeros((side, side, 4), dtype=np.uint8)
    left, top = cx - side // 2, cy - side // 2
    sx0, sy0 = max(left, 0), max(top, 0)
    sx1, sy1 = min(left + side, rgba.shape[1]), min(top + side, rgba.shape[0])
    canvas[sy0 - top:sy1 - top, sx0 - left:sx1 - left] = rgba[sy0:sy1, sx0:sx1]

    result = Image.fromarray(canvas, "RGBA").resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.save(target, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("mapping", type=Path)
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    for stem, person_id in mapping.items():
        source = args.raw_dir / f"{stem}.png"
        target = args.out_dir / f"{person_id}.png"
        to_transparent_square(source, target)
        print(f"{person_id}: {target}")


if __name__ == "__main__":
    main()
