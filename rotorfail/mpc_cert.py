"""Certificate for the residual-Koopman MPC loop (task D8).

With a DARE terminal cost (P) and no active input constraint the receding-horizon MPC of `FailureMPC` (horizon N, constant
measured disturbance d over the horizon, terminal cost x'Px without a linear term) has the closed-form first move
    u = -K s + G d,    K = (R + B'PB)^-1 B'PA,   A_cl = A - B K,   Kf = (R + B'PB)^-1 B',
    G = -Kf (P + sum_{i=1}^{N-1} (A_cl')^i P),
where s = (x7, f_est) is the 10-state measured deviation and d the residual (entering the 7 physical rows). The feedforward is
time varying along the horizon (j steps in: G_j = -Kf (P + sum_{i=1}^{N-1-j} (A_cl')^i P)); the whole predicted input sequence is
u_j = M_j s + N_j d with x_{j+1} = A_cl x_j + (B G_j + I) d, so the set of (s, d) for which no input bound is active anywhere
on the horizon is a polytope; `unconstrained_region` returns its robust (all |d| <= d_max) face data. (The infinite-horizon
feedforward -Kf (I - A_cl')^-1 P is the limit N -> infinity; it is NOT what the finite-horizon QP computes.)

`design_ellipsoid` inscribes a contractive ellipsoid {s : s'Q^-1 s <= 1} in the region (SDP, A_cl Q A_cl' <= lam Q) and
`mismatch_margin` returns the largest uniform one-step plant-mismatch bound for which the ellipsoid is robustly invariant under
s+ = A_cl s + B G d_hat + d_true  (|d_hat| <= d_max by the clip, |d_true| <= delta; triangle-inequality bound in the P-norm).
"""
import cvxpy as cp
import numpy as np
from scipy.linalg import solve_discrete_are

from .control import failure_weights
from .koopman import NominalModel


def unconstrained_law(nom: NominalModel, weights=None, horizon=20):
    Q, R = failure_weights(**(weights or {}))
    A, B = nom.Ad, nom.Bd
    P = solve_discrete_are(A, B, Q, R)
    S = R + B.T @ P @ B
    K = np.linalg.solve(S, B.T @ P @ A)
    Acl = A - B @ K
    Kf = np.linalg.solve(S, B.T)
    law = dict(A=A, B=B, Q=Q, R=R, P=P, K=K, Acl=Acl, Kf=Kf, N=horizon)
    law["Gj"] = [_gain_j(law, j, horizon) for j in range(horizon)]
    law["G"] = law["Gj"][0]
    return law


def _gain_j(law, j, N):
    """Feedforward gain G_j of the unconstrained finite-horizon QP, j steps into the horizon (see the module docstring)."""
    Acl, P = law["Acl"], law["P"]
    n = Acl.shape[0]
    acc, Ap = P.copy(), np.eye(n)
    for _ in range(N - 1 - j):
        Ap = Ap @ Acl.T
        acc = acc + Ap @ P
    return -law["Kf"] @ acc


def horizon_gains(law, N):
    """M_j (m x n), N_j (m x n) with u_j = M_j s + N_j d for j = 0..N-1 (unconstrained policy)."""
    assert N == law["N"]
    A, B, K, Acl = law["A"], law["B"], law["K"], law["Acl"]
    n = A.shape[0]
    Ms, Ns = [], []
    X_s = np.eye(n)                       # x_j = X_s s + X_d d
    X_d = np.zeros((n, n))
    for j in range(N):
        G = law["Gj"][j]
        Ms.append(-K @ X_s)
        Ns.append(-K @ X_d + G)
        X_s = Acl @ X_s
        X_d = Acl @ X_d + (B @ G + np.eye(n))
    return Ms, Ns


def unconstrained_region(law, N, lo, hi, d_max):
    """Face data (h, b): the region is {s : h's <= b for all faces} for every |d_i| <= d_max_i (7 physical rows).
    lo, hi: input bounds as deviations from the trim. Returns (H (F x n), b (F,))."""
    Ms, Ns = horizon_gains(law, N)
    dm = np.zeros(law["A"].shape[0])
    dm[:7] = d_max
    H, b = [], []
    for M, Nn in zip(Ms, Ns):
        S = np.abs(Nn) @ dm
        for r in range(M.shape[0]):
            H.append(M[r]), b.append(hi[r] - S[r])
            H.append(-M[r]), b.append(-lo[r] - S[r])
    return np.array(H), np.array(b)


def design_ellipsoid(law, H, b, lam=0.995, scale=None, box=None, slack=1e-3, eps=1e-9, solver="CLARABEL"):
    """Largest-volume ellipsoid {s: s'Q^-1 s <= 1} with h'Qh <= b^2 for every face, |s_i| <= box_i (dict index -> bound) and
    A_cl Q A_cl' <= (lam - slack) Q; the contraction at lam is then re-verified with slack to spare.
    scale: per-state scales (the SDP is solved in scaled coordinates)."""
    n = law["A"].shape[0]
    S = np.ones(n) if scale is None else np.asarray(scale, float)
    Si = np.diag(1.0 / S)
    Acl_s = Si @ law["Acl"] @ np.diag(S)
    Q = cp.Variable((n, n), symmetric=True)
    cons = [Q >> eps * np.eye(n), cp.bmat([[(lam - slack) * Q, Acl_s @ Q], [Q @ Acl_s.T, Q]]) >> 0]
    for i, bi in (box or {}).items():
        cons.append(Q[i, i] <= (bi / S[i]) ** 2)
    for h, bb in zip(H, b):
        hs = h * S
        if bb <= 0:
            return None
        cons.append(hs @ Q @ hs <= bb ** 2)
    prob = cp.Problem(cp.Maximize(cp.log_det(Q)), cons)
    try:
        prob.solve(solver=solver)
    except cp.error.SolverError:
        prob.solve(solver="SCS", eps=1e-8, max_iters=200000)
    if Q.value is None:
        return None
    Qs = 0.5 * (Q.value + Q.value.T)
    return dict(status=prob.status, Qs=Qs, Q=np.diag(S) @ Qs @ np.diag(S), scale=S, solver=solver)


def verify_design(des, law, H, b, lam=0.995):
    """Numerical check, solver independent: worst eigenvalue of A_cl Q A_cl' - lam Q (scaled), face margins b^2 - h'Qh."""
    Qs, S = des["Qs"], des["scale"]
    Si = np.diag(1.0 / S)
    Acl_s = Si @ law["Acl"] @ np.diag(S)
    worst = float(np.max(np.linalg.eigvalsh(Acl_s @ Qs @ Acl_s.T - lam * Qs)))
    Q = des["Q"]
    face = float(np.min(b ** 2 - np.einsum("ij,jk,ik->i", H, Q, H)))
    return dict(worst_contraction=worst, min_face_margin=face, min_eig_Q=float(np.min(np.linalg.eigvalsh(Qs))))


def mismatch_margin(law, Q, d_max, lam=0.995):
    """(delta_star, Delta_dhat, per-state weights): with P = Q^-1, robust invariance of {s'Ps <= 1} holds if
    sqrt(lam) + Delta_dhat + delta * sum_i ||P^(1/2) e_i|| <= 1 (e_i the 7 physical unit vectors)."""
    P = np.linalg.inv(Q)
    L = np.linalg.cholesky(P)            # P = L L', ||P^(1/2) v|| = ||L' v||
    BG = law["B"] @ law["G"]
    dm = np.asarray(d_max, float)
    Dhat = float(sum(dm[i] * np.linalg.norm(L.T @ BG[:, i]) for i in range(7)))
    w = np.array([np.linalg.norm(L.T[:, i]) for i in range(7)])
    margin = 1.0 - np.sqrt(lam) - Dhat
    return (margin / w.sum() if margin > 0 else 0.0), Dhat, w
