"""The frozen manufactured solution of the annular Poisson problem (Geometry Lift 1).

    Omega  = { a^2 < x^2 + y^2 < 1 },  a = 0.35,  s = x^2 + y^2
    h      = (1 - s)(s - a^2)                         -- vanishes on BOTH boundary circles
    g      = 1 + 0.2 sin(pi x) cos(2 pi y) + 0.1 x - 0.1 y      -- positive on the unit disk
    u*     = h g                                      -- therefore u* = 0 on both components
    -Lap u* = f

``g`` is deliberately **not radial**: an implementation that only ever looks at
the radius -- a plausible way to get an annulus wrong -- cannot reproduce this
solution by accident, and the x/y swap symmetry that the square problem relied
on is genuinely absent here (registered NOT_APPLICABLE rather than faked).

The source is written out analytically, not differentiated at run time, so the
PINN residual and the forcing cannot share one wrong helper and certify each
other. With

    h'(s) = 1 + a^2 - 2 s,      Lap h  = 4 (1 + a^2) - 16 s,
    grad h = 2 h'(s) (x, y),    Lap g  = -pi^2 sin(pi x) cos(2 pi y),

the product rule gives

    Lap(h g) = g Lap h + 2 grad h . grad g + h Lap g
             = g (4 (1 + a^2) - 16 s) + 4 (1 + a^2 - 2 s) (x g_x + y g_y) + h Lap g

    f = -Lap u*.

Pure Python, no torch and no numpy: this module is the reference, so it must not
share an execution path with the model under test.
"""

from __future__ import annotations

import math
from typing import Sequence

from pinn.geometry.annulus import INNER_RADIUS, OUTER_RADIUS

A = INNER_RADIUS
R = OUTER_RADIUS

#: The non-radial modulation, frozen with the spec.
G_SIN_AMPLITUDE = 0.2
G_X_SLOPE = 0.1
G_Y_SLOPE = 0.1


def h(x: float, y: float) -> float:
    s = x * x + y * y
    return (1.0 - s) * (s - A * A)


def h_prime(x: float, y: float) -> float:
    """dh/ds."""

    s = x * x + y * y
    return 1.0 + A * A - 2.0 * s


def laplacian_h(x: float, y: float) -> float:
    s = x * x + y * y
    return 4.0 * (1.0 + A * A) - 16.0 * s


def g(x: float, y: float) -> float:
    return (1.0 + G_SIN_AMPLITUDE * math.sin(math.pi * x) * math.cos(2.0 * math.pi * y)
            + G_X_SLOPE * x - G_Y_SLOPE * y)


def g_x(x: float, y: float) -> float:
    return G_SIN_AMPLITUDE * math.pi * math.cos(math.pi * x) * math.cos(2.0 * math.pi * y) + G_X_SLOPE


def g_y(x: float, y: float) -> float:
    return -2.0 * G_SIN_AMPLITUDE * math.pi * math.sin(math.pi * x) * math.sin(2.0 * math.pi * y) - G_Y_SLOPE


def laplacian_g(x: float, y: float) -> float:
    """Lap g = -5 * amplitude * pi^2 sin(pi x) cos(2 pi y).

    d2/dx2 of ``A sin(pi x) cos(2 pi y)`` is ``-A pi^2 (...)`` and d2/dy2 is
    ``-4 A pi^2 (...)``; with the frozen amplitude 0.2 the five cancels it, which
    is why the spec writes Lap g = -pi^2 sin(pi x) cos(2 pi y). The factor is kept
    explicit here so the identity survives a change of amplitude.
    """

    return -5.0 * G_SIN_AMPLITUDE * (math.pi ** 2) * math.sin(math.pi * x) * math.cos(2.0 * math.pi * y)


def solution(x: float, y: float) -> float:
    return h(x, y) * g(x, y)


def gradient(x: float, y: float) -> tuple[float, float]:
    """grad u* = g grad h + h grad g, with grad h = 2 h'(s) (x, y)."""

    hp = 2.0 * h_prime(x, y)
    return (g(x, y) * hp * x + h(x, y) * g_x(x, y),
            g(x, y) * hp * y + h(x, y) * g_y(x, y))


def laplacian(x: float, y: float) -> float:
    s = x * x + y * y
    return (g(x, y) * laplacian_h(x, y)
            + 4.0 * (1.0 + A * A - 2.0 * s) * (x * g_x(x, y) + y * g_y(x, y))
            + h(x, y) * laplacian_g(x, y))


def forcing(x: float, y: float) -> float:
    """f = -Lap u*, written analytically (never differentiated at run time)."""

    return -laplacian(x, y)


def normal_derivative(x: float, y: float, component: str) -> float:
    """du*/dn on a boundary component, from the closed form (h = 0 there).

    On the boundary grad u* = g grad h = 2 g h'(s) (x, y), so

        outer (r = R = 1, n = (x, y) / R):   du/dn = 2 g h'(1) R = 2 g (a^2 - 1)
        inner (r = a,     n = -(x, y) / a):  du/dn = -2 g h'(a^2) a = -2 g (1 - a^2) a
    """

    from pinn.geometry.annulus import outward_normal

    nx, ny = outward_normal((x, y), component)
    ux, uy = gradient(x, y)
    return ux * nx + uy * ny


#: The exact integral of h over the annulus:
#:      int h dA = 2 pi int_a^1 (1 - r^2)(r^2 - a^2) r dr
#:               = pi int_{a^2}^{1} (1 - t)(t - a^2) dt = pi (1 - a^2)^3 / 6.
#: The non-radial part of g integrates to zero by symmetry -- 0.1x and -0.1y are
#: odd under (x, y) -> (-x, -y) while h is radial, and sin(pi x) cos(2 pi y) is
#: odd under x -> -x -- so int u* dA = int h dA. The symmetry argument is checked
#: numerically against the quadrature, never assumed (Geometry Lift 1 section 18).
def exact_integral_of_h(inner: float = A, outer: float = R) -> float:
    return math.pi * (outer * outer - inner * inner) ** 3 / 6.0


def exact_integral_of_solution() -> float:
    return exact_integral_of_h()


def exact_flux_integral() -> float:
    """int_{dOmega} du*/dn ds, computed in closed form from the radial factor.

    On each circle the non-radial part of g integrates to zero (same symmetry as
    above), so with |Gamma| = 2 pi r:

        outer: 2 pi R * 2 h'(R^2) R      = 4 pi R^2 (1 + a^2 - 2 R^2) / 1
        inner: 2 pi a * (-2 h'(a^2) a)   = -4 pi a^2 (1 - a^2)

    This is only used as a cross-check of the numerical flux identity.
    """

    outer_term = 4.0 * math.pi * R * R * (1.0 + A * A - 2.0 * R * R)
    inner_term = -4.0 * math.pi * A * A * (1.0 - A * A)
    return outer_term + inner_term


def rms(values: Sequence[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("no values")
    return math.sqrt(math.fsum(v * v for v in values) / len(values))


# ---------------------------------------------------------------- frozen scales
#
# Constants of the frozen problem, used as normalisers by the acceptance contract.
# Each one is recomputed from the annulus quadrature by a test (three quadrature
# orders agree to ~1e-15), so the literals here are a freeze, not a guess. They are
# annulus values: carrying the square problem's scales over would make a
# dimensionless criterion meaningless.

#: |Omega| = pi (R^2 - a^2)
AREA = 2.756747553525044

#: sqrt( int f^2 dA / |Omega| ) -- the forcing scale the PDE residual is measured against
F_RMS = 6.263142754572558

#: int_Omega u* dA = pi (1 - a^2)^3 / 6
INTEGRAL_U = 0.3537854743144156

#: int_Omega |grad u*|^2 dA, which equals int_Omega f u* dA (Green, u* = 0 on both circles)
DIRICHLET_ENERGY = 1.6399628956666412

#: sqrt( int (u*)^2 dA / |Omega| )
U_RMS = 0.1415921820111233

#: max over both boundary components of |du*/dn|
MAX_ABS_NORMAL_DERIVATIVE = 2.2752649367773703

#: |dOmega| = 2 pi (R + a)
PERIMETER = 8.482300164692441
