"""Trusted analytic reference for Poisson-1D v1.0.

This module is deliberately independent of every PINN model implementation.
Its source SHA-256 is recorded in the spec draft and checked during pre-lock.
"""

from __future__ import annotations

import math


SPEC_BINDING = "poisson-1d-dirichlet@1.0"
EQUATION_BINDING = "-u''(x)=pi^2*sin(pi*x);x in (0,1);u(0)=u(1)=0"


def solution(x: float) -> float:
    return math.sin(math.pi * float(x))


def first_derivative(x: float) -> float:
    return math.pi * math.cos(math.pi * float(x))


def second_derivative(x: float) -> float:
    return -(math.pi**2) * math.sin(math.pi * float(x))


def forcing(x: float) -> float:
    return (math.pi**2) * math.sin(math.pi * float(x))
