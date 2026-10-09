"""Structural analysis: controllability, observability, PBH tests, Gramians, delay margin."""
import numpy as np
from scipy.linalg import expm


def ctrb(A, B):
    n = A.shape[0]
    blocks = [B]
    for _ in range(n - 1):
        blocks.append(A @ blocks[-1])
    return np.hstack(blocks)


def obsv(A, C):
    return ctrb(A.T, C.T).T


def rank(M, tol=None):
    s = np.linalg.svd(M, compute_uv=False)
    if tol is None:
        tol = max(M.shape) * np.finfo(float).eps * s[0] * 1e3
    return int(np.sum(s > tol))


def scaled_rank(M):
    """Rank of a Krylov matrix after column normalization (blocks differ by large factors)."""
    norms = np.linalg.norm(M, axis=0)
    norms[norms == 0] = 1.0
    return rank(M / norms)


def pbh_controllability(A, B, tol=1e-8):
    """For each eigenvalue: min singular value of [lambda I - A, B] (scaled).

    A (near) zero value marks an uncontrollable mode.
    """
    n = A.shape[0]
    scale = max(np.linalg.norm(A), 1.0)
    rows = []
    for lam in np.linalg.eigvals(A):
        M = np.hstack((lam * np.eye(n) - A, B * scale / max(np.linalg.norm(B), 1e-12)))
        smin = np.linalg.svd(M, compute_uv=False)[-1] / scale
        rows.append((lam, smin, smin > tol))
    return rows


def pbh_observability(A, C, tol=1e-8):
    return pbh_controllability(A.T, C.T, tol)


def finite_gramian(A, B, T):
    """Controllability Gramian W(T) = int_0^T e^{As} B B^T e^{A^T s} ds (Van Loan)."""
    n = A.shape[0]
    M = np.block([[-A, B @ B.T], [np.zeros((n, n)), A.T]])
    E = expm(M * T)
    F22 = E[n:, n:]
    F12 = E[:n, n:]
    return F22.T @ F12


def gramian_summary(A, B, T):
    W = finite_gramian(A, B, T)
    ev = np.sort(np.linalg.eigvalsh(0.5 * (W + W.T)))
    return {"lambda_min": ev[0], "lambda_max": ev[-1], "cond": ev[-1] / max(ev[0], 1e-300)}


def delay_margin(A, B, K, dt=1e-4, max_delay=0.2):
    """Largest pure input delay h (s) for which x' = A x - B K x(t-h) stays stable.

    Checked on an exact ZOH discretization at step dt with an h/dt-step delay line.
    Returns (h_max, spectral radius at h_max).
    """
    from scipy.signal import cont2discrete

    n, m = B.shape
    Ad, Bd, *_ = cont2discrete((A, B, np.eye(n), np.zeros((n, m))), dt)
    lo, hi = 0, int(max_delay / dt)

    def stable(d):
        if d == 0:
            return np.max(np.abs(np.linalg.eigvals(Ad - Bd @ K))) < 1
        N = n + d * m
        M = np.zeros((N, N))
        M[:n, :n] = Ad
        M[:n, n + (d - 1) * m:] = Bd          # oldest buffered input acts now
        M[n:n + m, :n] = -K                    # newest buffer entry
        for k in range(1, d):
            M[n + k * m:n + (k + 1) * m, n + (k - 1) * m:n + k * m] = np.eye(m)
        return np.max(np.abs(np.linalg.eigvals(M))) < 1

    if not stable(0):
        return 0.0
    if stable(hi):
        return float(max_delay)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if stable(mid):
            lo = mid
        else:
            hi = mid
    return lo * dt
