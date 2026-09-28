"""The annular Poisson experiment runner (Geometry Lift 1).

Parallel to ``pinn/experiments2d/runner2d.py`` rather than a rewrite of it: the square
experiment is CLOSED at C2 and changing its runner would move the code identity its
results are bound to (the same precedent the 2D round set for the 1D runner).

What is geometry-specific lives in the modules this one calls; what is governance is
imported unchanged: the artifact store, the claim-set ledger and its derived status, the
sample registry, the state machine, the trust vector, the claim gate, PRELOCK and the
code-identity completeness check.

    python -m pinn.experiments_annulus.runner_annulus register-pool --problem-id ... --members ...
    python -m pinn.experiments_annulus.runner_annulus attempt --config ... --attempt-id ...
    python -m pinn.experiments_annulus.runner_annulus redteam --attempt ...
    python -m pinn.experiments_annulus.runner_annulus judge-reproduction --original ... --reproduction ...
    python -m pinn.experiments_annulus.runner_annulus apply-g6 --attempt ... --reproduction ...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from pinn.experiments.common import (
    CODE_IDENTITY_FILES,
    CODE_IDENTITY_PREFIXES,
    DECISION_SURFACES,
    ArtifactStore,
    assert_code_identity_complete,
    code_hash_from_manifest,
    code_manifest,
    environment_fingerprint,
    environment_identity,
    git_head,
    load_json,
    sha256_file,
    utc_now,
    workspace_dirty_paths,
)
from pinn.experiments.diagnosis import observed_signatures
from pinn.governance.canonical import canonical_bytes, canonical_sha256
from pinn.governance.claim_set_ledger import derive_claim_set_state, make_event, validate_claim_set_ledger
from pinn.governance.evaluation_sets import sample_set_hash
from pinn.governance.prelock import PrelockPaths, run_prelock
from pinn.governance.state_machine import (
    GateStatus,
    WorkflowState,
    advance,
    enter_validation,
    gate5_status,
)
from pinn.governance.trust_loop import (
    problem_definition_spec_hash,
    trust_vector_statuses,
    validate_claim_gate_decision,
    validate_problem_definition,
    validate_run_record,
    validate_trust_vector,
)
from pinn.governance.trust_vector import CLAIM_LEVELS, TrustStatus, claim_gate, seed_set_id
from pinn.governance import annulus_contract as contract

from . import datasets_annulus as ds
from . import diagnostics_annulus as diagnostics
from . import gates_annulus as gates
from . import localized_error_annulus as localized
from . import pinn_torch_annulus as pinn
from . import parallel_annulus as parallel

#: The TrustStatus -> GateStatus map, identical to the one the square runner uses.
GATE_FROM_TRUST = {TrustStatus.PASS: GateStatus.PASS, TrustStatus.FAIL: GateStatus.FAIL,
                   TrustStatus.PARTIAL: GateStatus.PARTIAL, TrustStatus.BLOCKED: GateStatus.BLOCKED,
                   TrustStatus.NOT_CHECKED: GateStatus.BLOCKED}

EXECUTOR = "pinn.experiments_annulus.runner_annulus (Claude, captain)"
CONSTITUTION_VERSION = "1.2"
EXPERIMENT_DIR = Path("experiments/annulus")
LEDGER_DIR = EXPERIMENT_DIR / "ledger"
PROBLEMS_DIR = EXPERIMENT_DIR / "problems"
REGISTRY_PATH = EXPERIMENT_DIR / "sample_set_registry.json"
GEOMETRY_PATH = "pinn/geometry/annulus.py"
ANALYTIC_PATH = "pinn/reference/analytic_annulus.py"
FDM_PATH = "scientific_reference/annulus_polar_fdm.py"
CONTRACT_PATH = "pinn/governance/annulus_contract.py"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log(message: str) -> None:
    print(f"[{utc_now()}] {message}", flush=True)


def load_registry() -> dict[str, str]:
    return load_json(REGISTRY_PATH) if REGISTRY_PATH.exists() else {}


def register_sample_set(manifest: Mapping[str, Any]) -> tuple[str, str]:
    registry = load_registry()
    artifact, samples = canonical_sha256(manifest), sample_set_hash(manifest)
    if registry.get(artifact, samples) != samples:
        raise SystemExit(f"registry binds artifact {artifact[:12]} to another sample identity")
    registry[artifact] = samples
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return artifact, samples


def write_ledger(path: Path, events: Sequence[Mapping[str, Any]]) -> None:
    errors = validate_claim_set_ledger(events, sample_set_hashes=load_registry())
    if errors:
        raise SystemExit(f"claim-set ledger invalid: {errors}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(events), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def pool_members(problem_id: str) -> dict[str, Any]:
    path = PROBLEMS_DIR / f"{problem_id}-claim-pool.json"
    return load_json(path) if path.exists() else {"members": {}}


def derived_claim_status(events: Sequence[Mapping[str, Any]], *, problem_id: str, revision: int, artifact_hash: str,
                         sample_hash: str) -> tuple[str, Any]:
    """The lifecycle state of a claim set, derived from the LEDGER -- the only source of truth."""

    state = derive_claim_set_state(events, problem_id=problem_id, revision=revision,
                                   claim_set_sha256=artifact_hash, sample_set_hashes=load_registry())
    if sample_hash in state.burnt_samples:
        return "BURNT", state
    return state.status, state


def claim_grids(name: str, member: Mapping[str, Any], boundary_nodes: int) -> dict[str, Any]:
    quadrature_points, quadrature_weights = ds.claim_quadrature(
        int(member["quadratureRadialOrder"]), int(member["quadratureAngularCount"]), float(member["angularOffset"]))
    pointwise_points = ds.claim_pointwise(int(member["pointwiseCglCount"]), int(member["pointwiseAngularCount"]),
                                          float(member["pointwiseAngularOffset"]))
    boundary = ds.boundary_sets(boundary_nodes)
    return {"label": name, "member": dict(member),
            "quadraturePoints": quadrature_points, "quadratureWeights": quadrature_weights,
            "pointwisePoints": pointwise_points,
            "boundary": {component: {"points": block["points"], "weights": block["weights"]}
                         for component, block in boundary.items()}}


# ------------------------------------------------------------------ ProblemDefinition

def build_problem_definition(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]], *, problem_id: str,
                             revision: int, root: Path, frozen_at: str) -> dict[str, Any]:
    from pinn.geometry import annulus as geo

    geometry_ref = {"artifactId": GEOMETRY_PATH, "sha256": sha256_file(root / GEOMETRY_PATH)}
    analytic_ref = {"artifactId": ANALYTIC_PATH, "sha256": sha256_file(root / ANALYTIC_PATH)}
    fdm_ref = {"artifactId": FDM_PATH, "sha256": sha256_file(root / FDM_PATH)}
    pre = config["preregistration"]
    document = {
        "schemaVersion": "pinn.problemDefinition/1.2",
        "problemId": problem_id,
        "revision": revision,
        "pde": {"form": "strong", "transient": False,
                "equations": [{"name": "poisson-annulus", "expressionRef": analytic_ref,
                               "independentVars": ["x", "y"], "dependentVars": ["u"]}]},
        "boundaryConditions": [
            {"name": "outer-dirichlet", "type": "dirichlet", "regionRef": "outerBoundary",
             "expressionRef": analytic_ref, "enforcement": "hard"},
            {"name": "inner-dirichlet", "type": "dirichlet", "regionRef": "innerBoundary",
             "expressionRef": analytic_ref, "enforcement": "hard"},
        ],
        # The ProblemDefinition schema's ``domainType`` vocabulary is
        # {interval, rectangle, disk, mesh, other}: it has no annulus, and its geometry
        # object takes no extra properties. Rather than widen a governance schema shared
        # with two CLOSED experiments, the annulus is expressed through the escape hatch
        # the schema already provides -- ``regions[].params``, a free-form object -- with
        # ``domainType: "other"``. The gap itself is reported as an AMENDMENT CANDIDATE
        # (add "annulus" to the vocabulary and a typed geometry block); it is not patched
        # here, and nothing about the run depends on the missing keyword.
        "geometry": {"domainType": "other", "dimension": 2, "regions": [
            {"id": "interior", "description": "a^2 < x^2 + y^2 < 1 (curved, multiply connected)",
             "params": {"geometryType": "annulus", "geometryId": geo.GEOMETRY["geometryId"],
                        "multiplyConnected": True, "innerRadius": geo.INNER_RADIUS,
                        "outerRadius": geo.OUTER_RADIUS, "membership": geo.GEOMETRY["membership"],
                        "equation": "-(u_xx+u_yy)(x,y)=f(x,y);a^2<x^2+y^2<1;u=0 on r=a and r=1",
                        "areaUniformTransform": geo.GEOMETRY["areaUniformRadialTransform"],
                        "quadratureJacobian": geo.GEOMETRY["quadratureJacobian"],
                        "contractRef": geometry_ref,
                        "schemaNote": "domainType 'other' because the schema vocabulary has no annulus; "
                                      "AMENDMENT CANDIDATE, not patched in this round"}},
            {"id": "outerBoundary", "description": "x^2 + y^2 = 1",
             "params": {"radius": geo.OUTER_RADIUS, "identity": "x^2 + y^2 = 1",
                        "outwardNormal": "(x, y) / R -- away from the origin"}},
            {"id": "innerBoundary", "description": "x^2 + y^2 = a^2",
             "params": {"radius": geo.INNER_RADIUS, "identity": "x^2 + y^2 = a^2",
                        "outwardNormal": "-(x, y) / a -- into the hole"}},
            {"id": "hole", "description": "x^2 + y^2 < a^2 -- NOT part of the domain",
             "params": {"radius": geo.INNER_RADIUS, "excluded": True}}]},
        "parameters": [{"name": "inner_radius_a", "value": geo.INNER_RADIUS, "unitRef": "1"},
                       {"name": "outer_radius_R", "value": geo.OUTER_RADIUS, "unitRef": "1"},
                       {"name": "modulation_amplitude", "value": 0.2, "unitRef": "1"}],
        "units": {"system": "nondimensional", "entries": [
            {"quantity": "length", "unit": "1", "symbolRef": "x"}, {"quantity": "field", "unit": "1", "symbolRef": "u"}]},
        "nondimensionalization": {"applied": False, "scales": [],
                                  "notes": "posed dimensionless by construction (annulus spec v1.0)"},
        "variables": [
            {"name": "x", "role": "independent", "domainRange": [-1.0, 1.0], "unitRef": "1"},
            {"name": "y", "role": "independent", "domainRange": [-1.0, 1.0], "unitRef": "1"},
            {"name": "u", "role": "dependent", "domainRange": [-1.0, 1.0], "unitRef": "1"},
        ],
        "referenceSolution": {"sources": [
            {"sourceId": "src-analytic", "method": "analytical", "evidenceLevel": "A",
             "independenceDeclaration": True, "provenance": analytic_ref},
            {"sourceId": "src-polar-fdm", "method": "numerical", "evidenceLevel": "B",
             "independenceDeclaration": True, "provenance": fdm_ref},
        ], "primarySourceId": "src-analytic"},
        "checkApplicability": [dict(entry) for entry in gates.REGISTRY],
        "preregistration": {"errorNorm": "relativeL2", "epsilonSpec": float(pre["epsilonSpec"]),
                            "seedRuns": int(config["seedProtocol"]["runs"]),
                            "seedFactors": ["init", "sample", "batch"],
                            "worstSeedFactor": float(pre["worstSeedFactor"]),
                            "dispersionLimit": float(pre["dispersionLimit"])},
        "evaluationSets": {
            "train": {"artifactId": sets["train"]["artifactId"], "sha256": canonical_sha256(sets["train"])},
            "dev": {"artifactId": sets["dev"]["artifactId"], "sha256": canonical_sha256(sets["dev"])},
            "claim": {"artifactId": sets["claim"]["artifactId"], "sha256": canonical_sha256(sets["claim"])},
            "phys": {"artifactId": sets["phys"]["artifactId"], "sha256": canonical_sha256(sets["phys"])},
            "minSeparation": float(config["sets"]["minSeparation"]),
            "claimSetStatus": "SEALED",
            "claimSetHistory": [],
        },
        "status": "FROZEN",
        "frozenAt": frozen_at,
        "frozenBy": EXECUTOR,
    }
    document["specHash"] = problem_definition_spec_hash(document)
    return document


def apply_ledger_state(pdef: dict[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    state = derive_claim_set_state(events, problem_id=pdef["problemId"], revision=pdef["revision"],
                                   claim_set_sha256=pdef["evaluationSets"]["claim"]["sha256"],
                                   sample_set_hashes=load_registry())
    sets = pdef["evaluationSets"]
    sets["claimSetStatus"] = state.status if state.status in ("SEALED", "OPENED") else "SEALED"
    sets["claimSetHistory"] = list(state.history)
    if state.status == "OPENED":
        sets["claimSetOpenedAtRevision"] = state.opened_at_revision
    else:
        sets.pop("claimSetOpenedAtRevision", None)
    pdef["specHash"] = problem_definition_spec_hash(pdef)
    return pdef


def dimension_entry(status: TrustStatus, checks: Sequence[Mapping[str, Any]], evidence: Sequence[Mapping[str, str]], *,
                    notes: str = "", extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    # Schema 1.2 (runner2d.dimension_entry). Until 2026-09-26 this wrote the pre-1.2 layout
    # (``evidenceRefs``), which the validator rejects before running any substantive check.
    entry: dict[str, Any] = {"status": status.value}
    if status is TrustStatus.NOT_CHECKED:
        return entry
    entry.update({"evidencePointers": [dict(e) for e in evidence], "judgedAt": utc_now(), "judgedBy": EXECUTOR,
                  "checks": [dict(c) for c in checks]})
    if notes:
        entry["notes"] = notes
    if extra:
        entry.update(extra)
    return entry


def statuses_of(dimensions: Mapping[str, Mapping[str, Any]]) -> dict[str, TrustStatus]:
    return {name: TrustStatus(entry["status"]) for name, entry in dimensions.items()}


DIMENSIONS = ("math", "impl", "train", "physics", "external", "repro")

STATEMENTS = {
    "C0": "The frozen annular Poisson problem definition is mathematically consistent and the implementation computes "
          "this problem (math, impl PASS; two-component hard boundary enforcement and polar derivatives verified).",
    "C1": "Under the frozen training protocol the annulus PINN training is reliable across the preregistered seed set "
          "(train PASS); accuracy is not asserted.",
    "C2": "Every seed model agrees with the analytic reference within the preregistered ACA-1..ACA-9 on the opened "
          "blind claim member and satisfies the annulus physics checks; Tier-1 Red Team maintained; independent "
          "reproduction confirmed.",
    "C3": "The C2 result holds across >= 5 independently qualified runs of the same method identity.",
}


def build_decision(vector_doc: Mapping[str, Any], tv_ref: Mapping[str, str], *, pdef: Mapping[str, Any],
                   code_hash: str, events: Sequence[Mapping[str, Any]], run_record: Mapping[str, Any],
                   statement_ref: Mapping[str, str], evidence_refs: Sequence[Mapping[str, str]],
                   decision_id: str) -> tuple[dict[str, Any], Any]:
    """ClaimGateDecision (schema 1.2, runner2d.decision_document) -- validated, never written here.

    Shared by the attempt's own finish(), its pre-opening preflight and the closure steps,
    so the one construction that r2 crashed in is exercised long before a claim set is.
    """
    gate = claim_gate(trust_vector_statuses(vector_doc), evidence_level="A", spec_hash=pdef["specHash"],
                      code_hash=code_hash, exploratory=False, stop_the_line=False)
    decision = {
        "schemaVersion": "pinn.claimGateDecision/1.2", "decisionId": decision_id,
        "problemId": pdef["problemId"], "revision": pdef["revision"], "specHash": pdef["specHash"],
        "codeHash": code_hash, "claimSetSha256": pdef["evaluationSets"]["claim"]["sha256"],
        "ledgerHead": events[-1]["eventId"],
        "trustVectorRef": {"artifactId": vector_doc["recordId"], "sha256": tv_ref["sha256"]},
        "referenceEvidenceLevel": "A", "runMode": "FORMAL", "qualifiedC2Runs": [],
        "allowedClaims": [{"level": level, "statementRef": dict(statement_ref),
                           "evidenceRefs": [dict(e) for e in evidence_refs] or [dict(tv_ref)],
                           "failureConditions": [
                               {"condition": "the frozen ProblemDefinition, reference or code identity is revised",
                                "consequence": "INVALIDATE_DECISION"},
                               {"condition": "a later independent reproduction falls outside the preregistered "
                                             "tolerance", "consequence": "DOWNGRADE"}]}
                          for level in gate.allowed],
        "blockedClaims": [{"level": level, "reason": "; ".join(gate.blocked.get(level, ("not licensed",))),
                           "missingPreconditions": list(gate.blocked.get(level, ()))}
                          for level in CLAIM_LEVELS if level not in gate.allowed],
        "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value,
                        "evidenceRef": dict(tv_ref)},
        "generatedAt": utc_now(), "decidedBy": EXECUTOR,
    }
    errors = validate_claim_gate_decision(decision, vector_doc, pdef, claim_set_events=events,
                                          run_records={run_record["runId"]: run_record})
    if errors:
        raise SystemExit(f"ClaimGateDecision invalid: {errors}")
    return decision, gate


class AttemptAnnulus:
    """One formal attempt of the annular Poisson experiment."""

    def __init__(self, *, config_path: Path, attempt_id: str, problem_id: str, revision: int, out_root: Path,
                 claim_pool_member: str | None = None, seed_offset: int = 0, reproduction_of: str | None = None,
                 stop_after_gate: int | None = None, device: str = "cpu", workers: int = 1):
        self.root = repo_root()
        self.config_path = config_path
        self.config = load_json(config_path)
        self.attempt_id = attempt_id
        self.problem_id = problem_id
        self.revision = int(revision)
        self.claim_pool_member = claim_pool_member
        self.seed_offset = int(seed_offset)
        self.reproduction_of = reproduction_of
        self.stop_after_gate = stop_after_gate
        self.threads = int(self.config["optimizer"].get("threads", 1))
        # The training device is an EXECUTION parameter handed in by the caller, never read from
        # the frozen config: the config sits inside codeHash and the G6 reproduction must run the
        # SAME codeHash on a CPU-only environment. It is recorded in identity.json and in every
        # run record, and it changes acceleratorClass -- which is an environment field, as it should be.
        self.device = str(device)
        # Parallel processes are execution too (parallel_annulus.py): identical runs, side by side.
        self.workers = max(1, int(workers))
        self.store = ArtifactStore(out_root / attempt_id)
        self.ledger_path = LEDGER_DIR / f"{problem_id}.json"
        self.dimensions: dict[str, Any] = {}
        self.summary: dict[str, Any] = {"attemptId": attempt_id, "problemId": problem_id, "revision": revision,
                                        "reproductionOf": reproduction_of, "seedOffset": self.seed_offset}
        self.state = WorkflowState.DRAFT
        self.events: list[dict[str, Any]] = []
        self.gate_details: dict[str, Any] = {}

    # ------------------------------------------------------------ helpers

    def accelerator_class(self) -> str:
        """The environment field that the training device actually changes (Constitution 28.1)."""

        if not self.device.startswith("cuda"):
            return "cpu-only"
        import torch  # type: ignore[import-not-found]

        return "cuda-" + torch.cuda.get_device_name(torch.device(self.device))

    def vector(self) -> dict[str, TrustStatus]:
        return {d: TrustStatus(self.dimensions[d]["status"]) if d in self.dimensions else TrustStatus.NOT_CHECKED
                for d in DIMENSIONS}

    def save_state(self, state: WorkflowState) -> None:
        self.state = state
        self.store.write_json("attempt_state.json", {"state": state.value, "at": utc_now()}, role="STATE")

    def move(self, before: WorkflowState, after: WorkflowState, *, gate: int | None, result: str,
             detail: str = "") -> None:
        self.store.transition(before.value, after.value, gate=gate, result=result, detail=detail)
        self.save_state(after)
        log(f"{before.value} -> {after.value} (gate {gate}, {result}) {detail}")

    def judge(self, dimension: str, checks: Sequence[Mapping[str, Any]], evidence: Sequence[Mapping[str, str]],
              **extra: Any) -> TrustStatus:
        status = gates.dimension_status(checks)
        notes = extra.pop("notes", "")
        if status is TrustStatus.PARTIAL and not notes:
            notes = "; ".join(c["reason"] for c in checks if c.get("status") == "PARTIAL")
        self.dimensions[dimension] = dimension_entry(status, checks, evidence, notes=notes, extra=extra or None)
        return status

    # ------------------------------------------------------------ phases

    def phase_identity(self) -> None:
        config_rel = self.config_path.resolve().relative_to(self.root).as_posix()
        dirty = workspace_dirty_paths(self.root)
        declared = [str(path).replace("\\", "/") for path in self.config.get("codeIdentityExtraFiles", [])]
        extra = [config_rel, *declared]
        manifest = code_manifest(self.root, extra)
        assert_code_identity_complete(manifest, self.root, extra_required=extra)
        self.code_hash = code_hash_from_manifest(manifest)
        self.code_manifest = manifest
        self.environment = environment_fingerprint(accelerator_class=self.accelerator_class())
        self.environment_id = environment_identity(self.environment)
        identity = {"gitHead": git_head(self.root), "dirtyCodeIdentityPaths": dirty, "codeHash": self.code_hash,
                    "codeManifest": manifest, "configPath": config_rel, "configSha256": sha256_file(self.config_path),
                    "codeIdentityBoundary": {"prefixes": list(CODE_IDENTITY_PREFIXES), "files": list(CODE_IDENTITY_FILES),
                                             "declaredByRun": declared, "decisionSurfaces": list(DECISION_SURFACES)},
                    "environment": self.environment, "environmentId": self.environment_id, "python": sys.version,
                    "constitutionVersion": CONSTITUTION_VERSION, "seedOffset": self.seed_offset,
                    "spatialDimension": 2, "geometryId": contract.GEOMETRY["geometryId"],
                    "executionDevice": {"training": self.device, "evaluation": "cpu",
                                        "source": "command line (--device); NOT a config value",
                                        "note": "device is execution, not method: the same codeHash has to be "
                                                "runnable on a CPU-only environment for the G6 reproduction"},
                    "executionParallelism": {"workers": self.workers,
                                             "source": "command line (--workers); NOT a config value",
                                             "note": "each seed trains in its own process with the same arguments "
                                                     "it would get sequentially; results are identical bit for bit"}}
        self.store.write_json("identity.json", identity, role="IDENTITY")
        self.summary.update({"codeHash": self.code_hash, "environmentId": self.environment_id,
                             "gitHead": identity["gitHead"], "workspaceDirty": bool(dirty),
                             "configId": self.config["configId"], "trainingDevice": self.device})
        if dirty:
            log(f"WARNING: uncommitted code-identity changes {dirty}; this run has no valid codeHash (28.1)")
        prelock = run_prelock(PrelockPaths.defaults(self.root))
        self.store.write_json("prelock.json", prelock, role="GOVERNANCE_CHECK")
        self.summary["prelock"] = prelock["prelockStatus"]
        if prelock["prelockStatus"] != "PASS":
            raise SystemExit("PRELOCK FAIL: the attempt does not start")
        log(f"identity: codeHash={self.code_hash[:12]} env={self.environment_id[:12]} "
            f"device={self.device} accelerator={self.environment['acceleratorClass']} "
            f"PRELOCK={prelock['prelockStatus']}")

    def phase_problem(self) -> None:
        members = pool_members(self.problem_id)["members"]
        frozen_file = PROBLEMS_DIR / f"{self.problem_id}-r{self.revision}.json"
        if self.claim_pool_member is None and frozen_file.exists():
            frozen_claim = load_json(frozen_file)["evaluationSets"]["claim"]["sha256"]
            for name, member in members.items():
                if member["artifactHash"] == frozen_claim:
                    self.claim_pool_member = name
                    log(f"frozen revision {self.revision} names pool member {name}; using it")
        if not self.claim_pool_member:
            raise SystemExit("an annulus attempt must name a preregistered claim pool member (--claim-pool-member)")
        if self.claim_pool_member not in members:
            raise SystemExit(f"claim pool member {self.claim_pool_member!r} is not preregistered for {self.problem_id}")
        member = members[self.claim_pool_member]
        if member["designatedRevision"] != self.revision:
            raise SystemExit(f"{self.claim_pool_member} is designated for revision {member['designatedRevision']}, "
                             f"not {self.revision}")
        claim_manifest = ds.claim_pool_manifests({self.claim_pool_member: member["grid"]},
                                                 label=self.problem_id)[self.claim_pool_member]
        if (canonical_sha256(claim_manifest) != member["artifactHash"]
                or sample_set_hash(claim_manifest) != member["sampleSetHash"]):
            raise SystemExit("regenerated pool member differs from the preregistered manifest")
        # EARLY GUARD: ask the ledger, never the manifest's static status field, and ask it here --
        # before the isolation scan, before the gates and long before any training.
        ledger_events = load_json(self.ledger_path) if self.ledger_path.exists() else []
        ledger_status, _state = derived_claim_status(ledger_events, problem_id=self.problem_id, revision=self.revision,
                                                     artifact_hash=member["artifactHash"],
                                                     sample_hash=member["sampleSetHash"])
        self.summary["claimSetLedgerStatusAtStart"] = ledger_status
        if self.reproduction_of is None and ledger_status in ("OPENED", "BURNT"):
            raise SystemExit(f"{self.claim_pool_member} is {ledger_status} in the ledger "
                             f"(samples {member['sampleSetHash'][:12]}); a formal attempt cannot reuse it. The pool "
                             f"manifest's own status field ({member.get('initialStatus')}) is registration-time "
                             "information and is not consulted.")
        log(f"claim pool member {self.claim_pool_member}: ledger-derived status {ledger_status}")

        boundary_nodes = int(self.config["sets"]["boundaryNodes"])
        self.grids = claim_grids(self.claim_pool_member, member["grid"], boundary_nodes)
        self.boundary = ds.boundary_sets(boundary_nodes)
        self.sets = ds.build_sets(self.config, claim_points=ds.points_of(claim_manifest),
                                  claim_artifact_id=claim_manifest["artifactId"],
                                  claim_generator=claim_manifest["generator"])
        self.sets["claim"] = claim_manifest
        self.set_refs = {role: self.store.write_canonical(f"sets/{role}.json", doc, role="EVALUATION_SET")
                         for role, doc in self.sets.items()}
        claim_artifact, claim_samples = register_sample_set(self.sets["claim"])
        log("checking sample-level isolation and geometry membership of the four sets")
        isolation = ds.isolation_report(self.sets, min_separation=self.config["sets"]["minSeparation"])
        isolation["claimSampleSetHash"] = claim_samples
        isolation["antiCollision"] = ds.component_anti_collision(ds.points_of(self.sets["claim"]))
        self.store.write_json("sets/isolation.json", isolation, role="EVALUATION_SET_ISOLATION",
                              parents=[r["artifactId"] for r in self.set_refs.values()])
        if isolation["errors"]:
            raise SystemExit(f"evaluation sets are not isolated / not on the domain: {isolation['errors']}")
        self.summary["evaluationSets"] = {
            "sizes": {role: len(doc["samples"]) for role, doc in self.sets.items()},
            "sampleSetHashes": isolation["sampleSetHashes"], "claimSampleSetHash": claim_samples,
            "membership": isolation["membership"]}

        self.phys_points, self.phys_weights = ds.phys_grid(int(self.config["sets"]["physRadialOrder"]),
                                                           int(self.config["sets"]["physAngularCount"]))
        self.grids["physPoints"] = self.phys_points
        self.grids["physWeights"] = self.phys_weights
        self.store.write_json("sets/boundary.json", {
            "role": "boundary", "nodesPerComponent": boundary_nodes,
            "components": {component: {"radius": block["radius"], "points": [list(p) for p in block["points"]],
                                       "weights": block["weights"], "normals": [list(n) for n in block["normals"]],
                                       "rule": block["rule"]}
                           for component, block in self.boundary.items()},
            "note": "spec-known boundary coordinates of BOTH components (protocol L1 boundaryIdentityExempt). Each "
                    "component carries its own outward normal: outer away from the origin, inner into the hole.",
        }, role="BOUNDARY_SET")
        self.store.write_json("sets/phys_weights.json", {
            "radialOrder": self.config["sets"]["physRadialOrder"],
            "angularCount": self.config["sets"]["physAngularCount"],
            "weights": self.phys_weights,
            "quadratureArea": math.fsum(self.phys_weights)}, role="EVALUATION_SET")
        self.pool = ds.points_of(self.sets["train"])
        self.dev_points = ds.points_of(self.sets["dev"])

        if frozen_file.exists():
            pdef = load_json(frozen_file)
            for role, doc in self.sets.items():
                if pdef["evaluationSets"][role]["sha256"] != canonical_sha256(doc):
                    raise SystemExit(f"frozen ProblemDefinition names another {role} set than the regenerated one")
            log(f"reusing frozen ProblemDefinition {frozen_file.name} (frozenAt {pdef['frozenAt']})")
        else:
            pdef = build_problem_definition(self.config, self.sets, problem_id=self.problem_id,
                                            revision=self.revision, root=self.root, frozen_at=utc_now())
            frozen_file.parent.mkdir(parents=True, exist_ok=True)
            frozen_file.write_bytes(canonical_bytes(pdef))
            log(f"ProblemDefinition frozen to {frozen_file.name}")
        events = load_json(self.ledger_path) if self.ledger_path.exists() else []
        state = derive_claim_set_state(events, problem_id=self.problem_id, revision=self.revision,
                                       claim_set_sha256=claim_artifact, sample_set_hashes=load_registry())
        if state.status == "NEVER_SEALED":
            if claim_samples in state.burnt_samples:
                raise SystemExit(f"claim samples {claim_samples[:12]} are BURNT; refusing to seal")
            events.append(make_event(prev_event_id=events[-1]["eventId"] if events else "GENESIS",
                                     problemId=self.problem_id, revision=self.revision, specHash=pdef["specHash"],
                                     claimSetSha256=claim_artifact, sampleSetHash=claim_samples, event="SEALED",
                                     actor=EXECUTOR, at=utc_now()))
            log(f"claim set {claim_artifact[:12]} (samples {claim_samples[:12]}) SEALED")
        write_ledger(self.ledger_path, events)
        self.events = events
        pdef = apply_ledger_state(pdef, events)
        errors = validate_problem_definition(pdef, claim_set_events=events, evaluation_sets=self.sets,
                                             sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid: {errors}")
        self.pdef = pdef
        self.pdef_ref = self.store.write_canonical("problem_definition.json", pdef, role="PROBLEM_DEFINITION",
                                                   parents=[r["artifactId"] for r in self.set_refs.values()])
        self.store.register("claim_set_ledger.json", canonical_sha256(events), role="LEDGER", note=str(self.ledger_path))
        self.summary.update({"specHash": pdef["specHash"], "claimSetSha256": claim_artifact,
                             "claimSampleSetHash": claim_samples, "ledgerHead": events[-1]["eventId"],
                             "claimPoolMember": self.claim_pool_member})
        log(f"ProblemDefinition FROZEN specHash={pdef['specHash'][:12]} sizes={self.summary['evaluationSets']['sizes']}")

    def phase_upstream_gates(self) -> None:
        self.save_state(WorkflowState.DRAFT)
        g1 = gates.gate1_math(self.pdef, [self.pdef_ref])
        g1_ref = self.store.write_json("gate1_math.json", {"checks": g1}, role="GATE_RESULT",
                                       parents=[self.pdef_ref["artifactId"]])
        math_status = self.judge("math", g1, [g1_ref])
        after = advance(WorkflowState.DRAFT, 1, GATE_FROM_TRUST[math_status], self.vector())
        self.move(WorkflowState.DRAFT, after, gate=1, result=GATE_FROM_TRUST[math_status].value)
        if after is not WorkflowState.SPEC_LOCKED:
            raise SystemExit(f"Gate 1 did not pass: {after}")

        g2, g2_detail = gates.gate2_baseline(self.phys_points, self.boundary, [self.set_refs["phys"]])
        g2_ref = self.store.write_json("gate2_baseline.json", {"checks": g2, "detail": g2_detail}, role="GATE_RESULT",
                                       parents=[self.set_refs["phys"]["artifactId"]])
        g2_status = TrustStatus.PASS if all(c["status"] == "PASS" for c in g2) else TrustStatus.FAIL
        after = advance(WorkflowState.SPEC_LOCKED, 2, GATE_FROM_TRUST[g2_status], self.vector())
        self.move(WorkflowState.SPEC_LOCKED, after, gate=2, result=GATE_FROM_TRUST[g2_status].value)
        if after is not WorkflowState.BASELINE_VERIFIED:
            raise SystemExit(f"Gate 2 did not pass: {after}")

        g3, g3_detail = gates.gate3_implementation(self.config, self.sets, self.dev_points, self.grids,
                                                   self.boundary, [self.set_refs["dev"]])
        g3_ref = self.store.write_json("gate3_implementation.json", {"checks": g3, "detail": g3_detail},
                                       role="GATE_RESULT", parents=[self.set_refs["dev"]["artifactId"]])
        self.gate_details = {"gate2": g2_detail, "gate3": g3_detail}
        impl_status = self.judge("impl", g3, [g3_ref])
        after = advance(WorkflowState.BASELINE_VERIFIED, 3, GATE_FROM_TRUST[impl_status], self.vector())
        self.move(WorkflowState.BASELINE_VERIFIED, after, gate=3, result=GATE_FROM_TRUST[impl_status].value)
        if after is not WorkflowState.IMPLEMENTATION_VERIFIED:
            raise SystemExit(f"Gate 3 did not pass: {after}")

    def phase_training(self) -> None:
        sp = self.config["seedProtocol"]
        off = self.seed_offset
        triplets = [{"index": i, "init": sp["initBase"] + off + i, "sample": sp["sampleBase"] + off + i,
                     "batch": sp["batchBase"] + off + i} for i in range(int(sp["runs"]))]
        seed_values = sorted({v for t in triplets for v in (t["init"], t["sample"], t["batch"])})
        self.seed_values = seed_values
        ledger_ref = self.store.write_json("seed_ledger.json", {
            "registeredAt": utc_now(),
            "rule": f"init={sp['initBase']}+{off}+i, sample={sp['sampleBase']}+{off}+i, "
                    f"batch={sp['batchBase']}+{off}+i, i in 0..{sp['runs'] - 1}",
            "triplets": triplets, "seedSetId": seed_set_id(seed_values), "appendOnly": True,
            "note": "registered before the first run started (Constitution 10.1); no seed is dropped afterwards"},
            role="SEED_LEDGER")
        self.started_at = utc_now()
        self.runs = []
        run_refs = []
        jobs = [{"config": self.config, "pool": self.pool, "dev_points": self.dev_points,
                 "seeds": {k: triplet[k] for k in ("init", "sample", "batch")},
                 "collocation_count": int(self.config["sampling"]["collocationCount"]), "device": self.device}
                for triplet in triplets]
        log(f"training {len(jobs)} seed triplets with collocationCount={self.config['sampling']['collocationCount']} "
            f"on {self.device}, {self.workers} worker process(es)")
        trained = parallel.train_many(jobs, workers=self.workers, log=log)
        for triplet, run in zip(triplets, trained):
            run["runIndex"] = triplet["index"]
            run_refs.append(self.store.write_json(f"runs/run-{triplet['index']:02d}.json", run,
                                                  role="RAW_MODEL_PREDICTION",
                                                  parents=[ledger_ref["artifactId"],
                                                           self.set_refs["train"]["artifactId"]]))
            self.runs.append(run)
            log(f"  done: devRelL2={run['devRelL2']:.3e} completed={run['completed']} "
                f"nan={run['nanEncountered']} {run['elapsedSeconds']:.1f}s")
        self.finished_at = utc_now()
        self.run_refs = run_refs
        # Every evaluation below -- Gates 3-5, physics, the localized criterion, the plots -- runs on
        # the CPU whatever device produced the weights, so no gate number depends on the accelerator
        # and the CPU reproduction of Environment B compares like with like.
        self.models = [pinn.model_from_weights(self.config, run["weights"], threads=self.threads) for run in self.runs]
        self.write_run_record(claim_opened=False)

    def write_run_record(self, *, claim_opened: bool) -> None:
        evaluated = {"dev": self.pdef["evaluationSets"]["dev"]["sha256"]}
        if claim_opened:
            evaluated["claim"] = self.pdef["evaluationSets"]["claim"]["sha256"]
        record = {
            "schemaVersion": "pinn.runRecord/1.0", "runId": f"run-{self.attempt_id}", "problemId": self.problem_id,
            "revision": self.revision, "specHash": self.pdef["specHash"], "codeHash": self.code_hash,
            "codeManifest": self.code_manifest, "environment": self.environment,
            "environmentId": self.environment_id, "seeds": self.seed_values,
            "seedSetId": seed_set_id(self.seed_values), "evaluatedOn": evaluated,
            "startedAt": self.started_at, "finishedAt": max(self.finished_at, utc_now()), "executedBy": EXECUTOR,
        }
        errors = validate_run_record(record)
        if errors:
            raise SystemExit(f"RunRecord invalid: {errors}")
        self.run_record = record
        self.run_record_ref = self.store.write_canonical("run_record.json", record, role="RUN_RECORD",
                                                         parents=[r["artifactId"] for r in self.run_refs])

    def phase_gate4(self) -> WorkflowState:
        g4, detail = gates.gate4_training(self.runs, self.pdef["preregistration"], [self.set_refs["dev"]])
        detail["seedSetId"] = seed_set_id(self.seed_values)
        detail["devSetSha256"] = self.pdef["evaluationSets"]["dev"]["sha256"]
        g4_ref = self.store.write_json("gate4_training.json", {"checks": g4, "detail": detail}, role="GATE_RESULT",
                                       parents=[r["artifactId"] for r in self.run_refs])
        self.store.write_json("training_report.json", {
            "seedStatistics": detail["seedStatistics"], "perSeed": detail["perSeed"], "seedSetId": detail["seedSetId"],
            "devSetSha256": detail["devSetSha256"], "excludedRuns": [], "bestSeedReported": False,
            "config": {k: self.config[k] for k in ("network", "optimizer", "lossWeights", "sampling", "seedProtocol")},
        }, role="TRAINING_REPORT", parents=[g4_ref["artifactId"]])
        self.summary["training"] = detail["seedStatistics"]
        status = self.judge("train", g4, [g4_ref])
        result = GATE_FROM_TRUST[status]
        after = advance(WorkflowState.IMPLEMENTATION_VERIFIED, 4, result, self.vector())
        self.move(WorkflowState.IMPLEMENTATION_VERIFIED, after, gate=4, result=result.value,
                  detail=f"C_train={status.value}: {detail['seedStatistics']['successRate']} within epsilon_spec, "
                         f"median {detail['seedStatistics']['median']:.3e}")
        return after

    def phase_failure(self, gate: int = 4) -> None:
        criteria = self.config["signatureCriteria"]
        localized_criterion = criteria[localized.LOCALIZED_SIGNATURE]
        per_seed = [diagnostics.dev_diagnostics(model, self.dev_points, self.phys_points, self.phys_weights,
                                                self.boundary, int(localized_criterion["radialBins"]),
                                                int(localized_criterion["angularSectors"]), threads=self.threads)
                    for model in self.models]
        stats = load_json(self.store.root / "gate4_training.json")["detail"]["seedStatistics"]
        # ``observed_signatures`` is reused unchanged, and it still reads the retired 1D
        # constant (max bin / median bin > 3.0). That rule is NOT CALIBRATED for d >= 2, so
        # it is handed a threshold it can never cross and its entry is then replaced
        # outright by the preregistered acceptance-criterion trigger. The retired statistic
        # stays in the record as a diagnostic, never as a decision.
        shared_criteria = dict(criteria)
        shared_criteria[localized.LOCALIZED_SIGNATURE] = dict(
            criteria[localized.LOCALIZED_SIGNATURE],
            bins=int(localized_criterion["radialBins"]) * int(localized_criterion["angularSectors"]),
            maxBinToMedianBinRatio=math.inf,
            retiredForDimension=">=2")
        observed = observed_signatures(per_seed, stats, shared_criteria,
                                       float(self.pdef["preregistration"]["epsilonSpec"]))
        observed = localized.apply_localized_signature(observed, per_seed, criteria, dimension=2)
        observed["perSeedFields"] = [{"pointwiseAbsError": d["pointwiseAbsError"], "residuals": d["residuals"],
                                      "cellRms": d["cellRms"], "hotspot": d["hotspot"],
                                      "fluxPerComponent": d["fluxPerComponent"],
                                      "maxBoundaryAbsPerComponent": d["maxBoundaryAbsPerComponent"]}
                                     for d in per_seed]
        observed["devPoints"] = [list(p) for p in self.dev_points]
        claim_note = None
        if gate == 5 and (self.store.root / "gate5b_external.json").exists():
            g5b = load_json(self.store.root / "gate5b_external.json")
            claim_note = {"failedMustPerSeed": [m["failedMust"] for m in g5b["perSeed"]],
                          "note": "Gate 5 FAIL on the OPENED claim set; the signatures below are measured on "
                                  "D_dev / D_phys only"}
        ref = self.store.write_json("failure_record.json", {
            "state": WorkflowState.FAILURE_RECORDED.value, "gate": gate, "recordedAt": utc_now(),
            "claimSetVerdict": claim_note, "observedSignatures": observed["observedSignatures"],
            "rules": observed["rules"], "medians": observed["medians"], "perSeed": observed["perSeed"],
            "seedStatistics": stats, "retrainedInPlace": False, "constitutionVersion": CONSTITUTION_VERSION,
            "geometryId": contract.GEOMETRY["geometryId"],
        }, role="FAILURE_RECORD", parents=[r["artifactId"] for r in self.run_refs])
        self.store.write_json("dev_diagnostics.json", observed, role="DIAGNOSTICS", parents=[ref["artifactId"]])
        self.summary["failure"] = {"gate": gate, "observedSignatures": observed["observedSignatures"],
                                   "medians": observed["medians"]}
        log(f"FAILURE_RECORDED at Gate {gate}; observedSignatures={observed['observedSignatures']}")

    def phase_validation(self) -> WorkflowState:
        state = enter_validation(WorkflowState.TRAINING_COMPLETED)
        self.move(WorkflowState.TRAINING_COMPLETED, state, gate=None, result="ENTER_VALIDATION")
        g5a, detail_a = gates.physics_checks(self.models, self.phys_points, self.phys_weights, self.boundary,
                                             self.config["physicsThresholds"], [self.set_refs["phys"]],
                                             threads=self.threads)
        g5a_ref = self.store.write_json("gate5a_physics.json", {"checks": g5a, "detail": detail_a}, role="GATE_RESULT",
                                        parents=[self.set_refs["phys"]["artifactId"]]
                                                + [r["artifactId"] for r in self.run_refs])
        physics = self.judge("physics", g5a, [g5a_ref])
        self.preflight_decision()
        claim_sha = self.pdef["evaluationSets"]["claim"]["sha256"]
        claim_samples = self.summary["claimSampleSetHash"]
        self.events.append(make_event(prev_event_id=self.events[-1]["eventId"], problemId=self.problem_id,
                                      revision=self.revision, specHash=self.pdef["specHash"],
                                      claimSetSha256=claim_sha, sampleSetHash=claim_samples, event="OPENED",
                                      codeHash=self.code_hash, actor=EXECUTOR, at=utc_now()))
        write_ledger(self.ledger_path, self.events)
        self.store.register("claim_set_ledger.json", canonical_sha256(self.events), role="LEDGER",
                            note=str(self.ledger_path))
        self.pdef = apply_ledger_state(self.pdef, self.events)
        errors = validate_problem_definition(self.pdef, claim_set_events=self.events, evaluation_sets=self.sets,
                                             sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid after OPENED: {errors}")
        self.pdef_ref = self.store.write_canonical("problem_definition.json", self.pdef, role="PROBLEM_DEFINITION")
        self.summary["ledgerHead"] = self.events[-1]["eventId"]
        log(f"claim set {claim_sha[:12]} (samples {claim_samples[:12]}) OPENED at revision {self.revision} "
            f"with codeHash {self.code_hash[:12]} -> BURNT")
        evaluations = [gates.claim_evaluation(model, self.grids, threads=self.threads) for model in self.models]
        g5b = gates.external_checks(evaluations, self.pdef["evaluationSets"]["claim"], [self.set_refs["claim"]])
        g5b_ref = self.store.write_json("gate5b_external.json", {
            "checks": g5b, "claimSetSha256": claim_sha, "claimSampleSetHash": claim_samples,
            "openedAtRevision": self.revision, "codeHash": self.code_hash, "grid": self.grids["label"],
            "perSeed": [{"metrics": {k: v["value"] for k, v in e["metrics"].items()},
                         "satisfied": {k: v["criterionSatisfied"] for k, v in e["metrics"].items()},
                         "failedMust": e["failedMustCriteria"], "failedShould": e["failedShouldCriteria"],
                         "diagnostics": e["diagnostics"]} for e in evaluations],
            "thresholds": {k: v["threshold"] for k, v in evaluations[0]["metrics"].items()},
            "validator": "pinn.validation.annulus.evaluate_fields (trusted annulus validator; control fixtures in gate3)",
        }, role="VALIDATION_METRIC", parents=[self.set_refs["claim"]["artifactId"]]
                                              + [r["artifactId"] for r in self.run_refs])
        external = self.judge("external", g5b, [g5b_ref], evaluationSet="claim", claimSetSha256=claim_sha)
        self.summary["claimEvaluation"] = {
            "perSeed": [{k: v["value"] for k, v in e["metrics"].items()} for e in evaluations],
            "failedMust": [e["failedMustCriteria"] for e in evaluations],
            "failedShould": [e["failedShouldCriteria"] for e in evaluations]}
        self.write_run_record(claim_opened=True)
        gate5 = gate5_status(physics=GATE_FROM_TRUST[physics], external=GATE_FROM_TRUST[external])
        after = advance(WorkflowState.VALIDATION, 5, gate5, self.vector())
        self.move(WorkflowState.VALIDATION, after, gate=5, result=gate5.value,
                  detail=f"C_physics={physics.value}, C_external={external.value} on claim set {claim_sha[:12]}")
        return after

    def phase_gate6_blocked(self, reason: str) -> None:
        g6 = gates.gate6_blocked(reason, [self.run_record_ref])
        g6_ref = self.store.write_json("gate6_reproducibility.json", {"checks": g6}, role="GATE_RESULT",
                                       parents=[self.run_record_ref["artifactId"]])
        self.judge("repro", g6, [g6_ref])

    def trust_vector_document(self, *, suffix: str = "", supersedes: str | None = None,
                              dimensions: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Schema-1.2 trust vector, validated against the frozen spec before anyone writes it."""
        dims = dict(dimensions) if dimensions is not None else {
            d: self.dimensions.get(d, {"status": TrustStatus.NOT_CHECKED.value}) for d in DIMENSIONS}
        document = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{self.attempt_id}{suffix}",
                    "problemId": self.problem_id, "revision": self.revision, "specHash": self.pdef["specHash"],
                    "dimensions": dims}
        if supersedes:
            document["supersedesRecordId"] = supersedes
        errors = validate_trust_vector(document, self.pdef)
        if errors:
            raise SystemExit(f"TrustVector invalid: {errors}")
        return document

    def decision_document(self, vector_doc: Mapping[str, Any], tv_ref: Mapping[str, str], *,
                          statement_ref: Mapping[str, str], suffix: str = "") -> tuple[dict[str, Any], Any]:
        """The ClaimGateDecision exactly as the square runner builds it (schema 1.2), validated."""
        return build_decision(vector_doc, tv_ref, pdef=self.pdef, code_hash=self.code_hash, events=self.events,
                              run_record=self.run_record, statement_ref=statement_ref,
                              evidence_refs=[dict(tv_ref)] + [self.store.ref(p) for p in
                                                              ("gate4_training.json", "gate5b_external.json")
                                                              if (self.store.root / p).exists()],
                              decision_id=f"cgd-{self.attempt_id}{suffix}")

    def preflight_decision(self) -> None:
        """Before the claim set is OPENED: build and validate everything the end of the run will build.

        r2 burnt DAC-M1 and then crashed writing its decision (2026-09-26). Everything that
        crash and the later validation found -- the call into ``claim_gate``, the vector
        layout, the registered-but-omitted checks -- is knowable here, with external and
        repro still NOT_CHECKED, so it is checked here, where failing costs no claim set.
        """
        vector = self.trust_vector_document(suffix="-preflight")
        gate = claim_gate(trust_vector_statuses(vector), evidence_level="A", spec_hash=self.pdef["specHash"],
                          code_hash=self.code_hash, exploratory=False, stop_the_line=False)
        record = {**self.run_record} if getattr(self, "run_record", None) else None
        if record is None:
            raise SystemExit("preflight needs the Gate 4 run record")
        probe = build_decision(vector, {"artifactId": "trust_vector-preflight.json", "sha256": "0" * 64},
                               pdef=self.pdef, code_hash=self.code_hash, events=self.events, run_record=record,
                               statement_ref={"artifactId": "claim_statements-preflight.json", "sha256": "0" * 64},
                               evidence_refs=[], decision_id=f"cgd-{self.attempt_id}-preflight")
        self.summary["preflight"] = {"trustVector": "valid (schema 1.2, every registered check recorded)",
                                     "decision": "valid", "allowedIfStoppedHere": list(gate.allowed),
                                     "checkedBeforeOpening": True}
        log(f"preflight before opening the claim set: trust vector and decision valid "
            f"(would allow {list(probe[1].allowed)} if stopped here)")

    def finish(self, final_state: WorkflowState, *, decision: bool) -> dict[str, Any]:
        vector_doc = self.trust_vector_document()
        if decision:
            statements_text = json.dumps(STATEMENTS, ensure_ascii=False, indent=2, allow_nan=False,
                                         sort_keys=True) + "\n"
            statement_ref = {"artifactId": "claim_statements.json",
                             "sha256": hashlib.sha256(statements_text.encode("utf-8")).hexdigest()}
            tv_ref = {"artifactId": "trust_vector.json", "sha256": canonical_sha256(vector_doc)}
            decision_doc, gate = self.decision_document(vector_doc, tv_ref, statement_ref=statement_ref)
            # validated above; only now is anything written
            written = self.store.write_json("claim_statements.json", STATEMENTS, role="CLAIM_STATEMENT")
            assert written["sha256"] == statement_ref["sha256"]
        tv_ref = self.store.write_canonical("trust_vector.json", vector_doc, role="TRUST_VECTOR",
                                            parents=[self.run_record_ref["artifactId"]])
        self.summary["trustVector"] = {name: entry["status"] for name, entry in vector_doc["dimensions"].items()}
        if decision:
            cgd_ref = self.store.write_canonical("claim_gate_decision.json", decision_doc, role="CLAIM_GATE_DECISION",
                                                 parents=[tv_ref["artifactId"]])
            self.summary.update({"allowedClaims": list(gate.allowed),
                                 "blockedClaims": [lvl for lvl in CLAIM_LEVELS if lvl not in gate.allowed],
                                 "highestAllowedClaim": gate.highest_allowed or "BLOCKED",
                                 "weakestLink": {"dimensions": list(gate.weakest_dimensions),
                                                 "status": gate.weakest_status.value},
                                 "decisionRef": cgd_ref})
        self.summary["finalState"] = final_state.value
        self.store.write_json("RUN_SUMMARY.json", self.summary, role="SUMMARY")
        return self.summary

    def run(self) -> dict[str, Any]:
        self.phase_identity()
        self.phase_problem()
        self.phase_upstream_gates()
        self.phase_training()
        after = self.phase_gate4()
        if after is not WorkflowState.TRAINING_COMPLETED:
            # Anything that is not a clean Gate 4 pass stops here -- FAIL, PARTIAL and
            # BLOCKED alike. The claim set is opened exactly once in its life, so it is
            # never opened on the strength of a training result the gate did not accept.
            self.phase_failure(gate=4)
            self.phase_gate6_blocked(f"Gate 4 did not pass (state {after.value}); reproduction is not attempted")
            return self.finish(after, decision=False)
        if self.stop_after_gate == 4:
            log("stopping after Gate 4 as requested (reproduction attempt)")
            self.phase_gate6_blocked("run stopped after Gate 4 by request (reproduction candidate)")
            return self.finish(WorkflowState.TRAINING_COMPLETED, decision=False)
        after = self.phase_validation()
        if after in (WorkflowState.FAILURE_RECORDED, WorkflowState.STOPPED_THE_LINE):
            self.phase_failure(gate=5)
            self.phase_gate6_blocked("Gate 5 did not pass; reproduction is not attempted")
            return self.finish(after, decision=False)
        self.phase_gate6_blocked("Gate 6 runs as a separate attempt in an independent environment "
                                 "(apply-g6 merges its verdict)")
        return self.finish(after, decision=True)


# ------------------------------------------------------------------ claim pool

def run_register_pool(problem_id: str, members: Sequence[str], designated_start: int, config_path: Path) -> None:
    """Seal the blind claim pool: one member per future revision, disjoint by construction."""

    config = load_json(config_path)
    pool_config = config["claimPool"]
    definitions = {name: pool_config["members"][name] for name in members}
    manifests = ds.claim_pool_manifests(definitions, label=problem_id)
    points = {name: ds.points_of(document) for name, document in manifests.items()}
    names = list(manifests)
    overlaps = {}
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            shared = len(set(points[first]) & set(points[second]))
            overlaps[f"{first}|{second}"] = shared
            if shared:
                raise SystemExit(f"claim pool members {first} and {second} share {shared} sample(s)")
    document = {"problemId": problem_id, "registeredAt": utc_now(), "registeredBy": EXECUTOR,
                "geometryId": contract.GEOMETRY["geometryId"],
                "rule": "each member has its own rotated quadrature grid and its own CGL-in-area-fraction pointwise "
                        "grid; angular counts are pairwise coprime and each member carries a distinct angular offset, "
                        "so no two members and no member and D_phys can share a node",
                "note": "initialStatus is registration-time information only; the runtime lifecycle state is derived "
                        "from the ledger (derived_claim_status), never read from here",
                "pairwiseSharedSamples": overlaps,
                "members": {}}
    for index, (name, manifest) in enumerate(manifests.items()):
        artifact, samples = register_sample_set(manifest)
        document["members"][name] = {
            "grid": dict(definitions[name]),
            "artifactId": manifest["artifactId"],
            "artifactHash": artifact,
            "sampleSetHash": samples,
            "sampleCount": len(manifest["samples"]),
            "designatedRevision": designated_start + index,
            "initialStatus": "SEALED",
        }
    path = PROBLEMS_DIR / f"{problem_id}-claim-pool.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    log(f"claim pool sealed: {list(document['members'])} -> {path}")


# ------------------------------------------------------------------ CLI

def run_tier1_for_attempt(attempt_dir: Path, *, device: str = "cpu", workers: int = 1) -> dict[str, Any]:
    """Tier-1 Red Team against an attempt whose Gate 5 passed (Constitution 22, Tier-1 set).

    It reads only registered artifacts of that attempt -- the REGISTERED train and dev sets,
    the frozen config named by its identity.json and its seed-0 run record -- and it never
    touches D_claim, the ledger or any historical verdict. Refusing to start unless Gate 5
    passed is part of the protocol: a Red Team is a stress test of an accepted result, not a
    second chance for a rejected one.
"""

    from . import redteam_annulus as redteam

    attempt_dir = Path(attempt_dir)
    if not (attempt_dir / "RUN_SUMMARY.json").exists():
        raise SystemExit(f"{attempt_dir} has no RUN_SUMMARY.json: it is not a finished attempt "
                         "(a stopped or aborted record is not red teamed, it is kept as it is)")
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    identity = load_json(attempt_dir / "identity.json")
    vector = summary.get("trustVector", {})
    if vector.get("physics") != "PASS" or vector.get("external") != "PASS":
        raise SystemExit(f"Gate 5 did not pass for {attempt_dir.name} "
                         f"(physics={vector.get('physics')}, external={vector.get('external')}); "
                         "the Tier-1 Red Team does not run")
    config_path = repo_root() / identity["configPath"]
    if sha256_file(config_path) != identity["configSha256"]:
        raise SystemExit("the config on disk is not the one the attempt ran; refusing to red team it")
    config = load_json(config_path)
    pdef = load_json(attempt_dir / "problem_definition.json")
    sets = {role: load_json(attempt_dir / f"sets/{role}.json") for role in ("train", "dev")}
    for role, doc in sets.items():
        if canonical_sha256(doc) != pdef["evaluationSets"][role]["sha256"]:
            raise SystemExit(f"the stored {role} set is not the one the ProblemDefinition names")
    baseline = load_json(attempt_dir / "runs/run-00.json")
    phys_points, phys_weights = ds.phys_grid(int(config["sets"]["physRadialOrder"]),
                                             int(config["sets"]["physAngularCount"]))
    criterion = config["signatureCriteria"]["sLocalizedError"]
    current = code_hash_from_manifest(code_manifest(repo_root(), [identity["configPath"],
                                                                 *config.get("codeIdentityExtraFiles", [])]))
    log(f"Tier-1 Red Team on {attempt_dir.name}: 8 retrains on device={device}, "
        f"baseline seeds {baseline['seeds']}")
    if current != identity["codeHash"]:
        log(f"WARNING: codeHash is now {current[:12]}, the attempt ran {identity['codeHash'][:12]}; "
            "the Tier-1 result is recorded against BOTH and is not evidence about the attempt's code")
    result = redteam.run_tier1(config, ds.points_of(sets["train"]), ds.points_of(sets["dev"]),
                               phys_points, phys_weights, baseline,
                               int(criterion["radialBins"]), int(criterion["angularSectors"]),
                               log=log, device=device, workers=workers)
    result.update({"attemptId": summary["attemptId"], "attemptCodeHash": identity["codeHash"],
                   "codeHashAtRedTeam": current, "specHash": pdef["specHash"],
                   "gate5TrustVector": vector, "executedBy": EXECUTOR, "at": utc_now(),
                   "claimSetTouched": False,
                   "note": "Tier-1 may maintain or downgrade a dimension, never upgrade one"})
    store = ArtifactStore(attempt_dir)
    store.write_json("tier1_redteam.json", result, role="RED_TEAM_RESULT")
    log(f"Tier-1: {result['dimensionImpact']} (passed={result['passed']})")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    attempt = sub.add_parser("attempt")
    attempt.add_argument("--config", type=Path, required=True)
    attempt.add_argument("--attempt-id", required=True)
    attempt.add_argument("--problem-id", required=True)
    attempt.add_argument("--revision", type=int, default=1)
    attempt.add_argument("--out-root", type=Path, default=EXPERIMENT_DIR / "runs")
    attempt.add_argument("--claim-pool-member")
    attempt.add_argument("--seed-offset", type=int, default=0)
    attempt.add_argument("--reproduction-of")
    attempt.add_argument("--stop-after-gate", type=int)
    attempt.add_argument("--device", default="cpu")
    attempt.add_argument("--workers", type=int, default=1)

    tier1 = sub.add_parser("tier1")
    tier1.add_argument("--attempt-dir", type=Path, required=True)
    tier1.add_argument("--device", default="cpu")
    tier1.add_argument("--workers", type=int, default=1)

    pool = sub.add_parser("register-pool")
    pool.add_argument("--problem-id", required=True)
    pool.add_argument("--members", nargs="+", required=True)
    pool.add_argument("--designated-start", type=int, default=1)
    pool.add_argument("--config", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "attempt":
        attempt_run = AttemptAnnulus(config_path=args.config, attempt_id=args.attempt_id, problem_id=args.problem_id,
                                     revision=args.revision, out_root=args.out_root,
                                     claim_pool_member=args.claim_pool_member, seed_offset=args.seed_offset,
                                     reproduction_of=args.reproduction_of, stop_after_gate=args.stop_after_gate,
                                     device=args.device, workers=args.workers)
        summary = attempt_run.run()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "tier1":
        print(json.dumps(run_tier1_for_attempt(args.attempt_dir, device=args.device, workers=args.workers),
                         ensure_ascii=False, indent=2)[:4000])
        return 0
    if args.command == "register-pool":
        run_register_pool(args.problem_id, args.members, args.designated_start, args.config)
        return 0
    raise SystemExit(f"unknown command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
