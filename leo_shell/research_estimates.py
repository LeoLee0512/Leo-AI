"""How long a full research run usually takes, by product configuration (display text only).

Deliberately outside the research code identity, like ``evidence_guide.py``: an estimate is a
measured wall time shown to the person, not part of the method, so correcting it after a smoke
run must not void the run it was measured on. The hard limit is the plan's ``budgetSeconds``,
which is inside the identity.
"""

#: Minutes, measured on the reference machine (the 1D number from the 2.2.6 smoke and the owner's
#: run; the 2D number from the 2.2.11 sandbox smoke with ten seeds trained side by side: 16.2 minutes
#: from the run confirmation to COMPLETED, measured while a 1D smoke ran alongside).
ESTIMATE_MINUTES = {"leo-poisson1d-hard-bc-v1": 8, "leo-poisson2d-hard-bc-v1": 17}
