"""3.2.7 · Whole-file runtime modules may only replace audited earlier releases.

3.2.6 changed bridge/leo_reasoning.py without registering the released predecessor, so every
connection stopped with RUNTIME_FEATURES_RUNTIME_MODULE_UNKNOWN (the owner could not enter the
workbench). The guard below reads git history: every released version of a runtime module that
differs from the current one must be registered in PREVIOUS_RUNTIME_MODULES.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))
import leo_runtime_features as features  # noqa: E402

# bridge file -> the module path it becomes in the daemon's source (see leo_runtime_features._contracts)
RUNTIME_MODULES = {"leo_reasoning.py": "openai4s/leo_reasoning.py",
                   "leo_thought_runtime.py": "openai4s/leo_thought.py",
                   "leo_turn_binding_runtime.py": "openai4s/server/leo_turn_binding.py"}


def test_only_absent_unchanged_or_registered_modules_may_be_replaced():
    new = (ROOT / "bridge/leo_reasoning.py").read_bytes()
    allowed = features.runtime_module_replacement_allowed
    assert allowed("openai4s/leo_reasoning.py", None, new)
    assert allowed("openai4s/leo_reasoning.py", new, new)
    assert not allowed("openai4s/leo_reasoning.py", b"# someone else's code\n", new)
    assert not allowed("openai4s/leo_thought.py", b"# someone else's code\n", new)
    released = "905cbd29ca54f608dc464322eba536d1501bc509586210c408db2cab5799f620"
    assert released in features.PREVIOUS_RUNTIME_MODULES["openai4s/leo_reasoning.py"]


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git history is needed for this guard")
def test_every_released_predecessor_of_a_changed_runtime_module_is_registered():
    try:
        tags = _git("tag", "-l", "v*").decode().split()
    except subprocess.CalledProcessError:
        pytest.skip("not a git checkout")
    if not tags:
        pytest.skip("no release tags in this checkout")
    for name, target in RUNTIME_MODULES.items():
        current = hashlib.sha256((ROOT / "bridge" / name).read_bytes()).hexdigest()
        missing = set()
        for tag in tags:
            try:
                released = hashlib.sha256(_git("show", f"{tag}:bridge/{name}")).hexdigest()
            except subprocess.CalledProcessError:
                continue  # the module did not exist in that release
            if released != current and released not in features.PREVIOUS_RUNTIME_MODULES.get(target, ()):
                missing.add((tag, released[:12]))
        assert not missing, f"{name}: register these released versions in PREVIOUS_RUNTIME_MODULES: {sorted(missing)}"
