"""Saturation-aware invariant ellipsoids via LMIs (Hu & Lin 2001, continuous time).

Closed loop: x' = A x + B sat(F x), F = -K, with symmetric saturation levels ubar
(the deviation of each input from its trim may not exceed ubar_i).

The ellipsoid E = {x : x^T Q^{-1} x <= 1} is contractively invariant if there is an
auxiliary gain H (with Y = H Q) such that
  (i)  for every vertex D (diagonal 0/1, D^- = I - D):
       A Q + Q A^T + B (D F Q + D^- Y) + (D F Q + D^- Y)^T B^T  <=  -eps I
  (ii) E lies inside the linear region of H:  [[ubar_i^2, Y_i], [Y_i^T, Q]] >= 0.
Inside E every trajectory converges to the origin despite the saturation.
"""
import itertools

import cvxpy as cp
import numpy as np


def invariant_ellipsoid(A, B, K, ubar, direction=None, eps=1e-6, decay=0.0, box=None,
                        solver="CLARABEL"):
    """Largest certified ellipsoid.

    direction=None : maximize log det Q (volume).
    direction=d    : maximize beta such that beta * d lies in E (extent along d).
    decay          : required exponential decay rate of V = x^T P x inside the linear
                     region (V' <= -2 decay V); 0 gives plain contractive invariance.
    box            : optional per-state bounds b_i with |x_i| <= b_i on E (Q_ii <= b_i^2),
                     e.g. to keep E inside the physical range of the motor states.
    Returns dict with Q, P, beta (if direction given) and solver status.
    """
    n, m = B.shape
    F = -K
    Q = cp.Variable((n, n), symmetric=True)
    Y = cp.Variable((m, n))
    cons = [Q >> eps * np.eye(n)]
    for bits in itertools.product([0, 1], repeat=m):
        D = np.diag(bits)
        Dm = np.eye(m) - D
        M = D @ F @ Q + Dm @ Y
        L = A @ Q + Q @ A.T + B @ M + (B @ M).T + 2 * decay * Q
        cons.append(0.5 * (L + L.T) << -eps * np.eye(n))
    for i in range(m):
        row = cp.reshape(Y[i, :], (1, n), order="C")
        cons.append(cp.bmat([[np.array([[ubar[i] ** 2]]), row], [row.T, Q]]) >> 0)
    if box is not None:
        for i, b in enumerate(box):
            if np.isfinite(b):
                cons.append(Q[i, i] <= b ** 2)
    if direction is None:
        prob = cp.Problem(cp.Maximize(cp.log_det(Q)), cons)
        _solve(prob, solver)
        beta = None
    else:
        d = np.asarray(direction, float).reshape(n, 1)
        t = cp.Variable()
        cons.append(cp.bmat([[cp.reshape(t, (1, 1), order="C"), d.T], [d, Q]]) >> 0)
        prob = cp.Problem(cp.Minimize(t), cons)
        _solve(prob, solver)
        beta = 1.0 / np.sqrt(t.value) if t.value is not None and t.value > 0 else None
    Qv = None if Q.value is None else 0.5 * (Q.value + Q.value.T)
    return {"status": prob.status, "Q": Qv, "P": None if Qv is None else np.linalg.inv(Qv), "beta": beta}


def _solve(prob, solver):
    """Solve with the preferred solver; fall back to SCS (high accuracy) on failure."""
    try:
        prob.solve(solver=solver)
        if prob.status in ("optimal", "optimal_inaccurate"):
            return
    except cp.error.SolverError:
        pass
    prob.solve(solver="SCS", eps=1e-7, max_iters=200000)


def slice_ellipse(P, i, j, num=200):
    """Boundary of the 2-D slice {x : x^T P x <= 1, x_k = 0 for k not in (i, j)}."""
    S = P[np.ix_([i, j], [i, j])]
    w, V = np.linalg.eigh(S)
    th = np.linspace(0, 2 * np.pi, num)
    circ = np.vstack((np.cos(th) / np.sqrt(w[0]), np.sin(th) / np.sqrt(w[1])))
    return V @ circ


def contains(P, x):
    return float(x @ P @ x) <= 1.0


def semi_axes(Q):
    """Largest |x_i| over the ellipsoid, for each coordinate: sqrt(Q_ii)."""
    return np.sqrt(np.diag(Q))
