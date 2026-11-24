# Poisson-1D independent reference component

This document records a mathematical derivation and the implementation contract
for independent diagnostics. It does not freeze a spec, execute formal Gate 2,
or establish a PINN accuracy claim. The active candidate remains a draft.

The candidate problem is dimensionless throughout:

\[
-u''(x)=\pi^2\sin(\pi x),\qquad 0<x<1,\qquad u(0)=u(1)=0.
\]

Differentiate the proposed solution directly:

\[
u_*(x)=\sin(\pi x),\quad
u_*'(x)=\pi\cos(\pi x),\quad
u_*''(x)=-\pi^2\sin(\pi x).
\]

Consequently `-u_*'' - f = 0`; both boundary values are mathematically zero.
If two solutions existed, their difference would satisfy `w''=0`, so
`w(x)=a+bx`. The two homogeneous boundary conditions imply `a=b=0`.
This proves uniqueness for the stated classical boundary value problem.
There is no time variable, dimensional parent problem, reference scaling, or
nondimensionalization operation in this candidate.

The independently integrated quantities are:

| Quantity | Derivation | Value |
| --- | --- | --- |
| Integral of u | `[-cos(pi*x)/pi]_0^1` | `2/pi` |
| Derivative at zero | `pi*cos(0)` | `pi` |
| Integral of u squared | half-angle identity over one half-period | `1/2` |
| Integral of derivative squared | `pi^2 * integral cos^2(pi*x)` | `pi^2/2` |
| Forcing RMS | `sqrt(pi^4 * integral sin^2(pi*x) / domain_length)` | `pi^2/sqrt(2)` |
| Energy identity | integration by parts, zero boundary contribution | `integral (u')^2 = integral f*u = pi^2/2` |

Binary64 `sin(pi)` evaluates to about `1.2246467991473532e-16`. The
candidate's analytic residual and boundary tolerances are respectively `1e-12`
and `1e-14`; a literal-zero assertion at the right endpoint would be invalid.

`poisson_fdm.py` uses a separate arithmetic path: assemble the three-point
finite-difference system `(-u[i-1]+2u[i]-u[i+1])/h^2=f[i]` and solve it with
Thomas elimination, using no PINN imports or analytic inverse. The diagnostic
sequence is exactly `N=32,64,128,256,512,1024,2048` subintervals. Error is the
maximum absolute error at interior nodes, and observed order is
`log2(E(N)/E(2N))`. Errors must decrease over the sequence and the final four
orders must lie in `[1.8,2.2]`. A single grid has no convergence order; the
B11 control records the missing evidence with an empty order list.

The finite-difference values are only baseline-subsystem diagnostics. They
never enter AC-1 through AC-8. A separate unit test approximates the second
derivative from three evaluations of `sin(pi*x)` on 99 interior points with
`h=1e-4`, comparing the forcing to within `1e-6`. That tolerance describes a
finite-difference diagnostic; it does not replace the analytic tolerance or
permit finite-difference derivatives in the AC metrics.

The validation component reads the existing byte-bound GL512 and CGL2000
assets. For AC-2, the candidate Scientific Spec explicitly requires the
maximum of the reference on the discrete CGL2000 grid in the denominator.
Since CGL2000 does not contain `x=0.5`, this value is
`0.9999992382301501`, rather than the continuous supremum `1`. The code follows
the candidate spec formula. Any shorthand in the plan referring to `1`
needs a governance clarification; the component does not amend either file.
