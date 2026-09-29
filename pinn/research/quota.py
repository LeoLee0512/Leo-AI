"""Blind claim grids a product install can reserve.

Preparation searches a predetermined list of Gauss-Legendre / Chebyshev-Gauss-Lobatto grids and
permanently reserves the first one disjoint from every historical and product claim set. A
reservation is never returned, even when the preparation or the run later fails: that is what
keeps a blind set from being re-drawn until a run looks good. The list is finite, so the desktop
shows how many grids remain before the operator commits one.

Each problem family has its own list and its own count (owner, 2026-09-29): a 1D grid and a 2D
grid are different objects and never share a sample identity.
"""
from pathlib import Path
import re

CLAIM_GRID_CAPACITY = 32
FAMILIES = ("poisson1d", "poisson2d")
RESERVATION_GLOB = "tasks/*/work/experiments/poisson1d/problems/*-claim-GL*.json"
REGISTERED_GLOB = "experiments/poisson1d/problems/*-claim-GL*.json"
_MEMBER = re.compile(r"-claim-(GL\d+-CGL\d+)\.json$")
_GLOBS = {
    "poisson1d": (RESERVATION_GLOB, REGISTERED_GLOB, _MEMBER),
    "poisson2d": ("tasks/*/work/experiments/poisson2d/problems/*-claim-D2C-GL*.json",
                  "experiments/poisson2d/problems/*-claim-D2C-GL*.json",
                  re.compile(r"-claim-(D2C-GL\d+-CGL\d+)\.json$")),
}


def _primes_from(start, count):
    found, value = [], start
    while len(found) < count:
        if value > 1 and all(value % d for d in range(2, int(value ** 0.5) + 1)):
            found.append(value)
        value += 1
    return found


# 2D: tensor GL of even order n (the calibration pool used 32..38 and D_phys is GL 40, so the list
# starts at 42) with interior tensor CGL of count m, where m - 1 runs through the primes from 61.
# Distinct primes make every two members' CGL nodes disjoint and keep m - 1 coprime to 6 and to the
# calibration members' 49, 53, 55 and 59 -- the construction rule of the 2D preregistration.
# Later members are larger, so their isolation scan (and preparation) takes longer.
_CGL_PRIMES_2D = _primes_from(61, CLAIM_GRID_CAPACITY)


def claim_grid_candidates(family="poisson1d"):
    """The predetermined search order: (member name, GL order, CGL count)."""
    if family == "poisson2d":
        for index, prime in enumerate(_CGL_PRIMES_2D):
            gl, cgl = 42 + 2 * index, prime + 1
            yield f"D2C-GL{gl}-CGL{cgl}", gl, cgl
        return
    if family != "poisson1d":
        raise ValueError("RESEARCH_FAMILY_INVALID")
    for index in range(CLAIM_GRID_CAPACITY):
        gl, cgl = 1024 + 32 * index, 4002 + 2 * index
        yield f"GL{gl}-CGL{cgl}", gl, cgl


def quota(research_root, code_root=None, family="poisson1d"):
    """Candidate grids already taken by this install's tasks or registered in the code root.

    Only members of the family's candidate list count; historical sets on other grids never
    consumed a slot. A grid reserved in both places is counted once.
    """
    candidates = {name for name, _, _ in claim_grid_candidates(family)}
    reservation, registered, member = _GLOBS[family]
    paths = list(Path(research_root).glob(reservation))
    if code_root is not None:
        paths += list(Path(code_root).glob(registered))
    taken = {m.group(1) for m in map(member.search, (p.name for p in paths)) if m and m.group(1) in candidates}
    used = len(taken)
    return {"capacity": CLAIM_GRID_CAPACITY, "used": used, "remaining": CLAIM_GRID_CAPACITY - used, "family": family}
