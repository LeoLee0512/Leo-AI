#!/usr/bin/env python3
"""Encode the approved icon master into desktop and web icon formats.

Run with a Python that has Pillow (the build environment need not carry it).
No artwork is generated or recoloured here. Every frame uses the entire same
master, so the taskbar never substitutes a cropped glyph for the desktop.

Since 2026-09-27 (Leo AI 2.1.2) the master is the owner's "Leo" script logo,
``assets/logos/leo-script.source.png``, made transparent by
``tools/make_logo_master.py`` from ``leo-script.original.webp``. The output file
names still say "lion": they are internal paths shared by the build, deployment,
taskbar-branding cache and provenance checks, and renaming them is a separate
change. The retired lion master stays in assets/logos as history.
"""
from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path

from PIL import Image

ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def build_frame(source: Image.Image, size: int) -> Image.Image:
    """Resize the entire square artwork without size-specific substitution."""
    if source.width != source.height:
        raise ValueError("The approved icon master must be square")
    return source.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=root / "assets/logos/leo-script.source.png")
    parser.add_argument("--output", type=Path, default=root / "stage/logos")
    args = parser.parse_args()
    with Image.open(args.source) as image:
        source = image.convert("RGBA")
    args.output.mkdir(parents=True, exist_ok=True)
    build_frame(source, 1024).save(args.output / "leo-lion-1024.png")
    frames = [build_frame(source, size) for size in ICO_SIZES]
    frames[-1].save(args.output / "leo-lion.ico", format="ICO",
                    sizes=[(s, s) for s in ICO_SIZES], append_images=frames[:-1])
    png = io.BytesIO()
    # 256 px behind a 128-unit viewBox: the start page shows it at 128 CSS px, which is
    # 192 device px at 150 % Windows scaling -- a 128 px bitmap would be upscaled and blur.
    build_frame(source, 256).save(png, format="PNG", optimize=True)
    encoded = base64.b64encode(png.getvalue()).decode("ascii")
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
           'role="img" aria-label="Leo AI"><title>Leo AI</title>'
           f'<image width="128" height="128" href="data:image/png;base64,{encoded}"/></svg>\n')
    for name in ("leo-lion.svg", "leo-favicon.svg"):
        (args.output / name).write_text(svg, encoding="utf-8", newline="\n")
    print(f"Encoded {len(frames)} same-composition ICO frames and 3 web assets in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
