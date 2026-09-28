"""Render the shipped theme background assets from their approved masters.

The masters in ``assets/backgrounds/*.src.png`` are the artwork exactly as it
was delivered: full 1672x941, untouched pixels.  They are never edited here and
never shipped -- three lossless PNGs are 7.4 MB, and the shell inlines every
background as a data URI on each injection.

What ships is one WebP per master at the SAME pixel dimensions, same crop, same
colours.  The only transformation is lossy compression, and the tool proves that
claim rather than asserting it: ``verify`` re-decodes each rendered file and
fails if the geometry changed at all, if the artwork was tinted
(:data:`MAX_TINT_DRIFT`), or if the paper grain was scrubbed
(:data:`MAX_GRAIN_DRIFT`).  Measured at q=82 the tint drift is under 0.4/255 --
far below a JND, and these assets are composited at 4-14% opacity.

Usage::

    python tools/build_backgrounds.py build    # render into the app theme dir
    python tools/build_backgrounds.py verify   # re-check what is on disk

Output goes to ``stage/backgrounds/`` -- the repository, not an installation.
That directory is the canonical source for the shipped artwork: it is committed,
``tools/build_launcher.ps1`` overlays it into the package, and
``tools/deploy_release.ps1`` installs it.  Rendering straight into a machine's
theme directory would put a product asset outside version control, which is the
gap this pipeline exists to close.

``--theme-dir`` overrides the destination, e.g. to re-verify what an
installation actually has on disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTERS_DIR = REPO_ROOT / "assets" / "backgrounds"
DEFAULT_THEME_DIR = REPO_ROOT / "stage"

# q=82/method=6 is the knee of the curve for this artwork: the paper grain
# survives, the wash edges stay soft, and each file lands near 140 KiB.  Raising
# it to 88 costs 60% more bytes for a drift improvement of about 0.1/255.
WEBP_QUALITY = 82
WEBP_METHOD = 6

# Two independent drift budgets, both in 8-bit levels.
#
# TINT is |mean(master) - mean(rendered)| per channel: it answers "was the
# artwork recoloured?".  A re-encode that shifts the paper towards yellow or
# lifts saturation moves this immediately, so the budget is tight.
#
# GRAIN is the mean absolute per-pixel difference: it answers "how hard did the
# encoder work on the paper texture?".  It is naturally larger than TINT because
# the fibre noise is exactly what a lossy codec smooths, and it is invisible at
# the 4-14% opacities these assets are composited at.
MAX_TINT_DRIFT = 0.5
MAX_GRAIN_DRIFT = 4.0

# key -> (master filename, what the asset is for).  The key becomes the CSS
# placeholder: "ink-autumn-branch" -> __LEO_BG_INK_AUTUMN_BRANCH__.
BACKGROUNDS: tuple[tuple[str, str, str], ...] = (
    (
        "ink-autumn-branch",
        "ink-autumn-branch.src.png",
        "Settings / content edge -- the rising branch (05_09_39 source)",
    ),
    (
        "ink-autumn-tree",
        "ink-autumn-tree.src.png",
        "Home / welcome and knowledge -- the rooted tree (05_09_52 source)",
    ),
    (
        "ink-autumn-branch-warm",
        "ink-autumn-branch-warm.src.png",
        "Sidebar / workspace and splash -- the warm branch (05_10_04 source)",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _drift(master, rendered) -> tuple[float, float]:
    """Return ``(tint, grain)`` drift in 8-bit levels; see the budgets above."""
    from PIL import ImageChops, ImageStat

    grain = max(ImageStat.Stat(ImageChops.difference(master, rendered)).mean)
    a = ImageStat.Stat(master).mean
    b = ImageStat.Stat(rendered).mean
    tint = max(abs(x - y) for x, y in zip(a, b))
    return tint, grain


def _check_drift(key: str, master, rendered) -> tuple[float, float] | None:
    """Validate both budgets; print and return ``None`` on failure."""
    tint, grain = _drift(master, rendered)
    if tint > MAX_TINT_DRIFT:
        print(f"{key}: tint drift {tint:.3f} exceeds {MAX_TINT_DRIFT}", file=sys.stderr)
        return None
    if grain > MAX_GRAIN_DRIFT:
        print(f"{key}: grain drift {grain:.3f} exceeds {MAX_GRAIN_DRIFT}", file=sys.stderr)
        return None
    return tint, grain


def build(theme_dir: Path) -> int:
    # build, unlike verify, cannot degrade: rendering is the whole job.
    try:
        from PIL import Image
    except ModuleNotFoundError:
        print(
            "Pillow is required to render the artwork. It is intentionally not "
            "a build dependency -- run this step with a Python that has it, "
            "then commit the result.",
            file=sys.stderr,
        )
        raise

    out_dir = theme_dir / "backgrounds"
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for key, master_name, purpose in BACKGROUNDS:
        master_path = MASTERS_DIR / master_name
        if not master_path.is_file():
            print(f"missing master: {master_path}", file=sys.stderr)
            return 1
        master = Image.open(master_path).convert("RGB")
        target = out_dir / f"{key}.webp"
        master.save(target, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)

        rendered = Image.open(target).convert("RGB")
        if rendered.size != master.size:
            print(f"{key}: geometry changed {master.size} -> {rendered.size}", file=sys.stderr)
            return 1
        measured = _check_drift(key, master, rendered)
        if measured is None:
            return 1
        tint, grain = measured

        entries.append(
            {
                "key": key,
                "file": target.name,
                "purpose": purpose,
                "width": master.width,
                "height": master.height,
                "bytes": target.stat().st_size,
                "sha256": _sha256(target),
                "master": master_name,
                "master_sha256": _sha256(master_path),
                "quality": WEBP_QUALITY,
                "tint_drift": round(tint, 4),
                "grain_drift": round(grain, 4),
            }
        )
        print(
            f"{key}: {master.width}x{master.height} "
            f"{target.stat().st_size / 1024:.1f} KiB "
            f"tint {tint:.3f} grain {grain:.3f}"
        )

    manifest = {
        "schema_version": 1,
        "note": (
            "Rendered by tools/build_backgrounds.py from the untouched masters in "
            "assets/backgrounds/. Same dimensions, same crop, same colours; the "
            "only transformation is WebP compression."
        ),
        "backgrounds": entries,
    }
    # newline="\n" is not cosmetic: this manifest is a committed source file and
    # the repository normalises to LF, so emitting os.linesep here would make
    # every regeneration show up as a whole-file rewrite.
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {out_dir / 'manifest.json'}")
    return 0


def verify(theme_dir: Path) -> int:
    # Pillow is an art-pipeline dependency, not a build one: it is deliberately
    # absent from requirements.lock, so `verify` has to be useful without it.
    # The hash and manifest checks need no decoder and always run; only the
    # re-decode drift check does. Without Pillow that check is reported NOT
    # TESTED and the command still fails on any hash mismatch -- what it must
    # never do is fold an unperformed check into a pass.
    try:
        from PIL import Image
    except ModuleNotFoundError:
        Image = None

    out_dir = theme_dir / "backgrounds"
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"missing manifest: {manifest_path}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_key = {entry["key"]: entry for entry in manifest.get("backgrounds", [])}
    failures = not_tested = 0
    for key, master_name, _purpose in BACKGROUNDS:
        entry = by_key.get(key)
        if entry is None:
            print(f"{key}: not registered in the manifest", file=sys.stderr)
            failures += 1
            continue
        target = out_dir / entry["file"]
        if not target.is_file():
            print(f"{key}: missing {target}", file=sys.stderr)
            failures += 1
            continue
        if _sha256(target) != entry["sha256"]:
            print(f"{key}: sha256 does not match the manifest", file=sys.stderr)
            failures += 1
            continue
        master_path = MASTERS_DIR / master_name
        if not master_path.is_file():
            print(f"{key}: master is missing: {master_path}", file=sys.stderr)
            failures += 1
            continue
        if _sha256(master_path) != entry["master_sha256"]:
            print(f"{key}: master has changed since the asset was rendered", file=sys.stderr)
            failures += 1
            continue
        if Image is None:
            print(f"{key}: hashes ok; drift NOT TESTED (Pillow unavailable)")
            not_tested += 1
            continue
        master = Image.open(master_path).convert("RGB")
        rendered = Image.open(target).convert("RGB")
        if rendered.size != master.size:
            print(f"{key}: geometry changed {master.size} -> {rendered.size}", file=sys.stderr)
            failures += 1
            continue
        measured = _check_drift(key, master, rendered)
        if measured is None:
            failures += 1
            continue
        tint, grain = measured
        print(
            f"{key}: ok ({rendered.width}x{rendered.height}, "
            f"tint {tint:.3f} grain {grain:.3f})"
        )
    if not_tested:
        print(
            f"{not_tested} asset(s) hash-verified only; install Pillow to check "
            f"tint and grain against the masters",
            file=sys.stderr,
        )
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument(
        "--theme-dir",
        type=Path,
        default=DEFAULT_THEME_DIR,
        help="directory holding backgrounds/ (default: the repository's stage/)",
    )
    args = parser.parse_args(argv)
    theme_dir = args.theme_dir.resolve()
    if args.action == "build":
        return build(theme_dir)
    return verify(theme_dir)


if __name__ == "__main__":
    raise SystemExit(main())
