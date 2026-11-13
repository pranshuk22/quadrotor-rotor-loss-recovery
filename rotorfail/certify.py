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


# ----------------------------------------------------------------------------------------------
# r-robust, saturation-aware certificate for a quasi-LPV closed loop (task D4)
# ----------------------------------------------------------------------------------------------
def _solve_robust(prob, solver):
    """Solve with the requested solver and accept optimal / optimal_inaccurate (the caller re-verifies
    the result numerically); fall back to SCS only if the solver fails or reports no solution."""
    try:
        if solver == "SCS":
            prob.solve(solver="SCS", eps=1e-6, max_iters=100000)
        else:
            prob.solve(solver=solver)
    except cp.error.SolverError:
        pass
    if prob.status not in ("optimal", "optimal_inaccurate") and solver != "SCS":
        try:
            prob.solve(solver="SCS", eps=1e-6, max_iters=100000)
        except cp.error.SolverError:
            pass


def _patterns(m):
    return [np.diag(b) for b in itertools.product([0, 1], repeat=m)]


def _lmi_blocks(A_list, B, K, Sx, Su, Q, Y, decay, gamma, mu):
    """Numerical LMI matrices (scaled coordinates) for every vertex and saturation pattern.

    Q, Y are scaled-coordinate matrices. Returns a list of symmetric matrices that must be negative
    definite; with gamma > 0 each is the Schur-complement block of the S-procedure for the remainder
    bound ||R~|| <= gamma ||e~||: [[L + mu I, gamma Q], [gamma Q, -mu I]] (mu > 0 is a variable of the
    design problem, 1/mu the S-procedure multiplier).
    """
    n, m = B.shape
    Sinv = np.diag(1.0 / Sx)
    Bt = Sinv @ B @ np.diag(Su)
    Ft = -np.diag(1.0 / Su) @ K @ np.diag(Sx)
    out = []
    for A in A_list:
        At = Sinv @ A @ np.diag(Sx)
        for D in _patterns(m):
            Dm = np.eye(m) - D
            M = D @ Ft @ Q + Dm @ Y
            L = At @ Q + Q @ At.T + Bt @ M + (Bt @ M).T + 2 * decay * Q
            L = 0.5 * (L + L.T)
            if gamma > 0:
                blk = np.block([[L + mu * np.eye(n), gamma * Q], [gamma * Q, -mu * np.eye(n)]])
            else:
                blk = L
            out.append(0.5 * (blk + blk.T))
    return out


def robust_invariant_ellipsoid(A_list, B, K, ubar, scale, direction=None, decay=0.1, eps=1e-5,
                               gamma=0.0, disc=None, polygon=64, solver="CLARABEL",
                               extra_box=None):
    """Largest saturation-aware ellipsoid common to all vertex matrices A_i of an LPV closed loop
    e' = A(rho) e + B sat(-K e) (+ remainder with ||R~|| <= gamma ||e~|| in scaled coordinates).

    scale : per-state scales Sx; the ellipsoid is also confined to the box |e_i| <= Sx_i
            (Q~_ii <= 1), which is the region on which gamma is valid.
    ubar  : input saturation levels (symmetric, deviation from the trim); inputs are scaled by ubar.
    direction : maximise beta with beta*direction in E; None maximises log det.
    disc  : optional (indices (i, j), centre c, radius R): the (e_i, e_j) projection of E, shifted by c,
            must lie in the disc of radius R. Enforced through a 'polygon'-sided inscribed polygon
            (support function condition, linear in Q), so the disc condition is sufficient.
    Returns dict(status, Q, P, Y, mu, beta, value, Qs = scaled Q~).
    """
    n, m = B.shape
    Sx = np.asarray(scale, float)
    Su = np.asarray(ubar, float)
    Sinv = np.diag(1.0 / Sx)
    Bt = Sinv @ B @ np.diag(Su)
    Ft = -np.diag(1.0 / Su) @ K @ np.diag(Sx)
    Q = cp.Variable((n, n), symmetric=True)
    Y = cp.Variable((m, n))
    mu = cp.Variable(nonneg=True)
    cons = [Q >> eps * np.eye(n)]
    for k in range(n):
        cons.append(Q[k, k] <= 1.0)
    if extra_box is not None:
        for k, b in extra_box.items():
            cons.append(Q[k, k] <= (b / Sx[k]) ** 2)
    for A in A_list:
        At = Sinv @ A @ np.diag(Sx)
        for D in _patterns(m):
            Dm = np.eye(m) - D
            M = D @ Ft @ Q + Dm @ Y
            L = At @ Q + Q @ At.T + Bt @ M + (Bt @ M).T + 2 * decay * Q
            L = 0.5 * (L + L.T)
            if gamma > 0:
                blk = cp.bmat([[L + mu * np.eye(n), gamma * Q], [gamma * Q, -mu * np.eye(n)]])
                cons.append(0.5 * (blk + blk.T) << -eps * np.eye(2 * n))
            else:
                cons.append(L << -eps * np.eye(n))
    for j in range(m):
        row = cp.reshape(Y[j, :], (1, n), order="C")
        cons.append(cp.bmat([[np.array([[1.0]]), row], [row.T, Q]]) >> 0)
    if disc is not None:
        (i, j), c, R = disc
        b = R * np.cos(np.pi / polygon)
        for k in range(polygon):
            u = np.array([np.cos(2 * np.pi * k / polygon), np.sin(2 * np.pi * k / polygon)])
            v = np.array([Sx[i] * u[0], Sx[j] * u[1]])             # u' Q_nn u = v' Q~_nn v
            rhs = b - float(c @ u)
            assert rhs > 0
            Qs = Q[np.ix_([i, j], [i, j])]
            cons.append(v @ Qs @ v <= rhs ** 2)
    if direction is None:
        prob = cp.Problem(cp.Maximize(cp.log_det(Q)), cons)
    else:
        d = (Sinv @ np.asarray(direction, float)).reshape(n, 1)
        t = cp.Variable()
        cons.append(cp.bmat([[cp.reshape(t, (1, 1), order="C"), d.T], [d, Q]]) >> 0)
        prob = cp.Problem(cp.Minimize(t), cons)
    _solve_robust(prob, solver)
    Qt = None if Q.value is None else 0.5 * (Q.value + Q.value.T)
    beta = None
    if direction is not None and t.value is not None and t.value > 0:
        beta = 1.0 / np.sqrt(t.value)
    Qf = None if Qt is None else np.diag(Sx) @ Qt @ np.diag(Sx)
    return {"status": prob.status, "Qs": Qt, "Q": Qf, "P": None if Qf is None else np.linalg.inv(Qf),
            "Y": None if Y.value is None else Y.value, "mu": None if mu.value is None else float(mu.value),
            "beta": beta, "value": prob.value,
            "solver": solver}


def verify_robust(res, A_func, B, K, ubar, scale, r_grid, nz_grid, decay=0.1, gamma=0.0, A_list=None):
    """Solver-independent check: worst eigenvalue over all inequalities (scaled units).

    Checks (a) every vertex matrix in A_list x every saturation pattern, (b) A_func(r, nz) on the grid
    r_grid x nz_grid x every saturation pattern, (c) the linear-region conditions, (d) Q > 0.
    Returns dict with the worst (largest) eigenvalue of the dynamics blocks, of the negated
    linear-region blocks, and the smallest eigenvalue of Q.
    """
    Qs, Y = res["Qs"], res["Y"]
    Sx = np.asarray(scale, float)
    mats = list(A_list or [])
    for r in r_grid:
        for nz in nz_grid:
            mats.append(A_func(r, nz))
    worst = -np.inf
    for blk in _lmi_blocks(mats, B, K, Sx, np.asarray(ubar, float), Qs, Y, decay, gamma, res.get("mu") or 0.0):
        worst = max(worst, float(np.max(np.linalg.eigvalsh(blk))))
    lin = np.inf
    for j in range(B.shape[1]):
        row = Y[j:j + 1, :]
        M = np.block([[np.array([[1.0]]), row], [row.T, Qs]])
        lin = min(lin, float(np.min(np.linalg.eigvalsh(0.5 * (M + M.T)))))
    return {"worst_dynamics": worst, "worst_linear_region": lin, "min_eig_Q": float(np.min(np.linalg.eigvalsh(Qs)))}


def synthesize_gain(A_list, B, ubar, scale, direction=None, gain_bound=8.0, decay=0.1, eps=1e-5,
                    disc=None, polygon=64, solver="CLARABEL"):
    """Hu-Lin design LMIs (task D5): choose the feedback gain F (u = F e, K = -F) together with the
    ellipsoid, for an LPV model with vertex matrices A_list.

    Variables (scaled coordinates): Q, Yf = F~ Q, Z = H~ Q. For every vertex and saturation pattern D
        A~ Q + Q A~' + B~ (D Yf + (I - D) Z) + (.)' + 2 decay Q  <  -eps I,
    linear region [[1, Z_j], [Z_j', Q]] >= 0, box Q_ii <= 1, optional disc condition, and the gain-size
    bound [[g^2 I, Yf], [Yf', Q]] >= 0, i.e. ||F~ x~|| <= g on the ellipsoid (g = gain_bound, scaled
    input units, fixed a priori). Objective: beta along `direction` (maximise) or log det.
    Returns dict(status, Q, Qs, F (unscaled), beta, value).
    """
    n, m = B.shape
    Sx = np.asarray(scale, float)
    Su = np.asarray(ubar, float)
    Sinv = np.diag(1.0 / Sx)
    Bt = Sinv @ B @ np.diag(Su)
    Q = cp.Variable((n, n), symmetric=True)
    Yf = cp.Variable((m, n))
    Z = cp.Variable((m, n))
    cons = [Q >> eps * np.eye(n)]
    for k in range(n):
        cons.append(Q[k, k] <= 1.0)
    for A in A_list:
        At = Sinv @ A @ np.diag(Sx)
        for D in _patterns(m):
            Dm = np.eye(m) - D
            M = D @ Yf + Dm @ Z
            L = At @ Q + Q @ At.T + Bt @ M + (Bt @ M).T + 2 * decay * Q
            cons.append(0.5 * (L + L.T) << -eps * np.eye(n))
    for j in range(m):
        row = cp.reshape(Z[j, :], (1, n), order="C")
        cons.append(cp.bmat([[np.array([[1.0]]), row], [row.T, Q]]) >> 0)
    cons.append(cp.bmat([[gain_bound ** 2 * np.eye(m), Yf], [Yf.T, Q]]) >> 0)
    if disc is not None:
        (i, j), c, R = disc
        b = R * np.cos(np.pi / polygon)
        for k in range(polygon):
            u = np.array([np.cos(2 * np.pi * k / polygon), np.sin(2 * np.pi * k / polygon)])
            v = np.array([Sx[i] * u[0], Sx[j] * u[1]])
            rhs = b - float(c @ u)
            assert rhs > 0
            cons.append(v @ Q[np.ix_([i, j], [i, j])] @ v <= rhs ** 2)
    if direction is None:
        prob = cp.Problem(cp.Maximize(cp.log_det(Q)), cons)
    else:
        d = (Sinv @ np.asarray(direction, float)).reshape(n, 1)
        t = cp.Variable()
        cons.append(cp.bmat([[cp.reshape(t, (1, 1), order="C"), d.T], [d, Q]]) >> 0)
        prob = cp.Problem(cp.Minimize(t), cons)
    _solve_robust(prob, solver)
    if Q.value is None:
        return {"status": prob.status, "Q": None, "Qs": None, "F": None, "Yf": None, "Z": None, "beta": None,
                "value": None}
    Qs = 0.5 * (Q.value + Q.value.T)
    Ft = Yf.value @ np.linalg.inv(Qs)
    F = np.diag(Su) @ Ft @ np.diag(1.0 / Sx)                     # unscaled: u = F e
    beta = None
    if direction is not None and t.value is not None and t.value > 0:
        beta = 1.0 / np.sqrt(t.value)
    return {"status": prob.status, "Q": np.diag(Sx) @ Qs @ np.diag(Sx), "Qs": Qs, "F": F, "Yf": Yf.value,
            "Z": Z.value, "beta": beta, "value": prob.value}


def verify_design(res, A_list, B, ubar, scale, decay=0.1, gain_bound=None):
    """Solver-independent check of a synthesised (Q, Yf, Z): eigenvalues of every design block."""
    Sx = np.asarray(scale, float)
    Su = np.asarray(ubar, float)
    Sinv = np.diag(1.0 / Sx)
    Bt = Sinv @ B @ np.diag(Su)
    Q, Yf, Z = res["Qs"], res["Yf"], res["Z"]
    m = B.shape[1]
    worst = -np.inf
    for A in A_list:
        At = Sinv @ A @ np.diag(Sx)
        for D in _patterns(m):
            Dm = np.eye(m) - D
            M = D @ Yf + Dm @ Z
            L = At @ Q + Q @ At.T + Bt @ M + (Bt @ M).T + 2 * decay * Q
            worst = max(worst, float(np.max(np.linalg.eigvalsh(0.5 * (L + L.T)))))
    lin = np.inf
    for j in range(m):
        row = Z[j:j + 1, :]
        Mx = np.block([[np.array([[1.0]]), row], [row.T, Q]])
        lin = min(lin, float(np.min(np.linalg.eigvalsh(0.5 * (Mx + Mx.T)))))
    out = {"worst_dynamics": worst, "worst_linear_region": lin, "min_eig_Q": float(np.min(np.linalg.eigvalsh(Q)))}
    if gain_bound is not None:
        Mg = np.block([[gain_bound ** 2 * np.eye(m), Yf], [Yf.T, Q]])
        out["worst_gain_bound"] = float(np.min(np.linalg.eigvalsh(0.5 * (Mg + Mg.T))))
    return out
