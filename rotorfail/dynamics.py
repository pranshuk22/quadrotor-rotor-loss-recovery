"""Nonlinear 6-DOF quadrotor dynamics with rotor failure, saturation and motor lag.

Full simulation state (17):
    x = [ d (3, inertial position), v (3, inertial velocity),
          quat (4, body->inertial, scalar first), w (3, body rates p,q,r),
          f (4, produced rotor thrusts, first-order lag of the commands) ]

Rotational dynamics are eq. (4) of Mueller & D'Andrea 2014 with I^P w_dot_Pi neglected:
    I^B w_dot = tau_res - w x ( I^T w + Izz_P * w_Sigma * e3 ).
"""
import numpy as np

from .params import G, QuadParams

E3 = np.array([0.0, 0.0, 1.0])
N_STATE = 17
IDX_D = slice(0, 3)
IDX_V = slice(3, 6)
IDX_Q = slice(6, 10)
IDX_W = slice(10, 13)
IDX_F = slice(13, 17)


# ---------------------------------------------------------------- rotations
def quat_to_rot(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def euler_to_quat(phi: float, theta: float, psi: float) -> np.ndarray:
    """ZYX (yaw-pitch-roll) Euler angles to quaternion."""
    cr, sr = np.cos(phi / 2), np.sin(phi / 2)
    cp, sp = np.cos(theta / 2), np.sin(theta / 2)
    cy, sy = np.cos(psi / 2), np.sin(psi / 2)
    return np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ])


def rot_to_euler(R: np.ndarray) -> np.ndarray:
    """Rotation matrix to ZYX Euler angles (phi, theta, psi)."""
    theta = -np.arcsin(np.clip(R[2, 0], -1.0, 1.0))
    phi = np.arctan2(R[2, 1], R[2, 2])
    psi = np.arctan2(R[1, 0], R[0, 0])
    return np.array([phi, theta, psi])


def quat_mult(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ])


def reduced_attitude(x: np.ndarray) -> np.ndarray:
    """n = inertial 'up' direction expressed in body axes (= R^T e3)."""
    return quat_to_rot(x[IDX_Q]).T @ E3


# ---------------------------------------------------------------- dynamics
def saturate(f_cmd: np.ndarray, p: QuadParams, alive: np.ndarray) -> np.ndarray:
    """A running motor produces f in [f_min, f_max]; a command <= 0 stops it (f = 0)."""
    f = np.where(np.asarray(f_cmd) <= 0.0, 0.0, np.clip(f_cmd, p.f_min, p.f_max))
    return np.where(alive, f, 0.0)


def body_rate_derivative(w: np.ndarray, f: np.ndarray, p: QuadParams) -> np.ndarray:
    w_sigma = np.sum(p.prop_speeds(f))
    h = p.I_T @ w + p.Izz_P * w_sigma * E3
    tau = p.body_torque(f * p.thrust_efficiency(w), w[2])
    return np.linalg.solve(p.I_B, tau - np.cross(w, h))


def deriv(x: np.ndarray, f_cmd: np.ndarray, p: QuadParams, alive: np.ndarray,
          motor_lag: bool = True) -> np.ndarray:
    """Time derivative of the full state for a given thrust command."""
    q = x[IDX_Q]
    w = x[IDX_W]
    f_sat = saturate(f_cmd, p, alive)
    if motor_lag:
        f = np.where(alive, x[IDX_F], 0.0)
        f_dot = np.where(alive, (f_sat - f) / p.sigma_mot, 0.0)
    else:
        f = f_sat
        f_dot = np.zeros(4)
    R = quat_to_rot(q)
    acc = R @ E3 * np.sum(f) * p.thrust_efficiency(w) / p.m - G * E3
    q_dot = 0.5 * quat_mult(q, np.concatenate(([0.0], w)))
    w_dot = body_rate_derivative(w, f, p)
    return np.concatenate((x[IDX_V], acc, q_dot, w_dot, f_dot))


def rk4_step(x: np.ndarray, f_cmd: np.ndarray, dt: float, p: QuadParams,
             alive: np.ndarray, motor_lag: bool = True) -> np.ndarray:
    k1 = deriv(x, f_cmd, p, alive, motor_lag)
    k2 = deriv(x + 0.5 * dt * k1, f_cmd, p, alive, motor_lag)
    k3 = deriv(x + 0.5 * dt * k2, f_cmd, p, alive, motor_lag)
    k4 = deriv(x + dt * k3, f_cmd, p, alive, motor_lag)
    x_new = x + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    x_new[IDX_Q] /= np.linalg.norm(x_new[IDX_Q])
    return x_new


def make_state(d=(0, 0, 0), v=(0, 0, 0), euler=(0, 0, 0), w=(0, 0, 0), f=None,
               p: QuadParams | None = None) -> np.ndarray:
    if f is None:
        p = p or QuadParams()
        f = np.full(4, p.weight / 4.0)
    return np.concatenate((d, v, euler_to_quat(*euler), w, f)).astype(float)


def quat_from_n(n: np.ndarray) -> np.ndarray:
    """An attitude quaternion whose body-frame 'up' vector R^T e3 equals n.

    Uses the shortest rotation taking n to e3 (the free spin angle about n is zero).
    """
    n = np.asarray(n, float) / np.linalg.norm(n)
    v = np.cross(n, E3)
    s, c = np.linalg.norm(v), float(n @ E3)
    if s < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0]) if c > 0 else np.array([0.0, 1.0, 0.0, 0.0])
    ax, ang = v / s, np.arctan2(s, c)
    return np.concatenate(([np.cos(ang / 2)], np.sin(ang / 2) * ax))
