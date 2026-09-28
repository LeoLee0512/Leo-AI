"""R3 minimal experimental runner: drive one Poisson 1D attempt through the amended state machine.

    attempt        --config C --attempt-id A --problem-id P [--revision r] [--claim-pool-member NAME] [--reenter-from DIR] [--seed-offset k]
    register-pool  --problem-id P --members GL640-CGL2400:640:2400 ...
    diagnose       --attempt DIR --levels 4 8 16 --seeds-per-level 5 [--baseline-attempt DIR]      (sampling, Experiment 2)
    bc-diagnose    --attempt DIR                                                                      (Experiment 3A/3B, sBcResidual)
    revise         --attempt DIR --revised-config C
    finalize / failure-diagnostics / plots / redteam / repro-package

Every document is validated by ``pinn.governance`` before it is written; every
transition goes through ``state_machine``.  Claim-set identity follows the
samples (``sampleSetHash`` on every ledger event, registry of legacy artifacts).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from pinn.governance.canonical import canonical_bytes, canonical_sha256
from pinn.governance.claim_set_ledger import derive_claim_set_state, make_event, validate_claim_set_ledger
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set, sample_set_hash
from pinn.governance.nodes import anti_collision
from pinn.governance.prelock import PrelockPaths, run_prelock
from pinn.governance.state_machine import (
    GATE_RUNS_IN,
    ROOT_CAUSE_GATE,
    FailureSignature,
    GateStatus,
    RootCauseClass,
    TriageRoute,
    WorkflowState,
    advance,
    diagnose,
    enter_validation,
    gate5_status,
    reenter,
    revise,
)
from pinn.governance.trust_loop import (
    diagnosis_coverage_errors,
    problem_definition_spec_hash,
    trust_vector_statuses,
    validate_claim_gate_decision,
    validate_diagnosis_record,
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
    environment_id,
    independent_environments,
    reproduction_status,
    seed_set_id,
)
from pinn.validation.poisson import load_candidate_protocol

from pinn.research.context import CURRENT, RunContext, using, data_path, actor

from . import bc_diagnosis, claim_metrics, criteria, datasets, diagnosis, gates, pinn_torch, redteam, report, repro_package
from .common import (
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
)

CONSTITUTION_VERSION = "1.2"
EXECUTOR = "pinn.experiments.runner (Claude, captain)"
GATE_FROM_TRUST = {TrustStatus.PASS: GateStatus.PASS, TrustStatus.FAIL: GateStatus.FAIL,
                   TrustStatus.PARTIAL: GateStatus.PARTIAL, TrustStatus.BLOCKED: GateStatus.BLOCKED,
                   TrustStatus.NOT_CHECKED: GateStatus.BLOCKED}
LEDGER_DIR = Path("experiments/poisson1d/ledger")
PROBLEMS_DIR = Path("experiments/poisson1d/problems")
REGISTRY_PATH = data_path(LEDGER_DIR) / "sample_set_registry.json"


def repo_root() -> Path:
    return CURRENT.get().code_root if CURRENT.get() else Path(__file__).resolve().parents[2]


def log(message: str) -> None:
    print(f"[{utc_now()}] {message}", flush=True)


def load_registry() -> dict[str, str]:
    return load_json(data_path(REGISTRY_PATH)) if data_path(REGISTRY_PATH).exists() else {}


def register_sample_set(manifest: Mapping[str, Any]) -> tuple[str, str]:
    """Record artifactHash -> sampleSetHash for a claim manifest (the resolver for legacy ledger events)."""

    registry = load_registry()
    artifact, samples = canonical_sha256(manifest), sample_set_hash(manifest)
    if registry.get(artifact, samples) != samples:
        raise SystemExit(f"registry binds artifact {artifact[:12]} to another sample identity")
    registry[artifact] = samples
    data_path(REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    data_path(REGISTRY_PATH).write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return artifact, samples


def write_ledger(path: Path, events: Sequence[Mapping[str, Any]]) -> None:
    errors = validate_claim_set_ledger(events, sample_set_hashes=load_registry())
    if errors:
        raise SystemExit(f"claim-set ledger invalid: {errors}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(events), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ ProblemDefinition

def build_problem_definition(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]], *, problem_id: str,
                             revision: int, root: Path, frozen_at: str) -> dict[str, Any]:
    spec_ref = {"artifactId": "governance/POISSON_1D_V1.0_spec.draft.json", "sha256": sha256_file(root / "governance/POISSON_1D_V1.0_spec.draft.json")}
    analytic_ref = {"artifactId": "pinn/reference/analytic_poisson.py", "sha256": sha256_file(root / "pinn/reference/analytic_poisson.py")}
    fdm_ref = {"artifactId": "scientific_reference/poisson_fdm.py", "sha256": sha256_file(root / "scientific_reference/poisson_fdm.py")}
    pre = config["preregistration"]
    enforcement = "hard" if config["network"].get("outputParameterization", "identity") != "identity" else "soft"
    document = {
        "schemaVersion": "pinn.problemDefinition/1.2",
        "problemId": problem_id,
        "revision": revision,
        "pde": {"form": "strong", "transient": False,
                "equations": [{"name": "poisson-1d", "expressionRef": spec_ref, "independentVars": ["x"], "dependentVars": ["u"]}]},
        "boundaryConditions": [
            {"name": "left-dirichlet", "type": "dirichlet", "regionRef": "x0", "expressionRef": spec_ref, "enforcement": enforcement},
            {"name": "right-dirichlet", "type": "dirichlet", "regionRef": "x1", "expressionRef": spec_ref, "enforcement": enforcement},
        ],
        "geometry": {"domainType": "interval", "dimension": 1, "regions": [
            {"id": "interior", "description": "0 < x < 1"}, {"id": "x0", "description": "x = 0"}, {"id": "x1", "description": "x = 1"}]},
        "parameters": [{"name": "forcing_amplitude_pi_squared", "value": math.pi ** 2, "unitRef": "1"},
                       {"name": "forcing_wavenumber_k", "value": 1.0, "unitRef": "1"}],
        "units": {"system": "nondimensional", "entries": [
            {"quantity": "length", "unit": "1", "symbolRef": "x"}, {"quantity": "field", "unit": "1", "symbolRef": "u"}]},
        "nondimensionalization": {"applied": False, "scales": [], "notes": "posed dimensionless by construction (spec draft v1.0)"},
        "variables": [
            {"name": "x", "role": "independent", "domainRange": [0.0, 1.0], "unitRef": "1"},
            {"name": "u", "role": "dependent", "domainRange": [-1.5, 1.5], "unitRef": "1"},
        ],
        "referenceSolution": {"sources": [
            {"sourceId": "src-analytic", "method": "analytical", "evidenceLevel": "A", "independenceDeclaration": True, "provenance": analytic_ref},
            {"sourceId": "src-fdm", "method": "numerical", "evidenceLevel": "B", "independenceDeclaration": True, "provenance": fdm_ref},
        ], "primarySourceId": "src-analytic"},
        "checkApplicability": [dict(entry) for entry in gates.REGISTRY],
        "preregistration": {"errorNorm": "relativeL2", "epsilonSpec": float(pre["epsilonSpec"]), "seedRuns": int(config["seedProtocol"]["runs"]),
                            "seedFactors": ["init", "sample", "batch"], "worstSeedFactor": float(pre["worstSeedFactor"]),
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
        "frozenBy": actor(EXECUTOR),
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


# ------------------------------------------------------------------ trust vector

def dimension_entry(status: TrustStatus, checks: Sequence[Mapping[str, Any]], evidence: Sequence[Mapping[str, str]], *,
                    notes: str = "", extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {"status": status.value}
    if status is TrustStatus.NOT_CHECKED:
        return entry
    entry.update({"evidencePointers": [dict(e) for e in evidence], "judgedAt": utc_now(), "judgedBy": actor(EXECUTOR),
                  "checks": [dict(c) for c in checks]})
    if notes:
        entry["notes"] = notes
    if extra:
        entry.update(extra)
    return entry


def statuses_of(dimensions: Mapping[str, Mapping[str, Any]]) -> dict[str, TrustStatus]:
    return {d: TrustStatus(dimensions[d]["status"]) for d in DIMENSIONS}


def pool_members(problem_id: str) -> dict[str, Any]:
    path = data_path(PROBLEMS_DIR) / f"{problem_id}-claim-pool.json"
    return load_json(path) if path.exists() else {"members": {}}


# ------------------------------------------------------------------ the attempt

class Attempt:
    def __init__(self, *, config_path: Path, attempt_id: str, problem_id: str, revision: int, out_root: Path,
                 ledger_path: Path, reenter_from: Path | None, claim_pool_member: str | None = None, seed_offset: int = 0,
                 reproduction_of: Path | None = None) -> None:
        self.root = repo_root()
        self.config_path = config_path
        self.config = load_json(config_path)
        self.attempt_id = attempt_id
        self.problem_id = problem_id
        self.revision = revision
        self.store = ArtifactStore(out_root / attempt_id)
        self.ledger_path = ledger_path
        self.reenter_from = reenter_from
        self.claim_pool_member = claim_pool_member
        self.seed_offset = int(seed_offset)
        self.reproduction_of = reproduction_of
        self.protocol = load_candidate_protocol(self.root)
        self.summary: dict[str, Any] = {"attemptId": attempt_id, "problemId": problem_id, "revision": revision,
                                        "constitutionVersion": CONSTITUTION_VERSION, "startedAt": utc_now()}
        self.dimensions: dict[str, dict[str, Any]] = {d: {"status": "NOT_CHECKED"} for d in DIMENSIONS}
        self.claim_grid: dict[str, Any] | None = None   # None -> frozen GL512 / CGL2000

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
        if CURRENT.get():
            from pinn.research.worker import scientific_identity
            manifest = scientific_identity(self.root)
        else:
            manifest = code_manifest(self.root, [config_rel])
        self.code_hash = code_hash_from_manifest(manifest)
        self.code_manifest = manifest
        self.environment = environment_fingerprint()
        self.environment_id = environment_identity(self.environment)
        identity = {"gitHead": git_head(self.root), "dirtyCodeIdentityPaths": dirty, "codeHash": self.code_hash,
                    "codeManifest": manifest, "configPath": config_rel, "configSha256": sha256_file(self.config_path),
                    "environment": self.environment, "environmentId": self.environment_id, "python": sys.version,
                    "constitutionVersion": CONSTITUTION_VERSION, "seedOffset": self.seed_offset}
        if CURRENT.get():
            identity["executionContext"] = CURRENT.get().document()
            if dirty:
                raise SystemExit("formal product run requires clean code identity")
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
        frozen_file = data_path(PROBLEMS_DIR) / f"{self.problem_id}-r{self.revision}.json"
        if self.claim_pool_member is None and frozen_file.exists():
            frozen_claim = load_json(frozen_file)["evaluationSets"]["claim"]["sha256"]
            for name, member in pool_members(self.problem_id)["members"].items():
                if member["artifactHash"] == frozen_claim:
                    self.claim_pool_member = name
                    log(f"frozen revision {self.revision} names pool member {name}; using it")
        if self.claim_pool_member:
            pool = pool_members(self.problem_id)["members"]
            if self.claim_pool_member not in pool:
                raise SystemExit(f"claim pool member {self.claim_pool_member!r} is not preregistered for {self.problem_id}")
            member = pool[self.claim_pool_member]
            if member["designatedRevision"] != self.revision:
                raise SystemExit(f"{self.claim_pool_member} is designated for revision {member['designatedRevision']}, not {self.revision}")
            if self.reproduction_of is None and member["status"] == "BURNT":
                raise SystemExit(f"{self.claim_pool_member} is BURNT; a formal attempt cannot reuse it")
            claim_manifest = datasets.claim_pool_manifests({self.claim_pool_member: (member["glOrder"], member["cglCount"])}, label=self.problem_id)[self.claim_pool_member]
            if canonical_sha256(claim_manifest) != member["artifactHash"] or sample_set_hash(claim_manifest) != member["sampleSetHash"]:
                raise SystemExit("regenerated pool member differs from the preregistered manifest")
            gl_nodes, gl_weights, cgl = datasets.claim_grid(member["glOrder"], member["cglCount"])
            self.claim_grid = {"label": self.claim_pool_member, "glOrder": member["glOrder"], "cglCount": member["cglCount"],
                               "glNodes": gl_nodes, "glWeights": gl_weights, "cglNodes": cgl}
            self.sets = datasets.build_sets(self.config, claim_nodes=self.protocol.quadrature_nodes,
                                            claim_pointwise=self.protocol.pointwise_nodes, claim_label=label)
            self.sets["claim"] = claim_manifest
        else:
            self.sets = datasets.build_sets(self.config, claim_nodes=self.protocol.quadrature_nodes,
                                            claim_pointwise=self.protocol.pointwise_nodes, claim_label=label)
        self.set_refs = {role: self.store.write_canonical(f"sets/{role}.json", doc, role="EVALUATION_SET") for role, doc in self.sets.items()}
        claim_artifact, claim_samples = register_sample_set(self.sets["claim"])
        isolation = datasets.isolation_report(self.sets, min_separation=self.config["sets"]["minSeparation"])
        isolation["claimSampleSetHash"] = claim_samples
        isolation["generation"] = {
            "train": f"pool of {self.config['sampling']['poolSize']} uniform interior points, numpy default_rng({self.config['sampling']['poolSeed']}), plus boundary {{0, 1}}",
            "dev": f"{self.config['sets']['devSize']} uniform interior points, numpy default_rng({self.config['sets']['devSeed']})",
            "phys": f"Gauss-Legendre order {self.config['sets']['physOrder']} nodes on [0,1]",
            "claim": (f"claim pool member {self.claim_pool_member}: GL{self.claim_grid['glOrder']} + CGL{self.claim_grid['cglCount']} without endpoints"
                      if self.claim_grid else "frozen protocol GL512 + CGL2000 nodes without the spec-known boundary coordinates {0, 1}"),
        }
        self.store.write_json("sets/isolation.json", isolation, role="EVALUATION_SET_ISOLATION", parents=[r["artifactId"] for r in self.set_refs.values()])
        if not isolation["disjoint"]:
            raise SystemExit(f"evaluation sets are not sample-disjoint: {isolation['errors']}")
        self.summary["evaluationSets"] = {"sizes": isolation["sizes"], "hashes": isolation["hashes"], "claimSampleSetHash": claim_samples}
        self.phys_nodes, self.phys_weights = datasets.gauss_legendre_unit(self.config["sets"]["physOrder"])
        self.store.write_json("sets/phys_weights.json", {"order": self.config["sets"]["physOrder"], "weights": self.phys_weights}, role="EVALUATION_SET")
        self.pool = datasets.points_of(self.sets["train"], "interior")
        self.dev_points = datasets.points_of(self.sets["dev"])

        problem_file = data_path(PROBLEMS_DIR) / f"{self.problem_id}-r{self.revision}.json"
        if problem_file.exists():
            pdef = load_json(problem_file)
            for role, doc in self.sets.items():
                if pdef["evaluationSets"][role]["sha256"] != canonical_sha256(doc):
                    raise SystemExit(f"frozen ProblemDefinition {problem_file.name} names another {role} set than the regenerated one")
            log(f"reusing frozen ProblemDefinition {problem_file.name} (frozenAt {pdef['frozenAt']})")
        else:
            pdef = build_problem_definition(self.config, self.sets, problem_id=self.problem_id, revision=self.revision, root=self.root, frozen_at=utc_now())
            problem_file.parent.mkdir(parents=True, exist_ok=True)
            problem_file.write_bytes(canonical_bytes(pdef))
            log(f"ProblemDefinition frozen to {problem_file.name} (enforcement {pdef['boundaryConditions'][0]['enforcement']})")
        events = load_json(self.ledger_path) if self.ledger_path.exists() else []
        state = derive_claim_set_state(events, problem_id=self.problem_id, revision=self.revision, claim_set_sha256=claim_artifact,
                                       sample_set_hashes=load_registry())
        if state.status == "NEVER_SEALED":
            if claim_samples in state.burnt_samples:
                raise SystemExit(f"claim samples {claim_samples[:12]} are BURNT (opened under {state.burnt_sample_artifacts[claim_samples][:12]}); refusing to seal")
            events.append(make_event(prev_event_id=events[-1]["eventId"] if events else "GENESIS", problemId=self.problem_id,
                                     revision=self.revision, specHash=pdef["specHash"], claimSetSha256=claim_artifact, sampleSetHash=claim_samples,
                                     event="SEALED", actor=actor(EXECUTOR), at=utc_now()))
            log(f"claim set {claim_artifact[:12]} (samples {claim_samples[:12]}) SEALED for {self.problem_id} r{self.revision}")
        write_ledger(self.ledger_path, events)
        self.events = events
        pdef = apply_ledger_state(pdef, events)
        errors = validate_problem_definition(pdef, claim_set_events=events, evaluation_sets=self.sets, sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid: {errors}")
        self.pdef = pdef
        self.pdef_ref = self.store.write_canonical("problem_definition.json", pdef, role="PROBLEM_DEFINITION", parents=[r["artifactId"] for r in self.set_refs.values()])
        if CURRENT.get():
            # Gate 1–3 refer to the sealed version even after OPENED updates the current record.
            self.pdef_ref = self.store.write_canonical("problem_definition_sealed.json", pdef,
                role="PROBLEM_DEFINITION", parents=[r["artifactId"] for r in self.set_refs.values()])
        self.store.write_canonical("claim_set_ledger.json", events, role="LEDGER")
        self.summary.update({"specHash": pdef["specHash"], "claimSetSha256": claim_artifact, "claimSampleSetHash": claim_samples,
                             "ledgerHead": events[-1]["eventId"]})
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
            upstream_dims = [d for g in range(1, gate) for d in gates_dimensions(g)]
            upstream = {d: TrustStatus(prior[d]["status"]) if d in upstream_dims else TrustStatus.NOT_CHECKED for d in DIMENSIONS}
            for d in upstream_dims:
                self.dimensions[d] = dict(prior[d])
            self.save_state(WorkflowState.REVISED)
            start = reenter(WorkflowState.REVISED, route, upstream)
            self.move(WorkflowState.REVISED, start, gate=gate, result="REENTER",
                      detail=f"re-entry at Gate {gate} after {cause.value}; Gate {gate} and downstream dimensions reset to NOT_CHECKED")
            self.summary["reentry"] = {"from": str(self.reenter_from), "gate": gate, "rootCause": cause.value}

        g1 = gates.gate1_math(self.pdef, [self.pdef_ref])
        g1_ref = self.store.write_json("gate1_math.json", {"checks": g1}, role="GATE_RESULT", parents=[self.pdef_ref["artifactId"]])
        g2, g2_detail = gates.gate2_baseline(self.phys_nodes, [self.set_refs["phys"]])
        g2_ref = self.store.write_json("gate2_baseline.json", {"checks": g2, "detail": g2_detail}, role="GATE_RESULT", parents=[self.set_refs["phys"]["artifactId"]])
        g3, g3_detail = gates.gate3_implementation(self.config, self.sets, self.protocol, self.dev_points, [self.set_refs["dev"]])
        g3_ref = self.store.write_json("gate3_implementation.json", {"checks": g3, "detail": g3_detail}, role="GATE_RESULT", parents=[self.set_refs["dev"]["artifactId"]])
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
            "registeredAt": utc_now(), "rule": f"init={sp['initBase']}+{off}+i, sample={sp['sampleBase']}+{off}+i, batch={sp['batchBase']}+{off}+i, i in 0..{sp['runs'] - 1}",
            "triplets": triplets, "seedSetId": seed_set_id(seed_values), "appendOnly": True,
            "note": "registered before the first run started (Constitution 10.1)"}, role="SEED_LEDGER")
        self.started_at = utc_now()
        self.runs = []
        run_refs = []
        for triplet in triplets:
            seeds = {k: triplet[k] for k in ("init", "sample", "batch")}
            log(f"training seed triplet {seeds} with collocationCount={self.config['sampling']['collocationCount']}")
            run = pinn_torch.train_run(self.config, self.pool, self.dev_points, seeds, collocation_count=int(self.config["sampling"]["collocationCount"]))
            run["runIndex"] = triplet["index"]
            run_refs.append(self.store.write_json(f"runs/run-{triplet['index']:02d}.json", run, role="RAW_MODEL_PREDICTION",
                                                  parents=[ledger_ref["artifactId"], self.set_refs["train"]["artifactId"]]))
            self.runs.append(run)
            log(f"  done: devRelL2={run['devRelL2']:.3e} completed={run['completed']} nan={run['nanEncountered']} {run['elapsedSeconds']:.1f}s")
        self.finished_at = utc_now()
        self.run_refs = run_refs
        self.models = [pinn_torch.model_from_weights(self.config, run["weights"]) for run in self.runs]
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
            "startedAt": self.started_at, "finishedAt": max(self.finished_at, utc_now()), "executedBy": actor(EXECUTOR),
        }
        errors = validate_run_record(record)
        if errors:
            raise SystemExit(f"RunRecord invalid: {errors}")
        self.run_record = record
        self.run_record_ref = self.store.write_canonical("run_record.json", record, role="RUN_RECORD", parents=[r["artifactId"] for r in self.run_refs])

    def phase_gate4(self) -> WorkflowState:
        g4, detail = gates.gate4_training(self.runs, self.pdef["preregistration"], [self.set_refs["dev"]])
        detail["seedSetId"] = seed_set_id(self.seed_values)
        detail["devSetSha256"] = self.pdef["evaluationSets"]["dev"]["sha256"]
        g4_ref = self.store.write_json("gate4_training.json", {"checks": g4, "detail": detail}, role="GATE_RESULT", parents=[r["artifactId"] for r in self.run_refs])
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
                  detail=f"C_train={status.value}: {detail['seedStatistics']['successRate']} within epsilon_spec, median {detail['seedStatistics']['median']:.3e}")
        return after

    def phase_failure(self, gate: int = 4) -> None:
        bins = int(self.config["signatureCriteria"]["sLocalizedError"]["bins"])
        per_seed = [diagnosis.dev_diagnostics(m, self.dev_points, self.phys_nodes, self.phys_weights, bins) for m in self.models]
        stats = load_json(self.store.root / "gate4_training.json")["detail"]["seedStatistics"]
        observed = diagnosis.observed_signatures(per_seed, stats, self.config["signatureCriteria"], float(self.pdef["preregistration"]["epsilonSpec"]))
        observed["perSeedCurves"] = [{"u": d["u"], "residuals": d["residuals"], "pointwiseAbsError": d["pointwiseAbsError"], "binRms": d["binRms"]} for d in per_seed]
        observed["devPoints"] = self.dev_points
        claim_note = None
        if gate == 5 and (self.store.root / "gate5b_external.json").exists():
            g5b = load_json(self.store.root / "gate5b_external.json")
            claim_note = {"failedMustPerSeed": [m["failedMust"] for m in g5b["perSeed"]],
                          "note": "Gate 5 FAIL on the OPENED claim set; the signatures below are measured on D_dev / D_phys only"}
        ref = self.store.write_json("failure_record.json", {
            "state": WorkflowState.FAILURE_RECORDED.value, "gate": gate, "recordedAt": utc_now(), "claimSetVerdict": claim_note,
            "observedSignatures": observed["observedSignatures"], "rules": observed["rules"], "medians": observed["medians"],
            "perSeed": observed["perSeed"], "seedStatistics": stats, "retrainedInPlace": False, "constitutionVersion": CONSTITUTION_VERSION,
        }, role="FAILURE_RECORD", parents=[r["artifactId"] for r in self.run_refs])
        self.store.write_json("dev_diagnostics.json", observed, role="DIAGNOSTICS", parents=[ref["artifactId"]])
        self.summary["failure"] = {"gate": gate, "observedSignatures": observed["observedSignatures"], "medians": observed["medians"]}
        log(f"FAILURE_RECORDED at Gate {gate}; observedSignatures={observed['observedSignatures']}")

    def claim_evaluation(self, model) -> dict[str, Any]:
        if self.claim_grid is None:
            return gates.claim_evaluation(model, self.protocol)
        g = self.claim_grid
        fld_gl = pinn_torch.fields(model, g["glNodes"])
        fld_cgl = pinn_torch.fields(model, g["cglNodes"])
        fld_b = pinn_torch.fields(model, [0.0, 1.0])
        return claim_metrics.evaluate_on_grids(gl_nodes=g["glNodes"], gl_weights=g["glWeights"], cgl_nodes=g["cglNodes"],
                                               u_gl=fld_gl["u"], du_gl=fld_gl["ux"], d2u_gl=fld_gl["uxx"], u_cgl=fld_cgl["u"],
                                               u_boundary=[fld_cgl["u"][0], fld_cgl["u"][-1]], du_boundary=fld_b["ux"], grid_label=g["label"])

    def phase_validation(self) -> WorkflowState:
        state = enter_validation(WorkflowState.TRAINING_COMPLETED)
        self.move(WorkflowState.TRAINING_COMPLETED, state, gate=None, result="ENTER_VALIDATION")
        g5a, detail_a = gates.physics_checks(self.models, self.phys_nodes, self.phys_weights, self.config["physicsThresholds"], [self.set_refs["phys"]])
        detail_a["thresholdSource"] = self.config["thresholdSources"]["physics"]
        g5a_ref = self.store.write_json("gate5a_physics.json", {"checks": g5a, "detail": detail_a}, role="GATE_RESULT",
                                        parents=[self.set_refs["phys"]["artifactId"]] + [r["artifactId"] for r in self.run_refs])
        physics = self.judge("physics", g5a, [g5a_ref])
        claim_sha = self.pdef["evaluationSets"]["claim"]["sha256"]
        claim_samples = self.summary["claimSampleSetHash"]
        self.events.append(make_event(prev_event_id=self.events[-1]["eventId"], problemId=self.problem_id, revision=self.revision,
                                      specHash=self.pdef["specHash"], claimSetSha256=claim_sha, sampleSetHash=claim_samples, event="OPENED",
                                      codeHash=self.code_hash, actor=actor(EXECUTOR), at=utc_now()))
        write_ledger(self.ledger_path, self.events)
        self.store.write_canonical("claim_set_ledger.json", self.events, role="LEDGER")
        self.pdef = apply_ledger_state(self.pdef, self.events)
        errors = validate_problem_definition(self.pdef, claim_set_events=self.events, evaluation_sets=self.sets, sample_set_hashes=load_registry())
        if errors:
            raise SystemExit(f"ProblemDefinition invalid after OPENED: {errors}")
        self.pdef_ref = self.store.write_canonical("problem_definition.json", self.pdef, role="PROBLEM_DEFINITION")
        self.summary["ledgerHead"] = self.events[-1]["eventId"]
        log(f"claim set {claim_sha[:12]} (samples {claim_samples[:12]}) OPENED at revision {self.revision} with codeHash {self.code_hash[:12]} -> BURNT")
        evaluations = [self.claim_evaluation(m) for m in self.models]
        g5b = gates.external_checks(evaluations, self.pdef["evaluationSets"]["claim"], [self.set_refs["claim"]])
        g5b_ref = self.store.write_json("gate5b_external.json", {
            "checks": g5b, "claimSetSha256": claim_sha, "claimSampleSetHash": claim_samples, "openedAtRevision": self.revision, "codeHash": self.code_hash,
            "grid": self.claim_grid["label"] if self.claim_grid else "GL512-CGL2000 (frozen protocol, trusted validator)",
            "perSeed": [{"metrics": {k: v["value"] for k, v in e["metrics"].items()}, "satisfied": {k: v["criterionSatisfied"] for k, v in e["metrics"].items()},
                         "failedMust": e["failedMustCriteria"], "failedShould": e["failedShouldCriteria"],
                         "diagnostics": {k: v for k, v in e["diagnostics"].items() if k != "boundaryResiduals"}} for e in evaluations],
            "thresholds": {k: v["threshold"] for k, v in evaluations[0]["metrics"].items()},
            "validator": "pinn.validation.poisson.evaluate_samples" if self.claim_grid is None else "pinn.experiments.claim_metrics.evaluate_on_grids (identical formulas, fresh grid)",
        }, role="VALIDATION_METRIC", parents=[self.set_refs["claim"]["artifactId"]] + [r["artifactId"] for r in self.run_refs])
        external = self.judge("external", g5b, [g5b_ref], evaluationSet="claim", claimSetSha256=claim_sha)
        self.summary["claimEvaluation"] = {"perSeedAC1": [e["metrics"]["AC-1"]["value"] for e in evaluations],
                                           "perSeedAC3": [e["metrics"]["AC-3"]["value"] for e in evaluations],
                                           "failedMust": [e["failedMustCriteria"] for e in evaluations]}
        self.write_run_record(claim_opened=True)
        gate5 = gate5_status(physics=GATE_FROM_TRUST[physics], external=GATE_FROM_TRUST[external])
        after = advance(WorkflowState.VALIDATION, 5, gate5, self.vector())
        self.move(WorkflowState.VALIDATION, after, gate=5, result=gate5.value,
                  detail=f"C_physics={physics.value}, C_external={external.value} on claim set {claim_sha[:12]} (samples {claim_samples[:12]})")
        return after

    def phase_reproduction(self, after_gate4: WorkflowState) -> dict[str, Any]:
        """G6 reproduction run (new-code runner): judge against the original right away (see ``judge_reproduction``)."""

        report_doc = judge_reproduction(self.reproduction_of, self.store.root, write=False,
                                        environment_override=self.environment, environment_id_override=self.environment_id)
        report_doc["gate4State"] = after_gate4.value
        self.store.write_json("reproduction_report.json", report_doc, role="REPRODUCTION_REPORT", parents=["run_record.json", "training_report.json"])
        self.summary["reproduction"] = {"cRepro": report_doc["cRepro"], "independent": report_doc["independentEnvironments"],
                                        "withinTolerance": report_doc["withinTolerance"], "medianAbsDiff": report_doc["metrics"]["medianAbsDiff"],
                                        "strongFieldsDiffering": report_doc["strongFieldsDiffering"], "sameCode": report_doc["sameCode"]}
        log(f"G6 reproduction: {report_doc['summaryLine']}")
        return report_doc

    def phase_gate6(self) -> WorkflowState:
        reason = ("Independent reproduction has not yet been applied to this attempt. "
                  "G6 remains BLOCKED until an independently qualified reproduction is verified (Constitution 54).")
        g6 = gates.gate6_blocked(reason, [self.run_record_ref])
        g6_ref = self.store.write_json("gate6_reproducibility.json", {"checks": g6, "environment": self.environment, "environmentId": self.environment_id}, role="GATE_RESULT")
        repro = self.judge("repro", g6, [g6_ref])
        result = GATE_FROM_TRUST[repro]
        after = advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, result, self.vector())
        self.move(WorkflowState.REPRODUCIBILITY_CHECK, after, gate=6, result=result.value, detail="C_repro BLOCKED: protocol not executed")
        return after

    def decision_document(self, vector_doc: Mapping[str, Any], tv_ref: Mapping[str, str], *, suffix: str = "", stop: bool = False) -> dict[str, Any]:
        gate = claim_gate(trust_vector_statuses(vector_doc), evidence_level="A", spec_hash=self.pdef["specHash"], code_hash=self.code_hash,
                          exploratory=False, stop_the_line=stop)
        statements = {
            "C0": "The frozen Poisson 1D problem definition is mathematically consistent and the implementation computes this problem (math, impl PASS).",
            "C1": "Under the frozen training protocol the PINN training is reliable across the preregistered seed set (train PASS); accuracy is not asserted.",
            "C2": "Every seed model agrees with the analytic reference within the preregistered AC-1..AC-7 on the opened blind claim set and satisfies the physics checks; Tier-1 Red Team maintained; independent reproduction confirmed.",
            "C3": "The C2 result holds across >= 5 independently qualified runs of the same method identity.",
        }
        statement_ref = self.store.write_json(f"claim_statements{suffix}.json", statements, role="CLAIM_STATEMENT")
        evidence_refs = [dict(tv_ref)] + [self.store.ref(p) for p in ("gate4_training.json", "gate5b_external.json") if (self.store.root / p).exists()]
        decision = {
            "schemaVersion": "pinn.claimGateDecision/1.2", "decisionId": f"cgd-{self.attempt_id}{suffix.replace('_', '-')}", "problemId": self.problem_id,
            "revision": self.revision, "specHash": self.pdef["specHash"], "codeHash": self.code_hash,
            "claimSetSha256": self.pdef["evaluationSets"]["claim"]["sha256"], "ledgerHead": self.events[-1]["eventId"],
            "trustVectorRef": {"artifactId": vector_doc["recordId"], "sha256": tv_ref["sha256"]}, "referenceEvidenceLevel": "A",
            "runMode": "FORMAL", "qualifiedC2Runs": [],
            "allowedClaims": [{"level": lvl, "statementRef": statement_ref, "evidenceRefs": evidence_refs,
                               "failureConditions": [{"condition": "the frozen ProblemDefinition, reference or code identity is revised", "consequence": "INVALIDATE_DECISION"},
                                                     {"condition": "a later independent reproduction falls outside the preregistered tolerance", "consequence": "DOWNGRADE"}]}
                              for lvl in gate.allowed],
            "blockedClaims": [{"level": lvl, "reason": "; ".join(gate.blocked.get(lvl, ("not licensed",))), "missingPreconditions": list(gate.blocked.get(lvl, ()))}
                              for lvl in CLAIM_LEVELS if lvl not in gate.allowed],
            "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value, "evidenceRef": dict(tv_ref)},
            "generatedAt": utc_now(), "decidedBy": actor(EXECUTOR),
        }
        errors = validate_claim_gate_decision(decision, vector_doc, self.pdef, claim_set_events=self.events, run_records={self.run_record["runId"]: self.run_record})
        if errors:
            raise SystemExit(f"ClaimGateDecision invalid: {errors}")
        self.summary.update({"allowedClaims": list(gate.allowed), "highestAllowedClaim": gate.highest_allowed or "BLOCKED",
                             "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value}})
        return decision

    def phase_decision(self, final_state: WorkflowState) -> None:
        vector_doc = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{self.attempt_id}", "problemId": self.problem_id,
                      "revision": self.revision, "specHash": self.pdef["specHash"], "dimensions": self.dimensions}
        errors = validate_trust_vector(vector_doc, self.pdef)
        if errors:
            raise SystemExit(f"TrustVector invalid: {errors}")
        tv_ref = self.store.write_canonical("trust_vector.json", vector_doc, role="TRUST_VECTOR")
        decision = self.decision_document(vector_doc, tv_ref, stop=final_state is WorkflowState.STOPPED_THE_LINE)
        cgd_ref = self.store.write_canonical("claim_gate_decision.json", decision, role="CLAIM_GATE_DECISION", parents=[tv_ref["artifactId"]])
        self.summary.update({"currentTrustVectorRef": tv_ref, "currentDecisionRef": cgd_ref, "finalState": final_state.value, "trustVector": {d: self.dimensions[d]["status"] for d in DIMENSIONS},
                             "trustVectorRef": tv_ref, "decisionRef": cgd_ref, "finishedAt": utc_now()})

    def finish(self, final_state: WorkflowState, *, decision: bool) -> dict[str, Any]:
        if decision:
            self.phase_decision(final_state)
        else:
            vector_doc = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{self.attempt_id}", "problemId": self.problem_id,
                          "revision": self.revision, "specHash": self.pdef["specHash"], "dimensions": self.dimensions}
            errors = validate_trust_vector(vector_doc, self.pdef)
            if errors:
                raise SystemExit(f"TrustVector invalid: {errors}")
            self.store.write_canonical("trust_vector.json", vector_doc, role="TRUST_VECTOR")
            self.summary.update({"finalState": final_state.value, "trustVector": {d: self.dimensions[d]["status"] for d in DIMENSIONS},
                                 "allowedClaims": [], "highestAllowedClaim": ("n/a (G6 reproduction attempt; claims are decided on the original attempt)"
                                                                               if self.reproduction_of is not None else
                                                                               "BLOCKED (no ClaimGateDecision: the line is in FAILURE_RECORDED)"),
                                 "finishedAt": utc_now()})
        self.store.write_json("RUN_SUMMARY.json", self.summary, role="SUMMARY")
        report.write_trust_report(self.store.root, self.root)
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


def gates_dimensions(gate: int) -> tuple[str, ...]:
    from pinn.governance.state_machine import GATE_DIMENSIONS

    return GATE_DIMENSIONS[gate]


def resume_attempt(attempt_dir: Path) -> "Attempt":
    root = repo_root()
    identity = load_json(attempt_dir / "identity.json")
    pdef = load_json(attempt_dir / "problem_definition.json")
    state_doc = load_json(attempt_dir / "attempt_state.json")
    ledger_path = data_path(LEDGER_DIR) / f"{pdef['problemId']}.json"
    attempt = Attempt(config_path=root / identity["configPath"], attempt_id=attempt_dir.name, problem_id=pdef["problemId"], revision=pdef["revision"],
                      out_root=attempt_dir.parent, ledger_path=ledger_path, reenter_from=None, seed_offset=identity.get("seedOffset", 0))
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
    attempt.phys_nodes, attempt.phys_weights = datasets.gauss_legendre_unit(attempt.config["sets"]["physOrder"])
    attempt.pool = datasets.points_of(attempt.sets["train"], "interior")
    attempt.dev_points = datasets.points_of(attempt.sets["dev"])
    if (attempt_dir / "run_record.json").exists():
        attempt.run_record = load_json(attempt_dir / "run_record.json")
        attempt.run_record_ref = attempt.store.ref("run_record.json")
    isolation = load_json(attempt_dir / "sets/isolation.json")
    attempt.summary.update({"codeHash": attempt.code_hash, "environmentId": attempt.environment_id, "gitHead": identity["gitHead"],
                            "workspaceDirty": bool(identity["dirtyCodeIdentityPaths"]), "configId": attempt.config["configId"],
                            "prelock": load_json(attempt_dir / "prelock.json")["prelockStatus"], "specHash": pdef["specHash"],
                            "claimSetSha256": pdef["evaluationSets"]["claim"]["sha256"], "claimSampleSetHash": isolation.get("claimSampleSetHash", sample_set_hash(attempt.sets["claim"])),
                            "ledgerHead": attempt.events[-1]["eventId"], "evaluationSets": {"sizes": isolation["sizes"], "hashes": isolation["hashes"]},
                            "resumedFinalisation": {"at": utc_now(), "note": "assembled by the runner at the current git HEAD from the stored gate results; codeHash is the training/opening code identity recorded in identity.json"}})
    if (attempt_dir / "gate4_training.json").exists():
        attempt.summary["training"] = load_json(attempt_dir / "gate4_training.json")["detail"]["seedStatistics"]
    if (attempt_dir / "gate5b_external.json").exists():
        g5b = load_json(attempt_dir / "gate5b_external.json")
        attempt.summary["claimEvaluation"] = {"perSeedAC1": [m["metrics"]["AC-1"] for m in g5b["perSeed"]], "failedMust": [m["failedMust"] for m in g5b["perSeed"]]}
    return attempt


# ------------------------------------------------------------------ claim pool

def run_register_pool(problem_id: str, members: Sequence[str], designated_start: int) -> None:
    root = repo_root()
    spec = {}
    for item in members:
        name, gl, cgl = item.split(":")
        spec[name] = (int(gl), int(cgl))
    manifests = datasets.claim_pool_manifests(spec, label=problem_id)
    registry_before = load_registry()
    ledger_path = data_path(LEDGER_DIR) / f"{problem_id}.json"
    events = load_json(ledger_path) if ledger_path.exists() else []
    burnt_samples: dict[str, str] = {}
    for e in events:
        if e["event"] == "OPENED":
            sample = e.get("sampleSetHash") or registry_before.get(e["claimSetSha256"])
            if sample:
                burnt_samples[sample] = e["claimSetSha256"]
    # isolation against train / dev / phys of the frozen r1 definition and against each other
    r1 = load_json(data_path(PROBLEMS_DIR) / f"{problem_id}-r1.json")
    config = None
    for attempt in sorted(Path("experiments/poisson1d/runs").glob("*")):
        pd = attempt / "problem_definition.json"
        if pd.exists() and load_json(pd)["problemId"] == problem_id:
            config = load_json(root / load_json(attempt / "identity.json")["configPath"])
            base_sets = {role: load_json(attempt / f"sets/{role}.json") for role in ("train", "dev", "phys")}
            break
    if config is None:
        raise SystemExit("no attempt of this problem found to take train / dev / phys from")
    loaded_base = {role: load_evaluation_set(doc) for role, doc in base_sets.items()}
    out = {"schema": "leo.claimPool/1.0", "problemId": problem_id, "registeredAt": utc_now(), "constitutionVersion": CONSTITUTION_VERSION,
           "identityRule": "sampleSetHash = canonical_sha256(sorted(sample identities)); burn follows sampleSetHash (ledger L4s/L6/L7/L8)",
           "burntBefore": {v: k for k, v in burnt_samples.items()}, "members": {}}
    names = list(manifests)
    for index, name in enumerate(names):
        doc = manifests[name]
        artifact, samples = register_sample_set(doc)
        points = [s["inputs"][0] for s in doc["samples"]]
        ac = anti_collision(points, 64)
        loaded = load_evaluation_set(doc)
        iso = disjointness_errors({**loaded_base, "claim": loaded}, min_separation=config["sets"]["minSeparation"])
        pairwise = {other: len(set(loaded.identities) & set(load_evaluation_set(manifests[other]).identities)) for other in names if other != name}
        member = {"glOrder": spec[name][0], "cglCount": spec[name][1], "artifactId": doc["artifactId"], "artifactHash": artifact, "sampleSetHash": samples,
                  "sampleCount": len(points), "designatedRevision": designated_start + index, "antiCollisionMinDistance": ac.min_distance,
                  "antiCollisionOk": ac.min_distance > 1e-12, "isolationErrors": iso, "sharedWithOtherMembers": pairwise,
                  "burnt": samples in burnt_samples, "status": "SEALED"}
        if not member["antiCollisionOk"] or iso or any(pairwise.values()) or member["burnt"]:
            raise SystemExit(f"pool member {name} not admissible: {member}")
        out["members"][name] = member
        (data_path(PROBLEMS_DIR) / f"{problem_id}-claim-{name}.json").write_bytes(canonical_bytes(doc))
        # preregistration seal at revision 1 (the pool is registered before any revision consumes it)
        events.append(make_event(prev_event_id=events[-1]["eventId"] if events else "GENESIS", problemId=problem_id, revision=1,
                                 specHash=r1["specHash"], claimSetSha256=artifact, sampleSetHash=samples, event="SEALED",
                                 actor=actor(EXECUTOR) + " [claim pool preregistration]", at=utc_now()))
        log(f"pool member {name}: {len(points)} samples, sampleSetHash {samples[:12]}, designated revision {member['designatedRevision']}, SEALED")
    write_ledger(ledger_path, events)
    (data_path(PROBLEMS_DIR) / f"{problem_id}-claim-pool.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ Experiment 2 diagnosis (sampling)

def run_diagnose(attempt_dir: Path, levels: Sequence[int], seeds_per_level: int, baseline_attempt: Path | None) -> None:
    root = repo_root()
    store = ArtifactStore(attempt_dir)
    state_doc = load_json(attempt_dir / "attempt_state.json")
    if state_doc["state"] != WorkflowState.FAILURE_RECORDED.value:
        raise SystemExit(f"diagnosis starts from FAILURE_RECORDED, attempt is in {state_doc['state']}")
    identity = load_json(attempt_dir / "identity.json")
    config = load_json(root / identity["configPath"])
    pdef = load_json(attempt_dir / "problem_definition.json")
    failure = load_json(attempt_dir / "failure_record.json")
    sets = {role: load_json(attempt_dir / f"sets/{role}.json") for role in ("train", "dev", "phys", "claim")}
    pool = datasets.points_of(sets["train"], "interior")
    dev_points = datasets.points_of(sets["dev"])
    observed = failure["observedSignatures"]
    if not observed:
        raise SystemExit("no observed signature fired; nothing to diagnose")
    primary = "sPinnCfd" if "sPinnCfd" in observed else ("sLocalizedError" if "sLocalizedError" in observed else observed[0])
    log(f"diagnosing {attempt_dir.name}: observed={observed}, primary={primary}; controlled sampling intervention levels={list(levels)} x {seeds_per_level} seeds")
    plan_ref = store.write_json("intervention_plan.json", {
        "registeredAt": utc_now(), "factor": "sampling", "changed": ["sampling"], "levels": [int(v) for v in levels], "seedsPerLevel": int(seeds_per_level),
        "heldFixed": ["architecture", "optimizer", "lrSchedule", "lossWeights", "trainingBudget", "spec", "reference", "seedProtocol"],
        "evaluationSet": "dev", "candidateRootCauses": "every admissible cause of every observed signature under Constitution 1.2",
        "decisionRule": "name rSamplingDeficiency only if the per-level median dev error strictly decreases with sampling density and every other candidate is excluded by recorded evidence; otherwise rUndetermined and STOP_THE_LINE",
    }, role="INTERVENTION_PLAN")
    result = diagnosis.run_intervention(config, pool, dev_points, levels, seeds_per_level, config["seedProtocol"])
    intervention_ref = store.write_json("intervention.json", result, role="DISCRIMINATING_EXPERIMENT", parents=[plan_ref["artifactId"]])
    g2 = load_json(attempt_dir / "gate2_baseline.json")["detail"]
    g3 = load_json(attempt_dir / "gate3_implementation.json")["detail"]
    baseline_text = "not available"
    if baseline_attempt is not None and (baseline_attempt / "gate4_training.json").exists():
        b = load_json(baseline_attempt / "gate4_training.json")["detail"]["seedStatistics"]
        baseline_text = f"median {b['median']:.2e} with k/N = {b['successRate']} (attempt {baseline_attempt.name}, same architecture / optimizer / spec, {config['sampling']['collocationCount']} points)"
    failing_level = next((lvl for lvl in result["levels"] if lvl["collocationCount"] == int(config["sampling"]["collocationCount"])), result["levels"][0])
    facts = {
        "errorSpan": f"from {result['levels'][0]['medianError']:.2e} ({result['levels'][0]['level']}) to {result['levels'][-1]['medianError']:.2e} ({result['levels'][-1]['level']})",
        "T1": g3["T1"]["maxSecondDerivativeDiff"], "T3": g3["T3"]["residualMaxOnReference"], "T4": g3["T4"]["boundaryLossOnReference"],
        "G2a": g2["analyticResidualMax"], "fdmOrders": [round(o["order"], 3) for o in g2["fdm"].get("orders", []) if isinstance(o, dict) and isinstance(o.get("order"), (int, float))][-4:],
        "bestLevelMedian": result["levels"][-1]["medianError"], "baselineMedian": baseline_text,
        "architecture": f"{config['network']['hiddenLayers']}x{config['network']['width']} {config['network']['activation']}",
        "failingTrainLoss": min(r["finalLoss"]["pde"] for r in failing_level["runs"] if r["finalLoss"]), "failingMedian": failing_level["medianError"],
    }
    excludes = diagnosis.exclusion_records(observed, facts, constitution_version=CONSTITUTION_VERSION)
    evidence_map = {
        "sPinnCfd": {"pinnProvenance": store.ref("run_record.json"), "referenceProvenance": store.ref("gate2_baseline.json"), "gridConvergence": store.ref("gate2_baseline.json")},
        "sLocalizedError": {"errorSpatialDistribution": store.ref("dev_diagnostics.json"), "samplingConfigDiff": intervention_ref},
        "sBcResidual": {"boundaryResidualDistribution": store.ref("dev_diagnostics.json"), "samplingConfigDiff": intervention_ref, "hardConstraintDiff": store.ref("gate3_implementation.json")},
        "sConservation": {"conservationResiduals": store.ref("dev_diagnostics.json"), "admissibilityChecks": store.ref("gate2_baseline.json")},
        "sSeedSensitive": {"multiSeedStatistics": store.ref("gate4_training.json")},
    }
    record = diagnosis.diagnosis_record(
        diagnosis_id=f"dg-{attempt_dir.name}-r1", problem_id=pdef["problemId"], revision=pdef["revision"], spec_hash=pdef["specHash"],
        constitution_version=CONSTITUTION_VERSION, observed=observed, primary=primary, root_cause="rSamplingDeficiency",
        signature_evidence=evidence_map[primary], experiment_id="exp-int-sampling", excludes=excludes,
        intervention=diagnosis.intervention_document(result), evidence_pointers=[intervention_ref, store.ref("failure_record.json")],
        round_no=1, decided_by=actor(EXECUTOR), decided_at=utc_now())
    finish_diagnosis(store, attempt_dir, record, evidence_map[primary], observed, primary, "rSamplingDeficiency", result, intervention_ref)


def finish_diagnosis(store: ArtifactStore, attempt_dir: Path, record: dict[str, Any], signature_evidence: Mapping[str, Any],
                     observed: Sequence[str], primary: str, attempted: str, experiment_result: Mapping[str, Any],
                     evidence_ref: Mapping[str, str]) -> None:
    record_errors = validate_diagnosis_record(record, constitution_version=CONSTITUTION_VERSION)
    coverage = diagnosis_coverage_errors([record]) if not record_errors else []
    evidence = {key: ref["artifactId"] for key, ref in signature_evidence.items()}
    evidence["discriminatingExperiment"] = record["discriminatingExperiment"]
    evidence["explainedSignatures"] = [FailureSignature(s) for s in observed]
    verdict: dict[str, Any] = {"attempted": attempted, "recordErrors": record_errors, "coverageErrors": coverage}
    state, route = None, None
    if attempted != "rUndetermined" and not record_errors and not coverage:
        try:
            state, route = diagnose(WorkflowState.FAILURE_RECORDED, FailureSignature(primary), RootCauseClass(attempted), evidence, constitution_version=CONSTITUTION_VERSION)
        except ValueError as exc:
            verdict["stateMachineRefusal"] = str(exc)
    if state is None:
        if attempted != "rUndetermined":
            log(f"{attempted} cannot be named: {verdict}; filing rUndetermined and stopping the line")
        record = dict(record, rootCause="rUndetermined", discriminatingExperiment={
            "experimentId": record["discriminatingExperiment"]["experimentId"], "evaluationSet": "dev", "excludes": {},
            "evidencePointers": record["discriminatingExperiment"]["evidencePointers"]})
        record_errors = validate_diagnosis_record(record, constitution_version=CONSTITUTION_VERSION)
        if record_errors:
            raise SystemExit(f"rUndetermined record invalid: {record_errors}")
        evidence["discriminatingExperiment"] = record["discriminatingExperiment"]
        state, route = diagnose(WorkflowState.FAILURE_RECORDED, FailureSignature(primary), RootCauseClass.UNDETERMINED, evidence, constitution_version=CONSTITUTION_VERSION)
    store.write_canonical("diagnosis_record.json", record, role="DIAGNOSIS_RECORD", parents=[evidence_ref["artifactId"]])
    store.write_json("diagnosis_verdict.json", {**verdict, "rootCause": record["rootCause"], "state": state.value,
                                                "route": None if route is None else {"gate": route.gate, "reentryState": route.reentry_state.value},
                                                "experimentSummary": {k: v for k, v in experiment_result.items() if k in ("medianStrictlyDecreasing", "criterion", "criterionSummary", "decision", "medians")}},
                     role="DIAGNOSIS_VERDICT")
    store.transition(WorkflowState.FAILURE_RECORDED.value, state.value, gate=None if route is None else route.gate,
                     result=f"DIAGNOSED:{record['rootCause']}" if route else f"STOP:{record['rootCause']}", detail=f"observed={list(observed)}")
    (attempt_dir / "attempt_state.json").write_text(json.dumps({"state": state.value, "at": utc_now(),
                                                                "dimensions": load_json(attempt_dir / "attempt_state.json").get("dimensions")}, indent=2) + "\n",
                                                   encoding="utf-8", newline="\n")
    log(f"diagnosis: rootCause={record['rootCause']} state={state.value}")


# ------------------------------------------------------------------ Experiment 3A / 3B diagnosis (boundary)

def run_bc_diagnose(attempt_dir: Path) -> None:
    root = repo_root()
    store = ArtifactStore(attempt_dir)
    state_doc = load_json(attempt_dir / "attempt_state.json")
    if state_doc["state"] != WorkflowState.FAILURE_RECORDED.value:
        raise SystemExit(f"diagnosis starts from FAILURE_RECORDED, attempt is in {state_doc['state']}")
    identity = load_json(attempt_dir / "identity.json")
    config = load_json(root / identity["configPath"])
    pdef = load_json(attempt_dir / "problem_definition.json")
    failure = load_json(attempt_dir / "failure_record.json")
    observed = failure["observedSignatures"]
    if observed != ["sBcResidual"]:
        raise SystemExit(f"bc-diagnose expects observedSignatures == [sBcResidual], got {observed}")
    sets = {role: load_json(attempt_dir / f"sets/{role}.json") for role in ("train", "dev", "phys")}
    pool = datasets.points_of(sets["train"], "interior")
    dev_points = datasets.points_of(sets["dev"])
    plan_ref = store.write_json("bc_intervention_plan.json", {
        "registeredAt": utc_now(), "preregistration": "experiments/poisson1d/EXPERIMENT3_PREREGISTRATION_20260916.md sections 3-7",
        "3A": {"factor": "lossWeights.bc", "levels": list(bc_diagnosis.LAMBDA_LEVELS), "pairedSeeds": int(config["seedProtocol"]["runs"]),
               "criterion": {"rho": criteria.RHO, "q": criteria.Q, "minPairedSeeds": criteria.MIN_PAIRED_SEEDS}},
        "3B": {"change": "outputParameterization x(1-x)N (hard Dirichlet)", "pairedSeeds": int(config["seedProtocol"]["runs"])},
        "evaluationSet": "dev / phys only; no claim set is opened", "decisionRules": "section 6", "revisionRules": "section 7",
    }, role="INTERVENTION_PLAN")
    weight_path = attempt_dir / "bc_intervention_3a.json"
    if weight_path.exists():
        weight = load_json(weight_path)
        log("3A results already on disk; not re-running (resume-safe)")
    else:
        log("Experiment 3A: soft-boundary weight intervention (30 paired runs)")
        weight = bc_diagnosis.run_weight_intervention(config, pool, dev_points, log=log)
        store.write_json("bc_intervention_3a.json", weight, role="DISCRIMINATING_EXPERIMENT", parents=[plan_ref["artifactId"]])
    hard_path = attempt_dir / "bc_intervention_3b.json"
    if hard_path.exists():
        hard = load_json(hard_path)
        log("3B results already on disk; not re-running (resume-safe)")
    else:
        log("Experiment 3B: hard Dirichlet parameterization (10 paired runs)")
        hard = bc_diagnosis.run_hard_bc(config, pool, dev_points, log=log)
        store.write_json("bc_intervention_3b.json", hard, role="DISCRIMINATING_EXPERIMENT", parents=[plan_ref["artifactId"]])
    weight_ref, hard_ref = store.ref("bc_intervention_3a.json"), store.ref("bc_intervention_3b.json")
    decision = bc_diagnosis.decide_root_cause(weight, hard)
    revision = bc_diagnosis.revision_choice(decision, weight)
    store.write_json("bc_decision.json", {**decision, "revisionChoice": revision, "decidedAt": utc_now()}, role="DIAGNOSIS_DECISION",
                     parents=[weight_ref["artifactId"], hard_ref["artifactId"]])
    log(f"decision: {decision['rootCause']} ({decision['branch']}); revision {revision}")
    g2 = load_json(attempt_dir / "gate2_baseline.json")["detail"]
    g3 = load_json(attempt_dir / "gate3_implementation.json")["detail"]
    facts = {"T1": g3["T1"]["maxSecondDerivativeDiff"], "T3": g3["T3"]["residualMaxOnReference"], "T4": g3["T4"]["boundaryLossOnReference"], "G2a": g2["analyticResidualMax"]}
    root_cause = decision["rootCause"]
    excludes = bc_diagnosis.exclusions(weight, hard, facts, named=root_cause, constitution_version=CONSTITUTION_VERSION) if root_cause != "rUndetermined" else {}
    signature_evidence = {"boundaryResidualDistribution": store.ref("dev_diagnostics.json"), "samplingConfigDiff": weight_ref, "hardConstraintDiff": hard_ref}
    record = diagnosis.diagnosis_record(
        diagnosis_id=f"dg-{attempt_dir.name}-bc-r1", problem_id=pdef["problemId"], revision=pdef["revision"], spec_hash=pdef["specHash"],
        constitution_version=CONSTITUTION_VERSION, observed=observed, primary="sBcResidual", root_cause=root_cause,
        signature_evidence=signature_evidence, experiment_id="exp-3a-weight", excludes=excludes, intervention=None,
        evidence_pointers=[weight_ref, hard_ref, store.ref("failure_record.json"), store.ref("bc_decision.json")],
        round_no=1, decided_by=actor(EXECUTOR), decided_at=utc_now())
    finish_diagnosis(store, attempt_dir, record, signature_evidence, observed, "sBcResidual", root_cause,
                     {"criterion": weight["criterion"], "criterionSummary": weight["criterionSummary"], "decision": decision}, weight_ref)


# ------------------------------------------------------------------ revise

def run_revise(attempt_dir: Path, revised_config: Path) -> None:
    root = repo_root()
    store = ArtifactStore(attempt_dir)
    state_doc = load_json(attempt_dir / "attempt_state.json")
    if state_doc["state"] != WorkflowState.DIAGNOSED.value:
        raise SystemExit(f"REVISED follows DIAGNOSED, attempt is in {state_doc['state']}")
    identity = load_json(attempt_dir / "identity.json")
    before = load_json(root / identity["configPath"])
    after = load_json(revised_config)
    record = load_json(attempt_dir / "diagnosis_record.json")
    root_cause = record["rootCause"]
    changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
    allowed_top = {"configId", "description"}
    detail: dict[str, Any] = {}
    if root_cause == "rSamplingDeficiency":
        allowed_top |= {"sampling"}
        sub = {k for k in set(before["sampling"]) | set(after["sampling"]) if before["sampling"].get(k) != after["sampling"].get(k)}
        if sub != {"collocationCount"}:
            raise SystemExit(f"revision must change only sampling.collocationCount, changed {sorted(sub)}")
        detail["sampling.collocationCount"] = {"before": before["sampling"]["collocationCount"], "after": after["sampling"]["collocationCount"]}
    elif root_cause == "rOptimizationFailure":
        allowed_top |= {"lossWeights"}
        sub = {k for k in set(before["lossWeights"]) | set(after["lossWeights"]) if before["lossWeights"].get(k) != after["lossWeights"].get(k)}
        if sub != {"bc"}:
            raise SystemExit(f"revision must change only lossWeights.bc, changed {sorted(sub)}")
        choice = load_json(attempt_dir / "bc_decision.json")["revisionChoice"]
        if choice.get("value") != after["lossWeights"]["bc"]:
            raise SystemExit(f"revised lossWeights.bc {after['lossWeights']['bc']} is not the preregistered choice {choice}")
        detail["lossWeights.bc"] = {"before": before["lossWeights"]["bc"], "after": after["lossWeights"]["bc"]}
    elif root_cause == "rSpecDefect":
        allowed_top |= {"network"}
        sub = {k for k in set(before["network"]) | set(after["network"]) if before["network"].get(k) != after["network"].get(k)}
        if sub != {"outputParameterization"} or after["network"].get("outputParameterization") != "x(1-x)N":
            raise SystemExit(f"a spec revision may only switch the boundary enforcement to hard, changed {sorted(sub)}")
        detail["network.outputParameterization"] = {"before": before["network"].get("outputParameterization", "identity"), "after": "x(1-x)N"}
        detail["boundaryConditions.enforcement"] = {"before": "soft", "after": "hard"}
    else:
        raise SystemExit(f"no revision is defined for root cause {root_cause}")
    if not changed <= allowed_top:
        raise SystemExit(f"revision changes more than the diagnosed factor: {sorted(changed)}")
    state = revise(WorkflowState.DIAGNOSED)
    store.write_json("revision_record.json", {
        "revisedAt": utc_now(), "rootCause": root_cause, "changed": detail,
        "unchanged": sorted(set(before) - {k for k in changed}), "beforeConfig": identity["configPath"],
        "afterConfig": revised_config.resolve().relative_to(root).as_posix(), "afterConfigSha256": sha256_file(revised_config), "state": state.value,
    }, role="REVISION_RECORD")
    store.transition(WorkflowState.DIAGNOSED.value, state.value, gate=None, result="REVISED", detail=f"only {list(detail)} changed")
    (attempt_dir / "attempt_state.json").write_text(json.dumps({"state": state.value, "at": utc_now(), "dimensions": state_doc.get("dimensions")}, indent=2) + "\n",
                                                   encoding="utf-8", newline="\n")
    log(f"REVISED ({root_cause}): {detail}")


# ------------------------------------------------------------------ Tier-1 Red Team

def run_redteam(attempt_dir: Path, label: str = "tier1") -> None:
    attempt = resume_attempt(attempt_dir)
    if attempt.state is not WorkflowState.REPRODUCIBILITY_CHECK and attempt.state is not WorkflowState.ACCEPTED:
        raise SystemExit(f"Tier-1 runs after Gate 5 PASS; attempt is in {attempt.state.value}")
    baseline_run = load_json(attempt_dir / "runs/run-00.json")
    log("Tier-1 Red Team: P1, P4, P6, P8, P9, P16 (one retrain each, D_dev only); P7, P11 NOT_APPLICABLE")
    tier1 = redteam.run_tier1(attempt.config, attempt.pool, attempt.dev_points, attempt.phys_nodes, attempt.phys_weights, baseline_run, log=log)
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
    vector_doc = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{attempt.attempt_id}-{label}", "problemId": attempt.problem_id,
                  "revision": attempt.revision, "specHash": attempt.pdef["specHash"], "supersedesRecordId": prior["recordId"], "dimensions": dims}
    errors = validate_trust_vector(vector_doc, attempt.pdef)
    if errors:
        raise SystemExit(f"Tier-1 TrustVector invalid: {errors}")
    tv_ref = attempt.store.write_canonical(f"trust_vector_{label}.json", vector_doc, role="TRUST_VECTOR", parents=[tier_ref["artifactId"]])
    attempt.dimensions = dims
    decision = attempt.decision_document(vector_doc, tv_ref, suffix=f"_{label}")
    cgd_ref = attempt.store.write_canonical(f"claim_gate_decision_{label}.json", decision, role="CLAIM_GATE_DECISION", parents=[tv_ref["artifactId"]])
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.update({"currentTrustVectorRef": tv_ref, "currentDecisionRef": cgd_ref})
    summary.setdefault("redTeam", {})[label] = {"passed": tier1["passed"], "dimensionImpact": tier1["dimensionImpact"], "worstCase": tier1["worstCase"],
                                              "trustVectorAfter": {d: dims[d]["status"] for d in DIMENSIONS},
                                              "allowedClaimsAfter": attempt.summary["allowedClaims"], "highestAllowedClaimAfter": attempt.summary["highestAllowedClaim"]}
    attempt.store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    attempt.store.transition(attempt.state.value, attempt.state.value, gate=None, result=f"TIER1:{'PASS' if tier1['passed'] else 'DOWNGRADE'}",
                             detail=str(tier1["dimensionImpact"]))
    log(f"Tier-1 {'PASS' if tier1['passed'] else 'DOWNGRADE'}: {tier1['dimensionImpact']}; highest allowed claim {attempt.summary['highestAllowedClaim']}")


# ------------------------------------------------------------------ G6 judgement of a stored reproduction attempt

def judge_reproduction(original_dir: Path, reproduction_dir: Path, *, write: bool = True,
                       environment_override: Mapping[str, Any] | None = None, environment_id_override: str | None = None) -> dict[str, Any]:
    """Constitution 54 (A-0001): same specHash, same codeHash, independent environment, different seed set, dev metrics within the frozen tolerance.

    Reads only stored records (RunRecord, training_report) of both attempts; never touches a claim set.
    """

    original_record = load_json(original_dir / "run_record.json")
    original_training = load_json(original_dir / "training_report.json")["seedStatistics"]
    repro_record = load_json(reproduction_dir / "run_record.json")
    repro_training = load_json(reproduction_dir / "training_report.json")["seedStatistics"]
    if validate_run_record(original_record) or validate_run_record(repro_record):
        raise SystemExit("a RunRecord does not validate; reproduction cannot be judged")
    tolerance = {"devRelL2MedianAbsDiff": 1e-4, "seedProtocolVerdictMustAgree": True}
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
    within = median_diff <= float(tolerance["devRelL2MedianAbsDiff"]) and (verdict_agree or not tolerance.get("seedProtocolVerdictMustAgree", True))
    original_q = RunQualification(run_id=original_record["runId"], spec_hash=original_record["specHash"], code_hash=original_record["codeHash"],
                                  environment_id=original_record["environmentId"], seed_set_id=original_record["seedSetId"])
    repro_q = RunQualification(run_id=repro_record["runId"], spec_hash=repro_record["specHash"], code_hash=repro_record["codeHash"],
                               environment_id=env_b_id, seed_set_id=repro_record["seedSetId"])
    verdict = reproduction_status(original_q, repro_q, within_tolerance=within)
    line = (f"independent={independent} ({differing}), sameSpec={same_spec}, sameCode={same_code}, differentSeeds={different_seeds}, "
            f"median A {a_med:.3e} vs B {b_med:.3e} (|diff| {median_diff:.3e} <= {tolerance['devRelL2MedianAbsDiff']}: {median_diff <= tolerance['devRelL2MedianAbsDiff']}), "
            f"verdict A {original_training['status']} vs B {repro_training['status']} -> C_repro {verdict.status.value}")
    report_doc = {
        "reproductionOf": original_dir.name, "originalRunId": original_record["runId"], "reproductionRunId": repro_record["runId"],
        "specHash": repro_record["specHash"], "sameSpec": same_spec, "codeHashA": original_record["codeHash"], "codeHashB": repro_record["codeHash"], "sameCode": same_code,
        "seedSetIdA": original_record["seedSetId"], "seedSetIdB": repro_record["seedSetId"], "seedsB": repro_record["seeds"], "differentSeedSet": different_seeds,
        "environmentA": original_record["environment"], "environmentIdA": original_record["environmentId"],
        "environmentB": env_b_map, "environmentIdB": env_b_id, "independentEnvironments": independent, "strongFieldsDiffering": differing,
        "tolerance": tolerance,
        "metrics": {"medianA": a_med, "medianB": b_med, "medianAbsDiff": median_diff, "successRateA": original_training["successRate"],
                    "successRateB": repro_training["successRate"], "verdictA": original_training["status"], "verdictB": repro_training["status"],
                    "iqrA": original_training["iqr"], "iqrB": repro_training["iqr"], "worstA": original_training["worst"], "worstB": repro_training["worst"],
                    "divergentB": repro_training["divergent"]},
        "withinTolerance": within, "cRepro": verdict.status.value, "problems": list(verdict.problems), "claimSetTouched": False,
        "judgedAt": utc_now(), "summaryLine": line,
    }
    if write:
        store = ArtifactStore(reproduction_dir)
        store.write_json("reproduction_report.json", report_doc, role="REPRODUCTION_REPORT", parents=["run_record.json", "training_report.json"])
        log(f"judge-reproduction {reproduction_dir.name}: {line}")
    return report_doc


# ------------------------------------------------------------------ G6 on the original attempt

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
    verified = judge_reproduction(attempt_dir, reproduction_dir, write=False)
    for key in ("cRepro", "sameSpec", "sameCode", "independentEnvironments", "differentSeedSet", "withinTolerance", "metrics"):
        if report_doc[key] != verified[key]:
            raise SystemExit("reproduction report disagrees with measured records")
    status = TrustStatus(verified["cRepro"])
    reason = (f"independent reproduction {reproduction_dir.name}: environments independent={report_doc['independentEnvironments']} "
              f"(strong fields differing {report_doc['strongFieldsDiffering']}), same spec={report_doc['sameSpec']}, same code={report_doc['sameCode']}, "
              f"different seed set={report_doc['differentSeedSet']}, dev median A {report_doc['metrics']['medianA']:.3e} vs B {report_doc['metrics']['medianB']:.3e} "
              f"(|diff| {report_doc['metrics']['medianAbsDiff']:.3e} vs tolerance {report_doc['tolerance']['devRelL2MedianAbsDiff']}), "
              f"k/N {report_doc['metrics']['successRateA']} vs {report_doc['metrics']['successRateB']} -> {status.value}")
    evidence = [{"artifactId": f"{reproduction_dir.name}/reproduction_report.json", "sha256": sha256_file(reproduction_dir / "reproduction_report.json")},
                {"artifactId": f"{reproduction_dir.name}/run_record.json", "sha256": sha256_file(reproduction_dir / "run_record.json")}]
    if CURRENT.get():
        # Product evidence pointers are resolvable within the original attempt.
        # Copy exact bytes, retaining the separately verified reproduction attempt.
        for pointer in evidence:
            src = reproduction_dir / Path(pointer["artifactId"]).name
            target = attempt_dir / pointer["artifactId"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(src.read_bytes())
            attempt.store.register(pointer["artifactId"], sha256_file(target), role="REPRODUCTION_EVIDENCE")
    g6 = [gates.check("G6-independentReproduction", status, reason, evidence)]
    g6_ref = attempt.store.write_json("gate6_reproducibility_executed.json", {"checks": g6, "reproduction": report_doc}, role="GATE_RESULT")
    current_summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    current_ref = current_summary.get("currentTrustVectorRef")
    base_vector_path = attempt_dir / current_ref["artifactId"] if current_ref else (attempt_dir / "trust_vector_tier1v2.json" if (attempt_dir / "trust_vector_tier1v2.json").exists() else attempt_dir / "trust_vector.json")
    if current_ref and sha256_file(base_vector_path) != current_ref["sha256"]:
        raise SystemExit("current trust vector identity mismatch")
    prior = load_json(base_vector_path)
    dims = copy.deepcopy(prior["dimensions"])
    dims["repro"] = dimension_entry(status, g6, [g6_ref])
    attempt.dimensions = dims
    result = GATE_FROM_TRUST[status]
    vector_doc = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{attempt.attempt_id}-g6", "problemId": attempt.problem_id,
                  "revision": attempt.revision, "specHash": attempt.pdef["specHash"], "supersedesRecordId": prior["recordId"], "dimensions": dims}
    errors = validate_trust_vector(vector_doc, attempt.pdef)
    if errors:
        raise SystemExit(f"G6 TrustVector invalid: {errors}")
    tv_ref = attempt.store.write_canonical("trust_vector_g6.json", vector_doc, role="TRUST_VECTOR", parents=[g6_ref["artifactId"]])
    decision = attempt.decision_document(vector_doc, tv_ref, suffix="_g6")
    cgd_ref = attempt.store.write_canonical("claim_gate_decision_g6.json", decision, role="CLAIM_GATE_DECISION", parents=[tv_ref["artifactId"]])
    signed = "C2" in attempt.summary["allowedClaims"]
    after = advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, result, attempt.vector(), claim_decision_signed=signed)
    attempt.store.transition(WorkflowState.REPRODUCIBILITY_CHECK.value, after.value, gate=6, result=result.value,
                             detail=f"C_repro={status.value} from {reproduction_dir.name}; ClaimGateDecision {cgd_ref['artifactId']} allowed {attempt.summary['allowedClaims']}")
    attempt.save_state(after)
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.update({"currentTrustVectorRef": tv_ref, "currentDecisionRef": cgd_ref, "g6": {"cRepro": status.value, "reproductionAttempt": reproduction_dir.name, "report": report_doc["metrics"],
                           "independentEnvironments": report_doc["independentEnvironments"]},
                    "finalState": after.value, "trustVectorFinal": {d: dims[d]["status"] for d in DIMENSIONS},
                    "allowedClaimsFinal": attempt.summary["allowedClaims"], "highestAllowedClaimFinal": attempt.summary["highestAllowedClaim"],
                    "decisionRefFinal": cgd_ref})
    attempt.store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    report.write_trust_report(attempt_dir, attempt.root)
    log(f"Gate 6 {result.value}: state {after.value}; vector {summary['trustVectorFinal']}; highest allowed claim {attempt.summary['highestAllowedClaim']}")


# ------------------------------------------------------------------ CLI

def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if "--context" in values:
        index = values.index("--context")
        context_file = Path(values[index + 1])
        del values[index:index + 2]
        with using(RunContext.from_document(load_json(context_file))):
            return _main(values)
    return _main(values)


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R3 minimal Poisson 1D experiment runner")
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("attempt")
    a.add_argument("--config", required=True, type=Path)
    a.add_argument("--attempt-id", required=True)
    a.add_argument("--problem-id", required=True)
    a.add_argument("--revision", type=int, default=1)
    a.add_argument("--out-root", type=Path, default=Path("experiments/poisson1d/runs"))
    a.add_argument("--ledger", type=Path, default=None)
    a.add_argument("--reenter-from", type=Path, default=None)
    a.add_argument("--claim-pool-member", default=None)
    a.add_argument("--seed-offset", type=int, default=0)
    a.add_argument("--reproduction-of", type=Path, default=None, help="G6 mode: reproduce this attempt; stop after Gate 4")
    rp = sub.add_parser("register-pool")
    rp.add_argument("--problem-id", required=True)
    rp.add_argument("--members", nargs="+", required=True, help="NAME:glOrder:cglCount ...")
    rp.add_argument("--designated-start", type=int, default=2)
    d = sub.add_parser("diagnose")
    d.add_argument("--attempt", required=True, type=Path)
    d.add_argument("--levels", nargs="+", type=int, required=True)
    d.add_argument("--seeds-per-level", type=int, default=5)
    d.add_argument("--baseline-attempt", type=Path, default=None)
    bd = sub.add_parser("bc-diagnose")
    bd.add_argument("--attempt", required=True, type=Path)
    r = sub.add_parser("revise")
    r.add_argument("--attempt", required=True, type=Path)
    r.add_argument("--revised-config", required=True, type=Path)
    f = sub.add_parser("finalize")
    f.add_argument("--attempt", required=True, type=Path)
    fd = sub.add_parser("failure-diagnostics")
    fd.add_argument("--attempt", required=True, type=Path)
    fd.add_argument("--gate", type=int, required=True)
    pl = sub.add_parser("plots")
    pl.add_argument("--experiment", required=True, choices=("1", "2"))
    pl.add_argument("--attempt", required=True, type=Path)
    pl.add_argument("--revised-attempt", type=Path, default=None)
    pl.add_argument("--baseline-attempt", type=Path, default=None)
    rt = sub.add_parser("redteam")
    rt.add_argument("--attempt", required=True, type=Path)
    rt.add_argument("--label", default="tier1")
    jr = sub.add_parser("judge-reproduction")
    jr.add_argument("--original", required=True, type=Path)
    jr.add_argument("--reproduction", required=True, type=Path)
    ag = sub.add_parser("apply-g6")
    ag.add_argument("--attempt", required=True, type=Path)
    ag.add_argument("--reproduction", required=True, type=Path)
    rpk = sub.add_parser("repro-package")
    rpk.add_argument("--attempt", required=True, type=Path)
    rpk.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "attempt":
        ledger = args.ledger or data_path(LEDGER_DIR) / f"{args.problem_id}.json"
        attempt = Attempt(config_path=args.config, attempt_id=args.attempt_id, problem_id=args.problem_id, revision=args.revision,
                          out_root=args.out_root, ledger_path=ledger, reenter_from=args.reenter_from, claim_pool_member=args.claim_pool_member,
                          seed_offset=args.seed_offset, reproduction_of=args.reproduction_of)
        summary = attempt.run()
        print(json.dumps({k: summary[k] for k in ("attemptId", "finalState", "trustVector", "highestAllowedClaim") if k in summary}, indent=2))
        return 0
    if args.command == "register-pool":
        run_register_pool(args.problem_id, args.members, args.designated_start)
        return 0
    if args.command == "diagnose":
        run_diagnose(args.attempt, args.levels, args.seeds_per_level, args.baseline_attempt)
        return 0
    if args.command == "bc-diagnose":
        run_bc_diagnose(args.attempt)
        return 0
    if args.command == "revise":
        run_revise(args.attempt, args.revised_config)
        return 0
    if args.command == "finalize":
        attempt = resume_attempt(args.attempt)
        decision = attempt.state not in (WorkflowState.FAILURE_RECORDED, WorkflowState.STOPPED_THE_LINE)
        summary = attempt.finish(attempt.state, decision=decision)
        print(json.dumps({k: summary[k] for k in ("attemptId", "finalState", "trustVector", "highestAllowedClaim") if k in summary}, indent=2))
        return 0
    if args.command == "failure-diagnostics":
        attempt = resume_attempt(args.attempt)
        attempt.runs = [load_json(p) for p in sorted(args.attempt.glob("runs/run-*.json"))]
        attempt.run_refs = [attempt.store.ref(f"runs/{p.name}") for p in sorted(args.attempt.glob("runs/run-*.json"))]
        attempt.models = [pinn_torch.model_from_weights(attempt.config, run["weights"]) for run in attempt.runs]
        attempt.phase_failure(gate=args.gate)
        attempt.finish(attempt.state, decision=False)
        return 0
    if args.command == "plots":
        paths = report.plots_experiment1(args.attempt) if args.experiment == "1" else report.plots_experiment2(args.attempt, args.revised_attempt, args.baseline_attempt)
        for p in paths:
            print(p)
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
    out = repro_package.write_package(args.attempt, repo_root(), args.out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
