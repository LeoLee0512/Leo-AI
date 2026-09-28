"""Frozen validation-node artifacts and anti-collision measurements."""

from __future__ import annotations

import argparse
import ast
from bisect import bisect_left
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import struct
from typing import Iterable, Sequence


NPY_MAGIC = b"\x93NUMPY"


def generate_cgl2000() -> tuple[float, ...]:
    """Authoritative pre-freeze generator for the CGL2000 artifact."""

    return tuple(0.5 * (1.0 - math.cos(j * math.pi / 1999.0)) for j in range(2000))


def generate_gl512() -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Generate GL512 once for freezing; not used by validation at runtime."""

    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - generation environment only
        raise RuntimeError("NumPy is required only to regenerate the frozen GL512 assets") from exc
    nodes, weights = np.polynomial.legendre.leggauss(512)
    mapped_nodes = 0.5 * (nodes + 1.0)
    mapped_weights = 0.5 * weights
    return tuple(float(x) for x in mapped_nodes), tuple(float(w) for w in mapped_weights)


def float64_bytes(values: Iterable[float]) -> bytes:
    return b"".join(struct.pack("<d", float(value)) for value in values)


def data_sha256(values: Iterable[float]) -> str:
    return hashlib.sha256(float64_bytes(values)).hexdigest()


def combined_data_sha256(*arrays: Iterable[float]) -> str:
    digest = hashlib.sha256()
    for values in arrays:
        digest.update(float64_bytes(values))
    return digest.hexdigest()


def write_npy_f64(path: str | Path, values: Sequence[float]) -> None:
    """Write a deterministic NumPy v1.0 C-order ``<f8`` one-dimensional file."""

    destination = Path(path)
    header = "{'descr': '<f8', 'fortran_order': False, 'shape': (%d,), }" % len(values)
    prefix_length = len(NPY_MAGIC) + 2 + 2
    padding = (16 - ((prefix_length + len(header.encode("latin1")) + 1) % 16)) % 16
    header_bytes = (header + (" " * padding) + "\n").encode("latin1")
    if len(header_bytes) > 65535:
        raise ValueError("NumPy v1.0 header is too long")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        NPY_MAGIC
        + bytes((1, 0))
        + struct.pack("<H", len(header_bytes))
        + header_bytes
        + float64_bytes(values)
    )


def read_npy_f64(path: str | Path) -> tuple[float, ...]:
    raw = Path(path).read_bytes()
    if not raw.startswith(NPY_MAGIC + bytes((1, 0))):
        raise ValueError("expected a NumPy v1.0 artifact")
    header_length = struct.unpack("<H", raw[8:10])[0]
    header_end = 10 + header_length
    try:
        header = ast.literal_eval(raw[10:header_end].decode("latin1").strip())
    except (SyntaxError, ValueError) as exc:
        raise ValueError("invalid NumPy header") from exc
    if header.get("descr") != "<f8":
        raise ValueError("artifact dtype must be explicit little-endian float64 (<f8)")
    if header.get("fortran_order") is not False:
        raise ValueError("artifact must use C order")
    shape = header.get("shape")
    if not isinstance(shape, tuple) or len(shape) != 1 or not isinstance(shape[0], int):
        raise ValueError("artifact shape must be one-dimensional")
    payload = raw[header_end:]
    if len(payload) != shape[0] * 8:
        raise ValueError("artifact payload length does not match its shape")
    return tuple(item[0] for item in struct.iter_unpack("<d", payload))


@dataclass(frozen=True)
class AntiCollisionMeasurement:
    min_distance: float
    denominator: int
    numerator: int
    node_index: int


def anti_collision(values: Sequence[float], d_max: int) -> AntiCollisionMeasurement:
    ordered = sorted(float(value) for value in values)
    best = AntiCollisionMeasurement(math.inf, -1, -1, -1)
    original_indices = {value: index for index, value in enumerate(values)}
    for denominator in range(2, d_max + 1):
        for numerator in range(1, denominator):
            target = numerator / denominator
            pivot = bisect_left(ordered, target)
            for position in (pivot - 1, pivot):
                if 0 <= position < len(ordered):
                    value = ordered[position]
                    distance = abs(value - target)
                    if distance < best.min_distance:
                        best = AntiCollisionMeasurement(
                            distance,
                            denominator,
                            numerator,
                            original_indices[value],
                        )
    return best


def generate_assets(output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    cgl = generate_cgl2000()
    gl_nodes, gl_weights = generate_gl512()
    paths = {
        "CGL2000": output / "CGL2000.npy",
        "GL512_nodes": output / "GL512_nodes.npy",
        "GL512_weights": output / "GL512_weights.npy",
    }
    write_npy_f64(paths["CGL2000"], cgl)
    write_npy_f64(paths["GL512_nodes"], gl_nodes)
    write_npy_f64(paths["GL512_weights"], gl_weights)
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}


def _main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate frozen validation-node assets")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    for name, digest in generate_assets(args.output_dir).items():
        print(f"{name}\t{digest}")
    return 0


if __name__ == "__main__":  # pragma: no cover - operator command
    raise SystemExit(_main())
