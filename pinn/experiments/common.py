"""R3 minimal experimental runner -- shared plumbing (artifacts, identities, state log).

Scope (2026-09-15 experiment authorization, PART 3): only what the two Poisson 1D
experiments need.  Every governance document is written in the canonical JSON
form of ``pinn.governance.canonical`` so that ``sha256(file bytes) ==
canonical_sha256(document)``; every artifact is registered in a provenance
manifest with its hash, producer and parents; every state transition is
appended to a transition log.  No UI, no scheduler, no plugin system.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pinn.governance.canonical import canonical_bytes, canonical_sha256
from pinn.governance.trust_loop import code_hash_from_manifest
from pinn.governance.trust_vector import EnvironmentFingerprint, environment_id

#: Files whose bytes are the method identity (Constitution 28.1: code, configs, lock files).
#:
#: The rule is a decision surface, not a directory: a file belongs here when its bytes
#: can change how a ScientificSpec is interpreted, what a Gate returns, which
#: FailureSignature is generated, what a DiagnosisRecord says, a TrustVector status, a
#: ClaimGateDecision, a Red-Team verdict or a reproducibility verdict. Everything the
#: pipeline *executes* lives under these prefixes; the named files below are the
#: non-code inputs it reads that carry the same power.
CODE_IDENTITY_PREFIXES: tuple[str, ...] = ("pinn/", "scientific_reference/", "specs/")
CODE_IDENTITY_FILES: tuple[str, ...] = (
    "governance/PINN_RESEARCH_CONSTITUTION.md",
    "governance/POISSON_1D_V1.0_spec.draft.json",
    "governance/POISSON_1D_V1.0_protocol.draft.json",
    "governance/POISSON_1D_V1.0_lock.draft.json",
    # Added by the code-identity completeness audit (2026-09-16), prospectively, for the
    # next revision only -- historical runs keep the manifests they recorded:
    #   * the protocol compilation decides which Tier-1 perturbations are mandatory and
    #     how an applicability registration must be justified. Its text is what made P11
    #     mandatory for C2, so it can change a Red-Team verdict.
    #   * the adversarial core manifest is an input of PRELOCK, which gates whether a
    #     formal attempt starts at all.
    "governance/PINN_TRUST_PROTOCOLS_R1.md",
    "adversarial/core_manifest.draft.json",
)

#: The decision surfaces the boundary above is meant to cover. Named so a reviewer can
#: check a candidate file against a list instead of a habit.
DECISION_SURFACES: tuple[str, ...] = (
    "ScientificSpec interpretation",
    "Gate results",
    "FailureSignature generation",
    "DiagnosisRecord content",
    "TrustVector status",
    "ClaimGateDecision",
    "Red-Team verdict",
    "reproducibility verdict",
)


class CodeIdentityError(RuntimeError):
    """A manifest that does not cover every decision-relevant module has no valid codeHash."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def git_output(repo_root: Path, *args: str) -> str:
    """git stdout decoded as UTF-8 (git emits UTF-8 paths; the Windows console code page must not decode them)."""

    completed = subprocess.run(["git", *args], cwd=str(repo_root), check=True, capture_output=True)
    return completed.stdout.decode("utf-8")


def git_head(repo_root: Path) -> str:
    return git_output(repo_root, "rev-parse", "HEAD").strip()


def tracked_code_files(repo_root: Path) -> list[str]:
    tracked = git_output(repo_root, "ls-files", "-z").split("\0")
    selected = [p for p in tracked if p and (p.startswith(CODE_IDENTITY_PREFIXES) or p in CODE_IDENTITY_FILES)]
    return sorted(selected)


def all_tracked_paths(repo_root: Path) -> set[str]:
    """Every path git tracks, not only the ones inside the identity boundary."""

    return {p.replace("\\", "/") for p in git_output(repo_root, "ls-files", "-z").split("\0") if p}


def untracked_identity_paths(repo_root: Path) -> list[str]:
    """Files inside the identity boundary that git does not track.

    The hole this closes is not hypothetical. ``code_manifest`` enumerates
    ``git ls-files`` and ``workspace_dirty_paths`` passes ``--untracked-files=no``, so a
    brand-new module under ``pinn/`` that a run actually imports is invisible to both: the
    recorded codeHash omits it and nothing complains. It happened -- the nested-budget
    preregistration first recorded a hash that was missing ``checkpoint_annulus.py``, and it
    was noticed only because the hash was recomputed after the commit.

    ``--others`` is used WITHOUT ``--exclude-standard`` on purpose: a helper does not leave
    the method identity by being listed in ``.gitignore``. Byte-code caches are the single
    exclusion, because they are outputs of the modules, not sources of behaviour.
    """

    found: list[str] = []
    for entry in git_output(repo_root, "ls-files", "--others", "-z").split("\0"):
        path = entry.strip().replace("\\", "/")
        if not path or not (path.startswith(CODE_IDENTITY_PREFIXES) or path in CODE_IDENTITY_FILES):
            continue
        if "__pycache__/" in path or path.endswith((".pyc", ".pyo")):
            continue
        found.append(path)
    return sorted(found)


def code_manifest(repo_root: Path, extra_files: Sequence[str] = ()) -> list[dict[str, str]]:
    """Sorted ``[{path, sha256}]`` over the tracked code identity files plus the run's config files."""

    paths = sorted(set(tracked_code_files(repo_root)) | {p.replace("\\", "/") for p in extra_files})
    return [{"path": p, "sha256": sha256_file(repo_root / p)} for p in paths]


def required_identity_paths(repo_root: Path, extra_required: Sequence[str] = ()) -> list[str]:
    """Every path a formal run's manifest must contain: the boundary plus the run's own declarations.

    ``extra_required`` is what the run itself declares -- its frozen config and, when a
    formal run is driven by a script outside the prefixes (``experiments/**`` holds the
    drivers next to the evidence they write), that driver. A declared file that never
    reaches the manifest is the failure this function exists to catch.
    """

    return sorted(set(tracked_code_files(repo_root)) | {p.replace("\\", "/") for p in extra_required})


def assert_code_identity_complete(manifest: Sequence[Mapping[str, str]], repo_root: Path,
                                  extra_required: Sequence[str] = ()) -> None:
    """Fail closed before PRELOCK if the manifest omits a decision-relevant module.

    The check is mechanical: every tracked file inside the identity boundary, plus every
    file the run declared, must appear in the manifest with the bytes it has on disk. A
    run whose manifest is incomplete has a codeHash that does not identify the method
    that produced its results, so it must not start (Constitution 28.1).
    """

    present = {entry["path"]: entry["sha256"] for entry in manifest}
    required = required_identity_paths(repo_root, extra_required)
    missing = [path for path in required if path not in present]
    if missing:
        raise CodeIdentityError(
            "code identity is incomplete: these decision-relevant modules are not in the manifest, "
            f"so the codeHash does not identify the method: {missing}"
        )
    declared = [p.replace("\\", "/") for p in extra_required]
    absent = [p for p in declared if not (repo_root / p).is_file()]
    if absent:
        raise CodeIdentityError(f"declared code-identity files that do not exist: {absent}")
    # A declared file that git does not track has no fixed bytes to identify: it can be
    # edited or deleted without any record, so it cannot carry a codeHash (ruling item 3).
    tracked = all_tracked_paths(repo_root)
    untracked_declaration = [p for p in declared if p not in tracked]
    if untracked_declaration:
        raise CodeIdentityError(
            "codeIdentityExtraFiles must be git-tracked; these are not, so their bytes are not "
            f"recoverable from the repository and cannot identify a method: {untracked_declaration}")
    # And nothing inside the boundary may be untracked, declared or not: a module a run
    # imports must be in the manifest, and only tracked files ever reach it.
    hidden = untracked_identity_paths(repo_root)
    if hidden:
        raise CodeIdentityError(
            "untracked files inside the code-identity boundary: a module the run can import but the "
            "manifest cannot see means the codeHash does not identify the method that produced the "
            "results (Constitution 28.1). Commit or remove them: {hidden}")
    stale = [path for path in required
             if (repo_root / path).is_file() and present[path] != sha256_file(repo_root / path)]
    if stale:
        raise CodeIdentityError(
            f"the manifest no longer matches the files on disk: {stale}")


def workspace_dirty_paths(repo_root: Path) -> list[str]:
    """Tracked code-identity files with uncommitted modifications (a run on them has no valid codeHash)."""

    dirty: list[str] = []
    for line in git_output(repo_root, "status", "--porcelain", "--untracked-files=no").splitlines():
        path = line[3:].strip().replace("\\", "/")
        if path.startswith(CODE_IDENTITY_PREFIXES) or path in CODE_IDENTITY_FILES:
            dirty.append(path)
    return dirty


def machine_id() -> str:
    if sys.platform == "win32":
        try:
            import winreg  # type: ignore[import-not-found]

            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            return "win-" + str(winreg.QueryValueEx(key, "MachineGuid")[0])
        except OSError:
            pass
    return "node-" + sha256_bytes(platform.node().encode("utf-8"))[:16]


def dependency_lock_hash() -> str:
    """Hash of the installed distribution list (name==version, sorted): the lock of this installation."""

    from importlib import metadata

    entries = sorted({f"{d.metadata['Name']}=={d.version}" for d in metadata.distributions() if d.metadata.get("Name")})
    return sha256_bytes("\n".join(entries).encode("utf-8"))


def environment_fingerprint(*, accelerator_class: str = "cpu-only") -> dict[str, str]:
    """Strong + weak fields of Constitution 28.1 for the interpreter running this process."""

    framework = "none"
    blas = "unknown"
    try:
        import torch  # type: ignore[import-not-found]

        major, minor = torch.__version__.split("+")[0].split(".")[:2]
        framework = f"torch-{major}.{minor}"
        config = torch.__config__.show()
        blas = "mkl" if "BLAS_INFO=mkl" in config else ("openblas" if "openblas" in config.lower() else "unknown")
    except ImportError:
        pass
    family = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
    return {
        "machineId": machine_id(),
        "osFamily": family,
        "acceleratorClass": accelerator_class,
        "frameworkVersion": framework,
        "blasBackend": blas,
        "dependencyLockHash": dependency_lock_hash(),
        "installationId": "prefix-" + sha256_bytes(str(Path(sys.prefix).resolve()).lower().encode("utf-8"))[:16],
        "osVersion": platform.version(),
        "pythonVersion": platform.python_version(),
        "acceleratorDriver": "",
    }


def environment_identity(fingerprint: Mapping[str, str]) -> str:
    return environment_id(EnvironmentFingerprint.from_mapping(fingerprint))


class ArtifactStore:
    """Writes documents under ``root`` and keeps the provenance manifest + state transition log."""

    def __init__(self, root: Path, *, producer: str = "pinn.experiments.runner") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.producer = producer
        self.manifest_path = self.root / "PROVENANCE_MANIFEST.json"
        self.state_log_path = self.root / "STATE_TRANSITIONS.json"
        self.entries: list[dict[str, Any]] = []
        self.transitions: list[dict[str, Any]] = []
        if self.manifest_path.exists():
            self.entries = json.loads(self.manifest_path.read_text(encoding="utf-8"))["artifacts"]
        if self.state_log_path.exists():
            self.transitions = json.loads(self.state_log_path.read_text(encoding="utf-8"))["transitions"]

    # ---------------------------------------------------------------- writing
    def write_canonical(self, relpath: str, document: Any, *, role: str, parents: Sequence[str] = (),
                        producer_type: str = "TRUSTED_RUNNER", note: str = "") -> dict[str, str]:
        """Write ``document`` as canonical JSON; the file hash equals the document's canonical hash."""

        data = canonical_bytes(document)
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        digest = sha256_bytes(data)
        assert digest == canonical_sha256(document)
        return self.register(relpath, digest, role=role, parents=parents, producer_type=producer_type, note=note)

    def write_json(self, relpath: str, document: Any, *, role: str, parents: Sequence[str] = (),
                   producer_type: str = "TRUSTED_RUNNER", note: str = "") -> dict[str, str]:
        """Human-readable JSON (reports, histories); hashed as written."""

        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        return self.register(relpath, sha256_file(path), role=role, parents=parents, producer_type=producer_type, note=note)

    def write_text(self, relpath: str, text: str, *, role: str, parents: Sequence[str] = (), note: str = "") -> dict[str, str]:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return self.register(relpath, sha256_file(path), role=role, parents=parents, producer_type="TRUSTED_RUNNER", note=note)

    def register(self, relpath: str, digest: str, *, role: str, parents: Sequence[str] = (),
                 producer_type: str = "TRUSTED_RUNNER", note: str = "") -> dict[str, str]:
        relpath = relpath.replace("\\", "/")
        entry = {
            "artifactId": relpath,
            "sha256": digest,
            "artifactRole": role,
            "producerType": producer_type,
            "producer": self.producer,
            "parentArtifactIds": list(parents),
            "recordedAt": utc_now(),
        }
        if note:
            entry["note"] = note
        self.entries = [e for e in self.entries if e["artifactId"] != relpath] + [entry]
        self._flush()
        return {"artifactId": relpath, "sha256": digest}

    def ref(self, relpath: str) -> dict[str, str]:
        relpath = relpath.replace("\\", "/")
        for entry in self.entries:
            if entry["artifactId"] == relpath:
                return {"artifactId": relpath, "sha256": entry["sha256"]}
        raise KeyError(relpath)

    # ------------------------------------------------------------ transitions
    def transition(self, before: str, after: str, *, gate: int | None, result: str, detail: str = "") -> None:
        self.transitions.append({
            "at": utc_now(), "from": before, "to": after, "gate": gate, "result": result, "detail": detail,
        })
        self._flush()

    def _flush(self) -> None:
        self.manifest_path.write_text(
            json.dumps({"schema": "leo.provenanceManifest/1.0", "artifacts": self.entries}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        self.state_log_path.write_text(
            json.dumps({"schema": "leo.stateTransitions/1.0", "transitions": self.transitions}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def artifact_ref(path: str | Path, artifact_id: str) -> dict[str, str]:
    return {"artifactId": artifact_id, "sha256": sha256_file(path)}
