"""Trust-vector calculus: weakest-link claim gating (Amendment A-0001, draft 3).

A trust vector has six dimensions -- math, impl, train, physics, external,
repro -- and each carries one ``TrustStatus``.  Only PASS supports a claim.
The only legal combination operator is the meet (the weakest link); the
statuses form a chain and carry no arithmetic, so "average trust" is a type
error rather than a number.

Draft 2 (review of 2026-09-14) added ``Applicability`` as a separate type,
the seed bands 0.8 / 0.9 and independently qualified C2 runs for C3.

Draft 3 (adversarial governance review of 2026-09-15) adds:

* INV-A1: a registered check list must contain at least one APPLICABLE
  check.  "Every check NOT_APPLICABLE" is not a weaker NOT_CHECKED, it is an
  illegal registration -- every trust dimension is the subject of a MUST
  Gate and therefore owes at least one check (see
  ``dimension_status_from_checks``).
* ``seed_statistics``: the multi-seed rule computed from the per-seed errors
  themselves.  Dispersion is judged as ``IQR > limit * median`` -- a
  multiplication, never a division -- so a zero or near-zero median can
  neither divide by zero nor need a preregistered floor.  NaN / Inf errors are
  divergent runs: they stay in N, never in k, and make the worst seed
  divergent.
* ``EnvironmentFingerprint`` / ``independent_environments``: the single
  definition of "independent execution environment" that both C3 run
  qualification and Gate 6 reproduction use.  Two environments are
  independent iff at least one *strong* material field differs; patch-level
  differences (weak fields) never make a new environment.
* ``seed_set_id`` derived from the actual seed values, so renaming a seed set
  cannot make it a new one.
* ``reproduction_status``: C_repro from one reproduction record, through the
  same environment rule.

This module deliberately imports nothing from ``state_machine``; the state
machine imports it.  ``TrustStatus`` is *not* a ``GateStatus``: the
Constitution's four Gate statuses are unchanged, and NOT_CHECKED exists only
as a trust-vector dimension status (a check that has not been executed yet).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .canonical import canonical_sha256


class TrustStatus(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_CHECKED = "NOT_CHECKED"

    def _no_arithmetic(self, *_args):
        raise TypeError("TrustStatus has no arithmetic; combine statuses with meet()")

    __add__ = __radd__ = __sub__ = __rsub__ = _no_arithmetic
    __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __floordiv__ = _no_arithmetic


class Applicability(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


DIMENSIONS: tuple[str, ...] = ("math", "impl", "train", "physics", "external", "repro")

#: Support rank on the chain FAIL < BLOCKED < NOT_CHECKED < PARTIAL < PASS
#: (merge notes C1).  Everything below PASS blocks; the rank only decides
#: which dimension is reported as the weakest link.
SUPPORT_RANK: dict[TrustStatus, int] = {
    TrustStatus.FAIL: 0,
    TrustStatus.BLOCKED: 1,
    TrustStatus.NOT_CHECKED: 2,
    TrustStatus.PARTIAL: 3,
    TrustStatus.PASS: 4,
}

CLAIM_LEVELS: tuple[str, ...] = ("C0", "C1", "C2", "C3")
EVIDENCE_LEVELS: tuple[str, ...] = ("A", "B", "C", "D")

#: Dimensions that must be PASS for each claim level.  These only tighten the
#: MVP plan's prerequisite matrix (G1,G3 / +G4 / G1-G6): C0 needs math+impl,
#: C1 adds train, C2 and C3 need every dimension.
REQUIRED_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "C0": ("math", "impl"),
    "C1": ("math", "impl", "train"),
    "C2": DIMENSIONS,
    "C3": DIMENSIONS,
}

#: C3 (Robustness) additionally needs independently qualified C2 runs.
MINIMUM_QUALIFIED_C2_RUNS_FOR_C3 = 5
MINIMUM_C3_ENVIRONMENTS = 2

#: Seed protocol (Kimi section 3 as revised by the 2026-09-14 review).
SEED_FAIL_BELOW = 0.8
SEED_PASS_FROM = 0.9
MINIMUM_SEED_RUNS = 10
TRANSITIONAL_SEED_RUNS = 5
#: Worst seed may not exceed WORST_SEED_FACTOR * epsilon_spec; the IQR may not
#: exceed DISPERSION_LIMIT * median.  Both are preregistration starting points.
WORST_SEED_FACTOR = 3.0
DISPERSION_LIMIT = 1.0


def coerce_vector(vector: Mapping[str, object]) -> dict[str, TrustStatus]:
    """Return a checked ``{dimension: TrustStatus}`` mapping or raise.

    Accepts ``TrustStatus`` members and plain ``str`` values; any other type
    (including another string Enum such as ``GateStatus``) is rejected so that
    Gate results reach a dimension only through an explicit conversion.
    """

    if not isinstance(vector, Mapping):
        raise TypeError("trust vector must be a mapping of dimension -> status")
    if set(vector) != set(DIMENSIONS):
        raise ValueError(f"trust vector must have exactly the dimensions {DIMENSIONS}")
    result: dict[str, TrustStatus] = {}
    for dimension in DIMENSIONS:
        value = vector[dimension]
        if isinstance(value, TrustStatus):
            result[dimension] = value
        elif type(value) is str and value in TrustStatus.__members__:
            result[dimension] = TrustStatus[value]
        else:
            raise ValueError(f"{dimension}: {value!r} is not a TrustStatus")
    return result


def meet(statuses: Iterable[TrustStatus]) -> TrustStatus:
    """The weakest status of a non-empty collection (the lattice meet)."""

    items = list(statuses)
    if not items:
        raise ValueError("meet() of no statuses is undefined")
    for item in items:
        if not isinstance(item, TrustStatus):
            raise TypeError(f"{item!r} is not a TrustStatus")
    return min(items, key=lambda status: SUPPORT_RANK[status])


def weakest_link(vector: Mapping[str, object]) -> tuple[TrustStatus, tuple[str, ...]]:
    """The weakest status and every dimension that attains it (in fixed order)."""

    checked = coerce_vector(vector)
    status = meet(checked.values())
    return status, tuple(d for d in DIMENSIONS if checked[d] is status)


# ------------------------------------------------------------------ checks

@dataclass(frozen=True)
class CheckResult:
    """One named check inside a dimension.

    NOT_APPLICABLE means the problem does not owe this check (it must say why);
    it carries no status and never enters the meet.  APPLICABLE checks carry
    exactly one TrustStatus.
    """

    check_id: str
    applicability: Applicability
    status: TrustStatus | None = None
    reason: str | None = None
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise ValueError("check_id must be a non-empty string")
        if not isinstance(self.applicability, Applicability):
            raise TypeError(f"{self.applicability!r} is not an Applicability")
        if self.applicability is Applicability.APPLICABLE:
            if not isinstance(self.status, TrustStatus):
                raise ValueError(f"{self.check_id}: an applicable check needs a TrustStatus")
        else:
            if self.status is not None:
                raise ValueError(f"{self.check_id}: a NOT_APPLICABLE check has no status")
            if not isinstance(self.reason, str) or not self.reason.strip():
                raise ValueError(f"{self.check_id}: NOT_APPLICABLE must state why the check is not owed")


class NoApplicableCheck(ValueError):
    """INV-A1: a registered check list with no APPLICABLE check is illegal.

    "Applicability was assessed and nothing is owed" is not a state a trust
    dimension can be in: each dimension is the subject of a MUST Gate, so a
    problem for which every check of a dimension is NOT_APPLICABLE has a
    spec defect (the check registry is incomplete), not an exempt dimension.
    Registering nothing at all (an empty list) is the ordinary NOT_CHECKED.
    """


def dimension_status_from_checks(checks: Iterable[CheckResult]) -> TrustStatus:
    """Meet of the applicable checks.

    An empty list is NOT_CHECKED (nothing registered yet).  A non-empty list
    whose checks are all NOT_APPLICABLE raises ``NoApplicableCheck`` (INV-A1)
    instead of silently becoming NOT_CHECKED, so that "all N/A" can never be
    read as either a weak pass or an honest not-yet-checked.
    """

    items = list(checks)
    for item in items:
        if not isinstance(item, CheckResult):
            raise TypeError(f"{item!r} is not a CheckResult")
    if not items:
        return TrustStatus.NOT_CHECKED
    applicable = [item.status for item in items if item.applicability is Applicability.APPLICABLE]
    if not applicable:
        raise NoApplicableCheck(
            "every registered check is NOT_APPLICABLE; a trust dimension owes at least one "
            "applicable check (INV-A1) -- fix the check registry of the spec, do not exempt the dimension"
        )
    return meet(applicable)  # type: ignore[arg-type]  -- statuses are TrustStatus by construction


# ---------------------------------------------------------------- training

def training_reliability_status(
    *,
    runs: int,
    successes: int,
    median_ok: bool,
    worst_ok: bool,
    iqr_ok: bool,
    minimum_runs: int = MINIMUM_SEED_RUNS,
    transitional_runs: int = TRANSITIONAL_SEED_RUNS,
) -> TrustStatus:
    """C_train from already-judged seed statistics (see ``seed_statistics`` for the judging).

    ``successes`` is the number of runs that met the preregistered error
    criterion.  Fewer than ``transitional_runs`` runs is not an executed
    protocol (BLOCKED).  A median above the criterion or k/N < 0.8 is FAIL.
    Between ``transitional_runs`` and ``minimum_runs`` the dimension is capped
    at PARTIAL; so is 0.8 <= k/N < 0.9, a worst seed beyond its bound, or an
    IQR beyond its bound.  The best seed never enters this decision.
    """

    for name, value in (("runs", runs), ("successes", successes),
                        ("minimum_runs", minimum_runs), ("transitional_runs", transitional_runs)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    for name, value in (("median_ok", median_ok), ("worst_ok", worst_ok), ("iqr_ok", iqr_ok)):
        if value is not True and value is not False:
            raise ValueError(f"{name} must be a boolean")
    if successes > runs:
        raise ValueError("successes cannot exceed runs")
    if transitional_runs < 1 or minimum_runs < transitional_runs:
        raise ValueError("run thresholds must satisfy 1 <= transitional_runs <= minimum_runs")
    if runs < transitional_runs:
        return TrustStatus.BLOCKED
    ratio = successes / runs
    if median_ok is False or ratio < SEED_FAIL_BELOW:
        return TrustStatus.FAIL
    if runs < minimum_runs or ratio < SEED_PASS_FROM or worst_ok is False or iqr_ok is False:
        return TrustStatus.PARTIAL
    return TrustStatus.PASS


@dataclass(frozen=True)
class SeedStatistics:
    """What the multi-seed protocol reports: never the best seed."""

    runs: int
    successes: int
    divergent: int
    median: float          # +inf when at least half of the runs diverged
    iqr: float             # +inf when the upper quartile is divergent
    worst: float           # +inf when any run diverged
    median_ok: bool
    worst_ok: bool
    dispersion_ok: bool
    status: TrustStatus


def _sanitized_error(value: object, index: int) -> float:
    """A per-seed error: finite non-negative -> itself; NaN / Inf -> +inf (divergent)."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"errors[{index}]: {value!r} is not a number")
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        return math.inf
    if number < 0:
        raise ValueError(f"errors[{index}]: an error norm cannot be negative ({number!r})")
    return number


def _median(sorted_values: Sequence[float]) -> float:
    count = len(sorted_values)
    middle = count // 2
    if count % 2:
        return sorted_values[middle]
    low, high = sorted_values[middle - 1], sorted_values[middle]
    if math.isinf(low) or math.isinf(high):
        return math.inf
    return (low + high) / 2.0


def _quartiles(sorted_values: Sequence[float]) -> tuple[float, float]:
    """Q1 and Q3 by the median-of-halves rule (Tukey hinges), the preregistered convention."""

    count = len(sorted_values)
    half = count // 2
    lower = sorted_values[:half]
    upper = sorted_values[half + (count % 2):]
    return _median(lower), _median(upper)


def seed_statistics(
    errors: Sequence[object],
    *,
    epsilon_spec: float,
    minimum_runs: int = MINIMUM_SEED_RUNS,
    transitional_runs: int = TRANSITIONAL_SEED_RUNS,
    worst_factor: float = WORST_SEED_FACTOR,
    dispersion_limit: float = DISPERSION_LIMIT,
) -> SeedStatistics:
    """Judge the multi-seed protocol from the per-seed error norms.

    Rules (all comparisons explicit, no division anywhere):

    * an error that is NaN or infinite is a divergent run: it stays in N,
      is never a success, and makes the worst seed divergent;
    * a negative error is a caller bug (error norms are non-negative) and
      raises;
    * success: error <= epsilon_spec;
    * median_ok: median <= epsilon_spec;
    * worst_ok: worst <= worst_factor * epsilon_spec;
    * dispersion_ok: NOT (IQR > dispersion_limit * median).  With median = 0
      and IQR = 0 this is ok (0 > 0 is false); with median = 0 and IQR > 0 it
      is not ok (IQR > 0); nothing is divided, so no floor is needed and no
      floating-point "median approximately zero" rule exists.
    """

    if isinstance(epsilon_spec, bool) or not isinstance(epsilon_spec, (int, float)):
        raise ValueError("epsilon_spec must be a number")
    if not math.isfinite(epsilon_spec) or epsilon_spec <= 0:
        raise ValueError("epsilon_spec must be a finite positive number")
    for name, value in (("worst_factor", worst_factor), ("dispersion_limit", dispersion_limit)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite positive number")
    if isinstance(errors, (str, bytes, Mapping)):
        raise TypeError("errors must be a sequence of per-seed error norms")
    values = [_sanitized_error(value, index) for index, value in enumerate(errors)]
    runs = len(values)
    divergent = sum(1 for value in values if math.isinf(value))
    successes = sum(1 for value in values if value <= epsilon_spec)
    if runs == 0:
        return SeedStatistics(0, 0, 0, math.inf, math.inf, math.inf, False, False, False, TrustStatus.BLOCKED)
    ordered = sorted(values)
    median = _median(ordered)
    q1, q3 = _quartiles(ordered) if runs >= 2 else (ordered[0], ordered[0])
    iqr = math.inf if math.isinf(q3) else q3 - q1
    worst = ordered[-1]
    median_ok = median <= epsilon_spec
    worst_ok = worst <= worst_factor * epsilon_spec
    dispersion_ok = not (iqr > dispersion_limit * median)
    status = training_reliability_status(
        runs=runs, successes=successes, median_ok=median_ok, worst_ok=worst_ok, iqr_ok=dispersion_ok,
        minimum_runs=minimum_runs, transitional_runs=transitional_runs,
    )
    return SeedStatistics(runs, successes, divergent, median, iqr, worst, median_ok, worst_ok, dispersion_ok, status)


# ------------------------------------------------------------ environments

#: Material fields of an execution environment.  A difference in any STRONG
#: field makes two environments independent; WEAK fields are recorded but a
#: difference confined to them is the same environment (Kimi R2 section 4.1).
ENVIRONMENT_STRONG_FIELDS: tuple[str, ...] = (
    "machineId",            # hardware identity (stable machine fingerprint, not hostname)
    "osFamily",             # windows / linux / macos
    "acceleratorClass",     # cpu-only, or the GPU model
    "frameworkVersion",     # framework name + major.minor
    "blasBackend",          # openblas / mkl / accelerate / cublas ...
    "dependencyLockHash",   # hash of the resolved dependency lock
    "installationId",       # the concrete installation: venv / conda prefix id, or the container image digest
)
ENVIRONMENT_WEAK_FIELDS: tuple[str, ...] = (
    "osVersion",
    "pythonVersion",        # patch-level; the major.minor is part of dependencyLockHash / frameworkVersion
    "acceleratorDriver",
)
ENVIRONMENT_FIELDS: tuple[str, ...] = ENVIRONMENT_STRONG_FIELDS + ENVIRONMENT_WEAK_FIELDS


@dataclass(frozen=True)
class EnvironmentFingerprint:
    machineId: str
    osFamily: str
    acceleratorClass: str
    frameworkVersion: str
    blasBackend: str
    dependencyLockHash: str
    installationId: str
    osVersion: str = ""
    pythonVersion: str = ""
    acceleratorDriver: str = ""

    def __post_init__(self) -> None:
        for name in ENVIRONMENT_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            if name in ENVIRONMENT_STRONG_FIELDS and not value.strip():
                raise ValueError(f"{name} is a strong environment field and must be non-empty")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "EnvironmentFingerprint":
        if not isinstance(raw, Mapping):
            raise TypeError("environment must be a mapping of material fields")
        unknown = set(raw) - set(ENVIRONMENT_FIELDS)
        if unknown:
            raise ValueError(f"unknown environment fields {sorted(unknown)}; hostnames, paths and users are not identity")
        missing = [name for name in ENVIRONMENT_STRONG_FIELDS if name not in raw]
        if missing:
            raise ValueError(f"environment is missing strong fields {missing}")
        return cls(**{name: raw.get(name, "") for name in ENVIRONMENT_FIELDS})  # type: ignore[arg-type]

    def strong_material(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in ENVIRONMENT_STRONG_FIELDS}


def environment_id(fingerprint: EnvironmentFingerprint) -> str:
    """The environment identity: a hash of the strong fields only.

    Because weak fields are excluded, ``environment_id(a) != environment_id(b)``
    is *exactly* ``independent_environments(a, b)``: there is one rule, used by
    C3 run qualification and by Gate 6 alike.
    """

    if not isinstance(fingerprint, EnvironmentFingerprint):
        raise TypeError(f"{fingerprint!r} is not an EnvironmentFingerprint")
    return canonical_sha256(fingerprint.strong_material())


def independent_environments(a: EnvironmentFingerprint, b: EnvironmentFingerprint) -> bool:
    """Independent iff at least one strong field differs.

    Cases the 2026-09-15 review asked about:
      A. same machine, a second independent installation (different venv /
         conda prefix, hence a different installationId): independent --
         this is the weakest admissible form, it tests that the result is not
         tied to one installation's state;
      B. same machine, two containers of the same image: same installationId
         (the image digest), same machineId: NOT independent;
      C. different machines, identical lock file: independent (machineId);
      D. two nodes of one cluster: independent iff their machineIds differ;
      E. different OS or accelerator: independent.
    Patch-level differences (osVersion, pythonVersion patch, driver patch)
    never make a new environment.
    """

    for value in (a, b):
        if not isinstance(value, EnvironmentFingerprint):
            raise TypeError(f"{value!r} is not an EnvironmentFingerprint")
    return a.strong_material() != b.strong_material()


def seed_set_id(seeds: Iterable[object]) -> str:
    """Identity of a seed set: hash of the sorted distinct seed values, never of a name."""

    values: list[int] = []
    for seed in seeds:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError(f"seed {seed!r} is not a non-negative integer")
        values.append(seed)
    if not values:
        raise ValueError("a seed set needs at least one seed")
    return canonical_sha256(sorted(set(values)))


# ---------------------------------------------------------------- C3 runs

@dataclass(frozen=True)
class RunQualification:
    """Identity of one SUPPORTED @ C2 run, on the axes C3 independence is judged by.

    ``environment_id`` and ``seed_set_id`` are *derived* identities (see
    ``environment_id`` and ``seed_set_id``); ``from_record`` derives them from
    the material, which is how a validator must build them.
    """

    run_id: str
    spec_hash: str
    code_hash: str
    environment_id: str
    seed_set_id: str

    def __post_init__(self) -> None:
        for name in ("run_id", "spec_hash", "code_hash", "environment_id", "seed_set_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

    @classmethod
    def from_record(
        cls, *, run_id: str, spec_hash: str, code_hash: str,
        environment: EnvironmentFingerprint | Mapping[str, object], seeds: Iterable[object],
    ) -> "RunQualification":
        fingerprint = environment if isinstance(environment, EnvironmentFingerprint) \
            else EnvironmentFingerprint.from_mapping(environment)
        return cls(run_id=run_id, spec_hash=spec_hash, code_hash=code_hash,
                   environment_id=environment_id(fingerprint), seed_set_id=seed_set_id(seeds))


@dataclass(frozen=True)
class C3Support:
    qualified_runs: int
    satisfied: bool
    problems: tuple[str, ...]


def c3_run_support(records: Sequence[RunQualification], *, spec_hash: str, code_hash: str) -> C3Support:
    """How many of ``records`` are independently qualified runs of the method (spec_hash, code_hash).

    A method is one spec and one code identity; runs of a different spec or
    code are runs of a different method and do not count.  Among the matching
    runs, seed sets must be distinct (a copied run is not a new run) and at
    least MINIMUM_C3_ENVIRONMENTS execution environments must appear.
    """

    problems: list[str] = []
    for record in records:
        if not isinstance(record, RunQualification):
            raise TypeError(f"{record!r} is not a RunQualification")
    matching = [r for r in records if r.spec_hash == spec_hash and r.code_hash == code_hash]
    foreign = len(records) - len(matching)
    if foreign:
        problems.append(f"{foreign} run(s) belong to a different spec or code identity and do not count")
    run_ids = [r.run_id for r in matching]
    if len(set(run_ids)) != len(run_ids):
        problems.append("duplicate runIds among the C2 runs")
    seed_sets = {r.seed_set_id for r in matching}
    if len(seed_sets) != len(matching):
        problems.append(f"only {len(seed_sets)} distinct seed set(s) among {len(matching)} matching run(s)")
    environments = {r.environment_id for r in matching}
    qualified = len(seed_sets) if len(set(run_ids)) == len(run_ids) else 0
    if qualified and len(environments) < MINIMUM_C3_ENVIRONMENTS:
        problems.append(
            f"only {len(environments)} distinct environment(s); C3 needs at least {MINIMUM_C3_ENVIRONMENTS}"
        )
    if qualified < MINIMUM_QUALIFIED_C2_RUNS_FOR_C3:
        problems.append(
            f"C3 needs at least {MINIMUM_QUALIFIED_C2_RUNS_FOR_C3} independently qualified C2 runs, have {qualified}"
        )
    satisfied = qualified >= MINIMUM_QUALIFIED_C2_RUNS_FOR_C3 and len(environments) >= MINIMUM_C3_ENVIRONMENTS
    return C3Support(qualified, satisfied, tuple(problems))


# ------------------------------------------------------------- Gate 6

@dataclass(frozen=True)
class ReproductionVerdict:
    status: TrustStatus
    problems: tuple[str, ...]


def reproduction_status(
    original: RunQualification,
    reproduction: RunQualification,
    *,
    within_tolerance: bool,
) -> ReproductionVerdict:
    """C_repro from one reproduction of ``original`` (merge notes C12, Gate 6).

    PASS needs: the same method (spec and code identity), an independent
    environment (the same rule as C3: a different derived environment id),
    a different seed set, and the reproduced result inside the preregistered
    tolerance.  A reproduction that is not one by this definition (same
    environment, or the same seeds -- that only shows determinism) is a
    protocol not executed: BLOCKED.  Executed but outside tolerance: FAIL.
    """

    for value in (original, reproduction):
        if not isinstance(value, RunQualification):
            raise TypeError(f"{value!r} is not a RunQualification")
    if within_tolerance is not True and within_tolerance is not False:
        raise ValueError("within_tolerance must be a boolean")
    problems: list[str] = []
    if original.run_id == reproduction.run_id:
        problems.append("a run does not reproduce itself")
    if original.spec_hash != reproduction.spec_hash or original.code_hash != reproduction.code_hash:
        problems.append("a reproduction must run the same method (spec and code identity)")
    if original.environment_id == reproduction.environment_id:
        problems.append("the reproduction ran in the same execution environment; same machine and same "
                        "installation only show determinism")
    if original.seed_set_id == reproduction.seed_set_id:
        problems.append("the reproduction reused the seed set; same seeds only show determinism")
    if problems:
        return ReproductionVerdict(TrustStatus.BLOCKED, tuple(problems))
    if within_tolerance:
        return ReproductionVerdict(TrustStatus.PASS, ())
    return ReproductionVerdict(TrustStatus.FAIL, ("the reproduced result fell outside the preregistered tolerance",))


# ------------------------------------------------------------------ claims

@dataclass(frozen=True)
class ClaimGate:
    allowed: tuple[str, ...]
    blocked: dict[str, tuple[str, ...]]
    weakest_status: TrustStatus
    weakest_dimensions: tuple[str, ...]

    @property
    def highest_allowed(self) -> str | None:
        return self.allowed[-1] if self.allowed else None


def claim_gate(
    vector: Mapping[str, object],
    *,
    evidence_level: str,
    c2_runs: Sequence[RunQualification] = (),
    spec_hash: str | None = None,
    code_hash: str | None = None,
    exploratory: bool = False,
    stop_the_line: bool = False,
) -> ClaimGate:
    """Decide which claim levels the vector permits; everything else is blocked with reasons.

    Fail-closed inputs (stop-the-line, unknown evidence level, non-boolean
    ``exploratory``, C2 runs supplied without the method identity) block every
    level.  Nothing here is evidence that a claim is true: a permitted level
    still needs its ScientificClaim to be written and its failure conditions
    to be watched.
    """

    checked = coerce_vector(vector)
    weakest_status, weakest_dimensions = weakest_link(checked)

    closed: list[str] = []
    if stop_the_line is not False:
        closed.append("stop-the-line is active")
    if evidence_level not in EVIDENCE_LEVELS:
        closed.append(f"unknown evidence level {evidence_level!r}")
    if exploratory is not True and exploratory is not False:
        closed.append("exploratory flag must be a boolean")
    runs = list(c2_runs)
    if runs and (not isinstance(spec_hash, str) or not isinstance(code_hash, str)):
        closed.append("C2 runs were supplied without the method's spec and code identity")

    support = C3Support(0, False, ("no independently qualified C2 runs supplied",))
    if runs and not closed:
        support = c3_run_support(runs, spec_hash=spec_hash, code_hash=code_hash)  # type: ignore[arg-type]

    allowed: list[str] = []
    blocked: dict[str, tuple[str, ...]] = {}
    for level in CLAIM_LEVELS:
        reasons = list(closed)
        missing = [d for d in REQUIRED_DIMENSIONS[level] if checked[d] is not TrustStatus.PASS]
        if missing:
            reasons.append("dimensions not PASS: " + ", ".join(f"{d}={checked[d].value}" for d in missing))
        if level in ("C2", "C3") and evidence_level == "D":
            reasons.append("evidence level D excludes numerical accuracy claims")
        if level in ("C2", "C3") and exploratory is True:
            reasons.append("EXPLORATORY runs are capped at C1")
        if level == "C3":
            if "C2" not in allowed:
                reasons.append("C3 requires C2 to be allowed")
            if not closed and not support.satisfied:
                reasons.extend(support.problems)
        if reasons:
            blocked[level] = tuple(reasons)
        else:
            allowed.append(level)
    return ClaimGate(tuple(allowed), blocked, weakest_status, weakest_dimensions)


def allowed_claim_levels(vector: Mapping[str, object], **kwargs) -> tuple[str, ...]:
    return claim_gate(vector, **kwargs).allowed
