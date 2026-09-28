"""Read-only, offline verification and immutable export of research evidence."""
from pathlib import Path
import json
import shutil

from pinn.experiments.common import sha256_file
from pinn.research.storage import read as load_json
from pinn.governance.trust_loop import (validate_claim_gate_decision, validate_trust_vector,
    validate_run_record, validate_problem_definition)


def contained(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(p in ("..", ".") for p in rel.parts):
        raise ValueError("EVIDENCE_PATH_INVALID")
    path = root / rel
    if not path.resolve().is_relative_to(root):
        raise ValueError("EVIDENCE_PATH_INVALID")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("EVIDENCE_LINK_FORBIDDEN")
    return path


def read_ref(root, ref):
    path = contained(root, ref["artifactId"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("EVIDENCE_HASH_MISMATCH")
    return load_json(path)


def tree_hashes(root, exclude=("PACKAGE_MANIFEST.json",)):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        contained(root, rel)
        if path.is_file() and rel not in exclude:
            result[rel] = sha256_file(path)
    return result


def verify_package(root):
    manifest = load_json(Path(root) / "PACKAGE_MANIFEST.json")
    expected = manifest["fileHashes"]
    if not expected or "PACKAGE_MANIFEST.json" in expected or tree_hashes(root) != expected:
        raise ValueError("PACKAGE_INTEGRITY_FAILED")
    return manifest


def verify_references(root, value):
    """Resolve every physical pointer, including pointers inside individual checks."""
    if isinstance(value, dict):
        if "artifactId" in value and "sha256" in value:
            read_ref(root, value)
        else:
            for child in value.values():
                verify_references(root, child)
    elif isinstance(value, list):
        for child in value:
            verify_references(root, child)


def verify_attempt(root):
    """Only an explicit current pointer can supply a product's displayed claim."""
    root = Path(root)
    manifest = load_json(root / "PROVENANCE_MANIFEST.json")["artifacts"]
    entries = {e["artifactId"]: e for e in manifest}
    if len(entries) != len(manifest):
        raise ValueError("DUPLICATE_ARTIFACT")
    for entry in manifest:
        path = contained(root, entry["artifactId"])
        if sha256_file(path) != entry["sha256"]:
            raise ValueError("EVIDENCE_HASH_MISMATCH: " + entry["artifactId"])
        if any(parent not in entries for parent in entry.get("parentArtifactIds", [])):
            raise ValueError("MISSING_EVIDENCE_PARENT")
    summary = load_json(root / "RUN_SUMMARY.json")
    if not summary.get("currentTrustVectorRef"):
        return {"scientificState": summary["finalState"], "allowedClaims": [], "verified": True,
                "reason": "No current claim decision; no accuracy claim is permitted."}
    vector = read_ref(root, summary["currentTrustVectorRef"])
    decision = read_ref(root, summary["currentDecisionRef"])
    verify_references(root, vector["dimensions"])
    # trustVectorRef uses a logical record ID; the summary holds its physical pointer.
    if decision["trustVectorRef"]["sha256"] != summary["currentTrustVectorRef"]["sha256"]:
        raise ValueError("DECISION_VECTOR_HASH_MISMATCH")
    verify_references(root, decision["allowedClaims"])
    verify_references(root, decision["weakestLink"])
    pdef = load_json(root / "problem_definition.json")
    ledger = load_json(root / "claim_set_ledger.json")
    record = load_json(root / "run_record.json")
    identity = load_json(root / "identity.json")
    sets = {role: load_json(root / "sets" / (role + ".json")) for role in ("train", "dev", "phys", "claim")}
    errors = validate_problem_definition(pdef, claim_set_events=ledger, evaluation_sets=sets)
    errors += validate_run_record(record) + validate_trust_vector(vector, pdef)
    errors += validate_claim_gate_decision(decision, vector, pdef, claim_set_events=ledger,
                                          run_records={record["runId"]: record})
    if record["codeHash"] != identity["codeHash"] or decision["codeHash"] != identity["codeHash"]:
        errors.append("method identity mismatch")
    if any(record[key] != pdef[key] for key in ("problemId", "revision", "specHash")):
        errors.append("run and problem identity mismatch")
    if any(record[key] != identity[key] for key in ("codeManifest", "environment", "environmentId")):
        errors.append("run and execution identity mismatch")
    if errors:
        raise ValueError("CLAIM_VALIDATION_FAILED: " + "; ".join(errors))
    return {"scientificState": summary["finalState"], "verified": True,
            "allowedClaims": [c["level"] for c in decision["allowedClaims"]],
            "blockedClaims": decision["blockedClaims"], "dimensions": vector["dimensions"],
            "decisionRef": summary["currentDecisionRef"], "specHash": pdef["specHash"], "codeHash": identity["codeHash"]}


def export_tree(source, destination, *, source_root=None, source_manifest=()):
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("EXPORT_DESTINATION_EXISTS_OR_NESTED")
    before = tree_hashes(source, exclude=())
    shutil.copytree(source, destination)
    if tree_hashes(destination, exclude=()) != before or tree_hashes(source, exclude=()) != before:
        raise ValueError("EXPORT_SOURCE_CHANGED")
    if source_root is not None:
        source_root = Path(source_root)
        for entry in source_manifest:
            src = contained(source_root, entry["path"])
            if sha256_file(src) != entry["sha256"]:
                raise ValueError("EXPORT_CODE_IDENTITY_CHANGED")
            target = contained(destination, "source/" + entry["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        # PRELOCK also reads the amendment register and Git attributes.
        for src in [source_root / ".gitattributes", *(source_root / "governance/AMENDMENTS").glob("*.md")]:
            target = destination / "source" / src.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        (destination / "REPRODUCE.md").write_text(
            "# 独立复现\n\n首先在 source 目录用不含 Torch 的 Python 也可验证证据：\n\n"
            "`python -m pinn.research.worker verify --task-root ..`\n\n"
            "复现需要独立安装的 Python 科学环境，安装 source/pinn/research/requirements-science.lock。"
            "保留原包不变，在新的输出目录执行。先预览再明确执行：\n\n"
            "`python -m pinn.research.reproduce --package .. --out <新的绝对路径>`\n\n"
            "审阅预览后追加 `--execute`。程序只运行复现所需 Gate 1–4，不重开 Claim 集。"
            "输出的 reproduction_report.json 是复现证据，不自动提升原实验 Claim。\n",
            encoding="utf-8")
    (destination / "PACKAGE_MANIFEST.json").write_text(json.dumps({"packageType": "LEO_RESEARCH_EVIDENCE/1",
        "fileHashes": tree_hashes(destination)}, ensure_ascii=False, indent=2), encoding="utf-8")
    verify_package(destination)
    return destination
