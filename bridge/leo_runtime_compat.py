"""Versioned, bounded compatibility and browse overlays for Leo AI's runtime.

The SDK calling convention is extended without changing completion validation.
The separately byte-checked chat guard rejects model calls in explicit browse
mode, including calls whose configuration already contains a pinned credential.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import tempfile
from pathlib import Path

VERSION = 1
MARKER = "LEO_SUBMIT_OUTPUT_COMPAT_VERSION = 1"
DECLARATION = MARKER + "\n_LEO_COMPLETION_BULLETS_UNSET = object()\n"
NORMALIZATION = '''        # Leo SDK input compatibility v1. Never invent completion evidence.
        if completion_bullets is _LEO_COMPLETION_BULLETS_UNSET:
            if not isinstance(output, dict) or "completion_bullets" not in output:
                raise TypeError("_Host.submit_output() missing 1 required positional argument: 'completion_bullets'")
            envelope = dict(output)
            completion_bullets = envelope.pop("completion_bullets")
            if "output" in envelope:
                options = {
                    "output_schema": output_schema,
                    "task_status": task_status,
                    "source_files": source_files,
                    "entry_points": entry_points,
                    "architecture_summary": architecture_summary,
                    "test_evidence": test_evidence,
                }
                unknown = set(envelope) - {"output", *options}
                if unknown:
                    raise TypeError("submit_output envelope has unknown fields: " + ", ".join(sorted(map(str, unknown))))
                for name in options:
                    if name in envelope:
                        if options[name] is not None:
                            raise TypeError("submit_output received duplicate option: " + name)
                        options[name] = envelope[name]
                output = envelope["output"]
                output_schema = options["output_schema"]
                task_status = options["task_status"]
                source_files = options["source_files"]
                entry_points = options["entry_points"]
                architecture_summary = options["architecture_summary"]
                test_evidence = options["test_evidence"]
            else:
                # Flat form: every field except the explicitly extracted
                # completion_bullets remains in the output, including summary.
                output = envelope
'''

BROWSE_VERSION = 1
BROWSE_ENV = "LEO_STUDIO_BROWSE_ONLY"
BROWSE_MARKER = "# LEO_BROWSE_GUARD_VERSION = 1"
# Audited installed upstream openai4s/llm/client.py, exact LF and CRLF bytes.
# A different revision requires a new source audit, never a fuzzy patch.
BROWSE_SOURCE_SHA256 = frozenset({
    "99a65f666be44bbf46a69cc5b04ca95e8aae0cf14b5c2371a36d4655a69d11fa",
    "6b3406b0aa692e3179ef05103367f4e3cb4bff1028150938026176ba84b7334f",
})
BROWSE_ANCHOR = '    """Route one normalized request through the configured provider adapter."""\n'
BROWSE_GUARD = '''    # LEO_BROWSE_GUARD_VERSION = 1
    import os as _leo_browse_os
    _leo_browse_mode = _leo_browse_os.environ.get("LEO_STUDIO_BROWSE_ONLY", "0")
    if _leo_browse_mode != "0":
        _leo_browse_code = "LEO_BROWSE_ONLY" if _leo_browse_mode == "1" else "LEO_BROWSE_MODE_INVALID"
        _leo_browse_error = LLMError("Leo AI browse mode blocks model requests; connect a model to continue.")
        _leo_browse_error.error_code = _leo_browse_code
        _leo_browse_error.status = 403
        _leo_browse_error.retryable = False
        raise _leo_browse_error
'''


class CompatibilityError(ValueError):
    pass


def _method(source: bytes) -> ast.FunctionDef:
    tree = ast.parse(source)
    owners = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "_Host"]
    methods = [node for owner in owners for node in owner.body
               if isinstance(node, ast.FunctionDef) and node.name == "submit_output"]
    if len(owners) != 1 or len(methods) != 1:
        raise CompatibilityError("RUNTIME_COMPAT_LAYOUT_CHANGED")
    return methods[0]


def compatible_source(original: bytes) -> bytes:
    source = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in source else "\n"
    if MARKER in source:
        if (DECLARATION.replace("\n", newline) in source
                and NORMALIZATION.replace("\n", newline) in source):
            return original
        raise CompatibilityError("RUNTIME_COMPAT_OVERLAY_CONFLICT")
    method = _method(original)
    if ([arg.arg for arg in method.args.args] != ["self", "output", "completion_bullets"]
            or method.args.defaults or len(method.body) != 2
            or not isinstance(method.body[0], ast.Expr)
            or not isinstance(method.body[1], ast.Return)):
        raise CompatibilityError("RUNTIME_COMPAT_LAYOUT_CHANGED")
    lines = original.splitlines(keepends=True)
    start = sum(map(len, lines[:method.lineno - 1]))
    finish = sum(map(len, lines[:method.end_lineno]))
    old_method = original[start:finish].decode("utf-8")
    signature = "        completion_bullets: list[str],"
    returning = "        return self._call("
    if old_method.count(signature) != 1 or old_method.count(returning) != 1:
        raise CompatibilityError("RUNTIME_COMPAT_LAYOUT_CHANGED")
    new_method = old_method.replace(signature, "        completion_bullets: list[str] = _LEO_COMPLETION_BULLETS_UNSET,", 1)
    new_method = new_method.replace(returning, NORMALIZATION.replace("\n", newline) + returning, 1)
    result = original[:start] + new_method.encode("utf-8") + original[finish:]
    anchor = ('HOST_CAPABILITY_VERSION = "2"' + newline).encode("utf-8")
    if result.count(anchor) != 1:
        raise CompatibilityError("RUNTIME_COMPAT_CAPABILITY_CHANGED")
    result = result.replace(anchor, anchor + newline.encode() + DECLARATION.replace("\n", newline).encode(), 1)
    compile(result, "leo-runtime-compat-overlay", "exec")
    # The host-bound return expression must remain exactly the upstream one.
    if ast.dump(_method(result).body[-1]) != ast.dump(method.body[-1]):
        raise CompatibilityError("RUNTIME_COMPAT_VALIDATION_FAILED")
    return result


def browse_compatible_source(original: bytes) -> bytes:
    """Patch only an audited whole file; recheck all original bytes on repeats."""
    source = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in source else "\n"
    guard = BROWSE_GUARD.replace("\n", newline).encode("utf-8")
    if BROWSE_MARKER in source:
        if original.count(guard) != 1:
            raise CompatibilityError("RUNTIME_BROWSE_OVERLAY_CONFLICT")
        candidate = original.replace(guard, b"", 1)
        if hashlib.sha256(candidate).hexdigest() not in BROWSE_SOURCE_SHA256:
            raise CompatibilityError("RUNTIME_BROWSE_SOURCE_UNKNOWN")
        if browse_compatible_source(candidate) != original:
            raise CompatibilityError("RUNTIME_BROWSE_OVERLAY_CONFLICT")
        return original
    if hashlib.sha256(original).hexdigest() not in BROWSE_SOURCE_SHA256:
        raise CompatibilityError("RUNTIME_BROWSE_SOURCE_UNKNOWN")
    anchor = BROWSE_ANCHOR.replace("\n", newline).encode("utf-8")
    if original.count(anchor) != 1:
        raise CompatibilityError("RUNTIME_BROWSE_LAYOUT_CHANGED")
    updated = original.replace(anchor, anchor + guard, 1)
    compile(updated, "leo-runtime-browse-overlay", "exec")
    return updated


def _install_overlay(base: Path, target: Path, original: bytes, updated: bytes, *, check: bool) -> dict:
    """Preserve exact originals and atomically replace one already checked file."""
    previous_digest = hashlib.sha256(original).hexdigest()
    digest = hashlib.sha256(updated).hexdigest()
    changed = updated != original
    if changed and not check:
        backup_root = base / "runtime-compat-originals"
        backup_root.mkdir(mode=0o700, exist_ok=True)
        if backup_root.is_symlink() or backup_root.resolve(strict=True) != backup_root:
            raise CompatibilityError("RUNTIME_COMPAT_BACKUP_PATH_INVALID")
        backup = backup_root / (previous_digest + ".py")
        if backup.exists():
            if backup.is_symlink() or backup.read_bytes() != original:
                raise CompatibilityError("RUNTIME_COMPAT_BACKUP_CONFLICT")
        else:
            with backup.open("xb") as handle:
                handle.write(original)
                handle.flush()
                os.fsync(handle.fileno())
        descriptor, temporary = tempfile.mkstemp(prefix=".leo-runtime-compat-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, target.stat().st_mode & 0o777)
            if target.is_symlink() or target.resolve(strict=True) != target or target.read_bytes() != original:
                raise CompatibilityError("RUNTIME_COMPAT_SOURCE_CHANGED")
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"applied": not check or not changed, "changed": changed and not check,
            "needs_update": changed if check else False,
            "previous_sha256": previous_digest, "sha256": digest}


def apply_compatibility(base: Path, *, check: bool = False) -> dict:
    base = base.resolve(strict=True)
    sources = (base / "sources").resolve(strict=True)
    source_root = (base / "active-source").resolve(strict=True)
    if source_root == sources or sources not in source_root.parents:
        raise CompatibilityError("RUNTIME_COMPAT_SOURCE_PATH_INVALID")
    relative = Path("openai4s/sdk/host.py")
    browse_relative = Path("openai4s/llm/client.py")
    prepared = []
    # Validate both inputs before changing either, including unknown chat bytes.
    for resource, transform in ((relative, compatible_source), (browse_relative, browse_compatible_source)):
        target = source_root / resource
        if target.is_symlink() or target.resolve(strict=True) != target:
            raise CompatibilityError("RUNTIME_COMPAT_SOURCE_PATH_INVALID")
        original = target.read_bytes()
        prepared.append((target, original, transform(original)))
    host, browse = [_install_overlay(base, *item, check=check) for item in prepared]
    browse.update({"version": BROWSE_VERSION, "source_file": browse_relative.as_posix()})
    return {"compatibility": "submit-output", "version": VERSION,
            "applied": host["applied"] and browse["applied"],
            "changed": host["changed"] or browse["changed"],
            "needs_update": host["needs_update"] or browse["needs_update"],
            "source_revision": source_root.name, "source_file": relative.as_posix(),
            "previous_sha256": host["previous_sha256"], "sha256": host["sha256"],
            "browse_guard": browse["applied"], "browse_guard_details": browse}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "check"))
    parser.add_argument("--base", type=Path, default=Path.home() / ".local/share/leo-ai-studio")
    args = parser.parse_args(argv)
    try:
        result = apply_compatibility(args.base, check=args.action == "check")
        print(json.dumps({"ok": True, "data": result}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, SyntaxError) as exc:
        code = str(exc) if isinstance(exc, CompatibilityError) else "RUNTIME_COMPAT_PREPARATION_FAILED"
        print(json.dumps({"ok": False, "error": {"code": code,
            "message": "Leo AI runtime compatibility preparation failed; completion validation remains unchanged."}}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
