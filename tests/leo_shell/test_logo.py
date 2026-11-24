"""The "Leo" script logo that replaced the lion (Leo AI 2.1.2).

Standard library only (the governance environment has no Pillow): the 256 px ICO frame is
a PNG, decoded here to prove the corners are transparent and the edge carries no dark
fringe -- the supplied artwork had black corners and no alpha channel.
"""

from __future__ import annotations

import base64
import re
import struct
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOGOS = REPO / "stage" / "logos"


def _ico_frames(data: bytes) -> dict[int, bytes]:
    _reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    assert kind == 1
    frames = {}
    for i in range(count):
        width, _h, _c, _r, _p, _b, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
        frames[width or 256] = data[offset:offset + size]
    return frames


def _decode_rgba_png(png: bytes) -> tuple[int, int, list[bytearray]]:
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, width = 8, b"", 0
    while pos < len(png):
        length, kind = struct.unpack_from(">I4s", png, pos)
        body = png[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
            assert (depth, colour, interlace) == (8, 6, 0), "8-bit RGBA, not interlaced"
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw, stride, rows, prev = zlib.decompress(idat), width * 4, [], bytearray(width * 4)
    for y in range(height):
        kind, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if kind == 1:
                line[x] = (line[x] + a) & 255
            elif kind == 2:
                line[x] = (line[x] + b) & 255
            elif kind == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, rows


def test_the_icon_carries_every_size_and_its_largest_frame_is_rgba():
    frames = _ico_frames((LOGOS / "leo-lion.ico").read_bytes())
    assert sorted(frames) == [16, 24, 32, 48, 64, 128, 256]
    assert frames[256][:8] == b"\x89PNG\r\n\x1a\n"


def test_corners_are_transparent_and_the_edge_has_no_dark_fringe():
    width, height, rows = _decode_rgba_png(_ico_frames((LOGOS / "leo-lion.ico").read_bytes())[256])
    pixel = lambda x, y: tuple(rows[y][4 * x:4 * x + 4])
    for x, y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1), (4, 4)):
        assert pixel(x, y)[3] == 0, (x, y)
    # Visible edge only: at alpha 1/255 the resampler leaves stray RGB (seen: two such pixels
    # in the 256 frame, one of them yellow) that no screen can show; from ~6 % opacity on,
    # a dark colour would be a real fringe.
    edge = [pixel(x, y) for y in range(height) for x in range(width) if 16 <= pixel(x, y)[3] < 255]
    assert edge, "the tile edge is anti-aliased"
    darkest = min((r + g + b) / 3 for r, g, b, _a in edge)
    assert darkest > 180, f"dark fringe on the tile edge (luminance {darkest:.0f})"
    r, g, b, a = pixel(width // 2, height // 8)
    assert a == 255 and min(r, g, b) > 230, "cream tile"
    assert any(pixel(x, height // 2)[:3] < (60, 60, 60) for x in range(width)), "the black 'Leo' strokes are there"


def test_the_web_marks_embed_the_same_logo_and_no_longer_call_it_a_lion():
    for name in ("leo-lion.svg", "leo-favicon.svg"):
        svg = (LOGOS / name).read_text(encoding="utf-8")
        assert "<title>Leo AI</title>" in svg and "lion" not in svg.lower()
        png = base64.b64decode(re.search(r"base64,([A-Za-z0-9+/=]+)", svg).group(1))
        assert struct.unpack(">II", png[16:24]) == (256, 256), "256 px so it stays sharp at 150 % scaling"


def test_the_start_page_no_longer_wraps_the_mark_in_the_lion_badge():
    shell = (REPO / "stage" / "shell.html").read_text(encoding="utf-8")
    rule = re.search(r"\.mark\{[^}]*\}", shell).group(0)
    assert "background" not in rule and "filter" not in rule and "border:" not in rule


def test_the_script_logo_sources_are_kept():
    # 3.0.0: the retired lion master left the tree (it stays in the private Git history).
    logos = REPO / "assets" / "logos"
    for name in ("leo-script.original.webp", "leo-script.source.png"):
        assert (logos / name).is_file(), name
