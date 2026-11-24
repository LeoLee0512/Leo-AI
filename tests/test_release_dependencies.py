"""Release dependencies must reject changed, missing, and undeclared bytes."""
import json
import pytest
from tools import science_environment as science


@pytest.fixture
def wheelhouse(tmp_path, monkeypatch):
    lock = tmp_path / "science.lock"
    lock.write_text("numpy==2.4.5\n")
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    wheel = wheels / "numpy.whl"
    wheel.write_bytes(b"registered wheel bytes")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"requirements_sha256": science.sha(lock), "wheels": [
        {"filename": wheel.name, "package": "numpy", "version": "2.4.5",
         "size": wheel.stat().st_size, "sha256": science.sha(wheel)}]}))
    for name, value in (("LOCK", lock), ("WHEELS", wheels), ("MANIFEST", manifest)):
        monkeypatch.setattr(science, name, value)
    assert science.verify_wheelhouse() == []
    return wheel, lock


@pytest.mark.parametrize("mutation", ["changed", "missing", "extra", "lock"])
def test_science_wheelhouse_rejects_drift(wheelhouse, mutation):
    wheel, lock = wheelhouse
    if mutation == "changed":
        wheel.write_bytes(b"tampered wheel contents")
    elif mutation == "missing":
        wheel.unlink()
    elif mutation == "extra":
        (wheel.parent / "undeclared.whl").write_bytes(b"extra")
    else:
        lock.write_text("numpy==2.4.6\n")
    assert science.verify_wheelhouse(), mutation
