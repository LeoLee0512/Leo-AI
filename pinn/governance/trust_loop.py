"""Document validation for the trust loop (Amendment A-0001, draft 3).

Documents: ProblemDefinition (the frozen layer-1 spec), EvaluationSet
manifests, the ClaimSetEvent ledger, TrustVector, RunRecord, DiagnosisRecord
and ClaimGateDecision.  Structural rules live in the JSON schemas next to
this module, written in the keyword subset that ``jsonschema_lite``
understands.  Every rule that subset cannot express (conditional
requirements, cross references, positivity, hash binding, derivations,
evaluation-set discipline, consistency with the calculus) is enforced here
and fails closed.

Draft 3 binds the documents to each other instead of trusting declared
fields:

* the spec's ``checkApplicability`` registry (in specHash) decides which
  checks a dimension shows and whether they are applicable -- a TrustVector
  cannot omit, add or re-label a check;
* ``claimSetStatus`` / ``claimSetHistory`` are derived from the append-only
  ledger, never trusted as written;
* the ClaimGateDecision must cite the ledger head, the claim set the spec
  names, the code identity that was OPENED on it and the evidence level the
  spec registers for the primary reference;
* ``environmentId`` / ``seedSetId`` / ``codeHash`` are recomputed from their
  material.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256
from .claim_set_ledger import (
    OPENED,
    SEALED,
    ClaimSetState,
    derive_claim_set_state,
    validate_claim_set_ledger,
)
from .evaluation_sets import EvaluationSet, disjointness_errors, load_evaluation_set, sample_set_hash, validate_evaluation_set
from .jsonschema_lite import validate as validate_schema
from .state_machine import (
    ROOT_CAUSE_GATE,
    SIGNATURE_EVIDENCE,
    ConstitutionVersionError,
    FailureSignature,
    RootCauseClass,
    admissible_root_causes,
    discriminating_experiment_errors,
)
from .trust_vector import (
    CLAIM_LEVELS,
    DIMENSIONS,
    SUPPORT_RANK,
    Applicability,
    CheckResult,
    EnvironmentFingerprint,
    NoApplicableCheck,
    RunQualification,
    TrustStatus,
    claim_gate,
    coerce_vector,
    dimension_status_from_checks,
    environment_id,
    seed_set_id,
)

SCHEMA_DIR = Path(__file__).with_name("schemas")
PROBLEM_DEFINITION_SCHEMA = "problem-definition.schema.json"
TRUST_VECTOR_SCHEMA = "trust-vector.schema.json"
CLAIM_GATE_DECISION_SCHEMA = "claim-gate-decision.schema.json"
RUN_RECORD_SCHEMA = "run-record.schema.json"
DIAGNOSIS_RECORD_SCHEMA = "diagnosis-record.schema.json"

#: Fields outside the method identity.  ``revision`` is an edition counter of
#: the document; the claim set and its state are bound through the ledger.
SPEC_HASH_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset({"specHash", "revision"})
SPEC_HASH_EXCLUDED_EVALUATION_SET_KEYS: frozenset[str] = frozenset(
    {"claim", "claimSetStatus", "claimSetOpenedAtRevision", "claimSetHistory"}
)
EXECUTED_STATUSES = (TrustStatus.PASS.value, TrustStatus.PARTIAL.value, TrustStatus.FAIL.value)


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def problem_definition_spec_hash(document: Mapping[str, Any]) -> str:
    """specHash = canonical hash of the method identity: everything but specHash, revision and the claim-set state."""

    material: dict[str, Any] = {}
    for key, value in document.items():
        if key in SPEC_HASH_EXCLUDED_TOP_LEVEL:
            continue
        if key == "evaluationSets" and isinstance(value, Mapping):
            material[key] = {k: v for k, v in value.items() if k not in SPEC_HASH_EXCLUDED_EVALUATION_SET_KEYS}
        else:
            material[key] = value
    return canonical_sha256(material)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ------------------------------------------------------------------ layer 1

def check_registry(document: Mapping[str, Any]) -> dict[str, dict[str, tuple[str, str | None]]]:
    """``{dimension: {checkId: (applicability, reason)}}`` from the frozen spec."""

    registry: dict[str, dict[str, tuple[str, str | None]]] = {dimension: {} for dimension in DIMENSIONS}
    for entry in document.get("checkApplicability", []):
        registry[entry["dimension"]][entry["checkId"]] = (entry["applicability"], entry.get("reason"))
    return registry


def _check_registry_errors(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(document["checkApplicability"]):
        path = f"checkApplicability[{index}]"
        if entry["checkId"] in seen:
            errors.append(f"{path}.checkId: {entry['checkId']!r} registered twice")
        seen.add(entry["checkId"])
        if entry["applicability"] == Applicability.NOT_APPLICABLE.value and not str(entry.get("reason", "")).strip():
            errors.append(f"{path}.reason: NOT_APPLICABLE must state which premise of the check the problem lacks")
    registry = check_registry(document)
    for dimension in DIMENSIONS:
        applicable = [cid for cid, (app, _) in registry[dimension].items() if app == Applicability.APPLICABLE.value]
        if not applicable:
            errors.append(
                f"checkApplicability: dimension {dimension!r} has no APPLICABLE check (INV-A1); every trust "
                "dimension is the subject of a MUST Gate and owes at least one check"
            )
    return errors


def _preregistration_errors(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    pre = document["preregistration"]
    for key in ("epsilonSpec", "worstSeedFactor", "dispersionLimit"):
        if not pre[key] > 0:
            errors.append(f"preregistration.{key}: must be strictly positive")
    if "qoiBand" in pre and not pre["qoiBand"] > 0:
        errors.append("preregistration.qoiBand: must be strictly positive")
    sets = document["evaluationSets"]
    if "minSeparation" in sets and not sets["minSeparation"] > 0:
        errors.append("evaluationSets.minSeparation: must be strictly positive")
    return errors


def validate_problem_definition(
    document: Any,
    *,
    claim_set_events: Sequence[Mapping[str, Any]] | None = None,
    evaluation_sets: Mapping[str, Any] | None = None,
    sample_set_hashes: Mapping[str, str] | None = None,
) -> list[str]:
    """Structure, cross references, registry, preregistration, evaluation sets, spec hash.

    With ``claim_set_events`` the claim-set state must agree with the ledger
    (the document's own fields are never the source of truth).  With
    ``evaluation_sets`` (``{role: manifest}``) each manifest must hash to the
    artifact the spec names and the sets must be sample-disjoint, and the claim
    set's samples must not have been opened before under any artifact
    (``sample_set_hashes``: ``{claimSetSha256: sampleSetHash}`` for ledger events
    that predate the field; new events carry it themselves).
    """

    errors = validate_schema(document, load_schema(PROBLEM_DEFINITION_SCHEMA))
    if errors:
        return errors

    pde = document["pde"]
    if pde["transient"] is True and not document.get("initialConditions"):
        errors.append("initialConditions: required because pde.transient is true")

    if document["status"] == "FROZEN":
        for key in ("frozenAt", "frozenBy"):
            if key not in document:
                errors.append(f"{key}: required because status is FROZEN")

    region_ids = [region["id"] for region in document["geometry"]["regions"]]
    if len(set(region_ids)) != len(region_ids):
        errors.append("geometry.regions: ids must be unique")
    for group in ("boundaryConditions", "initialConditions"):
        for index, condition in enumerate(document.get(group, [])):
            if condition["regionRef"] not in region_ids:
                errors.append(f"{group}[{index}].regionRef: {condition['regionRef']!r} is not a geometry region")

    variables = document["variables"]
    names = [variable["name"] for variable in variables]
    if len(set(names)) != len(names):
        errors.append("variables: names must be unique")
    roles = {variable["name"]: variable["role"] for variable in variables}
    if "dependent" not in roles.values():
        errors.append("variables: at least one dependent variable is required")
    for index, variable in enumerate(variables):
        low, high = variable["domainRange"]
        if not low < high:
            errors.append(f"variables[{index}].domainRange: min must be below max")

    for index, equation in enumerate(pde["equations"]):
        for role, key in (("independent", "independentVars"), ("dependent", "dependentVars")):
            for name in equation[key]:
                if name not in roles:
                    errors.append(f"pde.equations[{index}].{key}: {name!r} is not a declared variable")
                elif roles[name] != role:
                    errors.append(f"pde.equations[{index}].{key}: {name!r} is not a {role} variable")

    units = {entry["unit"] for entry in document["units"]["entries"]}
    for index, parameter in enumerate(document["parameters"]):
        if "unitRef" in parameter and parameter["unitRef"] not in units:
            errors.append(f"parameters[{index}].unitRef: {parameter['unitRef']!r} is not a declared unit")
    for index, variable in enumerate(variables):
        if variable["unitRef"] not in units:
            errors.append(f"variables[{index}].unitRef: {variable['unitRef']!r} is not a declared unit")

    nondim = document["nondimensionalization"]
    if nondim["applied"] is True and not nondim["scales"]:
        errors.append("nondimensionalization.scales: required because applied is true")
    for index, scale in enumerate(nondim["scales"]):
        if not scale["scaleValue"] > 0:
            errors.append(f"nondimensionalization.scales[{index}].scaleValue: must be strictly positive")

    sources = document["referenceSolution"]["sources"]
    source_ids = [source["sourceId"] for source in sources]
    if len(set(source_ids)) != len(source_ids):
        errors.append("referenceSolution.sources: sourceIds must be unique")
    if document["referenceSolution"]["primarySourceId"] not in source_ids:
        errors.append("referenceSolution.primarySourceId: does not name a registered source")

    errors.extend(_check_registry_errors(document))
    errors.extend(_preregistration_errors(document))
    errors.extend(_evaluation_set_errors(document, claim_set_events))
    if evaluation_sets is not None:
        errors.extend(_evaluation_set_manifest_errors(document, evaluation_sets))
        if claim_set_events is not None and "claim" in evaluation_sets and not errors:
            errors.extend(_claim_blindness_errors(document, evaluation_sets["claim"], claim_set_events, sample_set_hashes))

    if document["specHash"] != problem_definition_spec_hash(document):
        errors.append("specHash: does not match the canonical hash of the method identity")
    return errors


def primary_evidence_level(document: Mapping[str, Any]) -> str | None:
    primary = document["referenceSolution"]["primarySourceId"]
    for source in document["referenceSolution"]["sources"]:
        if source["sourceId"] == primary:
            return source["evidenceLevel"]
    return None


def _evaluation_set_errors(document: Mapping[str, Any],
                           claim_set_events: Sequence[Mapping[str, Any]] | None) -> list[str]:
    """Train / dev / claim discipline (review finding 3 of draft 1, issue 3 of draft 2)."""

    errors: list[str] = []
    sets = document["evaluationSets"]
    revision = document["revision"]
    hashes = {name: sets[name]["sha256"] for name in ("train", "dev", "claim")}
    if "phys" in sets:
        hashes["phys"] = sets["phys"]["sha256"]
    if len(set(hashes.values())) != len(hashes):
        errors.append("evaluationSets: train, dev, claim (and phys) must be distinct artifacts")
    status = sets["claimSetStatus"]
    opened_at = sets.get("claimSetOpenedAtRevision")
    history = sets["claimSetHistory"]

    # Self-consistency of the declared fields (necessary, never sufficient).
    for index, entry in enumerate(history):
        if entry["openedAtRevision"] > revision:
            errors.append(f"evaluationSets.claimSetHistory[{index}]: opened at a revision later than the current one")
    recorded = [entry for entry in history if entry["sha256"] == hashes["claim"]]
    if status == OPENED:
        if opened_at is None:
            errors.append("evaluationSets.claimSetOpenedAtRevision: required because the claim set is OPENED")
        elif opened_at != revision:
            errors.append(
                "evaluationSets.claimSetOpenedAtRevision: an OPENED claim set must have been opened for the current revision"
            )
        if not any(entry["openedAtRevision"] == revision for entry in recorded):
            errors.append("evaluationSets.claimSetHistory: an OPENED claim set must be recorded there for this revision")
    else:
        if opened_at is not None:
            errors.append("evaluationSets.claimSetOpenedAtRevision: only allowed while the claim set is OPENED")
        if recorded:
            errors.append(
                "evaluationSets.claimSetStatus: SEALED but the history records this claim set as opened; "
                "a claim set is never sealed again after being opened"
            )
    burnt = {entry["sha256"] for entry in history if entry["openedAtRevision"] < revision}
    if hashes["claim"] in burnt:
        errors.append(
            "evaluationSets.claim: this claim set was opened for an earlier revision and is no longer blind; "
            "register a fresh preregistered claim set"
        )

    if claim_set_events is None:
        return errors
    ledger_errors = validate_claim_set_ledger(claim_set_events)
    if ledger_errors:
        return errors + [f"claimSetLedger: {error}" for error in ledger_errors]
    state = derive_claim_set_state(claim_set_events, problem_id=document["problemId"], revision=revision,
                                   claim_set_sha256=hashes["claim"])
    if state.status == "NEVER_SEALED":
        errors.append("evaluationSets.claim: the ledger has no SEALED event for this claim set at this revision")
    elif state.status != status:
        errors.append(f"evaluationSets.claimSetStatus: declared {status} but the ledger derives {state.status}")
    if state.status == OPENED and state.opened_at_revision != revision:
        errors.append("evaluationSets.claim: the ledger opened this claim set at another revision; it is burnt here")
    if hashes["claim"] in state.burnt and state.status != OPENED:
        errors.append("evaluationSets.claim: this claim set has an OPENED event in the ledger and is burnt")
    if list(state.history) != list(history):
        errors.append("evaluationSets.claimSetHistory: does not equal the ledger's OPENED events for this problem")
    if status == OPENED and opened_at is not None and state.opened_at_revision != opened_at:
        errors.append("evaluationSets.claimSetOpenedAtRevision: differs from the ledger")
    return errors


def _claim_blindness_errors(document: Mapping[str, Any], claim_manifest: Mapping[str, Any],
                            claim_set_events: Sequence[Mapping[str, Any]],
                            sample_set_hashes: Mapping[str, str] | None = None) -> list[str]:
    """The claim set's *samples* must not have been opened before (2026-09-16: identity follows the samples).

    ``sample_set_hash(manifest)`` is blind to artifactId and metadata.  If the
    ledger has an OPENED event for these samples under any artifact other than
    the one this revision opened itself, the set is burnt and re-wrapping it is
    refused.
    """

    sets = document["evaluationSets"]
    claim_sha = sets["claim"]["sha256"]
    samples = sample_set_hash(claim_manifest)
    resolver = {**dict(sample_set_hashes or {}), claim_sha: samples}
    ledger_errors = validate_claim_set_ledger(claim_set_events, sample_set_hashes=resolver)
    if ledger_errors:
        return [f"claimSetLedger: {error}" for error in ledger_errors]
    state = derive_claim_set_state(claim_set_events, problem_id=document["problemId"], revision=document["revision"],
                                   claim_set_sha256=claim_sha, sample_set_hashes=resolver)
    opened_by = state.burnt_sample_artifacts.get(samples) if state.burnt_sample_artifacts else None
    if opened_by is not None and opened_by != claim_sha:
        return [
            f"evaluationSets.claim: the samples of this claim set (sampleSetHash {samples[:12]}) were already OPENED under "
            f"artifact {opened_by[:12]}; a re-wrapped claim set is burnt, not blind -- register a fresh preregistered set"
        ]
    if opened_by == claim_sha and (state.status != OPENED or state.opened_at_revision != document["revision"]):
        return ["evaluationSets.claim: these samples were opened at another revision; the set is burnt here"]
    return []


def _evaluation_set_manifest_errors(document: Mapping[str, Any], manifests: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    sets = document["evaluationSets"]
    loaded: dict[str, EvaluationSet] = {}
    for role in ("train", "dev", "claim", "phys"):
        if role not in sets:
            continue
        if role not in manifests:
            errors.append(f"evaluationSets.{role}: manifest not supplied; sample-level isolation cannot be verified")
            continue
        manifest_errors = validate_evaluation_set(manifests[role])
        if manifest_errors:
            errors.extend(f"evaluationSets.{role}: {error}" for error in manifest_errors)
            continue
        item = load_evaluation_set(manifests[role])
        if item.sha256 != sets[role]["sha256"]:
            errors.append(f"evaluationSets.{role}.sha256: the supplied manifest hashes to {item.sha256[:12]}..., not the registered artifact")
            continue
        if item.artifact_id != sets[role]["artifactId"]:
            errors.append(f"evaluationSets.{role}.artifactId: manifest names {item.artifact_id!r}")
        loaded[role] = item
    if errors:
        return errors
    return [f"evaluationSets: {error}" for error in disjointness_errors(loaded, min_separation=sets.get("minSeparation"))]


# ------------------------------------------------------------------ vector

def _check_results(entry: Mapping[str, Any], prefix: str, errors: list[str]) -> list[CheckResult] | None:
    results: list[CheckResult] = []
    for index, raw in enumerate(entry.get("checks", [])):
        path = f"{prefix}.checks[{index}]"
        applicability = Applicability(raw["applicability"])
        status = raw.get("status")
        reason = raw.get("reason")
        if applicability is Applicability.APPLICABLE and status is None:
            errors.append(f"{path}.status: required for an APPLICABLE check")
            return None
        if applicability is Applicability.NOT_APPLICABLE and status is not None:
            errors.append(f"{path}.status: a NOT_APPLICABLE check carries no status")
            return None
        if applicability is Applicability.NOT_APPLICABLE and not (isinstance(reason, str) and reason.strip()):
            errors.append(f"{path}.reason: NOT_APPLICABLE must state why the check is not owed")
            return None
        results.append(CheckResult(
            check_id=raw["checkId"],
            applicability=applicability,
            status=TrustStatus[status] if status is not None else None,
            reason=reason,
            evidence=tuple(pointer["artifactId"] for pointer in raw.get("evidencePointers", [])),
        ))
    ids = [result.check_id for result in results]
    if len(set(ids)) != len(ids):
        errors.append(f"{prefix}.checks: checkIds must be unique")
    return results


def _registry_conformance(results: Sequence[CheckResult], registered: Mapping[str, tuple[str, str | None]],
                          prefix: str) -> list[str]:
    errors: list[str] = []
    shown = {result.check_id: result for result in results}
    for check_id, (applicability, _) in registered.items():
        if check_id not in shown:
            errors.append(f"{prefix}.checks: registered check {check_id!r} is missing; a check cannot be silently omitted")
        elif shown[check_id].applicability.value != applicability:
            errors.append(
                f"{prefix}.checks: {check_id!r} is {shown[check_id].applicability.value} here but "
                f"{applicability} in the frozen spec; applicability is fixed at SPEC_LOCKED"
            )
    for check_id in shown:
        if check_id not in registered:
            errors.append(f"{prefix}.checks: {check_id!r} is not registered in the spec's checkApplicability")
    return errors


def validate_trust_vector(document: Any, problem_definition: Mapping[str, Any] | None = None) -> list[str]:
    errors = validate_schema(document, load_schema(TRUST_VECTOR_SCHEMA))
    if errors:
        return errors
    registry = check_registry(problem_definition) if problem_definition is not None else None
    if problem_definition is not None:
        for key in ("problemId", "revision", "specHash"):
            if document[key] != problem_definition[key]:
                errors.append(f"{key}: differs from the problem definition")
    for dimension in DIMENSIONS:
        entry = document["dimensions"][dimension]
        status = entry["status"]
        prefix = f"dimensions.{dimension}"
        if status == TrustStatus.NOT_CHECKED.value:
            for key in ("evidencePointers", "judgedAt", "judgedBy", "worstCase", "evaluationSet", "claimSetSha256"):
                if key in entry:
                    errors.append(f"{prefix}.{key}: a NOT_CHECKED dimension carries no judgement")
            if entry.get("checks"):
                errors.append(f"{prefix}.checks: a NOT_CHECKED dimension has executed no check")
            continue
        for key in ("evidencePointers", "judgedAt", "judgedBy"):
            if key not in entry:
                errors.append(f"{prefix}.{key}: required unless status is NOT_CHECKED")
        if not entry.get("evidencePointers"):
            errors.append(f"{prefix}.evidencePointers: a judged dimension needs at least one pointer")
        if status == TrustStatus.PARTIAL.value and not entry.get("notes", "").strip():
            errors.append(f"{prefix}.notes: PARTIAL must state what is missing")
        if entry.get("perturbationsRun") and not entry.get("worstCase"):
            errors.append(f"{prefix}.worstCase: required when perturbations ran (the worst case is what is reported)")
        if status in EXECUTED_STATUSES and not entry.get("checks"):
            errors.append(f"{prefix}.checks: an executed dimension must show the checks it aggregates")
        if entry.get("checks"):
            results = _check_results(entry, prefix, errors)
            if results is not None:
                try:
                    derived = dimension_status_from_checks(results)
                except NoApplicableCheck as exc:
                    errors.append(f"{prefix}.checks: {exc}")
                else:
                    if SUPPORT_RANK[TrustStatus[status]] > SUPPORT_RANK[derived]:
                        errors.append(
                            f"{prefix}.status: {status} is above the meet of the applicable checks ({derived.value}); "
                            "a dimension is never judged higher than its evidence"
                        )
                    elif SUPPORT_RANK[TrustStatus[status]] < SUPPORT_RANK[derived] and not entry.get("notes", "").strip():
                        errors.append(
                            f"{prefix}.notes: status {status} is below the meet {derived.value}; a manual "
                            "downgrade must be explained"
                        )
                if registry is not None:
                    errors.extend(_registry_conformance(results, registry[dimension], prefix))
        if entry.get("evaluationSet") == "claim" and "claimSetSha256" not in entry:
            errors.append(f"{prefix}.claimSetSha256: required when the judgement was made on the claim set")
        if "claimSetSha256" in entry and entry.get("evaluationSet") != "claim":
            errors.append(f"{prefix}.claimSetSha256: only a claim-set judgement names a claim set")
        if problem_definition is not None and "claimSetSha256" in entry \
                and entry["claimSetSha256"] != problem_definition["evaluationSets"]["claim"]["sha256"]:
            errors.append(f"{prefix}.claimSetSha256: is not the claim set the problem definition names")
        if dimension == "external" and status == TrustStatus.PASS.value and entry.get("evaluationSet") != "claim":
            errors.append(
                f"{prefix}.evaluationSet: external verification can only PASS on the sealed claim set, not on dev"
            )
    return errors


def trust_vector_statuses(document: Mapping[str, Any]) -> dict[str, TrustStatus]:
    return coerce_vector({d: document["dimensions"][d]["status"] for d in DIMENSIONS})


# ------------------------------------------------------------------- runs

def code_hash_from_manifest(manifest: Sequence[Mapping[str, Any]]) -> str:
    return canonical_sha256(sorted(({"path": e["path"], "sha256": e["sha256"]} for e in manifest), key=lambda e: e["path"]))


def validate_run_record(document: Any) -> list[str]:
    """Structure plus the three derivations: codeHash, environmentId, seedSetId."""

    errors = validate_schema(document, load_schema(RUN_RECORD_SCHEMA))
    if errors:
        return errors
    paths = [entry["path"] for entry in document["codeManifest"]]
    if len(set(paths)) != len(paths):
        errors.append("codeManifest: paths must be unique")
    if document["codeHash"] != code_hash_from_manifest(document["codeManifest"]):
        errors.append("codeHash: does not recompute from the code manifest")
    try:
        fingerprint = EnvironmentFingerprint.from_mapping(document["environment"])
    except (TypeError, ValueError) as exc:
        errors.append(f"environment: {exc}")
    else:
        if document["environmentId"] != environment_id(fingerprint):
            errors.append("environmentId: does not recompute from the environment's strong fields")
    if document["seedSetId"] != seed_set_id(document["seeds"]):
        errors.append("seedSetId: does not recompute from the seed values")
    if _parse_time(document["finishedAt"]) < _parse_time(document["startedAt"]):
        errors.append("finishedAt: earlier than startedAt")
    return errors


def _qualified_runs(document: Mapping[str, Any], errors: list[str],
                    run_records: Mapping[str, Mapping[str, Any]] | None) -> list[RunQualification]:
    records: list[RunQualification] = []
    for index, raw in enumerate(document.get("qualifiedC2Runs", [])):
        path = f"qualifiedC2Runs[{index}]"
        try:
            fingerprint = EnvironmentFingerprint.from_mapping(raw["environment"])
        except (TypeError, ValueError) as exc:
            errors.append(f"{path}.environment: {exc}")
            continue
        derived_environment = environment_id(fingerprint)
        derived_seeds = seed_set_id(raw["seeds"])
        if raw["environmentId"] != derived_environment:
            errors.append(f"{path}.environmentId: does not recompute from the environment's strong fields")
        if raw["seedSetId"] != derived_seeds:
            errors.append(f"{path}.seedSetId: does not recompute from the seed values")
        if run_records is not None:
            record = run_records.get(raw["runId"])
            if record is None:
                errors.append(f"{path}.runId: {raw['runId']!r} is not a registered run record")
            else:
                for key in ("specHash", "codeHash", "environmentId", "seedSetId"):
                    if record.get(key) != raw[key]:
                        errors.append(f"{path}.{key}: differs from the registered run record")
                if sorted(set(record.get("seeds", []))) != sorted(set(raw["seeds"])):
                    errors.append(f"{path}.seeds: differ from the registered run record")
        records.append(RunQualification(run_id=raw["runId"], spec_hash=raw["specHash"], code_hash=raw["codeHash"],
                                        environment_id=derived_environment, seed_set_id=derived_seeds))
    return records


# ------------------------------------------------------------------ claims

def validate_claim_gate_decision(
    document: Any,
    trust_vector: Any,
    problem_definition: Any,
    *,
    claim_set_events: Sequence[Mapping[str, Any]],
    run_records: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """A decision is only valid against its spec, its vector, the ledger and its runs."""

    errors = validate_schema(document, load_schema(CLAIM_GATE_DECISION_SCHEMA))
    definition_errors = validate_problem_definition(problem_definition, claim_set_events=claim_set_events)
    errors.extend(f"problemDefinition: {error}" for error in definition_errors)
    if not definition_errors:
        errors.extend(f"trustVector: {error}" for error in validate_trust_vector(trust_vector, problem_definition))
    if errors:
        return errors

    for key in ("problemId", "revision", "specHash"):
        if document[key] != problem_definition[key]:
            errors.append(f"{key}: differs from the problem definition")
        if document[key] != trust_vector[key]:
            errors.append(f"{key}: differs from the trust vector")
    if document["trustVectorRef"]["artifactId"] != trust_vector["recordId"]:
        errors.append("trustVectorRef.artifactId: does not name the supplied trust vector")
    if document["claimSetSha256"] != problem_definition["evaluationSets"]["claim"]["sha256"]:
        errors.append("claimSetSha256: is not the claim set the problem definition names")
    level = primary_evidence_level(problem_definition)
    if document["referenceEvidenceLevel"] != level:
        errors.append(
            f"referenceEvidenceLevel: {document['referenceEvidenceLevel']} but the frozen spec registers the "
            f"primary reference at level {level}; the level is not re-labelled at decision time"
        )

    state: ClaimSetState = derive_claim_set_state(
        claim_set_events, problem_id=document["problemId"], revision=document["revision"],
        claim_set_sha256=document["claimSetSha256"],
    )
    if document["ledgerHead"] != state.head:
        errors.append("ledgerHead: does not name the last event of the supplied ledger")
    external = trust_vector["dimensions"]["external"]
    judged_on_claim = external.get("evaluationSet") == "claim" and external["status"] in EXECUTED_STATUSES
    if judged_on_claim:
        if state.status != OPENED:
            errors.append("external: judged on the claim set, but the ledger has no OPENED event for it at this revision")
        elif state.opened_code_hash != document["codeHash"]:
            errors.append(
                "codeHash: differs from the code identity recorded when the claim set was OPENED; code changed "
                "after the claim set was seen -- bump the revision and preregister a new claim set"
            )
    elif state.status not in (SEALED, OPENED):
        errors.append("claimSetSha256: the claim set is not sealed in the ledger")

    records = _qualified_runs(document, errors, run_records)
    if errors:
        return errors

    gate = claim_gate(
        trust_vector_statuses(trust_vector),
        evidence_level=document["referenceEvidenceLevel"],
        c2_runs=records,
        spec_hash=document["specHash"],
        code_hash=document["codeHash"],
        exploratory=document["runMode"] == "EXPLORATORY",
    )
    declared_allowed = [claim["level"] for claim in document["allowedClaims"]]
    declared_blocked = [claim["level"] for claim in document["blockedClaims"]]
    if len(set(declared_allowed)) != len(declared_allowed):
        errors.append("allowedClaims: duplicate levels")
    for item in declared_allowed:
        if item not in gate.allowed:
            reasons = "; ".join(gate.blocked.get(item, ()))
            errors.append(f"allowedClaims: {item} is not licensed by the trust vector ({reasons})")
        if item in declared_blocked:
            errors.append(f"{item}: listed as both allowed and blocked")
    for item in CLAIM_LEVELS:
        if item not in declared_allowed and item not in declared_blocked:
            errors.append(f"blockedClaims: {item} is neither allowed nor blocked; every level needs a verdict")

    weakest = document["weakestLink"]
    if weakest["status"] != gate.weakest_status.value:
        errors.append(
            f"weakestLink.status: {weakest['status']} but the trust vector's weakest status is {gate.weakest_status.value}"
        )
    if set(weakest["dimensions"]) != set(gate.weakest_dimensions):
        errors.append(
            "weakestLink.dimensions: must list exactly the dimensions attaining the weakest status "
            f"{sorted(gate.weakest_dimensions)}"
        )
    return errors


# --------------------------------------------------------------- diagnosis

def explained_signatures(document: Mapping[str, Any]) -> list[FailureSignature]:
    """The observed signatures this record explains: ``explainedSignatures`` or just the primary one."""

    primary = FailureSignature(document["signature"])
    listed = [FailureSignature(item) for item in document.get("explainedSignatures", [])]
    return [primary] + [item for item in listed if item is not primary]


def validate_diagnosis_record(document: Any, *, constitution_version: str | None = None) -> list[str]:
    """Signature evidence complete, root cause admissible under the record's Constitution version, every alternative excluded, gate derived.

    ``constitution_version`` (when the caller knows which version the run is
    bound to) must equal the record's own ``constitutionVersion``; the matrix
    and the naming obligations are always those of that version (A-0002 final
    closure review, Issue 1).  ``explainedSignatures`` (Issue 2) is the subset of
    ``observedSignatures`` this record explains; the exclusion duty covers every
    explained signature's candidates.  Coverage of all observed signatures is a
    property of the *set* of records: ``diagnosis_coverage_errors``.
    """

    errors = validate_schema(document, load_schema(DIAGNOSIS_RECORD_SCHEMA))
    if errors:
        return errors
    version = document["constitutionVersion"]
    if constitution_version is not None and version != constitution_version:
        errors.append(f"constitutionVersion: record is bound to {version} but the run is bound to {constitution_version}")
    try:
        matrix = admissible_root_causes(version)
    except ConstitutionVersionError as exc:
        return errors + [f"constitutionVersion: {exc}"]
    signature = FailureSignature(document["signature"])
    root_cause = RootCauseClass(document["rootCause"])
    observed = [FailureSignature(item) for item in document.get("observedSignatures", [document["signature"]])]
    explained = explained_signatures(document)
    if signature not in observed:
        errors.append("observedSignatures: must include the primary signature")
    outside = [item.value for item in explained if item not in observed]
    if outside:
        errors.append(f"explainedSignatures: {outside} were not observed; a record explains a subset of observedSignatures")
    missing = [key for key in SIGNATURE_EVIDENCE[signature] if key not in document["signatureEvidence"]]
    if missing:
        errors.append(f"signatureEvidence: {signature.value} requires {missing}")
    errors.extend(discriminating_experiment_errors(
        signature, root_cause, document["discriminatingExperiment"], constitution_version=version, explained=explained))
    if root_cause is RootCauseClass.UNDETERMINED:
        if "gate" in document:
            errors.append("gate: rUndetermined routes to no Gate; the line stops for a human")
    else:
        admissible = True
        for item in explained:
            if root_cause not in matrix[item]:
                admissible = False
                errors.append(f"rootCause: {root_cause.value} is not admissible for {item.value} under Constitution {version}")
        if admissible and "gate" in document and document["gate"] != ROOT_CAUSE_GATE[root_cause]:
            errors.append(f"gate: {root_cause.value} re-enters Gate {ROOT_CAUSE_GATE[root_cause]}; the Gate is derived, not chosen")
    return errors


def diagnosis_coverage_errors(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Signature coverage invariant over the DiagnosisRecords of one failure (A-0002 final closure review, Issue 2).

    One run may show several signatures with different root causes
    (``sPdeResidual <- rOptimizationFailure`` and ``sLocalizedError <-
    rSingularityTreatment``), so one record is never forced to explain
    everything.  Instead the *set* of records must satisfy:

    * every record is valid on its own and they belong to the same problem,
      revision, specHash, Constitution version and round;
    * every record lists the same ``observedSignatures``;
    * the union of ``explainedSignatures`` equals ``observedSignatures`` -- a
      signature that no record explains has silently disappeared;
    * every signature is explained by exactly one record.  Two records that
      attribute the same signature to different root causes are a contradiction
      the excludes discipline already forbids (each would have had to exclude
      the other); the MVP does not define multi-causal attribution of one
      signature -- when the experiments cannot separate two causes the record
      names rUndetermined and the line stops.
    """

    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)) or not records:
        return ["diagnosisRecords: a failure needs at least one DiagnosisRecord"]
    errors: list[str] = []
    for index, record in enumerate(records):
        record_errors = validate_diagnosis_record(record)
        errors.extend(f"diagnosisRecords[{index}]: {error}" for error in record_errors)
    if errors:
        return errors
    keys = {(r["problemId"], r["revision"], r["specHash"], r["constitutionVersion"], r["round"]) for r in records}
    if len(keys) != 1:
        errors.append("diagnosisRecords: records belong to different (problemId, revision, specHash, constitutionVersion, round)")
    observed_sets = {frozenset(r.get("observedSignatures", [r["signature"]])) for r in records}
    if len(observed_sets) != 1:
        errors.append("diagnosisRecords: every record must list the same observedSignatures")
        return errors
    observed = next(iter(observed_sets))
    explained_by: dict[str, list[str]] = {}
    for record in records:
        for item in explained_signatures(record):
            explained_by.setdefault(item.value, []).append(record["diagnosisId"])
    unexplained = sorted(observed - set(explained_by))
    if unexplained:
        errors.append(f"diagnosisRecords: observed signatures {unexplained} are explained by no record (coverage must be 100%)")
    for item, ids in sorted(explained_by.items()):
        if len(ids) > 1:
            causes = sorted({r["rootCause"] for r in records if item in {s.value for s in explained_signatures(r)}})
            errors.append(
                f"diagnosisRecords: {item} is explained by several records {ids} with root causes {causes}; "
                "a signature has exactly one record -- name rUndetermined when the experiments cannot separate the causes"
            )
    return errors
