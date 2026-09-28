"""Gate and calibration-mode state semantics."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"


class TestMode(str, Enum):
    WORKFLOW_E2E = "WORKFLOW_E2E"
    VALIDATOR_COMPONENT = "VALIDATOR_COMPONENT"
    TRAINING_E2E = "TRAINING_E2E"


# MVP plan 3.5 interprets the Constitution's *necessary* upstream gates.
# These are permission decisions, never evidence that a claim is supported.
CLAIM_PREREQUISITES = {
    "C0": (1, 3),
    "C1": (1, 3, 4),
    "C2": (1, 2, 3, 4, 5, 6),
}
OPERATION_PREREQUISITES = {
    3: (1,),
    4: (1, 3),
    5: (1, 2, 3, 4),
    6: (4,),
}


def _passed(gates: Mapping[int, GateStatus], required: tuple[int, ...]) -> bool:
    return all(gates.get(number) is GateStatus.PASS for number in required)


def claim_prerequisite_status(
    claim_level: str,
    gates: Mapping[int, GateStatus],
    *,
    evidence_level: str,
    stop_the_line: bool = False,
) -> GateStatus:
    """Return G7 prerequisite eligibility, without issuing a ScientificClaim.

    C3 additionally needs the five preregistered supported C2 runs and SR-1;
    this per-run helper cannot establish it. C4/C5 are outside this MVP.
    A positive result therefore does not supply evidence, scope or a verdict.
    """

    required = CLAIM_PREREQUISITES.get(claim_level)
    if stop_the_line is not False or evidence_level not in {"A", "B", "C", "D"}:
        return GateStatus.BLOCKED
    if required is None or (claim_level == "C2" and evidence_level == "D"):
        return GateStatus.BLOCKED
    return GateStatus.PASS if _passed(gates, required) else GateStatus.BLOCKED


def operation_prerequisite_status(
    gate_number: int,
    gates: Mapping[int, GateStatus],
    *,
    evidence_level: str,
    stop_the_line: bool = False,
) -> GateStatus:
    """Authorize a formal downstream operation according to plan section 3.6.

    A failed G2 only permits exploratory G3/G4 for a locked Level-D spec.
    G1=PASS is still required, as is G3=PASS for training. Diagnostic component
    tests are outside this formal-operation helper and do not promote gates.
    """

    required = OPERATION_PREREQUISITES.get(gate_number)
    if stop_the_line is not False or evidence_level not in {"A", "B", "C", "D"}:
        return GateStatus.BLOCKED
    if required is None or not _passed(gates, required):
        return GateStatus.BLOCKED
    if gates.get(1) in {GateStatus.FAIL, GateStatus.PARTIAL, GateStatus.BLOCKED}:
        # Plan section 5 explicitly blocks every downstream operation after G1 fails.
        return GateStatus.BLOCKED
    if gate_number in {3, 4} and gates.get(2) in {GateStatus.FAIL, GateStatus.PARTIAL}:
        if not (gates.get(2) is GateStatus.FAIL and evidence_level == "D"):
            return GateStatus.BLOCKED
    if gate_number == 6 and gates.get(5) in {GateStatus.FAIL, GateStatus.PARTIAL}:
        # Section 5 blocks G6 after an executed G5 failure. Do not turn this into
        # a new G5=PASS prerequisite: section 3.6 and U1 permit G6 for Level D
        # while its accuracy validation remains BLOCKED.
        return GateStatus.BLOCKED
    return GateStatus.PASS


def postlock_gate1_status(
    *,
    prelock_passed: bool,
    lock_path: str | Path,
    verify_lock: Callable[[Path], bool],
) -> GateStatus:
    """Evaluate Gate 1 only after a lock is supposed to exist.

    No lock means the post-lock Gate has not been executed and is therefore
    BLOCKED, not FAIL.  An existing but invalid lock is an executed FAIL.
    """

    if prelock_passed is not True:
        return GateStatus.BLOCKED
    try:
        source = Path(lock_path)
        if not source.exists() and not source.is_symlink():
            return GateStatus.BLOCKED
        if not source.is_file():
            return GateStatus.FAIL
        return GateStatus.PASS if verify_lock(source) is True else GateStatus.FAIL
    except Exception:
        # A verifier failure is an executed failure, including dependency errors.
        # Do not catch BaseException: an operator interrupt must still propagate.
        return GateStatus.FAIL


# ---------------------------------------------------------------------------
# Amendment A-0001 (draft 2): workflow states, two-layer FAIL triage and
# trust-vector gating.
#
# GateStatus above is unchanged (Constitution chapter 4).  The workflow states
# are the Constitution's chapter-3 machine plus the MVP plan's STOPPED_THE_LINE;
# nothing is added to the state set.  Gate 5 is evaluated inside VALIDATION as
# two MUST groups (physics consistency, independent numerical verification).
#
# Triage is two layers, as the 2026-09-14 review required: an observed
# FailureSignature (what was seen) never routes on its own; a diagnosis must
# name a RootCauseClass that is admissible for that signature, cite the
# discriminating experiment, and it is the root cause that decides the Gate.

from dataclasses import dataclass  # noqa: E402

from .trust_vector import DIMENSIONS, TrustStatus, coerce_vector  # noqa: E402


class WorkflowState(str, Enum):
    DRAFT = "DRAFT"
    SPEC_LOCKED = "SPEC_LOCKED"
    BASELINE_VERIFIED = "BASELINE_VERIFIED"
    IMPLEMENTATION_VERIFIED = "IMPLEMENTATION_VERIFIED"
    TRAINING_COMPLETED = "TRAINING_COMPLETED"
    VALIDATION = "VALIDATION"
    REPRODUCIBILITY_CHECK = "REPRODUCIBILITY_CHECK"
    ACCEPTED = "ACCEPTED"
    FAILURE_RECORDED = "FAILURE_RECORDED"
    DIAGNOSED = "DIAGNOSED"
    REVISED = "REVISED"
    STOPPED_THE_LINE = "STOPPED_THE_LINE"


class FailureSignature(str, Enum):
    """What was observed.  A signature is evidence for a diagnosis, never a route."""

    PDE_RESIDUAL = "sPdeResidual"
    BC_RESIDUAL = "sBcResidual"
    CONSERVATION = "sConservation"
    PINN_CFD = "sPinnCfd"
    SEED_SENSITIVE = "sSeedSensitive"
    LOCALIZED_ERROR = "sLocalizedError"


class RootCauseClass(str, Enum):
    """What was found.  The root cause, not the symptom, decides the re-entry Gate."""

    SPEC_DEFECT = "rSpecDefect"                  # equation, BC/IC, nondimensionalization or QoI defined wrongly
    DATA_DEFECT = "rDataDefect"                  # parameters, boundary data or reference data wrong
    SINGULARITY_TREATMENT = "rSingularityTreatment"  # a geometric singularity the spec does not treat
    REFERENCE_DEFECT = "rReferenceDefect"        # reference solver unconverged, wrong, or sharing a code path
    IMPLEMENTATION_DEFECT = "rImplementationDefect"  # AD, residual assembly, boundary operator, mask, scaling
    CAPACITY_LIMIT = "rCapacityLimit"            # the network cannot represent the solution
    OPTIMIZATION_FAILURE = "rOptimizationFailure"    # not converged, gradient pathology, loss weighting
    SAMPLING_DEFICIENCY = "rSamplingDeficiency"  # collocation density or distribution
    UNDETERMINED = "rUndetermined"               # the discriminating experiments did not separate the causes


class IllegalTransition(ValueError):
    """A transition the amended state machine does not contain."""


#: The state a gate executes in, and the state a PASS advances to.  Gate 5 runs
#: in VALIDATION, which is entered from TRAINING_COMPLETED by enter_validation().
GATE_RUNS_IN: dict[int, WorkflowState] = {
    1: WorkflowState.DRAFT,
    2: WorkflowState.SPEC_LOCKED,
    3: WorkflowState.BASELINE_VERIFIED,
    4: WorkflowState.IMPLEMENTATION_VERIFIED,
    5: WorkflowState.VALIDATION,
    6: WorkflowState.REPRODUCIBILITY_CHECK,
}
GATE_ADVANCES_TO: dict[int, WorkflowState] = {
    1: WorkflowState.SPEC_LOCKED,
    2: WorkflowState.BASELINE_VERIFIED,
    3: WorkflowState.IMPLEMENTATION_VERIFIED,
    4: WorkflowState.TRAINING_COMPLETED,
    5: WorkflowState.REPRODUCIBILITY_CHECK,
    6: WorkflowState.ACCEPTED,
}
#: Trust-vector dimensions judged by each gate (merge notes C2, C3).
GATE_DIMENSIONS: dict[int, tuple[str, ...]] = {
    1: ("math",),
    2: (),
    3: ("impl",),
    4: ("train",),
    5: ("physics", "external"),
    6: ("repro",),
}
#: Root cause -> the Gate whose subject it is (UNDETERMINED has no Gate: a human decides).
ROOT_CAUSE_GATE: dict[RootCauseClass, int] = {
    RootCauseClass.SPEC_DEFECT: 1,
    RootCauseClass.DATA_DEFECT: 1,
    RootCauseClass.SINGULARITY_TREATMENT: 1,
    RootCauseClass.REFERENCE_DEFECT: 2,
    RootCauseClass.IMPLEMENTATION_DEFECT: 3,
    RootCauseClass.CAPACITY_LIMIT: 4,
    RootCauseClass.OPTIMIZATION_FAILURE: 4,
    RootCauseClass.SAMPLING_DEFICIENCY: 4,
}
#: Which root causes a signature may be diagnosed as.  GovernanceSemantics =
#: f(constitutionVersion), never "latest code on master" (A-0002 final closure
#: review, Issue 1): each Constitution version that carries the closed matrix of
#: chapter 3.1 has its own table, and a PROPOSED amendment's cells live under
#: the version it *would* create.  They are reachable only through
#: ``admissible_root_causes(version)``, which refuses a version that is not in
#: ``locking.SUPPORTED_CONSTITUTION_VERSIONS`` -- the set an ACCEPTED amendment
#: extends (operation log 5.17 recipe).  So while A-0002 is PROPOSED, a run bound
#: to Constitution 1.1 cannot name an A-0002 cell, and "1.2" cannot be selected
#: at all.  UNDETERMINED is admissible everywhere.
#:
#: 1.1 (A-0001, effective 2026-09-15): DeepSeek attribution table, Red Team
#: P-matrix, review example (a localized error may be boundary code, geometry,
#: a corner singularity, capacity, sampling, loss weighting or a locally
#: distorted reference).
_MATRIX_1_1: dict[FailureSignature, tuple[RootCauseClass, ...]] = {
    FailureSignature.PDE_RESIDUAL: (
        RootCauseClass.SPEC_DEFECT, RootCauseClass.IMPLEMENTATION_DEFECT, RootCauseClass.CAPACITY_LIMIT,
        RootCauseClass.OPTIMIZATION_FAILURE, RootCauseClass.SAMPLING_DEFICIENCY,
    ),
    FailureSignature.BC_RESIDUAL: (
        RootCauseClass.SPEC_DEFECT, RootCauseClass.DATA_DEFECT, RootCauseClass.IMPLEMENTATION_DEFECT,
        RootCauseClass.OPTIMIZATION_FAILURE, RootCauseClass.SAMPLING_DEFICIENCY,
    ),
    FailureSignature.CONSERVATION: (
        RootCauseClass.SPEC_DEFECT, RootCauseClass.IMPLEMENTATION_DEFECT, RootCauseClass.CAPACITY_LIMIT,
        RootCauseClass.OPTIMIZATION_FAILURE, RootCauseClass.SAMPLING_DEFICIENCY,
    ),
    FailureSignature.PINN_CFD: (
        RootCauseClass.SPEC_DEFECT, RootCauseClass.DATA_DEFECT, RootCauseClass.SINGULARITY_TREATMENT,
        RootCauseClass.REFERENCE_DEFECT, RootCauseClass.IMPLEMENTATION_DEFECT, RootCauseClass.OPTIMIZATION_FAILURE,
    ),
    FailureSignature.SEED_SENSITIVE: (
        RootCauseClass.CAPACITY_LIMIT, RootCauseClass.OPTIMIZATION_FAILURE, RootCauseClass.SAMPLING_DEFICIENCY,
    ),
    FailureSignature.LOCALIZED_ERROR: (
        RootCauseClass.SINGULARITY_TREATMENT, RootCauseClass.REFERENCE_DEFECT, RootCauseClass.IMPLEMENTATION_DEFECT,
        RootCauseClass.CAPACITY_LIMIT, RootCauseClass.OPTIMIZATION_FAILURE, RootCauseClass.SAMPLING_DEFICIENCY,
    ),
}
#: 1.2 (A-0002, PROPOSED): the 1.1 table plus eight cells -- DeepSeek R2 three,
#: second-review two, closure-audit three.
_MATRIX_1_2: dict[FailureSignature, tuple[RootCauseClass, ...]] = {
    FailureSignature.PDE_RESIDUAL: _MATRIX_1_1[FailureSignature.PDE_RESIDUAL] + (
        RootCauseClass.SINGULARITY_TREATMENT,  # A-0002 draft 2: an untreated corner makes the residual unbounded there
    ),
    FailureSignature.BC_RESIDUAL: _MATRIX_1_1[FailureSignature.BC_RESIDUAL] + (
        RootCauseClass.CAPACITY_LIMIT,  # A-0002: complex boundary data a small network cannot fit
        RootCauseClass.SINGULARITY_TREATMENT,  # A-0002 draft 2: incompatible corner data no continuous network meets
    ),
    FailureSignature.CONSERVATION: _MATRIX_1_1[FailureSignature.CONSERVATION],
    FailureSignature.PINN_CFD: _MATRIX_1_1[FailureSignature.PINN_CFD] + (
        RootCauseClass.CAPACITY_LIMIT,  # A-0002: under-capacity shows as a gap before the residual
        RootCauseClass.SAMPLING_DEFICIENCY,  # A-0002 draft 2: an under-sampled region of small measure moves the QoI
    ),
    FailureSignature.SEED_SENSITIVE: _MATRIX_1_1[FailureSignature.SEED_SENSITIVE] + (
        RootCauseClass.IMPLEMENTATION_DEFECT,  # A-0002 draft 2: nondeterministic defects (RNG leakage, races, dropout)
        RootCauseClass.SPEC_DEFECT,  # A-0002 draft 3: *unintended* non-identifiability the frozen spec left open
    ),
    FailureSignature.LOCALIZED_ERROR: _MATRIX_1_1[FailureSignature.LOCALIZED_ERROR] + (
        RootCauseClass.SPEC_DEFECT,  # A-0002: a source term or boundary written at the wrong place
    ),
}
ADMISSIBLE_ROOT_CAUSES_BY_VERSION: dict[str, dict[FailureSignature, tuple[RootCauseClass, ...]]] = {
    "1.1": _MATRIX_1_1,
    "1.2": _MATRIX_1_2,
}
#: Structured naming obligations each version adds on top of ``excludes``
#: (A-0002 draft 2 / 3).  Under 1.1 none of them exist: a PROPOSED amendment
#: must not make 1.1 stricter either.
NAMING_OBLIGATIONS_BY_VERSION: dict[str, frozenset[str]] = {
    "1.1": frozenset(),
    "1.2": frozenset({"intervention", "determinismReplay", "identifiability"}),
}


class ConstitutionVersionError(ValueError):
    """A diagnosis asked for governance semantics of a Constitution version that is not effective."""


def effective_constitution_versions() -> tuple[str, ...]:
    """The versions whose semantics may be selected: exactly ``locking.SUPPORTED_CONSTITUTION_VERSIONS``.

    Read at call time (not import time) so the single source of truth stays in
    ``locking``; an ACCEPTED amendment adds its newVersion there and nowhere else.
    """

    from . import locking

    return tuple(locking.SUPPORTED_CONSTITUTION_VERSIONS)


def _effective(constitution_version: object) -> str:
    if not isinstance(constitution_version, str):
        raise TypeError("constitution_version must be the Constitution version string the run is bound to")
    if constitution_version not in ADMISSIBLE_ROOT_CAUSES_BY_VERSION:
        raise ConstitutionVersionError(
            f"Constitution {constitution_version} has no admissible matrix (chapter 3.1 exists from 1.1, A-0001)"
        )
    if constitution_version not in effective_constitution_versions():
        raise ConstitutionVersionError(
            f"Constitution {constitution_version} is not effective: its amendment is not ACCEPTED, so its "
            f"matrix cannot be used (effective versions {effective_constitution_versions()})"
        )
    return constitution_version


def admissible_root_causes(constitution_version: str) -> Mapping[FailureSignature, tuple[RootCauseClass, ...]]:
    """The closed matrix of the Constitution version a run is bound to; refuses versions not in force."""

    return ADMISSIBLE_ROOT_CAUSES_BY_VERSION[_effective(constitution_version)]


def naming_obligations(constitution_version: str) -> frozenset[str]:
    return NAMING_OBLIGATIONS_BY_VERSION[_effective(constitution_version)]


#: Evidence a diagnosis must carry: the signature's own artifacts, plus the
#: experiment that discriminated the root cause from the other admissible ones.
SIGNATURE_EVIDENCE: dict[FailureSignature, tuple[str, ...]] = {
    FailureSignature.PDE_RESIDUAL: ("residualStatistics", "autodiffComparison", "scalingSensitivity"),
    FailureSignature.BC_RESIDUAL: ("boundaryResidualDistribution", "samplingConfigDiff", "hardConstraintDiff"),
    FailureSignature.CONSERVATION: ("conservationResiduals", "admissibilityChecks"),
    FailureSignature.PINN_CFD: ("pinnProvenance", "referenceProvenance", "gridConvergence"),
    FailureSignature.SEED_SENSITIVE: ("multiSeedStatistics",),
    FailureSignature.LOCALIZED_ERROR: ("errorSpatialDistribution", "samplingConfigDiff"),
}
DISCRIMINATING_EXPERIMENT_KEY = "discriminatingExperiment"
#: The matrix is a scope-dependent governance decision (A-0002 draft 2): under the
#: forward-problem MVP, observation data does not enter the PDE operator, so
#: rDataDefect is not admissible for sPdeResidual / sConservation.  An inverse
#: PINN needs its own amendment and matrix.
MATRIX_SCOPE = "forward-problem-mvp"
#: Root causes that can only be named through a controlled intervention on one
#: factor (everything else held fixed, >= 3 levels, >= 3 seeds per level, the
#: per-level median error strictly decreasing along the levels).
INTERVENTION_FACTORS: dict[RootCauseClass, str] = {
    RootCauseClass.CAPACITY_LIMIT: "capacity",
    RootCauseClass.SAMPLING_DEFICIENCY: "sampling",
}
INTERVENTION_CONTROLS: tuple[str, ...] = (
    "architecture", "sampling", "optimizer", "lrSchedule", "lossWeights", "trainingBudget",
    "spec", "reference", "seedProtocol",
)
#: The control an intervention factor is allowed to change.
FACTOR_CONTROL: dict[str, str] = {"capacity": "architecture", "sampling": "sampling"}
MIN_INTERVENTION_LEVELS = 3
MIN_INTERVENTION_SEEDS = 3
DETERMINISM_REPLAY_KEY = "determinismReplay"
IDENTIFIABILITY_KEY = "identifiability"
#: Kinds of solution multiplicity P34 can exhibit.  None of them is a defect by
#: itself (A-0002 final closure review, Issue 3).
AMBIGUITY_TYPES: tuple[str, ...] = ("nullspace", "gauge", "normalization", "branch", "symmetry")
AMBIGUITY_INTENT: tuple[str, ...] = ("unintended", "intended", "undecided")
#: Diagnosis rounds on one spec before the line is stopped for a human.  The
#: counter is keyed by (problemId, specHash); specHash excludes ``revision``
#: (trust_loop.problem_definition_spec_hash), so an empty revision bump does
#: not reset it.
MAX_DIAGNOSIS_ROUNDS = 3


def intervention_errors(intervention: object, factor: str) -> list[str]:
    """A-0002 draft 2 (review items 2 C and 5): one factor changed, everything else held, a cross-seed trend.

    ``intervention = {factor, changed: [control], heldFixed: [controls], levels: [{level, seeds,
    medianError}], optimizationDiagnosticsClean?}``.  A single larger model (or one
    denser sampling) that happens to do better is not causal evidence: it also
    changes the optimization landscape.  Capacity additionally needs the
    optimization diagnostics to be clean, otherwise the cause may be optimization.
    """

    prefix = "discriminatingExperiment.intervention"
    if not isinstance(intervention, Mapping):
        return [f"{prefix}: naming {factor} requires a controlled {factor} intervention"]
    errors: list[str] = []
    if intervention.get("factor") != factor:
        errors.append(f"{prefix}.factor: must be {factor!r}")
    control = FACTOR_CONTROL[factor]
    changed = intervention.get("changed")
    if not isinstance(changed, list) or sorted(set(changed)) != [control]:
        errors.append(f"{prefix}.changed: exactly [{control!r}] may change; changing anything else with it makes the diagnosis invalid")
    held = intervention.get("heldFixed")
    required = [item for item in INTERVENTION_CONTROLS if item != control]
    if not isinstance(held, list) or any(item not in held for item in required):
        missing = [item for item in required if not isinstance(held, list) or item not in held]
        errors.append(f"{prefix}.heldFixed: must hold {missing} fixed")
    levels = intervention.get("levels")
    if not isinstance(levels, list) or len(levels) < MIN_INTERVENTION_LEVELS:
        errors.append(f"{prefix}.levels: at least {MIN_INTERVENTION_LEVELS} levels are needed; one improvement is insufficient evidence")
    else:
        medians: list[float] = []
        for index, level in enumerate(levels):
            seeds = level.get("seeds") if isinstance(level, Mapping) else None
            median = level.get("medianError") if isinstance(level, Mapping) else None
            if isinstance(seeds, bool) or not isinstance(seeds, int) or seeds < MIN_INTERVENTION_SEEDS:
                errors.append(f"{prefix}.levels[{index}].seeds: at least {MIN_INTERVENTION_SEEDS} seeds per level")
            if isinstance(median, bool) or not isinstance(median, (int, float)) or median != median or median < 0:
                errors.append(f"{prefix}.levels[{index}].medianError: must be a finite non-negative number")
            else:
                medians.append(float(median))
        if len(medians) == len(levels) and any(b >= a for a, b in zip(medians, medians[1:])):
            errors.append(f"{prefix}.levels: the per-level median error must strictly decrease along the levels {medians}")
    if factor == "capacity" and intervention.get("optimizationDiagnosticsClean") is not True:
        errors.append(f"{prefix}.optimizationDiagnosticsClean: capacity cannot be named while the optimization diagnostics are not clean")
    return errors


def replay_diverged(replay: Mapping[str, object]) -> bool:
    return float(replay["maxDivergence"]) > float(replay["epsilonDet"])  # type: ignore[arg-type]


def determinism_replay_errors(replay: object, *, must_diverge: bool) -> list[str]:
    """A-0002 draft 2 (review item 3 B): same seeds, same inputs, same environment -> the runs must agree.

    ``replay = {sameSeedRuns >= 2, maxDivergence, epsilonDet, defectLocated?}``.  Naming
    rImplementationDefect for sSeedSensitive requires the replay to diverge
    (``maxDivergence > epsilonDet``) and the nondeterminism source to be located;
    a replay that agrees excludes implementation nondeterminism instead.
    """

    prefix = f"discriminatingExperiment.{DETERMINISM_REPLAY_KEY}"
    if not isinstance(replay, Mapping):
        return [f"{prefix}: naming rImplementationDefect for sSeedSensitive requires a same-seed deterministic replay"]
    errors: list[str] = []
    runs = replay.get("sameSeedRuns")
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 2:
        errors.append(f"{prefix}.sameSeedRuns: at least two runs with identical seeds and inputs")
    for key in ("maxDivergence", "epsilonDet"):
        value = replay.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or value < 0:
            errors.append(f"{prefix}.{key}: must be a finite non-negative number")
    if errors:
        return errors
    if must_diverge:
        if not replay_diverged(replay):
            errors.append(f"{prefix}: the replay agreed within epsilonDet, so implementation nondeterminism is excluded, not supported")
        located = replay.get("defectLocated")
        if not isinstance(located, str) or not located.strip():
            errors.append(f"{prefix}.defectLocated: the nondeterminism source must be located before naming rImplementationDefect")
    return errors


def identifiability_errors(record: object) -> list[str]:
    """A-0002 draft 3 (final closure review, Issue 3): sSeedSensitive -> rSpecDefect is narrow.

    Seeds landing on different solutions is a *spec defect* only when the frozen
    ScientificSpec left open a non-identifiability (nullspace, gauge freedom,
    normalization or branch ambiguity) that the registered Claim needs resolved
    to be evaluated uniquely -- a pure-Neumann Poisson with an absolute-pressure
    claim and no gauge condition.  Legitimate multiplicity (a branch-aware claim,
    an intended multi-solution study, a spec that already fixes the gauge) is not
    a defect, and when the evidence cannot decide whether the multiplicity is
    intended the cause stays rUndetermined.  P34 therefore asks "does this
    multiplicity violate the identifiability the frozen Claim requires", not
    "are there several solutions".

    ``record = {ambiguityType, claimRequiresUniqueEvaluation, specResolvesAmbiguity,
    ambiguityIntent, nullspaceProjectionFraction?, evidencePointer?}``.
    """

    prefix = f"discriminatingExperiment.{IDENTIFIABILITY_KEY}"
    if not isinstance(record, Mapping):
        return [f"{prefix}: naming rSpecDefect for sSeedSensitive requires a P34 identifiability record"]
    errors: list[str] = []
    if record.get("ambiguityType") not in AMBIGUITY_TYPES:
        errors.append(f"{prefix}.ambiguityType: must be one of {AMBIGUITY_TYPES}")
    for key in ("claimRequiresUniqueEvaluation", "specResolvesAmbiguity"):
        if not isinstance(record.get(key), bool):
            errors.append(f"{prefix}.{key}: must be a boolean")
    intent = record.get("ambiguityIntent")
    if intent not in AMBIGUITY_INTENT:
        errors.append(f"{prefix}.ambiguityIntent: must be one of {AMBIGUITY_INTENT}")
    fraction = record.get("nullspaceProjectionFraction")
    if fraction is not None and (isinstance(fraction, bool) or not isinstance(fraction, (int, float))
                                 or fraction != fraction or not 0.0 <= float(fraction) <= 1.0):
        errors.append(f"{prefix}.nullspaceProjectionFraction: must be a number in [0, 1]")
    if errors:
        return errors
    if record["claimRequiresUniqueEvaluation"] is not True:
        errors.append(
            f"{prefix}: the registered Claim does not need a unique target (branch-aware or set-valued claim); "
            "legitimate multiplicity is not a spec defect, so rSpecDefect cannot be named"
        )
    if record["specResolvesAmbiguity"] is True:
        errors.append(
            f"{prefix}: the frozen spec already resolves the ambiguity (gauge / normalization fixed); "
            "seed sensitivity is then not a spec defect -- exclude the other candidates instead"
        )
    if intent == "intended":
        errors.append(f"{prefix}: the multiplicity is intended by the spec; legitimate multiplicity is not a defect")
    elif intent == "undecided":
        errors.append(
            f"{prefix}: the evidence cannot decide whether the multiplicity is intended; "
            "name rUndetermined and stop the line instead of calling it a spec defect"
        )
    return errors


def discriminating_experiment_errors(
    signature: FailureSignature,
    root_cause: RootCauseClass,
    experiment: object,
    *,
    constitution_version: str,
    explained: "Sequence[FailureSignature] | None" = None,
) -> list[str]:
    """Draft 3 (adversarial audit, item 1): a root cause is what is *left*, not what is chosen.

    ``experiment`` must be a mapping ``{"experimentId": ..., "excludes": {<other
    admissible root cause>: <how it was excluded>, ...}}``.  To name
    ``root_cause`` for ``signature``, every other admissible root cause of that
    signature must appear in ``excludes`` with a non-empty exclusion record;
    otherwise a cheaper Gate could be chosen by naming the most convenient
    cause.  ``rUndetermined`` needs an experimentId only (the experiments ran
    and did not separate the candidates; the line stops).

    The alternatives and the structured obligations come from the matrix of
    ``constitution_version`` (final closure review, Issue 1).  ``explained`` lists
    every observed signature this record explains (Issue 2, default: the primary
    signature only); the exclusion duty is the union over all of them.
    """

    try:
        matrix = admissible_root_causes(constitution_version)
        obligations = naming_obligations(constitution_version)
    except (ConstitutionVersionError, TypeError) as exc:
        return [str(exc)]
    explained_signatures = [signature] if not explained else list(explained)
    if signature not in explained_signatures:
        explained_signatures.insert(0, signature)
    if not isinstance(experiment, Mapping):
        return ["discriminatingExperiment must be a mapping with experimentId and excludes"]
    errors: list[str] = []
    experiment_id = experiment.get("experimentId")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        errors.append("discriminatingExperiment.experimentId: required")
    if root_cause is RootCauseClass.UNDETERMINED:
        return errors
    factor = INTERVENTION_FACTORS.get(root_cause)
    if factor is not None and "intervention" in obligations:
        errors.extend(intervention_errors(experiment.get("intervention"), factor))
    seed_explained = FailureSignature.SEED_SENSITIVE in explained_signatures
    if seed_explained and root_cause is RootCauseClass.IMPLEMENTATION_DEFECT and DETERMINISM_REPLAY_KEY in obligations:
        errors.extend(determinism_replay_errors(experiment.get(DETERMINISM_REPLAY_KEY), must_diverge=True))
    if seed_explained and root_cause is RootCauseClass.SPEC_DEFECT and IDENTIFIABILITY_KEY in obligations:
        errors.extend(identifiability_errors(experiment.get(IDENTIFIABILITY_KEY)))
    excludes = experiment.get("excludes")
    if not isinstance(excludes, Mapping):
        return errors + ["discriminatingExperiment.excludes: required mapping of excluded root cause -> exclusion record"]
    named: dict[RootCauseClass, object] = {}
    for key, value in excludes.items():
        try:
            cause = key if isinstance(key, RootCauseClass) else RootCauseClass(key)
        except ValueError:
            errors.append(f"discriminatingExperiment.excludes: {key!r} is not a RootCauseClass")
            continue
        if cause is root_cause:
            errors.append(f"discriminatingExperiment.excludes: the named root cause {cause.value} cannot exclude itself")
        if cause is RootCauseClass.UNDETERMINED:
            errors.append("discriminatingExperiment.excludes: rUndetermined is not a candidate to exclude")
        if not value:
            errors.append(f"discriminatingExperiment.excludes.{cause.value}: empty exclusion record")
        named[cause] = value
    alternatives: list[RootCauseClass] = []
    for item in explained_signatures:
        for cause in matrix[item]:
            if cause is not root_cause and cause not in alternatives:
                alternatives.append(cause)
    missing = [cause.value for cause in alternatives if cause not in named]
    if missing:
        explained_names = ", ".join(item.value for item in explained_signatures)
        errors.append(
            f"discriminatingExperiment.excludes: {root_cause.value} can only be named for {explained_names} "
            f"once every other admissible root cause is excluded; missing {missing}"
        )
    return errors


def from_gate_status(status: GateStatus) -> TrustStatus:
    """The explicit, only conversion from a Gate result to a dimension status."""

    if not isinstance(status, GateStatus):
        raise TypeError(f"{status!r} is not a GateStatus")
    return TrustStatus[status.name]


def gate5_status(*, physics: GateStatus, external: GateStatus) -> GateStatus:
    """Gate 5 PASSes only when both MUST groups PASS; FAIL dominates BLOCKED dominates PARTIAL."""

    for value in (physics, external):
        if not isinstance(value, GateStatus):
            raise TypeError(f"{value!r} is not a GateStatus")
    parts = (physics, external)
    if all(part is GateStatus.PASS for part in parts):
        return GateStatus.PASS
    if any(part is GateStatus.FAIL for part in parts):
        return GateStatus.FAIL
    if any(part is GateStatus.BLOCKED for part in parts):
        return GateStatus.BLOCKED
    return GateStatus.PARTIAL


def _dimensions_up_to(gate: int) -> tuple[str, ...]:
    return tuple(d for number in sorted(GATE_DIMENSIONS) if number <= gate for d in GATE_DIMENSIONS[number])


def advancement_allowed(vector: Mapping[str, object], gate: int) -> bool:
    """Every dimension judged up to ``gate`` is PASS and nothing later has been judged yet."""

    if gate not in GATE_DIMENSIONS:
        raise ValueError(f"unknown gate {gate!r}")
    checked = coerce_vector(vector)
    judged = _dimensions_up_to(gate)
    later = tuple(d for d in DIMENSIONS if d not in judged)
    return all(checked[d] is TrustStatus.PASS for d in judged) and all(
        checked[d] is TrustStatus.NOT_CHECKED for d in later
    )


def failure_state(rounds_completed: int) -> WorkflowState:
    """FAILURE_RECORDED for the first MAX_DIAGNOSIS_ROUNDS failures on a spec, then STOPPED_THE_LINE."""

    if isinstance(rounds_completed, bool) or not isinstance(rounds_completed, int) or rounds_completed < 0:
        raise ValueError("rounds_completed must be a non-negative integer")
    if rounds_completed >= MAX_DIAGNOSIS_ROUNDS:
        return WorkflowState.STOPPED_THE_LINE
    return WorkflowState.FAILURE_RECORDED


def enter_validation(state: WorkflowState) -> WorkflowState:
    if state is not WorkflowState.TRAINING_COMPLETED:
        raise IllegalTransition(f"VALIDATION is entered from TRAINING_COMPLETED, not {getattr(state, 'value', state)!r}")
    return WorkflowState.VALIDATION


def advance(
    state: WorkflowState,
    gate: int,
    result: GateStatus,
    vector: Mapping[str, object],
    *,
    claim_decision_signed: bool = False,
    rounds_completed: int = 0,
) -> WorkflowState:
    """Apply one executed gate result.

    INV1: PARTIAL and BLOCKED never advance (the state is returned unchanged).
    INV2: ACCEPTED has exactly one entry, gate 6 PASS with a signed decision.
    INV3: FAIL always goes to FAILURE_RECORDED (or STOPPED_THE_LINE once the
    diagnosis rounds are used up); there is no in-place retraining.
    """

    if not isinstance(state, WorkflowState):
        raise TypeError(f"{state!r} is not a WorkflowState")
    if not isinstance(result, GateStatus):
        raise TypeError(f"{result!r} is not a GateStatus")
    if gate not in GATE_RUNS_IN:
        raise ValueError(f"unknown gate {gate!r}")
    if GATE_RUNS_IN[gate] is not state:
        raise IllegalTransition(f"gate {gate} does not execute in state {state.value}")
    if result is GateStatus.FAIL:
        return failure_state(rounds_completed)
    if result is not GateStatus.PASS:
        return state
    if not advancement_allowed(vector, gate):
        raise IllegalTransition(f"the trust vector does not license advancing past gate {gate}")
    if gate == 6 and claim_decision_signed is not True:
        raise IllegalTransition("ACCEPTED requires a signed ClaimGateDecision")
    return GATE_ADVANCES_TO[gate]


@dataclass(frozen=True)
class TriageRoute:
    signature: FailureSignature
    root_cause: RootCauseClass
    gate: int
    reentry_state: WorkflowState


def diagnose(
    state: WorkflowState,
    signature: FailureSignature,
    root_cause: RootCauseClass,
    evidence: Mapping[str, object],
    *,
    constitution_version: str,
) -> tuple[WorkflowState, TriageRoute | None]:
    """FAILURE_RECORDED -> DIAGNOSED (or STOPPED_THE_LINE when the cause stays UNDETERMINED).

    The signature is what was seen; the root cause is what the discriminating
    experiment found.  The route follows the root cause, and only a root cause
    that is admissible for the signature *under the Constitution version the run
    is bound to* may be named -- there is no default version, so a direct call
    cannot pick up a PROPOSED amendment's cells.  ``evidence`` may carry
    ``explainedSignatures`` (Issue 2): every signature listed widens the
    exclusion duty to that signature's candidates as well.
    """

    matrix = admissible_root_causes(constitution_version)
    if state is not WorkflowState.FAILURE_RECORDED:
        raise IllegalTransition("diagnosis starts from FAILURE_RECORDED")
    if not isinstance(signature, FailureSignature):
        raise TypeError(f"{signature!r} is not a FailureSignature")
    if not isinstance(root_cause, RootCauseClass):
        raise TypeError(f"{root_cause!r} is not a RootCauseClass")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping of artifact name -> reference")
    required = SIGNATURE_EVIDENCE[signature] + (DISCRIMINATING_EXPERIMENT_KEY,)
    missing = [key for key in required if not evidence.get(key)]
    if missing:
        raise ValueError(f"{signature.value}: missing diagnosis evidence {missing}")
    explained_raw = evidence.get("explainedSignatures")
    explained = [signature]
    if explained_raw is not None:
        if not isinstance(explained_raw, (list, tuple)) or not all(isinstance(item, FailureSignature) for item in explained_raw):
            raise TypeError("explainedSignatures must be a list of FailureSignature")
        explained = [signature] + [item for item in explained_raw if item is not signature]
    problems = discriminating_experiment_errors(
        signature, root_cause, evidence[DISCRIMINATING_EXPERIMENT_KEY],
        constitution_version=constitution_version, explained=explained,
    )
    if problems:
        raise ValueError(f"{signature.value}: " + "; ".join(problems))
    if root_cause is RootCauseClass.UNDETERMINED:
        return WorkflowState.STOPPED_THE_LINE, None
    for item in explained:
        if root_cause not in matrix[item]:
            raise IllegalTransition(
                f"{root_cause.value} is not an admissible root cause for {item.value} under Constitution {constitution_version}"
            )
    gate = ROOT_CAUSE_GATE[root_cause]
    return WorkflowState.DIAGNOSED, TriageRoute(signature, root_cause, gate, GATE_RUNS_IN[gate])


def earliest_route(routes: "Sequence[TriageRoute]") -> TriageRoute:
    """Several DiagnosisRecords on one run (Issue 2) re-enter at the earliest Gate.

    Re-entering Gate k resets k and everything downstream, so the record with
    the smallest Gate subsumes the others; nothing is skipped.
    """

    if not routes or not all(isinstance(route, TriageRoute) for route in routes):
        raise TypeError("earliest_route needs a non-empty sequence of TriageRoute")
    return min(routes, key=lambda route: route.gate)


def revise(state: WorkflowState) -> WorkflowState:
    if state is not WorkflowState.DIAGNOSED:
        raise IllegalTransition("REVISED follows DIAGNOSED")
    return WorkflowState.REVISED


def reenter(state: WorkflowState, route: TriageRoute, vector: Mapping[str, object]) -> WorkflowState:
    """REVISED -> the state in which the routed gate executes.

    INV4 (conservatively applied): every dimension judged by the re-entry gate
    or later must have been reset to NOT_CHECKED, and everything upstream must
    still be PASS.  Downstream gates are re-run in order; nothing is skipped.
    """

    if state is not WorkflowState.REVISED:
        raise IllegalTransition("re-entry starts from REVISED")
    if not isinstance(route, TriageRoute):
        raise TypeError(f"{route!r} is not a TriageRoute")
    checked = coerce_vector(vector)
    upstream = _dimensions_up_to(route.gate - 1)
    downstream = tuple(d for d in DIMENSIONS if d not in upstream)
    if not all(checked[d] is TrustStatus.PASS for d in upstream):
        raise IllegalTransition("dimensions upstream of the re-entry gate must be PASS")
    if not all(checked[d] is TrustStatus.NOT_CHECKED for d in downstream):
        raise IllegalTransition("dimensions from the re-entry gate onwards must be reset to NOT_CHECKED")
    return route.reentry_state
