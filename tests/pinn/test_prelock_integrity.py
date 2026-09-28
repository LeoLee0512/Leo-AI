"""Reject corrupt candidates without creating a formal spec or running Gates."""
import copy
import hashlib
from dataclasses import replace
import json
from pathlib import Path
import shutil
import struct

import pytest

from pinn.governance.canonical import canonical_bytes, validate_canonical_json
from pinn.governance.prelock import PrelockPaths, declared_constitution_version, run_prelock

ROOT = Path(__file__).resolve().parents[2]
PATHS = PrelockPaths.defaults(ROOT)


def candidate(tmp_path, kind, mutate):
    path = getattr(PATHS, kind)
    obj = json.loads(path.read_text(encoding="utf-8"))
    mutate(obj)
    out = tmp_path / path.name
    out.write_bytes(canonical_bytes(obj))
    return run_prelock(replace(PATHS, **{kind: out}))


def test_original_candidate_is_prelock_only():
    result = run_prelock(PATHS)
    assert result["prelockStatus"] == "PASS"
    assert result["hashLockExecuted"] is result["trainingExecuted"] is result["p2Entered"] is False
    assert not (ROOT / "specs/poisson-1d/v1.0/lock.json").exists()


@pytest.mark.parametrize("mutate", [
    lambda s: s["equations"]["value"].update(forcing="f(x) = 0"),
    lambda s: s["equations"]["value"].update(governing="u''(x) = f(x)"),
    lambda s: s["boundaryConditions"]["value"][0].update(g=1.),
    lambda s: s["domain"]["value"].update(boundary=[0., 2.]),
    lambda s: s["acceptanceCriteria"].update(value=s["acceptanceCriteria"]["value"][:1]),
    lambda s: s["acceptanceCriteria"]["value"][0].update(threshold=1.),
    lambda s: s["acceptanceCriteria"]["value"][0].update(level="SHOULD"),
    lambda s: s["validationMetrics"]["value"][0].update(definition="training loss"),
    lambda s: s["validationMetrics"]["value"][0].update(grid="training"),
    lambda s: s["referenceSolution"]["value"]["primary"]["provenance"].update(evaluatorCodeSha256="0" * 64),
    lambda s: s["referenceSolution"]["value"]["primary"]["provenance"].update(evaluatorSourcePath="../external.py"),
    lambda s: s.update(validationMetrics=None),
    lambda s: s.update(acceptanceCriteria={"applicability": "APPLICABLE", "value": 3}),
    lambda s: s["acceptanceCriteria"]["value"][0].update(metricRef=[]),
    lambda s: s["validationMetrics"]["value"][0].update(id=[]),
    lambda s: s["trainingDomain"]["value"].update(collocation="(2,3)"),
    lambda s: s["trainingDomain"]["value"].update(adaptivePool="(2,3)"),
    lambda s: s["units"].update(value="seconds and Kelvin"),
    lambda s: s["independentVariables"].update(value=[{"symbol": "t", "meaning": "time", "networkInputIndex": 0}]),
    lambda s: s["targetQuantities"].update(value=[]),
])
def test_bad_spec_fails_without_crashing(tmp_path, mutate):
    result = candidate(tmp_path, "spec", mutate)
    assert result["prelockStatus"] == "FAIL"
    assert result["checks"]["spec"]["errors"]


@pytest.mark.parametrize("mutate", [
    lambda p: p["seeds"].update(values=[1, 2, 3, 4, 5]),
    lambda p: p["canonicalExecutor"].update(dtype="float32"),
    lambda p: p["boundarySet"].update(points=[0, 2]),
    lambda p: p["fdmProtocol"].update(nSequence=[4]),
    lambda p: p["antiCollision"].update(tolerance=-1.),
    lambda p: p["numerics"].update(epsilon=1.),
    lambda p: p["pointwiseGrid"]["artifact"].update(path="../CGL2000.npy"),
    lambda p: p["quadrature"]["generatorProvenance"].update(generatorImplementationSha256="0" * 64),
    lambda p: p["gate2a"]["checks"][0].update(tolerance=1.),
    lambda p: p["pointwiseGrid"].update(includesEndpoints=1),
])
def test_bad_protocol_fails(tmp_path, mutate):
    assert candidate(tmp_path, "protocol", mutate)["prelockStatus"] == "FAIL"


@pytest.mark.parametrize("raw", [b'{"x": NaN}\n', b'{"x": Infinity}\n', b'{"x": -Infinity}\n',
                                b'{"x": 1e999}\n', b'{"x": 1, "x": 2}\n', b'\xef\xbb\xbf{}\n',
                                b'{}\r\n', b'{}', b'{}\n\n'])
def test_ambiguous_or_noncanonical_bytes_rejected(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    assert not validate_canonical_json(path).passed


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_writer_refuses_nonfinite(value):
    with pytest.raises(ValueError):
        canonical_bytes({"metric": value})


def test_missing_evidence_is_failure(tmp_path):
    result = run_prelock(replace(PATHS, spec=tmp_path / "missing.json"))
    assert result["prelockStatus"] == "FAIL"


def test_changed_constitution_is_not_accepted(tmp_path):
    changed = tmp_path / "constitution.md"
    changed.write_bytes(PATHS.constitution.read_bytes() + b"Changed\n")
    assert run_prelock(replace(PATHS, constitution=changed))["prelockStatus"] == "FAIL"


@pytest.mark.parametrize("mutate", [
    lambda m: m["cases"][0]["subcases"][0]["construction"]["frozenParameters"].update(seeds=[1, 2, 3, 4, 5]),
    lambda m: m["cases"][1]["subcases"][0]["expected"].update(gateStatus={"G3": "PASS"}),
    lambda m: m["cases"][7]["subcases"][0]["expected"].update(stopTheLine=False),
    lambda m: m["cases"][-1]["subcases"][0]["expected"]["claimStatus"].update(C2="SUPPORTED"),
    lambda m: m["cases"][-3]["subcases"][0]["expected"]["claimStatus"].update(C1="BLOCKED"),
    lambda m: m["expectedVerdictRegistration"].update(declaredBeforeFirstExecution=False),
])
def test_expected_verdicts_and_seed_preregistration_cannot_be_relabelled(tmp_path, mutate):
    assert candidate(tmp_path, "manifest", mutate)["prelockStatus"] == "FAIL"


def test_hash_consistent_quadrature_replacement_is_rejected(tmp_path):
    for directory in ("governance", "pinn", "adversarial", "specs"):
        shutil.copytree(ROOT / directory, tmp_path / directory, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / ".gitattributes", tmp_path / ".gitattributes")
    paths = PrelockPaths.defaults(tmp_path)
    protocol = json.loads(paths.protocol.read_text(encoding="utf-8"))
    quadrature = protocol["quadrature"]
    record = quadrature["artifacts"]["weights"]
    path = tmp_path / record["path"]
    fake_weights = struct.pack("<512d", *([1 / 512] * 512))
    path.write_bytes(path.read_bytes()[:-4096] + fake_weights)
    record["artifactSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    record["dataSha256"] = hashlib.sha256(fake_weights).hexdigest()
    node_bytes = (tmp_path / quadrature["artifacts"]["nodes"]["path"]).read_bytes()[-4096:]
    quadrature["combinedDataSha256"] = hashlib.sha256(node_bytes + fake_weights).hexdigest()
    paths.protocol.write_bytes(canonical_bytes(protocol))
    result = run_prelock(paths)
    assert result["prelockStatus"] == "FAIL"
    assert any("contract" in error for error in result["checks"]["protocol"]["errors"])


@pytest.mark.parametrize("data", [b"\x93NUMPY\x01\x00", b"not an array", b"\x93NUMPY\x01\x00\xff\xff"])
def test_truncated_npy_produces_structured_failure(tmp_path, data):
    for directory in ("governance", "pinn", "adversarial", "specs"):
        shutil.copytree(ROOT / directory, tmp_path / directory, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / ".gitattributes", tmp_path / ".gitattributes")
    (tmp_path / "specs/poisson-1d/v1.0/assets/CGL2000.npy").write_bytes(data)
    result = run_prelock(PrelockPaths.defaults(tmp_path))
    assert result["prelockStatus"] == "FAIL"
    assert any("artifact invalid" in error for error in result["checks"]["protocol"]["errors"])


# ------------------------------------------ Constitution version binding (A-0001, 1.1)

def test_drafts_must_bind_the_version_the_constitution_declares(tmp_path):
    """A 1.0 draft against the 1.2 Constitution is a stale binding, not a supported alternative."""

    for kind in ("spec", "protocol", "lock_draft"):
        result = candidate(tmp_path, kind, lambda obj: obj.update(constitutionVersion="1.0"))
        assert result["prelockStatus"] == "FAIL"
        assert any("declares 1.2" in error for error in result["checks"]["constitutionBinding"]["errors"])
    result = candidate(tmp_path, "lock_draft", lambda obj: obj.update(constitutionVersion="9.0"))
    assert result["prelockStatus"] == "FAIL"


def test_constitution_without_a_declared_version_is_rejected(tmp_path):
    text = PATHS.constitution.read_bytes().decode("utf-8")
    stripped = tmp_path / "constitution.md"
    stripped.write_bytes(text.replace("| Version | 1.2 |", "| Edition | first |").encode("utf-8"))
    result = run_prelock(replace(PATHS, constitution=stripped))
    assert result["prelockStatus"] == "FAIL"
    assert any("declares no version" in error for error in result["checks"]["constitutionBinding"]["errors"])
    assert declared_constitution_version(PATHS.constitution.read_bytes()) == "1.2"
