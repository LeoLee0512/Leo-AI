"""Solver-independent validation components, without claim or Gate authority."""

from .poisson import (
    FieldSamples,
    PoissonProtocol,
    ValidationInputError,
    evaluate_samples,
    load_candidate_protocol,
    sample_callable_fixture,
)

__all__ = [
    "FieldSamples", "PoissonProtocol", "ValidationInputError", "evaluate_samples",
    "load_candidate_protocol", "sample_callable_fixture",
]
