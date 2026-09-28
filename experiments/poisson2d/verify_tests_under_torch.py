"""Run the 2D test modules under the training interpreter (torch + numpy present).

The repository's governance virtualenv has neither torch nor numpy, so
``pytest`` skips the numerically substantive 2D tests there.  That is a real gap
in what the default suite proves, so the same test functions are executed here
under the mamba interpreter through a minimal pytest shim (importorskip, approx,
raises).  This is a verification harness, not a second test framework: it calls
exactly the functions in ``tests/pinn/test_poisson2d_*.py`` and reports
pass/fail per function.

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -B experiments/poisson2d/verify_tests_under_torch.py
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

#: Only the modules whose substance the governance virtualenv SKIPS (no torch / numpy) belong here;
#: modules that run fully there, or that use pytest fixtures, are left to pytest.
MODULES = ["tests/pinn/test_poisson2d_identity.py", "tests/pinn/test_poisson2d_physics.py",
           "tests/pinn/test_ac2d9_invariants.py"]
OUT = Path("experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json")


class _Approx:
    def __init__(self, expected, abs_tol=None, rel_tol=None):
        self.expected = expected
        self.abs_tol = abs_tol
        self.rel_tol = rel_tol

    def __eq__(self, other):
        if self.abs_tol is None and self.rel_tol is None:
            return math.isclose(other, self.expected, rel_tol=1e-6, abs_tol=1e-12)
        if self.abs_tol is not None and abs(other - self.expected) <= self.abs_tol:
            return True
        if self.rel_tol is not None and abs(other - self.expected) <= self.rel_tol * abs(self.expected):
            return True
        return False

    def __repr__(self):
        return f"approx({self.expected}, abs={self.abs_tol}, rel={self.rel_tol})"


class _Raises:
    def __init__(self, exception):
        self.exception = exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"expected {self.exception.__name__} but nothing was raised")
        return issubclass(exc_type, self.exception)


def _shim() -> ModuleType:
    module = ModuleType("pytest")
    module.importorskip = lambda name, *a, **kw: importlib.import_module(name)
    module.approx = lambda expected, abs=None, rel=None: _Approx(expected, abs, rel)   # noqa: A002
    module.raises = lambda exception, *a, **kw: _Raises(exception)
    module.skip = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("skip is not available in this harness"))
    return module


def main() -> int:
    sys.modules.setdefault("pytest", _shim())
    results: list[dict[str, object]] = []
    for relative in MODULES:
        path = Path(relative)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        for name in sorted(n for n in dir(module) if n.startswith("test_")):
            function = getattr(module, name)
            try:
                function()
                results.append({"module": relative, "test": name, "status": "PASS"})
                print(f"PASS  {path.stem}::{name}", flush=True)
            except Exception as exc:                                     # noqa: BLE001
                results.append({"module": relative, "test": name, "status": "FAIL", "error": str(exc),
                                "traceback": traceback.format_exc()})
                print(f"FAIL  {path.stem}::{name}: {exc}", flush=True)
    failed = [r for r in results if r["status"] != "PASS"]
    document = {
        "purpose": "execute the 2D tests that the governance virtualenv skips (no torch / numpy there) under the training interpreter",
        "interpreter": sys.version,
        "interpreterInstallationId": "prefix-" + hashlib.sha256(str(Path(sys.prefix).resolve()).lower().encode("utf-8")).hexdigest()[:16],
        "pathRecordingRule": ("prospective rule (Final Closure Audit issue 3C): the interpreter is identified by its prefix hash, "
                              "the same installationId convention the environment fingerprint uses; the absolute path is not recorded"),
        "ranAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modules": MODULES,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{document['passed']} passed, {document['failed']} failed -> {OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
