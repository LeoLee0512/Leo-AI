"""Poisson 2D calibration runner: drive one attempt through the amended state machine.

    attempt        --config C --attempt-id A --problem-id P [--revision r] [--claim-pool-member NAME]
                   [--reenter-from DIR] [--seed-offset k] [--reproduction-of DIR]
    register-pool  --problem-id P --members D2C-GL32-CGL50:32:50 ...
    finalize / failure-diagnostics / redteam / judge-reproduction / apply-g6 / plots / repro-package

Same skeleton as the 1D runner (``pinn.experiments.runner``), which stays
untouched: the 1D calibration is CLOSED and its code identity must not move.
Everything dimension-independent is imported rather than copied: the governance
validators, the state machine, ``ArtifactStore`` / code identity / environment
fingerprint from ``pinn.experiments.common``, Gate 4 from ``pinn.experiments.gates``
and the failure-signature rules from ``pinn.experiments.diagnosis``.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from pinn.experiments.common import (
    ArtifactStore,
    code_hash_from_manifest,
    code_manifest,
    environment_fingerprint,
    environment_identity,
    git_head,
    load_json,
    sha256_file,
    utc_now,
    workspace_dirty_paths,
    assert_code_identity_complete,
    CODE_IDENTITY_FILES,
    CODE_IDENTITY_PREFIXES,
    DECISION_SURFACES,
)
from pinn.experiments.diagnosis import observed_signatures
from pinn.experiments2d import localized_error
from pinn.governance.canonical import canonical_bytes, canonical_sha256
from pinn.governance.claim_set_ledger import derive_claim_set_state, make_event, validate_claim_set_ledger
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set, sample_set_hash
from pinn.governance.prelock import PrelockPaths, run_prelock
from pinn.governance.state_machine import (
    GATE_DIMENSIONS,
    GATE_RUNS_IN,
    ROOT_CAUSE_GATE,
    FailureSignature,
    GateStatus,
    RootCauseClass,
    TriageRoute,
    WorkflowState,
    advance,
    enter_validation,
    gate5_status,
    reenter,
)
from pinn.governance.trust_loop import (
    problem_definition_spec_hash,
    trust_vector_statuses,
    validate_claim_gate_decision,
    validate_problem_definition,
    validate_run_record,
    validate_trust_vector,
)
from pinn.governance.trust_vector import (
    CLAIM_LEVELS,
    DIMENSIONS,
    EnvironmentFingerprint,
    RunQualification,
    TrustStatus,
    claim_gate,
    independent_environments,
    reproduction_status,
    seed_set_id,
)

from . import datasets2d as ds
from . import diagnostics2d, gates2d, pinn_torch2d as pinn2d, redteam2d, report2d

CONSTITUTION_VERSION = "1.2"
EXECUTOR = "pinn.experiments2d.runner2d (Claude, captain)"
GATE_FROM_TRUST = {TrustStatus.PASS: GateStatus.PASS, TrustStatus.FAIL: GateStatus.FAIL,
                   TrustStatus.PARTIAL: GateStatus.PARTIAL, TrustStatus.BLOCKED: GateStatus.BLOCKED,
                   TrustStatus.NOT_CHECKED: GateStatus.BLOCKED}
EXPERIMENT_DIR = Path("experiments/poisson2d")
LEDGER_DIR = EXPERIMENT_DIR / "ledger"
PROBLEMS_DIR = EXPERIMENT_DIR / "problems"
REGISTRY_PATH = LEDGER_DIR / "sample_set_registry.json"
SPEC_PATH = "specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json"
ANALYTIC_PATH = "pinn/reference/analytic_poisson2d.py"
FDM_PATH = "scientific_reference/poisson2d_fdm.py"


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
    """The lifecycle state of a claim set, derived from the ledger -- the only source of truth.

    Constitution 9.1: "claim 集状态由账本推导，不由文档声明".  The pool manifest's own
    ``status`` field is written once at registration time and is never written back, so
    runtime decisions must not read it (Final Closure Audit issue 4).  Burn follows the
    samples, so a set whose ``sampleSetHash`` was opened under any artifact is BURNT even
    when this (problemId, revision, artifact) key was never sealed.
    """

    state = derive_claim_set_state(events, problem_id=problem_id, revision=revision,
                                   claim_set_sha256=artifact_hash, sample_set_hashes=load_registry())
    if sample_hash in state.burnt_samples:
        return "BURNT", state
    return state.status, state


def claim_grids(name: str, gl_order: int, cgl_count: int, boundary_order: int) -> dict[str, Any]:
    quadrature_points, quadrature_weights = ds.gauss_legendre_square(gl_order)
    pointwise_points = ds.cgl_interior_square(cgl_count)
    boundary_points, boundary_weights = ds.boundary_nodes(boundary_order)
    return {"label": name, "glOrder": gl_order, "cglCount": cgl_count, "boundaryOrder": boundary_order,
            "quadraturePoints": quadrature_points, "quadratureWeights": quadrature_weights,
            "pointwisePoints": pointwise_points, "boundaryPoints": boundary_points, "boundaryWeights": boundary_weights}


# ------------------------------------------------------------------ ProblemDefinition

def build_problem_definition(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]], *, problem_id: str,
                             revision: int, root: Path, frozen_at: str) -> dict[str, Any]:
    spec_ref = {"artifactId": SPEC_PATH, "sha256": sha256_file(root / SPEC_PATH)}
    analytic_ref = {"artifactId": ANALYTIC_PATH, "sha256": sha256_file(root / ANALYTIC_PATH)}
    fdm_ref = {"artifactId": FDM_PATH, "sha256": sha256_file(root / FDM_PATH)}
    pre = config["preregistration"]
    edges = [("left-dirichlet", "x0"), ("right-dirichlet", "x1"), ("bottom-dirichlet", "y0"), ("top-dirichlet", "y1")]
    document = {
        "schemaVersion": "pinn.problemDefinition/1.2",
        "problemId": problem_id,
        "revision": revision,
        "pde": {"form": "strong", "transient": False,
                "equations": [{"name": "poisson-2d", "expressionRef": spec_ref, "independentVars": ["x", "y"], "dependentVars": ["u"]}]},
        "boundaryConditions": [
            {"name": name, "type": "dirichlet", "regionRef": region, "expressionRef": spec_ref, "enforcement": "hard"}
            for name, region in edges
        ],
        "geometry": {"domainType": "rectangle", "dimension": 2, "regions": [
            {"id": "interior", "description": "0 < x < 1 and 0 < y < 1"},
            {"id": "x0", "description": "x = 0, 0 <= y <= 1"}, {"id": "x1", "description": "x = 1, 0 <= y <= 1"},
            {"id": "y0", "description": "y = 0, 0 <= x <= 1"}, {"id": "y1", "description": "y = 1, 0 <= x <= 1"}]},
        "parameters": [{"name": "forcing_amplitude_two_pi_squared", "value": 2.0 * math.pi ** 2, "unitRef": "1"},
                       {"name": "forcing_wavenumber_kx", "value": 1.0, "unitRef": "1"},
                       {"name": "forcing_wavenumber_ky", "value": 1.0, "unitRef": "1"}],
        "units": {"system": "nondimensional", "entries": [
            {"quantity": "length", "unit": "1", "symbolRef": "x"}, {"quantity": "field", "unit": "1", "symbolRef": "u"}]},
        "nondimensionalization": {"applied": False, "scales": [], "notes": "posed dimensionless by construction (2D spec v1.0)"},
        "variables": [
            {"name": "x", "role": "independent", "domainRange": [0.0, 1.0], "unitRef": "1"},
            {"name": "y", "role": "independent", "domainRange": [0.0, 1.0], "unitRef": "1"},
            {"name": "u", "role": "dependent", "domainRange": [-1.5, 1.5], "unitRef": "1"},
        ],
        "referenceSolution": {"sources": [
            {"sourceId": "src-analytic", "method": "analytical", "evidenceLevel": "A", "independenceDeclaration": True, "provenance": analytic_ref},
            {"sourceId": "src-fdm2d", "method": "numerical", "evidenceLevel": "B", "independenceDeclaration": True, "provenance": fdm_ref},
        ], "primarySourceId": "src-analytic"},
        "checkApplicability": [dict(entry) for entry in gates2d.REGISTRY],
        "preregistration": {"errorNorm": "relativeL2", "epsilonSpec": float(pre["epsilonSpec"]),
                            "seedRuns": int(config["seedProtocol"]["runs"]), "seedFactors": ["init", "sample", "batch"],
                            "worstSeedFactor": float(pre["worstSeedFactor"]), "dispersionLimit": float(pre["dispersionLimit"])},
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
                                   claim_set_sha256=pdef["evaluationSets"]["claim"]["sha256"], sample_set_hashes=load_registry())
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
    return {d: TrustStatus(dimensions[d]["status"]) for d in DIMENSIONS}


# ------------------------------------------------------------------ the attempt

class Attempt2D:
    def __init__(self, *, config_path: Path, attempt_id: str, problem_id: str, revision: int, out_root: Path,
                 ledger_path: Path, reenter_from: Path | None, claim_pool_member: str | None = None,
                 seed_offset: int = 0, reproduction_of: Path | None = None) -> None:
        self.root = repo_root()
        self.config_path = config_path
        self.config = load_json(config_path)
        self.attempt_id = attempt_id
        self.problem_id = problem_id
        self.revision = revision
        self.store = ArtifactStore(out_root / attempt_id, producer=EXECUTOR)
        self.ledger_path = ledger_path
        self.reenter_from = reenter_from
        self.claim_pool_member = claim_pool_member
        self.seed_offset = int(seed_offset)
        self.reproduction_of = reproduction_of
        self.threads = int(self.config["optimizer"].get("threads", 1))
        self.summary: dict[str, Any] = {"attemptId": attempt_id, "problemId": problem_id, "revision": revision,
                                        "constitutionVersion": CONSTITUTION_VERSION, "dimension": 2, "startedAt": utc_now()}
        self.dimensions: dict[str, dict[str, Any]] = {d: {"status": "NOT_CHECKED"} for d in DIMENSIONS}
        self.grids: dict[str, Any] | None = None

    # ------------------------------------------------------------ helpers
    def vector(self) -> dict[str, TrustStatus]:
        return statuses_of(self.dimensions)

    def save_state(self, state: WorkflowState) -> None:
        self.state = state
        self.store.write_json("attempt_state.json", {"state": state.value, "at": utc_now(), "dimensions": self.dimensions}, role="STATE")

    def move(self, before: WorkflowState, after: WorkflowState, *, gate: int | None, result: str, detail: str = "") -> None:
        self.store.transition(before.value, after.value, gate=gate, result=result, detail=detail)
        self.save_state(after)

    def judge(self, dimension: str, checks: Sequence[Mapping[str, Any]], evidence: Sequence[Mapping[str, str]], **extra: Any) -> TrustStatus:
        status = gates2d.dimension_status(checks)
        notes = extra.pop("notes", "")
        if status is TrustStatus.PARTIAL and not notes:
            notes = "; ".join(c["reason"] for c in checks if c.get("status") == "PARTIAL")
        self.dimensions[dimension] = dimension_entry(status, checks, evidence, notes=notes, extra=extra or None)
        return status

    # ------------------------------------------------------------ phases
    def phase_identity(self) -> None:
        config_rel = self.config_path.resolve().relative_to(self.root).as_posix()
        dirty = workspace_dirty_paths(self.root)
        # A formal run may be driven by a script that lives outside the identity prefixes
        # (experiments/** holds the drivers next to the evidence they write). Such a driver
        # is decision-relevant, so the run declares it here and it enters the manifest.
        declared = [str(path).replace("\\", "/") for path in self.config.get("codeIdentityExtraFiles", [])]
        extra = [config_rel, *declared]
        manifest = code_manifest(self.root, extra)
        # Fail closed *before* PRELOCK and before any Gate: an incomplete manifest means the
        # codeHash does not identify the method that produced the results.
        assert_code_identity_complete(manifest, self.root, extra_required=extra)
        self.code_hash = code_hash_from_manifest(manifest)
        self.code_manifest = manifest
        self.environment = environment_fingerprint()
        self.environment_id = environment_identity(self.environment)
        identity = {"gitHead": git_head(self.root), "dirtyCodeIdentityPaths": dirty, "codeHash": self.code_hash,
                    "codeManifest": manifest, "configPath": config_rel, "configSha256": sha256_file(self.config_path),
                    "codeIdentityBoundary": {"prefixes": list(CODE_IDENTITY_PREFIXES), "files": list(CODE_IDENTITY_FILES),
                                             "declaredByRun": declared, "decisionSurfaces": list(DECISION_SURFACES)},
                    "environment": self.environment, "environmentId": self.environment_id, "python": sys.version,
                    "constitutionVersion": CONSTITUTION_VERSION, "seedOffset": self.seed_offset, "spatialDimension": 2}
        self.store.write_json("identity.json", identity, role="IDENTITY")
        self.summary.update({"codeHash": self.code_hash, "environmentId": self.environment_id, "gitHead": identity["gitHead"],
                             "workspaceDirty": bool(dirty), "configId": self.config["configId"]})
        if dirty:
            log(f"WARNING: uncommitted code-identity changes {dirty}; this run has no valid codeHash (Constitution 28.1)")
        prelock = run_prelock(PrelockPaths.defaults(self.root))
        self.store.write_json("prelock.json", prelock, role="GOVERNANCE_CHECK")
        self.summary["prelock"] = prelock["prelockStatus"]
        if prelock["prelockStatus"] != "PASS":
            raise SystemExit("PRELOCK FAIL: the attempt does not start")

    def phase_problem(self) -> None:
        label = f"{self.problem_id}-r{self.revision}"
        members = pool_members(self.problem_id)["members"]
        frozen_file = PROBLEMS_DIR / f"{self.problem_id}-r{self.revision}.json"
        if self.claim_pool_member is None and frozen_file.exists():
            frozen_claim = load_json(frozen_file)["evaluationSets"]["claim"]["sha256"]
            for name, member in members.items():
                if member["artifactHash"] == frozen_claim:
                    self.claim_pool_member = name
                    log(f"frozen revision {self.revision} names pool member {name}; using it")
        if not self.claim_pool_member:
            raise SystemExit("a 2D attempt must name a preregistered claim pool member (--claim-pool-member)")
        if self.claim_pool_member not in members:
            raise SystemExit(f"claim pool member {self.claim_pool_member!r} is not preregistered for {self.problem_id}")
        member = members[self.claim_pool_member]
        if member["designatedRevision"] != self.revision:
            raise SystemExit(f"{self.claim_pool_member} is designated for revision {member['designatedRevision']}, not {self.revision}")
        claim_manifest = ds.claim_pool_manifests({self.claim_pool_member: (member["glOrder"], member["cglCount"])},
                                                 label=self.problem_id)[self.claim_pool_member]
        if canonical_sha256(claim_manifest) != member["artifactHash"] or sample_set_hash(claim_manifest) != member["sampleSetHash"]:
            raise SystemExit("regenerated pool member differs from the preregistered manifest")
        # EARLY GUARD (Final Closure Audit issue 4): ask the ledger, never the manifest's static status field,
        # and ask it here -- before the isolation scan, before the gates and long before any training.
        ledger_events = load_json(self.ledger_path) if self.ledger_path.exists() else []
        ledger_status, _ = derived_claim_status(ledger_events, problem_id=self.problem_id, revision=self.revision,
                                                artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])
        self.summary["claimSetLedgerStatusAtStart"] = ledger_status
        if self.reproduction_of is None and ledger_status in ("OPENED", "BURNT"):
            raise SystemExit(f"{self.claim_pool_member} is {ledger_status} in the ledger "
                             f"(samples {member['sampleSetHash'][:12]}); a formal attempt cannot reuse it. "
                             f"The pool manifest's own status field ({member.get('initialStatus', member.get('status'))}) "
                             "is a registration-time record and is not consulted.")
        log(f"claim pool member {self.claim_pool_member}: ledger-derived status {ledger_status}")
        self.grids = claim_grids(self.claim_pool_member, member["glOrder"], member["cglCount"],
                                 int(self.config["sets"]["boundaryOrder"]))
        self.sets = ds.build_sets(self.config, claim_points=ds.points_of(claim_manifest),
                                  claim_artifact_id=claim_manifest["artifactId"],
                                  claim_generator=claim_manifest["generator"], label=label)
        self.sets["claim"] = claim_manifest
        self.set_refs = {role: self.store.write_canonical(f"sets/{role}.json", doc, role="EVALUATION_SET") for role, doc in self.sets.items()}
        claim_artifact, claim_samples = register_sample_set(self.sets["claim"])
        log("checking sample-level isolation of the four sets (pure-Python O(N*M) separation scan)")
        isolation = ds.isolation_report(self.sets, min_separation=self.config["sets"]["minSeparation"])
        isolation["claimSampleSetHash"] = claim_samples
        isolation["antiCollision"] = ds.component_anti_collision(ds.points_of(self.sets["claim"]))
        isolation["generation"] = {
            "train": f"pool of {self.config['sampling']['poolSize']} uniform interior points of the unit square, numpy default_rng({self.config['sampling']['poolSeed']})",
            "dev": f"{self.config['sets']['devSize']} uniform interior points, numpy default_rng({self.config['sets']['devSeed']})",
            "phys": f"tensor Gauss-Legendre order {self.config['sets']['physOrder']} on the unit square",
            "claim": f"claim pool member {self.claim_pool_member}: tensor GL{member['glOrder']} + interior tensor CGL{member['cglCount']}",
            "boundary": f"Gauss-Legendre order {self.config['sets']['boundaryOrder']} per edge (spec-known boundary coordinates, identity-exempt)",
        }
        self.store.write_json("sets/isolation.json", isolation, role="EVALUATION_SET_ISOLATION",
                              parents=[r["artifactId"] for r in self.set_refs.values()])
        if not isolation["disjoint"]:
            raise SystemExit(f"evaluation sets are not sample-disjoint: {isolation['errors']}")
        if not isolation["antiCollision"]["ok"]:
            raise SystemExit(f"claim set fails the anti-collision rule: {isolation['antiCollision']}")
        self.summary["evaluationSets"] = {"sizes": isolation["sizes"], "hashes": isolation["hashes"], "claimSampleSetHash": claim_samples}
        self.phys_points, self.phys_weights = ds.gauss_legendre_square(self.config["sets"]["physOrder"])
        self.boundary_points, self.boundary_weights = ds.boundary_nodes(int(self.config["sets"]["boundaryOrder"]))
        self.store.write_json("sets/boundary.json", {
            "role": "boundary", "order": self.config["sets"]["boundaryOrder"], "count": len(self.boundary_points),
            "points": [list(p) for p in self.boundary_points], "weights": self.boundary_weights,
            "note": "spec-known boundary coordinates of the four edges (protocol L1 boundaryIdentityExempt): evaluated as boundary "
                    "values and normal derivatives, never as claim samples",
        }, role="BOUNDARY_SET")
        self.store.write_json("sets/phys_weights.json", {"order": self.config["sets"]["physOrder"], "weights": self.phys_weights},
                              role="EVALUATION_SET")
        self.pool = ds.points_of(self.sets["train"])
        self.dev_points = ds.points_of(self.sets["dev"])

        if frozen_file.exists():
            pdef = load_json(frozen_file)
            for role, doc in self.sets.items():
                if pdef["evaluationSets"][role]["sha256"] != canonical_sha256(doc):
                    raise SystemExit(f"frozen ProblemDefinition {frozen_file.name} names another {role} set than the regenerated one")
            log(f"reusing frozen ProblemDefinition {frozen_file.name} (frozenAt {pdef['frozenAt']})")
        else:
            pdef = build_problem_definition(self.config, self.sets, problem_id=self.problem_id, revision=self.revision,
                                            root=self.root, frozen_at=utc_now())
            frozen_file.parent.mkdir(parents=True, exist_ok=True)
            frozen_file.write_bytes(canonical_bytes(pdef))
            log(f"ProblemDefinition frozen to {frozen_file.name} (enforcement {pdef['boundaryConditions'][0]['enforcement']})")
        events = load_json(self.ledger_path) if self.ledger_path.exists() else []
        state = derive_claim_set_state(events, problem_id=self.problem_id, revision=self.revision,
                                       claim_set_sha256=claim_artifact, sample_set_hashes=load_registry())
        if state.status == "NEVER_SEALED":
            if claim_samples in state.burnt_samples:
                raise SystemExit(f"claim samples {claim_samples[:12]} are BURNT; refusing to seal")
            events.append(make_event(prev_event_id=events[-1]["eventId"] if events else "GENESIS", problemId=self.problem_id,
                                     revision=self.revision, specHash=pdef["specHash"], claimSetSha256=claim_artifact,
                                     sampleSetHash=claim_samples, event="SEALED", actor=EXECUTOR, at=utc_now()))
            log(f"claim set {claim_artifact[:12]} (samples {claim_samples[:12]}) SEALED for {self.problem_id} r{self.revision}")
        write_ledger(self.ledger_path, events)
        self.events = events
        pdef = apply_ledger_state(pdef, events)
        errors = validate_problem_definition(pdef, claim_set_events=events, evaluation_sets=self.sets, sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid: {errors}")
        self.pdef = pdef
        self.pdef_ref = self.store.write_canonical("problem_definition.json", pdef, role="PROBLEM_DEFINITION",
                                                   parents=[r["artifactId"] for r in self.set_refs.values()])
        self.store.register("claim_set_ledger.json", canonical_sha256(events), role="LEDGER", note=str(self.ledger_path))
        self.summary.update({"specHash": pdef["specHash"], "claimSetSha256": claim_artifact, "claimSampleSetHash": claim_samples,
                             "ledgerHead": events[-1]["eventId"], "claimPoolMember": self.claim_pool_member})
        log(f"ProblemDefinition FROZEN specHash={pdef['specHash'][:12]} sets={self.summary['evaluationSets']['sizes']}")

    def phase_upstream_gates(self) -> None:
        reentry = self.reenter_from is not None
        start = WorkflowState.DRAFT
        if reentry:
            diagnosis_doc = load_json(self.reenter_from / "diagnosis_record.json")
            cause = RootCauseClass(diagnosis_doc["rootCause"])
            gate = ROOT_CAUSE_GATE[cause]
            route = TriageRoute(FailureSignature(diagnosis_doc["signature"]), cause, gate, GATE_RUNS_IN[gate])
            prior = load_json(self.reenter_from / "trust_vector.json")["dimensions"]
            upstream_dims = [d for g in range(1, gate) for d in GATE_DIMENSIONS[g]]
            upstream = {d: TrustStatus(prior[d]["status"]) if d in upstream_dims else TrustStatus.NOT_CHECKED for d in DIMENSIONS}
            for d in upstream_dims:
                self.dimensions[d] = dict(prior[d])
            self.save_state(WorkflowState.REVISED)
            start = reenter(WorkflowState.REVISED, route, upstream)
            self.move(WorkflowState.REVISED, start, gate=gate, result="REENTER",
                      detail=f"re-entry at Gate {gate} after {cause.value}; Gate {gate} and downstream dimensions reset to NOT_CHECKED")
            self.summary["reentry"] = {"from": str(self.reenter_from), "gate": gate, "rootCause": cause.value}

        g1 = gates2d.gate1_math(self.pdef, [self.pdef_ref])
        g1_ref = self.store.write_json("gate1_math.json", {"checks": g1}, role="GATE_RESULT", parents=[self.pdef_ref["artifactId"]])
        g2, g2_detail = gates2d.gate2_baseline(self.phys_points, self.boundary_points, [self.set_refs["phys"]])
        g2_ref = self.store.write_json("gate2_baseline.json", {"checks": g2, "detail": g2_detail}, role="GATE_RESULT",
                                       parents=[self.set_refs["phys"]["artifactId"]])
        g3, g3_detail = gates2d.gate3_implementation(self.config, self.sets, self.dev_points, self.grids, [self.set_refs["dev"]])
        g3_ref = self.store.write_json("gate3_implementation.json", {"checks": g3, "detail": g3_detail}, role="GATE_RESULT",
                                       parents=[self.set_refs["dev"]["artifactId"]])
        self.gate_details = {"gate2": g2_detail, "gate3": g3_detail}
        if start is WorkflowState.IMPLEMENTATION_VERIFIED:
            self.judge("math", g1, [g1_ref])
            self.judge("impl", g3, [g3_ref])
            self.store.transition(self.state.value, self.state.value, gate=None, result="REVERIFIED",
                                  detail="G1-G3 re-executed on the revised code identity; upstream PASS retained per the re-entry rule")
            self.save_state(self.state)
            if self.vector()["math"] is not TrustStatus.PASS or self.vector()["impl"] is not TrustStatus.PASS:
                raise SystemExit("upstream dimensions no longer PASS after revision; re-entry is not licensed")
            return
        if start is not WorkflowState.DRAFT:
            raise SystemExit(f"unsupported re-entry state {start}")
        if not reentry:
            self.save_state(WorkflowState.DRAFT)
        math_status = self.judge("math", g1, [g1_ref])
        after = advance(WorkflowState.DRAFT, 1, GATE_FROM_TRUST[math_status], self.vector())
        self.move(WorkflowState.DRAFT, after, gate=1, result=GATE_FROM_TRUST[math_status].value)
        if after is not WorkflowState.SPEC_LOCKED:
            raise SystemExit(f"Gate 1 did not pass: {after}")
        g2_status = TrustStatus.PASS if all(c["status"] == "PASS" for c in g2) else TrustStatus.FAIL
        after = advance(WorkflowState.SPEC_LOCKED, 2, GATE_FROM_TRUST[g2_status], self.vector())
        self.move(WorkflowState.SPEC_LOCKED, after, gate=2, result=GATE_FROM_TRUST[g2_status].value)
        if after is not WorkflowState.BASELINE_VERIFIED:
            raise SystemExit(f"Gate 2 did not pass: {after}")
        impl_status = self.judge("impl", g3, [g3_ref])
        after = advance(WorkflowState.BASELINE_VERIFIED, 3, GATE_FROM_TRUST[impl_status], self.vector())
        self.move(WorkflowState.BASELINE_VERIFIED, after, gate=3, result=GATE_FROM_TRUST[impl_status].value)
        if after is not WorkflowState.IMPLEMENTATION_VERIFIED:
            raise SystemExit(f"Gate 3 did not pass: {after}")

    def phase_training(self) -> None:
        sp = self.config["seedProtocol"]
        off = self.seed_offset
        triplets = [{"index": i, "init": sp["initBase"] + off + i, "sample": sp["sampleBase"] + off + i, "batch": sp["batchBase"] + off + i}
                    for i in range(int(sp["runs"]))]
        seed_values = sorted({v for t in triplets for v in (t["init"], t["sample"], t["batch"])})
        self.seed_values = seed_values
        ledger_ref = self.store.write_json("seed_ledger.json", {
            "registeredAt": utc_now(),
            "rule": f"init={sp['initBase']}+{off}+i, sample={sp['sampleBase']}+{off}+i, batch={sp['batchBase']}+{off}+i, i in 0..{sp['runs'] - 1}",
            "triplets": triplets, "seedSetId": seed_set_id(seed_values), "appendOnly": True,
            "note": "registered before the first run started (Constitution 10.1)"}, role="SEED_LEDGER")
        self.started_at = utc_now()
        self.runs = []
        run_refs = []
        for triplet in triplets:
            seeds = {k: triplet[k] for k in ("init", "sample", "batch")}
            log(f"training seed triplet {seeds} with collocationCount={self.config['sampling']['collocationCount']}")
            run = pinn2d.train_run(self.config, self.pool, self.dev_points, seeds,
                                   collocation_count=int(self.config["sampling"]["collocationCount"]))
            run["runIndex"] = triplet["index"]
            run_refs.append(self.store.write_json(f"runs/run-{triplet['index']:02d}.json", run, role="RAW_MODEL_PREDICTION",
                                                  parents=[ledger_ref["artifactId"], self.set_refs["train"]["artifactId"]]))
            self.runs.append(run)
            log(f"  done: devRelL2={run['devRelL2']:.3e} completed={run['completed']} nan={run['nanEncountered']} {run['elapsedSeconds']:.1f}s")
        self.finished_at = utc_now()
        self.run_refs = run_refs
        self.models = [pinn2d.model_from_weights(self.config, run["weights"], threads=self.threads) for run in self.runs]
        self.write_run_record(claim_opened=False)

    def write_run_record(self, *, claim_opened: bool) -> None:
        evaluated = {"dev": self.pdef["evaluationSets"]["dev"]["sha256"]}
        if claim_opened:
            evaluated["claim"] = self.pdef["evaluationSets"]["claim"]["sha256"]
        record = {
            "schemaVersion": "pinn.runRecord/1.0", "runId": f"run-{self.attempt_id}", "problemId": self.problem_id, "revision": self.revision,
            "specHash": self.pdef["specHash"], "codeHash": self.code_hash, "codeManifest": self.code_manifest,
            "environment": self.environment, "environmentId": self.environment_id, "seeds": self.seed_values,
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
        g4, detail = gates2d.gate4_training(self.runs, self.pdef["preregistration"], [self.set_refs["dev"]])
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
        per_seed = [diagnostics2d.dev_diagnostics(m, self.dev_points, self.phys_points, self.phys_weights,
                                                  self.boundary_points, self.boundary_weights,
                                                  int(criteria["sLocalizedError"]["tilesPerAxis"]), threads=self.threads)
                    for m in self.models]
        stats = load_json(self.store.root / "gate4_training.json")["detail"]["seedStatistics"]
        observed = observed_signatures(per_seed, stats, criteria, float(self.pdef["preregistration"]["epsilonSpec"]))
        # d >= 2: the inherited 1D max/median symptom rule is retired (it fires on 9/10 seeds of a
        # validated run). The signature now fires exactly when the localized-error acceptance
        # criterion this experiment preregistered -- AC2D-9 for Poisson-2D -- fails on D_dev.
        # Fail-closed: a 2D run whose signatureCriteria carry no such criterion has a
        # preregistration defect, and no signature may be invented for it after the fact.
        localized_error.assert_criterion_within_run_identity(self.config_path, self.code_manifest)
        observed = localized_error.apply_localized_signature(observed, per_seed, criteria, dimension=2)
        observed["perSeedFields"] = [{"pointwiseAbsError": d["pointwiseAbsError"], "residuals": d["residuals"],
                                      "tileRms": d["tileRms"], "hotspot": d["hotspot"]} for d in per_seed]
        observed["devPoints"] = [list(p) for p in self.dev_points]
        claim_note = None
        if gate == 5 and (self.store.root / "gate5b_external.json").exists():
            g5b = load_json(self.store.root / "gate5b_external.json")
            claim_note = {"failedMustPerSeed": [m["failedMust"] for m in g5b["perSeed"]],
                          "note": "Gate 5 FAIL on the OPENED claim set; the signatures below are measured on D_dev / D_phys only"}
        ref = self.store.write_json("failure_record.json", {
            "state": WorkflowState.FAILURE_RECORDED.value, "gate": gate, "recordedAt": utc_now(), "claimSetVerdict": claim_note,
            "observedSignatures": observed["observedSignatures"], "rules": observed["rules"], "medians": observed["medians"],
            "perSeed": observed["perSeed"], "seedStatistics": stats, "retrainedInPlace": False,
            "constitutionVersion": CONSTITUTION_VERSION,
        }, role="FAILURE_RECORD", parents=[r["artifactId"] for r in self.run_refs])
        self.store.write_json("dev_diagnostics.json", observed, role="DIAGNOSTICS", parents=[ref["artifactId"]])
        self.summary["failure"] = {"gate": gate, "observedSignatures": observed["observedSignatures"], "medians": observed["medians"]}
        log(f"FAILURE_RECORDED at Gate {gate}; observedSignatures={observed['observedSignatures']}")

    def phase_validation(self) -> WorkflowState:
        state = enter_validation(WorkflowState.TRAINING_COMPLETED)
        self.move(WorkflowState.TRAINING_COMPLETED, state, gate=None, result="ENTER_VALIDATION")
        g5a, detail_a = gates2d.physics_checks(self.models, self.phys_points, self.phys_weights, self.boundary_points,
                                               self.boundary_weights, self.config["physicsThresholds"],
                                               [self.set_refs["phys"]], threads=self.threads)
        detail_a["thresholdSource"] = self.config["thresholdSources"]["physics"]
        g5a_ref = self.store.write_json("gate5a_physics.json", {"checks": g5a, "detail": detail_a}, role="GATE_RESULT",
                                        parents=[self.set_refs["phys"]["artifactId"]] + [r["artifactId"] for r in self.run_refs])
        physics = self.judge("physics", g5a, [g5a_ref])
        claim_sha = self.pdef["evaluationSets"]["claim"]["sha256"]
        claim_samples = self.summary["claimSampleSetHash"]
        self.events.append(make_event(prev_event_id=self.events[-1]["eventId"], problemId=self.problem_id, revision=self.revision,
                                      specHash=self.pdef["specHash"], claimSetSha256=claim_sha, sampleSetHash=claim_samples,
                                      event="OPENED", codeHash=self.code_hash, actor=EXECUTOR, at=utc_now()))
        write_ledger(self.ledger_path, self.events)
        self.store.register("claim_set_ledger.json", canonical_sha256(self.events), role="LEDGER", note=str(self.ledger_path))
        self.pdef = apply_ledger_state(self.pdef, self.events)
        errors = validate_problem_definition(self.pdef, claim_set_events=self.events, evaluation_sets=self.sets,
                                             sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid after OPENED: {errors}")
        self.pdef_ref = self.store.write_canonical("problem_definition.json", self.pdef, role="PROBLEM_DEFINITION")
        self.summary["ledgerHead"] = self.events[-1]["eventId"]
        log(f"claim set {claim_sha[:12]} (samples {claim_samples[:12]}) OPENED at revision {self.revision} with codeHash {self.code_hash[:12]} -> BURNT")
        evaluations = [gates2d.claim_evaluation(m, self.grids, threads=self.threads) for m in self.models]
        g5b = gates2d.external_checks(evaluations, self.pdef["evaluationSets"]["claim"], [self.set_refs["claim"]])
        g5b_ref = self.store.write_json("gate5b_external.json", {
            "checks": g5b, "claimSetSha256": claim_sha, "claimSampleSetHash": claim_samples, "openedAtRevision": self.revision,
            "codeHash": self.code_hash, "grid": self.grids["label"],
            "perSeed": [{"metrics": {k: v["value"] for k, v in e["metrics"].items()},
                         "satisfied": {k: v["criterionSatisfied"] for k, v in e["metrics"].items()},
                         "failedMust": e["failedMustCriteria"], "failedShould": e["failedShouldCriteria"],
                         "diagnostics": e["diagnostics"]} for e in evaluations],
            "thresholds": {k: v["threshold"] for k, v in evaluations[0]["metrics"].items()},
            "validator": "pinn.validation.poisson2d.evaluate_fields (trusted 2D validator; T10 control fixtures in gate3)",
        }, role="VALIDATION_METRIC", parents=[self.set_refs["claim"]["artifactId"]] + [r["artifactId"] for r in self.run_refs])
        external = self.judge("external", g5b, [g5b_ref], evaluationSet="claim", claimSetSha256=claim_sha)
        self.summary["claimEvaluation"] = {
            "perSeed": [{k: v["value"] for k, v in e["metrics"].items()} for e in evaluations],
            "failedMust": [e["failedMustCriteria"] for e in evaluations],
            "failedShould": [e["failedShouldCriteria"] for e in evaluations]}
        self.write_run_record(claim_opened=True)
        gate5 = gate5_status(physics=GATE_FROM_TRUST[physics], external=GATE_FROM_TRUST[external])
        after = advance(WorkflowState.VALIDATION, 5, gate5, self.vector())
        self.move(WorkflowState.VALIDATION, after, gate=5, result=gate5.value,
                  detail=f"C_physics={physics.value}, C_external={external.value} on claim set {claim_sha[:12]} (samples {claim_samples[:12]})")
        return after

    def phase_reproduction(self, after_gate4: WorkflowState) -> dict[str, Any]:
        report_doc = judge_reproduction(self.reproduction_of, self.store.root, write=False,
                                        environment_override=self.environment, environment_id_override=self.environment_id)
        report_doc["gate4State"] = after_gate4.value
        self.store.write_json("reproduction_report.json", report_doc, role="REPRODUCTION_REPORT",
                              parents=["run_record.json", "training_report.json"])
        self.summary["reproduction"] = {"cRepro": report_doc["cRepro"], "independent": report_doc["independentEnvironments"],
                                        "withinTolerance": report_doc["withinTolerance"],
                                        "medianAbsDiff": report_doc["metrics"]["medianAbsDiff"],
                                        "strongFieldsDiffering": report_doc["strongFieldsDiffering"], "sameCode": report_doc["sameCode"]}
        log(f"G6 reproduction: {report_doc['summaryLine']}")
        return report_doc

    def phase_gate6(self) -> WorkflowState:
        reason = ("reproduction protocol not executed yet: no qualified independent installation was available when this attempt ran "
                  "-> BLOCKED (not FAIL); a reproduction package is written for an independent environment")
        g6 = gates2d.gate6_blocked(reason, [self.run_record_ref])
        g6_ref = self.store.write_json("gate6_reproducibility.json", {"checks": g6, "environment": self.environment,
                                                                      "environmentId": self.environment_id}, role="GATE_RESULT")
        repro = self.judge("repro", g6, [g6_ref])
        result = GATE_FROM_TRUST[repro]
        after = advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, result, self.vector())
        self.move(WorkflowState.REPRODUCIBILITY_CHECK, after, gate=6, result=result.value, detail="C_repro BLOCKED: protocol not executed")
        return after

    def decision_document(self, vector_doc: Mapping[str, Any], tv_ref: Mapping[str, str], *, suffix: str = "",
                          stop: bool = False) -> dict[str, Any]:
        gate = claim_gate(trust_vector_statuses(vector_doc), evidence_level="A", spec_hash=self.pdef["specHash"],
                          code_hash=self.code_hash, exploratory=False, stop_the_line=stop)
        statements = {
            "C0": "The frozen Poisson 2D problem definition is mathematically consistent and the implementation computes this problem "
                  "(math, impl PASS; component-separated derivatives and four-edge boundary enforcement verified).",
            "C1": "Under the frozen training protocol the 2D PINN training is reliable across the preregistered seed set (train PASS); "
                  "accuracy is not asserted.",
            "C2": "Every seed model agrees with the analytic reference within the preregistered AC2D-1..AC2D-7 and AC2D-9 on the opened "
                  "blind 2D claim set and satisfies the 2D physics checks; Tier-1 Red Team maintained; independent reproduction confirmed.",
            "C3": "The C2 result holds across >= 5 independently qualified runs of the same method identity.",
        }
        statement_ref = self.store.write_json(f"claim_statements{suffix}.json", statements, role="CLAIM_STATEMENT")
        evidence_refs = [dict(tv_ref)] + [self.store.ref(p) for p in ("gate4_training.json", "gate5b_external.json")
                                          if (self.store.root / p).exists()]
        decision = {
            "schemaVersion": "pinn.claimGateDecision/1.2", "decisionId": f"cgd-{self.attempt_id}{suffix.replace('_', '-')}",
            "problemId": self.problem_id, "revision": self.revision, "specHash": self.pdef["specHash"], "codeHash": self.code_hash,
            "claimSetSha256": self.pdef["evaluationSets"]["claim"]["sha256"], "ledgerHead": self.events[-1]["eventId"],
            "trustVectorRef": {"artifactId": vector_doc["recordId"], "sha256": tv_ref["sha256"]}, "referenceEvidenceLevel": "A",
            "runMode": "FORMAL", "qualifiedC2Runs": [],
            "allowedClaims": [{"level": lvl, "statementRef": statement_ref, "evidenceRefs": evidence_refs,
                               "failureConditions": [
                                   {"condition": "the frozen ProblemDefinition, reference or code identity is revised", "consequence": "INVALIDATE_DECISION"},
                                   {"condition": "a later independent reproduction falls outside the preregistered tolerance", "consequence": "DOWNGRADE"}]}
                              for lvl in gate.allowed],
            "blockedClaims": [{"level": lvl, "reason": "; ".join(gate.blocked.get(lvl, ("not licensed",))),
                               "missingPreconditions": list(gate.blocked.get(lvl, ()))}
                              for lvl in CLAIM_LEVELS if lvl not in gate.allowed],
            "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value, "evidenceRef": dict(tv_ref)},
            "generatedAt": utc_now(), "decidedBy": EXECUTOR,
        }
        errors = validate_claim_gate_decision(decision, vector_doc, self.pdef, claim_set_events=self.events,
                                              run_records={self.run_record["runId"]: self.run_record})
        if errors:
            raise SystemExit(f"ClaimGateDecision invalid: {errors}")
        self.summary.update({"allowedClaims": list(gate.allowed), "highestAllowedClaim": gate.highest_allowed or "BLOCKED",
                             "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value}})
        return decision

    def trust_vector_document(self, *, suffix: str = "", supersedes: str | None = None,
                              dimensions: Mapping[str, Any] | None = None) -> dict[str, Any]:
        document = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{self.attempt_id}{suffix}", "problemId": self.problem_id,
                    "revision": self.revision, "specHash": self.pdef["specHash"],
                    "dimensions": dict(dimensions) if dimensions is not None else self.dimensions}
        if supersedes:
            document["supersedesRecordId"] = supersedes
        errors = validate_trust_vector(document, self.pdef)
        if errors:
            raise SystemExit(f"TrustVector invalid: {errors}")
        return document

    def phase_decision(self, final_state: WorkflowState) -> None:
        vector_doc = self.trust_vector_document()
        tv_ref = self.store.write_canonical("trust_vector.json", vector_doc, role="TRUST_VECTOR")
        decision = self.decision_document(vector_doc, tv_ref, stop=final_state is WorkflowState.STOPPED_THE_LINE)
        cgd_ref = self.store.write_canonical("claim_gate_decision.json", decision, role="CLAIM_GATE_DECISION",
                                             parents=[tv_ref["artifactId"]])
        self.summary.update({"finalState": final_state.value, "trustVector": {d: self.dimensions[d]["status"] for d in DIMENSIONS},
                             "trustVectorRef": tv_ref, "decisionRef": cgd_ref, "finishedAt": utc_now()})

    def finish(self, final_state: WorkflowState, *, decision: bool) -> dict[str, Any]:
        if decision:
            self.phase_decision(final_state)
        else:
            vector_doc = self.trust_vector_document()
            self.store.write_canonical("trust_vector.json", vector_doc, role="TRUST_VECTOR")
            self.summary.update({"finalState": final_state.value, "trustVector": {d: self.dimensions[d]["status"] for d in DIMENSIONS},
                                 "allowedClaims": [],
                                 "highestAllowedClaim": ("n/a (G6 reproduction attempt; claims are decided on the original attempt)"
                                                         if self.reproduction_of is not None else
                                                         "BLOCKED (no ClaimGateDecision: the line is in FAILURE_RECORDED)"),
                                 "finishedAt": utc_now()})
        self.store.write_json("RUN_SUMMARY.json", self.summary, role="SUMMARY")
        report2d.write_trust_report(self.store.root, self.root)
        return self.summary

    def run(self) -> dict[str, Any]:
        self.phase_identity()
        self.phase_problem()
        self.phase_upstream_gates()
        self.phase_training()
        after = self.phase_gate4()
        if self.reproduction_of is not None:
            self.phase_reproduction(after)
            self.store.transition(after.value, after.value, gate=6, result="REPRODUCTION_RUN",
                                  detail="G6 reproduction attempt: stops after Gate 4; the claim set is not opened")
            return self.finish(after, decision=False)
        if after in (WorkflowState.FAILURE_RECORDED, WorkflowState.STOPPED_THE_LINE):
            self.phase_failure()
            return self.finish(after, decision=False)
        if after is not WorkflowState.TRAINING_COMPLETED:
            log(f"Gate 4 result did not advance (state {after.value}); no validation, no claim decision")
            return self.finish(after, decision=False)
        after = self.phase_validation()
        if after in (WorkflowState.FAILURE_RECORDED, WorkflowState.STOPPED_THE_LINE):
            self.phase_failure(gate=5)
            return self.finish(after, decision=False)
        if after is WorkflowState.REPRODUCIBILITY_CHECK:
            after = self.phase_gate6()
        return self.finish(after, decision=True)


def resume_attempt(attempt_dir: Path) -> Attempt2D:
    root = repo_root()
    identity = load_json(attempt_dir / "identity.json")
    pdef = load_json(attempt_dir / "problem_definition.json")
    state_doc = load_json(attempt_dir / "attempt_state.json")
    ledger_path = LEDGER_DIR / f"{pdef['problemId']}.json"
    attempt = Attempt2D(config_path=root / identity["configPath"], attempt_id=attempt_dir.name, problem_id=pdef["problemId"],
                        revision=pdef["revision"], out_root=attempt_dir.parent, ledger_path=ledger_path, reenter_from=None,
                        seed_offset=identity.get("seedOffset", 0))
    attempt.code_hash = identity["codeHash"]
    attempt.code_manifest = identity["codeManifest"]
    attempt.environment = identity["environment"]
    attempt.environment_id = identity["environmentId"]
    attempt.pdef = pdef
    attempt.pdef_ref = attempt.store.ref("problem_definition.json")
    attempt.sets = {role: load_json(attempt_dir / f"sets/{role}.json") for role in ("train", "dev", "phys", "claim")}
    attempt.set_refs = {role: attempt.store.ref(f"sets/{role}.json") for role in attempt.sets}
    attempt.events = load_json(ledger_path)
    attempt.dimensions = state_doc["dimensions"]
    attempt.state = WorkflowState(state_doc["state"])
    attempt.phys_points, attempt.phys_weights = ds.gauss_legendre_square(attempt.config["sets"]["physOrder"])
    attempt.boundary_points, attempt.boundary_weights = ds.boundary_nodes(int(attempt.config["sets"]["boundaryOrder"]))
    attempt.pool = ds.points_of(attempt.sets["train"])
    attempt.dev_points = ds.points_of(attempt.sets["dev"])
    isolation = load_json(attempt_dir / "sets/isolation.json")
    summary = load_json(attempt_dir / "RUN_SUMMARY.json") if (attempt_dir / "RUN_SUMMARY.json").exists() else {}
    member_name = summary.get("claimPoolMember")
    members = pool_members(attempt.problem_id)["members"]
    if member_name in members:
        member = members[member_name]
        attempt.grids = claim_grids(member_name, member["glOrder"], member["cglCount"], int(attempt.config["sets"]["boundaryOrder"]))
        attempt.claim_pool_member = member_name
    if (attempt_dir / "run_record.json").exists():
        attempt.run_record = load_json(attempt_dir / "run_record.json")
        attempt.run_record_ref = attempt.store.ref("run_record.json")
    attempt.summary.update({"codeHash": attempt.code_hash, "environmentId": attempt.environment_id, "gitHead": identity["gitHead"],
                            "workspaceDirty": bool(identity["dirtyCodeIdentityPaths"]), "configId": attempt.config["configId"],
                            "prelock": load_json(attempt_dir / "prelock.json")["prelockStatus"], "specHash": pdef["specHash"],
                            "claimSetSha256": pdef["evaluationSets"]["claim"]["sha256"],
                            "claimSampleSetHash": isolation.get("claimSampleSetHash", sample_set_hash(attempt.sets["claim"])),
                            "claimPoolMember": member_name, "ledgerHead": attempt.events[-1]["eventId"],
                            "evaluationSets": {"sizes": isolation["sizes"], "hashes": isolation["hashes"]},
                            "resumedFinalisation": {"at": utc_now(), "note": "assembled by the runner at the current git HEAD from the stored "
                                                    "gate results; codeHash is the training/opening code identity recorded in identity.json"}})
    if (attempt_dir / "gate4_training.json").exists():
        attempt.summary["training"] = load_json(attempt_dir / "gate4_training.json")["detail"]["seedStatistics"]
    return attempt


# ------------------------------------------------------------------ claim pool

def run_register_pool(problem_id: str, members: Sequence[str], designated_start: int, config_path: Path) -> None:
    config = load_json(config_path)
    spec = {}
    for item in members:
        name, gl, cgl = item.split(":")
        spec[name] = (int(gl), int(cgl))
    manifests = ds.claim_pool_manifests(spec, label=problem_id)
    ledger_path = LEDGER_DIR / f"{problem_id}.json"
    events = load_json(ledger_path) if ledger_path.exists() else []
    registry_before = load_registry()
    burnt_samples: dict[str, str] = {}
    for e in events:
        if e["event"] == "OPENED":
            sample = e.get("sampleSetHash") or registry_before.get(e["claimSetSha256"])
            if sample:
                burnt_samples[sample] = e["claimSetSha256"]
    base_sets = {
        "train": ds.manifest(f"set-train-{problem_id}-pool-check", "train",
                             ds.uniform_interior(config["sampling"]["poolSize"], config["sampling"]["poolSeed"]),
                             generator={"generatorId": "numpy.default_rng.random((n,2))", "generatorVersion": "numpy-2.4"}),
        "dev": ds.manifest(f"set-dev-{problem_id}-pool-check", "dev",
                           ds.uniform_interior(config["sets"]["devSize"], config["sets"]["devSeed"]),
                           generator={"generatorId": "numpy.default_rng.random((n,2))", "generatorVersion": "numpy-2.4"}),
        "phys": ds.manifest(f"set-phys-{problem_id}-pool-check", "phys", ds.gauss_legendre_square(config["sets"]["physOrder"])[0],
                            generator={"generatorId": f"tensor-gauss-legendre-{config['sets']['physOrder']}", "generatorVersion": "numpy"}),
    }
    loaded_base = {role: load_evaluation_set(doc) for role, doc in base_sets.items()}
    names = list(manifests)
    out = {"schema": "leo.claimPool/1.0", "problemId": problem_id, "registeredAt": utc_now(), "constitutionVersion": CONSTITUTION_VERSION,
           "spatialDimension": 2,
           "identityRule": "sampleSetHash = canonical_sha256(sorted(sample identities)); burn follows sampleSetHash (ledger L4s/L6/L7/L8)",
           "gridFamily": "{tensor Gauss-Legendre of order n} U {interior tensor Chebyshev-Gauss-Lobatto of count m}",
           "burntBefore": {v: k for k, v in burnt_samples.items()}, "members": {}}
    # A claim set is SEALED for a (problemId, revision, artifact) key and may only be OPENED under the same specHash
    # (ledger rule), so the revision-1 ProblemDefinition is frozen here, before any member is sealed and before any
    # training exists.  Members designated for later revisions carry a preregistration seal at revision 1, exactly as in
    # the 1D pool; the attempt of revision r seals its own member again under that revision's specHash.
    r1_path = PROBLEMS_DIR / f"{problem_id}-r1.json"
    if r1_path.exists():
        r1 = load_json(r1_path)
    else:
        first = names[0]
        first_doc = manifests[first]
        label = f"{problem_id}-r1"
        r1_sets = ds.build_sets(config, claim_points=ds.points_of(first_doc), claim_artifact_id=first_doc["artifactId"],
                                claim_generator=first_doc["generator"], label=label)
        r1_sets["claim"] = first_doc
        r1 = build_problem_definition(config, r1_sets, problem_id=problem_id, revision=1, root=repo_root(), frozen_at=utc_now())
        r1_path.parent.mkdir(parents=True, exist_ok=True)
        r1_path.write_bytes(canonical_bytes(r1))
        log(f"ProblemDefinition r1 frozen to {r1_path.name} (specHash {r1['specHash'][:12]}) before any claim set is sealed")
    seal_spec_hash = r1["specHash"]
    out["preregistrationSealSpecHash"] = seal_spec_hash
    out["preregistrationSealSpecHashMeaning"] = "ProblemDefinition revision 1 specHash, frozen before any member was sealed"
    for index, name in enumerate(names):
        doc = manifests[name]
        artifact, samples = register_sample_set(doc)
        points = ds.points_of(doc)
        ac = ds.component_anti_collision(points)
        loaded = load_evaluation_set(doc)
        log(f"pool member {name}: {len(points)} samples; running the isolation scan against train / dev / phys")
        iso = disjointness_errors({**loaded_base, "claim": loaded}, min_separation=config["sets"]["minSeparation"])
        pairwise = {other: len(set(loaded.identities) & set(load_evaluation_set(manifests[other]).identities))
                    for other in names if other != name}
        member = {"glOrder": spec[name][0], "cglCount": spec[name][1], "artifactId": doc["artifactId"], "artifactHash": artifact,
                  "sampleSetHash": samples, "sampleCount": len(points), "designatedRevision": designated_start + index,
                  "antiCollision": ac, "isolationErrors": iso, "sharedWithOtherMembers": pairwise,
                  "burnt": samples in burnt_samples, "initialStatus": "SEALED",
                  "statusNote": ("initialStatus is the registration-time record only; the lifecycle truth is the ledger "
                                 "(derived_claim_status). Runtime decisions must not read it."),
                  "status": "SEALED"}
        if not ac["ok"] or iso or any(pairwise.values()) or member["burnt"]:
            raise SystemExit(f"pool member {name} not admissible: {member}")
        out["members"][name] = member
        (PROBLEMS_DIR / f"{problem_id}-claim-{name}.json").parent.mkdir(parents=True, exist_ok=True)
        (PROBLEMS_DIR / f"{problem_id}-claim-{name}.json").write_bytes(canonical_bytes(doc))
        events.append(make_event(prev_event_id=events[-1]["eventId"] if events else "GENESIS", problemId=problem_id, revision=1,
                                 specHash=seal_spec_hash, claimSetSha256=artifact, sampleSetHash=samples,
                                 event="SEALED", actor=EXECUTOR + " [claim pool preregistration]", at=utc_now()))
        log(f"  {name}: sampleSetHash {samples[:12]}, designated revision {member['designatedRevision']}, SEALED")
    write_ledger(ledger_path, events)
    (PROBLEMS_DIR / f"{problem_id}-claim-pool.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                                                                encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ Tier-1 Red Team

def run_redteam(attempt_dir: Path, label: str = "tier1") -> None:
    attempt = resume_attempt(attempt_dir)
    if attempt.state is not WorkflowState.REPRODUCIBILITY_CHECK and attempt.state is not WorkflowState.ACCEPTED:
        raise SystemExit(f"Tier-1 runs after Gate 5 PASS; attempt is in {attempt.state.value}")
    baseline_run = load_json(attempt_dir / "runs/run-00.json")
    log("Tier-1 Red Team (2D): one retrain per applicable perturbation, D_dev only")
    tier1 = redteam2d.run_tier1(attempt.config, attempt.pool, attempt.dev_points, attempt.phys_points, attempt.phys_weights,
                                baseline_run, log=log)
    tier_ref = attempt.store.write_json(f"{label}_redteam.json", tier1, role="RED_TEAM_REPORT", parents=["runs/run-00.json"])
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2, "BLOCKED": 3, "NOT_CHECKED": 4}
    prior = load_json(attempt_dir / "trust_vector.json")
    dims = copy.deepcopy(prior["dimensions"])
    for dim, impact in tier1["dimensionImpact"].items():
        entry = dims[dim]
        if entry["status"] == "NOT_CHECKED":
            continue
        entry["perturbationsRun"] = sorted(r["id"] for r in tier1["results"] if r.get("applicability") == "APPLICABLE" and r["dimension"] == dim)
        entry["worstCase"] = tier1["worstCase"][dim]
        if order[impact] > order[entry["status"]]:
            entry["status"] = impact
            entry["notes"] = (entry.get("notes", "") + f"; Tier-1 Red Team downgraded to {impact}: {tier1['worstCase'][dim]}").strip("; ")
        entry["evidencePointers"] = entry.get("evidencePointers", []) + [tier_ref]
        entry["judgedAt"] = utc_now()
    vector_doc = attempt.trust_vector_document(suffix=f"-{label}", supersedes=prior["recordId"], dimensions=dims)
    tv_ref = attempt.store.write_canonical(f"trust_vector_{label}.json", vector_doc, role="TRUST_VECTOR", parents=[tier_ref["artifactId"]])
    attempt.dimensions = dims
    decision = attempt.decision_document(vector_doc, tv_ref, suffix=f"_{label}")
    attempt.store.write_canonical(f"claim_gate_decision_{label}.json", decision, role="CLAIM_GATE_DECISION", parents=[tv_ref["artifactId"]])
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.setdefault("redTeam", {})[label] = {
        "passed": tier1["passed"], "dimensionImpact": tier1["dimensionImpact"], "worstCase": tier1["worstCase"],
        "trustVectorAfter": {d: dims[d]["status"] for d in DIMENSIONS},
        "allowedClaimsAfter": attempt.summary["allowedClaims"], "highestAllowedClaimAfter": attempt.summary["highestAllowedClaim"]}
    attempt.store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    attempt.store.transition(attempt.state.value, attempt.state.value, gate=None,
                             result=f"TIER1:{'PASS' if tier1['passed'] else 'DOWNGRADE'}", detail=str(tier1["dimensionImpact"]))
    log(f"Tier-1 {'PASS' if tier1['passed'] else 'DOWNGRADE'}: {tier1['dimensionImpact']}; highest allowed claim {attempt.summary['highestAllowedClaim']}")


# ------------------------------------------------------------------ G6

def reproduction_tolerance(attempt_dir: Path | None = None) -> dict[str, Any]:
    """The tolerance frozen in the reproduction package (preregistered before the formal run)."""

    package = EXPERIMENT_DIR / "repro_package" / "PACKAGE_MANIFEST.json"
    if package.exists():
        return load_json(package)["expectedTolerance"]
    if attempt_dir is not None:
        identity = load_json(attempt_dir / "identity.json")
        config = load_json(repo_root() / identity["configPath"])
        return config["reproduction"]
    raise SystemExit("no preregistered reproduction tolerance found")


def judge_reproduction(original_dir: Path, reproduction_dir: Path, *, write: bool = True,
                       environment_override: Mapping[str, Any] | None = None,
                       environment_id_override: str | None = None) -> dict[str, Any]:
    """Constitution 54 (A-0001): same specHash, same codeHash, independent environment, different seed set, dev metrics within tolerance."""

    original_record = load_json(original_dir / "run_record.json")
    original_training = load_json(original_dir / "training_report.json")["seedStatistics"]
    repro_record = load_json(reproduction_dir / "run_record.json")
    repro_training = load_json(reproduction_dir / "training_report.json")["seedStatistics"]
    if validate_run_record(original_record) or validate_run_record(repro_record):
        raise SystemExit("a RunRecord does not validate; reproduction cannot be judged")
    tolerance = reproduction_tolerance(original_dir)
    env_b_map = dict(environment_override) if environment_override else repro_record["environment"]
    env_b_id = environment_id_override or repro_record["environmentId"]
    env_a = EnvironmentFingerprint.from_mapping(original_record["environment"])
    env_b = EnvironmentFingerprint.from_mapping(env_b_map)
    independent = independent_environments(env_a, env_b)
    differing = sorted(k for k in env_a.strong_material() if original_record["environment"][k] != env_b_map.get(k))
    same_spec = original_record["specHash"] == repro_record["specHash"]
    same_code = original_record["codeHash"] == repro_record["codeHash"]
    different_seeds = original_record["seedSetId"] != repro_record["seedSetId"]
    a_med, b_med = original_training["median"], repro_training["median"]
    median_diff = abs(a_med - b_med) if math.isfinite(a_med) and math.isfinite(b_med) else math.inf
    verdict_agree = original_training["status"] == repro_training["status"]
    relative_limit = float(tolerance.get("devRelL2MedianRelDiff", math.inf)) * abs(a_med) if math.isfinite(a_med) else math.inf
    within = (median_diff <= float(tolerance["devRelL2MedianAbsDiff"]) and median_diff <= relative_limit
              and (verdict_agree or not tolerance.get("seedProtocolVerdictMustAgree", True)))
    original_q = RunQualification(run_id=original_record["runId"], spec_hash=original_record["specHash"], code_hash=original_record["codeHash"],
                                  environment_id=original_record["environmentId"], seed_set_id=original_record["seedSetId"])
    repro_q = RunQualification(run_id=repro_record["runId"], spec_hash=repro_record["specHash"], code_hash=repro_record["codeHash"],
                               environment_id=env_b_id, seed_set_id=repro_record["seedSetId"])
    verdict = reproduction_status(original_q, repro_q, within_tolerance=within)
    line = (f"independent={independent} ({differing}), sameSpec={same_spec}, sameCode={same_code}, differentSeeds={different_seeds}, "
            f"median A {a_med:.3e} vs B {b_med:.3e} (|diff| {median_diff:.3e}; absolute limit {tolerance['devRelL2MedianAbsDiff']}, "
            f"relative limit {relative_limit:.3e} = {tolerance.get('devRelL2MedianRelDiff')} x median A; within={within}), "
            f"verdict A {original_training['status']} vs B {repro_training['status']} -> C_repro {verdict.status.value}")
    report_doc = {
        "reproductionOf": original_dir.name, "originalRunId": original_record["runId"], "reproductionRunId": repro_record["runId"],
        "specHash": repro_record["specHash"], "sameSpec": same_spec, "codeHashA": original_record["codeHash"],
        "codeHashB": repro_record["codeHash"], "sameCode": same_code, "seedSetIdA": original_record["seedSetId"],
        "seedSetIdB": repro_record["seedSetId"], "seedsB": repro_record["seeds"], "differentSeedSet": different_seeds,
        "environmentA": original_record["environment"], "environmentIdA": original_record["environmentId"],
        "environmentB": env_b_map, "environmentIdB": env_b_id, "independentEnvironments": independent,
        "strongFieldsDiffering": differing, "tolerance": tolerance,
        "metrics": {"medianA": a_med, "medianB": b_med, "medianAbsDiff": median_diff, "successRateA": original_training["successRate"],
                    "successRateB": repro_training["successRate"], "verdictA": original_training["status"], "verdictB": repro_training["status"],
                    "iqrA": original_training["iqr"], "iqrB": repro_training["iqr"], "worstA": original_training["worst"],
                    "worstB": repro_training["worst"], "divergentB": repro_training["divergent"]},
        "relativeLimit": relative_limit, "medianDiffOverIqrA": (median_diff / original_training["iqr"]) if original_training["iqr"] > 0 else None,
        "withinTolerance": within, "cRepro": verdict.status.value, "problems": list(verdict.problems), "claimSetTouched": False,
        "judgedAt": utc_now(), "summaryLine": line,
    }
    if write:
        ArtifactStore(reproduction_dir, producer=EXECUTOR).write_json(
            "reproduction_report.json", report_doc, role="REPRODUCTION_REPORT", parents=["run_record.json", "training_report.json"])
        log(f"judge-reproduction {reproduction_dir.name}: {line}")
    return report_doc


def run_apply_g6(attempt_dir: Path, reproduction_dir: Path) -> None:
    attempt = resume_attempt(attempt_dir)
    if attempt.state is not WorkflowState.REPRODUCIBILITY_CHECK:
        raise SystemExit(f"Gate 6 executes in REPRODUCIBILITY_CHECK; attempt is in {attempt.state.value}")
    report_doc = load_json(reproduction_dir / "reproduction_report.json")
    if report_doc["reproductionOf"] != attempt_dir.name:
        raise SystemExit("reproduction report belongs to another attempt")
    repro_record = load_json(reproduction_dir / "run_record.json")
    if validate_run_record(repro_record):
        raise SystemExit("reproduction RunRecord invalid")
    status = TrustStatus(report_doc["cRepro"])
    reason = (f"independent reproduction {reproduction_dir.name}: environments independent={report_doc['independentEnvironments']} "
              f"(strong fields differing {report_doc['strongFieldsDiffering']}), same spec={report_doc['sameSpec']}, "
              f"same code={report_doc['sameCode']}, different seed set={report_doc['differentSeedSet']}, dev median A "
              f"{report_doc['metrics']['medianA']:.3e} vs B {report_doc['metrics']['medianB']:.3e} (|diff| "
              f"{report_doc['metrics']['medianAbsDiff']:.3e} vs tolerance {report_doc['tolerance']['devRelL2MedianAbsDiff']}), "
              f"k/N {report_doc['metrics']['successRateA']} vs {report_doc['metrics']['successRateB']} -> {status.value}")
    evidence = [{"artifactId": f"{reproduction_dir.name}/reproduction_report.json", "sha256": sha256_file(reproduction_dir / "reproduction_report.json")},
                {"artifactId": f"{reproduction_dir.name}/run_record.json", "sha256": sha256_file(reproduction_dir / "run_record.json")}]
    g6 = [gates2d.check("G6-independentReproduction", status, reason, evidence)]
    g6_ref = attempt.store.write_json("gate6_reproducibility_executed.json", {"checks": g6, "reproduction": report_doc}, role="GATE_RESULT")
    base_path = attempt_dir / "trust_vector_tier1.json" if (attempt_dir / "trust_vector_tier1.json").exists() else attempt_dir / "trust_vector.json"
    prior = load_json(base_path)
    dims = copy.deepcopy(prior["dimensions"])
    dims["repro"] = dimension_entry(status, g6, [g6_ref])
    attempt.dimensions = dims
    result = GATE_FROM_TRUST[status]
    vector_doc = attempt.trust_vector_document(suffix="-g6", supersedes=prior["recordId"], dimensions=dims)
    tv_ref = attempt.store.write_canonical("trust_vector_g6.json", vector_doc, role="TRUST_VECTOR", parents=[g6_ref["artifactId"]])
    decision = attempt.decision_document(vector_doc, tv_ref, suffix="_g6")
    cgd_ref = attempt.store.write_canonical("claim_gate_decision_g6.json", decision, role="CLAIM_GATE_DECISION", parents=[tv_ref["artifactId"]])
    signed = "C2" in attempt.summary["allowedClaims"]
    after = advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, result, attempt.vector(), claim_decision_signed=signed)
    attempt.store.transition(WorkflowState.REPRODUCIBILITY_CHECK.value, after.value, gate=6, result=result.value,
                             detail=f"C_repro={status.value} from {reproduction_dir.name}; ClaimGateDecision {cgd_ref['artifactId']} "
                                    f"allowed {attempt.summary['allowedClaims']}")
    attempt.save_state(after)
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.update({"g6": {"cRepro": status.value, "reproductionAttempt": reproduction_dir.name, "report": report_doc["metrics"],
                           "independentEnvironments": report_doc["independentEnvironments"]},
                    "finalState": after.value, "trustVectorFinal": {d: dims[d]["status"] for d in DIMENSIONS},
                    "allowedClaimsFinal": attempt.summary["allowedClaims"],
                    "highestAllowedClaimFinal": attempt.summary["highestAllowedClaim"], "decisionRefFinal": cgd_ref})
    attempt.store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    report2d.write_trust_report(attempt_dir, attempt.root)
    log(f"Gate 6 {result.value}: state {after.value}; vector {summary['trustVectorFinal']}; highest allowed claim {attempt.summary['highestAllowedClaim']}")


# ------------------------------------------------------------------ CLI

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poisson 2D calibration experiment runner")
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("attempt")
    a.add_argument("--config", type=Path, required=True)
    a.add_argument("--attempt-id", required=True)
    a.add_argument("--problem-id", required=True)
    a.add_argument("--revision", type=int, default=1)
    a.add_argument("--out-root", type=Path, default=EXPERIMENT_DIR / "runs")
    a.add_argument("--ledger", type=Path, default=None)
    a.add_argument("--reenter-from", type=Path, default=None)
    a.add_argument("--claim-pool-member", default=None)
    a.add_argument("--seed-offset", type=int, default=0)
    a.add_argument("--reproduction-of", type=Path, default=None)
    rp = sub.add_parser("register-pool")
    rp.add_argument("--problem-id", required=True)
    rp.add_argument("--members", nargs="+", required=True)
    rp.add_argument("--designated-start", type=int, default=1)
    rp.add_argument("--config", type=Path, required=True)
    f = sub.add_parser("finalize")
    f.add_argument("--attempt", type=Path, required=True)
    fd = sub.add_parser("failure-diagnostics")
    fd.add_argument("--attempt", type=Path, required=True)
    fd.add_argument("--gate", type=int, default=5)
    rt = sub.add_parser("redteam")
    rt.add_argument("--attempt", type=Path, required=True)
    rt.add_argument("--label", default="tier1")
    jr = sub.add_parser("judge-reproduction")
    jr.add_argument("--original", type=Path, required=True)
    jr.add_argument("--reproduction", type=Path, required=True)
    ag = sub.add_parser("apply-g6")
    ag.add_argument("--attempt", type=Path, required=True)
    ag.add_argument("--reproduction", type=Path, required=True)
    pl = sub.add_parser("plots")
    pl.add_argument("--attempt", type=Path, required=True)
    pk = sub.add_parser("repro-package")
    pk.add_argument("--attempt", type=Path, required=True)
    pk.add_argument("--out", type=Path, default=EXPERIMENT_DIR / "repro_package")
    args = parser.parse_args(argv)

    if args.command == "attempt":
        ledger = args.ledger or LEDGER_DIR / f"{args.problem_id}.json"
        attempt = Attempt2D(config_path=args.config, attempt_id=args.attempt_id, problem_id=args.problem_id, revision=args.revision,
                            out_root=args.out_root, ledger_path=ledger, reenter_from=args.reenter_from,
                            claim_pool_member=args.claim_pool_member, seed_offset=args.seed_offset,
                            reproduction_of=args.reproduction_of)
        summary = attempt.run()
        print(json.dumps({k: summary[k] for k in ("attemptId", "finalState", "trustVector", "highestAllowedClaim") if k in summary},
                         ensure_ascii=False, indent=2))
        return 0
    if args.command == "register-pool":
        run_register_pool(args.problem_id, args.members, args.designated_start, args.config)
        return 0
    if args.command == "finalize":
        attempt = resume_attempt(args.attempt)
        attempt.models = []
        state = WorkflowState(load_json(args.attempt / "attempt_state.json")["state"])
        attempt.finish(state, decision=state not in (WorkflowState.FAILURE_RECORDED, WorkflowState.STOPPED_THE_LINE))
        return 0
    if args.command == "failure-diagnostics":
        attempt = resume_attempt(args.attempt)
        attempt.runs = [load_json(p) for p in sorted(args.attempt.glob("runs/run-*.json"))]
        attempt.run_refs = [attempt.store.ref(f"runs/{p.name}") for p in sorted(args.attempt.glob("runs/run-*.json"))]
        attempt.models = [pinn2d.model_from_weights(attempt.config, r["weights"], threads=attempt.threads) for r in attempt.runs]
        attempt.phase_failure(gate=args.gate)
        return 0
    if args.command == "redteam":
        run_redteam(args.attempt, args.label)
        return 0
    if args.command == "judge-reproduction":
        judge_reproduction(args.original, args.reproduction)
        return 0
    if args.command == "apply-g6":
        run_apply_g6(args.attempt, args.reproduction)
        return 0
    if args.command == "plots":
        paths = report2d.plots(args.attempt)
        print(json.dumps([str(p) for p in paths], ensure_ascii=False, indent=2))
        return 0
    from .repro_package2d import write_package

    out = write_package(args.attempt, repo_root(), args.out)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
