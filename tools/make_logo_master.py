#!/usr/bin/env python3
"""Turn the owner's "Leo" script logo into the transparent icon master.

The supplied file (``assets/logos/leo-script.original.webp``, 2026-09-27, replacing the
lion) is a cream rounded-square tile on PURE BLACK corners and carries no alpha channel.
Scaled as is, every desktop and taskbar icon would show black corners. This script:

1. finds the background by flood-filling the dark pixels connected to the four corners
   (the tile's corners are a continuous "squircle" curve, not circular arcs, so a
   geometric rounded rectangle does not fit -- the first attempt left a dark fringe);
2. shrinks the tile by ``--inset`` pixels so the black/cream blend at its old edge is cut
   away, and softens the new edge by supersampling;
3. writes an RGBA master. Nothing inside the tile is touched: the black "Leo" strokes are
   not connected to the corners, so the flood fill never reaches them.

Run with a Python that has Pillow, then ``tools/make_lion_icon.py`` to encode the
desktop and web formats (their file names still say "lion" for compatibility).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SUPERSAMPLE = 4


def tile_mask(image: Image.Image, inset: int, threshold: int = 128) -> Image.Image:
    """Opaque where the tile is: everything not dark-and-connected-to-a-corner, shrunk by ``inset``."""
    dark = image.convert("L").point(lambda v: 0 if v < threshold else 255)
    w, h = dark.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if dark.getpixel(corner) == 0:
            ImageDraw.floodfill(dark, corner, 128)          # 128 = background
    tile = dark.point(lambda v: 0 if v == 128 else 255)
    if inset:
        tile = tile.filter(ImageFilter.MinFilter(2 * inset + 1))
    big = tile.resize((w * SUPERSAMPLE, h * SUPERSAMPLE), Image.Resampling.NEAREST)
    big = big.filter(ImageFilter.GaussianBlur(SUPERSAMPLE * 0.6))
    return big.resize((w, h), Image.Resampling.LANCZOS)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=root / "assets/logos/leo-script.original.webp")
    parser.add_argument("--output", type=Path, default=root / "assets/logos/leo-script.source.png")
    parser.add_argument("--inset", type=int, default=2)
    args = parser.parse_args()
    with Image.open(args.source) as image:
        if image.width != image.height:
            raise ValueError("the logo must be square")
        rgb = image.convert("RGB")
        mask = tile_mask(image, args.inset)
    # Every pixel that is not fully opaque takes the tile's own cream as its colour.
    # Transparent pixels otherwise keep the old black RGB, and resampling to the small ICO
    # frames blends that black into the edge (the logo test caught a luminance-85 fringe).
    cream = rgb.getpixel((rgb.width // 2, max(8, args.inset * 4)))
    opaque = mask.point(lambda v: 255 if v == 255 else 0)
    master = Image.composite(rgb, Image.new("RGB", rgb.size, cream), opaque).convert("RGBA")
    master.putalpha(mask)
    master.save(args.output, optimize=True)
    print(f"{args.output}: {master.width}px, tile from corner flood fill, inset {args.inset}px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
