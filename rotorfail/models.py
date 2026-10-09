"""Linear state-space models (numerical Jacobians of exact nonlinear models).

Healthy hover model (12 states, 4 inputs = rotor thrusts):
    x_h = [x, y, z, vx, vy, vz, phi, theta, psi, p, q, r]

Failed-vehicle reduced-attitude model (rotor 4 lost; 7 states, 3 inputs f1..f3):
    s = [p, q, r, n_x, n_y, z, vz]
with n = R^T e3 the inertial up direction in body axes, n_z = sqrt(1 - n_x^2 - n_y^2),
    n_dot = -w x n,   z_ddot = f_Sigma * n_z / m - g.
These equations are autonomous in body coordinates, so the linearization about
the relaxed hover is LTI (no Floquet analysis needed). Horizontal position needs
the yaw angle and is handled by a separate outer loop (later work).

Both models can be extended with first-order motor states (thrust lag).
"""
from dataclasses import dataclass

import numpy as np

from .dynamics import body_rate_derivative
from .equilibrium import RelaxedHover, healthy_hover_thrust
from .params import G, QuadParams

HEALTHY_STATES = ["x", "y", "z", "vx", "vy", "vz", "phi", "theta", "psi", "p", "q", "r"]
FAILED_STATES = ["p", "q", "r", "n_x", "n_y", "z", "v_z"]


@dataclass
class LinearModel:
    A: np.ndarray
    B: np.ndarray
    x_trim: np.ndarray
    u_trim: np.ndarray
    states: list
    inputs: list


def jacobians(fun, x0, u0, eps=1e-6):
    """Central-difference Jacobians of x_dot = fun(x, u)."""
    n, m = len(x0), len(u0)
    A = np.zeros((n, n))
    B = np.zeros((n, m))
    for i in range(n):
        dx = np.zeros(n)
        dx[i] = eps
        A[:, i] = (fun(x0 + dx, u0) - fun(x0 - dx, u0)) / (2 * eps)
    for j in range(m):
        du = np.zeros(m)
        du[j] = eps
        B[:, j] = (fun(x0, u0 + du) - fun(x0, u0 - du)) / (2 * eps)
    return A, B


# ---------------------------------------------------------------- healthy
def healthy_f(x, u, p: QuadParams):
    """12-state Euler-angle (ZYX) model, used only for linearization/design."""
    phi, th, psi = x[6:9]
    w = x[9:12]
    cph, sph, cth, sth = np.cos(phi), np.sin(phi), np.cos(th), np.sin(th)
    cps, sps = np.cos(psi), np.sin(psi)
    R = np.array([
        [cth * cps, sph * sth * cps - cph * sps, cph * sth * cps + sph * sps],
        [cth * sps, sph * sth * sps + cph * cps, cph * sth * sps - sph * cps],
        [-sth, sph * cth, cph * cth],
    ])
    acc = R[:, 2] * np.sum(u) / p.m - np.array([0, 0, G])
    W = np.array([
        [1, sph * np.tan(th), cph * np.tan(th)],
        [0, cph, -sph],
        [0, sph / cth, cph / cth],
    ])
    eul_dot = W @ w
    w_dot = body_rate_derivative(w, u, p)
    return np.concatenate((x[3:6], acc, eul_dot, w_dot))


def healthy_linear(p: QuadParams) -> LinearModel:
    x0 = np.zeros(12)
    u0 = healthy_hover_thrust(p)
    A, B = jacobians(lambda x, u: healthy_f(x, u, p), x0, u0)
    return LinearModel(A, B, x0, u0, HEALTHY_STATES, ["f1", "f2", "f3", "f4"])


# ---------------------------------------------------------------- failed
def failed_f(s, u3, p: QuadParams):
    """7-state reduced-attitude + altitude model, rotor 4 failed, inputs f1..f3."""
    w = s[0:3]
    nx, ny = s[3], s[4]
    nz = np.sqrt(max(1.0 - nx * nx - ny * ny, 1e-12))
    n = np.array([nx, ny, nz])
    f = np.array([u3[0], u3[1], u3[2], 0.0])
    w_dot = body_rate_derivative(w, f, p)
    n_dot = -np.cross(w, n)
    vz_dot = np.sum(f) * nz / p.m - G
    return np.array([w_dot[0], w_dot[1], w_dot[2], n_dot[0], n_dot[1], s[6], vz_dot])


def failed_linear(p: QuadParams, eq: RelaxedHover) -> LinearModel:
    s0 = np.array([eq.w[0], eq.w[1], eq.w[2], eq.n[0], eq.n[1], 0.0, 0.0])
    u0 = eq.f[:3].copy()
    A, B = jacobians(lambda s, u: failed_f(s, u, p), s0, u0)
    return LinearModel(A, B, s0, u0, FAILED_STATES, ["f1", "f2", "f3"])


# ---------------------------------------------------------------- helpers
def add_motor_lag(model: LinearModel, sigma: float) -> LinearModel:
    """Augment with produced-thrust states: f_dot = (f_cmd - f) / sigma."""
    n, m = model.B.shape
    A = np.block([[model.A, model.B], [np.zeros((m, n)), -np.eye(m) / sigma]])
    B = np.vstack((np.zeros((n, m)), np.eye(m) / sigma))
    x_trim = np.concatenate((model.x_trim, model.u_trim))
    states = model.states + [f"{u}_act" for u in model.inputs]
    return LinearModel(A, B, x_trim, model.u_trim.copy(), states, model.inputs)


def select_states(model: LinearModel, keep: list) -> LinearModel:
    idx = [model.states.index(k) for k in keep]
    return LinearModel(model.A[np.ix_(idx, idx)], model.B[idx, :], model.x_trim[idx],
                       model.u_trim, [model.states[i] for i in idx], model.inputs)
