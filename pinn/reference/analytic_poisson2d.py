"""Trusted analytic reference for Poisson-2D v1.0 (manufactured solution).

    -(u_xx + u_yy) = 2 pi^2 sin(pi x) sin(pi y)   on  (0,1)^2
    u = 0                                        on  the four edges
    u*(x, y) = sin(pi x) sin(pi y)

This module is deliberately independent of every PINN model implementation and
of the 1D reference (``analytic_poisson``); it is imported by the trusted
validator, by Gate 1/2/3 and by the plots, never by the training loop's
optimizer.  The exact closed-form constants below are derived in
``scientific_reference/POISSON_2D_DERIVATION.md``.
"""

from __future__ import annotations

import math

SPEC_BINDING = "poisson-2d-dirichlet@1.0"
EQUATION_BINDING = "-(u_xx+u_yy)(x,y)=2*pi^2*sin(pi*x)*sin(pi*y);(x,y) in (0,1)^2;u=0 on the four edges"

PI = math.pi
#: int_0^1 int_0^1 u* dx dy = (2/pi)^2
INTEGRAL_U = 4.0 / (PI * PI)
#: int int f dx dy = 2 pi^2 (2/pi)^2 = 8
INTEGRAL_F = 8.0
#: int int |grad u*|^2 = int int f u* = pi^2 / 2
DIRICHLET_ENERGY = PI * PI / 2.0
#: ||f||_rms on the unit square = sqrt(int int f^2) = 2 pi^2 * 1/2 = pi^2
F_RMS = PI * PI
#: max |u*| = u*(1/2, 1/2)
MAX_ABS_U = 1.0


def solution(x: float, y: float) -> float:
    return math.sin(PI * float(x)) * math.sin(PI * float(y))


def dx(x: float, y: float) -> float:
    return PI * math.cos(PI * float(x)) * math.sin(PI * float(y))


def dy(x: float, y: float) -> float:
    return PI * math.sin(PI * float(x)) * math.cos(PI * float(y))


def dxx(x: float, y: float) -> float:
    return -(PI ** 2) * math.sin(PI * float(x)) * math.sin(PI * float(y))


def dyy(x: float, y: float) -> float:
    return -(PI ** 2) * math.sin(PI * float(x)) * math.sin(PI * float(y))


def laplacian(x: float, y: float) -> float:
    return dxx(x, y) + dyy(x, y)


def forcing(x: float, y: float) -> float:
    """f = -Delta u* = 2 pi^2 sin(pi x) sin(pi y)."""

    return 2.0 * (PI ** 2) * math.sin(PI * float(x)) * math.sin(PI * float(y))


def normal_derivative(x: float, y: float) -> float:
    """Outward normal derivative of u* on the four edges (used by the flux identity)."""

    if x == 0.0:
        return -dx(0.0, y)
    if x == 1.0:
        return dx(1.0, y)
    if y == 0.0:
        return -dy(x, 0.0)
    if y == 1.0:
        return dy(x, 1.0)
    raise ValueError("normal_derivative is defined on the boundary of the unit square only")
