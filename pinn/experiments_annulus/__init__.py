"""The annular Poisson experiment (Geometry Lift 1).

A separate package rather than a generalisation of ``pinn/experiments2d``: the
square 2D experiment is CLOSED at C2 and rewriting its modules would move the code
identity its results are bound to. What is genuinely geometry-independent (the
governance layer, the trust vector, the state machine, the claim ledger, the
multi-seed gate, the symptom rules) is imported and reused unchanged; what assumed
a rectangle is rebuilt here against the geometry contract.
"""
