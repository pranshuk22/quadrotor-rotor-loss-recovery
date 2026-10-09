"""Controllers: healthy hover LQR, failure-mode (relaxed hover) LQR, and the
detection-delay supervisor that switches between them.
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import solve_continuous_are

from .dynamics import IDX_D, IDX_F, IDX_Q, IDX_V, IDX_W, quat_to_rot, rot_to_euler, E3
from .equilibrium import RelaxedHover
from .models import LinearModel, add_motor_lag, failed_linear, healthy_linear
from .params import QuadParams


def lqr(A, B, Q, R):
    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    return K, P


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


# ---------------------------------------------------------------- healthy
def healthy_weights(alpha: float = 1.0):
    """Bryson-style weights; alpha scales all state weights (aggressiveness)."""
    max_err = np.array([0.5, 0.5, 0.3,      # position (m)
                        1.0, 1.0, 0.5,      # velocity (m/s)
                        0.2, 0.2, 0.5,      # phi, theta, psi (rad)
                        2.0, 2.0, 2.0])     # body rates (rad/s)
    Q = alpha * np.diag(1.0 / max_err ** 2)
    R = np.diag(np.full(4, 1.0 / 0.5 ** 2))  # 0.5 N per rotor
    return Q, R


@dataclass
class HealthyLQR:
    p: QuadParams
    alpha: float = 1.0
    ref: np.ndarray = field(default_factory=lambda: np.zeros(12))

    def __post_init__(self):
        self.model: LinearModel = healthy_linear(self.p)
        Q, R = healthy_weights(self.alpha)
        self.K, self.P = lqr(self.model.A, self.model.B, Q, R)

    def state12(self, x):
        R = quat_to_rot(x[IDX_Q])
        return np.concatenate((x[IDX_D], x[IDX_V], rot_to_euler(R), x[IDX_W]))

    def __call__(self, t, x):
        e = self.state12(x) - self.ref
        e[8] = wrap(e[8])
        return np.clip(self.model.u_trim - self.K @ e, self.p.f_min, self.p.f_max)


# ---------------------------------------------------------------- failed
def failure_weights(w_rate=1.0, w_att=20.0, w_r=0.0, w_z=4.0, w_vz=1.0, w_u=1.0,
                    n_motor=3):
    """Mueller & D'Andrea (2014, Sec. V-D) style weights: 1 on p,q, 20 on n,
    0 on motor states, 1 N^-2 on inputs; plus altitude weights (ours)."""
    q = [w_rate, w_rate, w_r, w_att, w_att, w_z, w_vz] + [0.0] * n_motor
    return np.diag(q), w_u * np.eye(3)


@dataclass
class FailureLQR:
    """LQR on the 7-state reduced-attitude/altitude model + motor lag states.

    Motor states are not measured; they are reconstructed by an internal
    first-order filter of the controller's own (saturated) commands.
    """
    p: QuadParams
    eq: RelaxedHover
    weights: dict = field(default_factory=dict)
    z_ref: float = 0.0
    motor_states: bool = True

    def __post_init__(self):
        base = failed_linear(self.p, self.eq)
        self.base = base
        if self.motor_states:
            self.model = add_motor_lag(base, self.p.sigma_mot)
            Q, R = failure_weights(**self.weights)
        else:
            self.model = base
            Q, R = failure_weights(**self.weights, n_motor=0)
        self.K, self.P = lqr(self.model.A, self.model.B, Q, R)
        self.f_est = self.eq.f[:3].copy()
        self.t_last = None

    def reset(self, f_now):
        self.f_est = np.clip(np.asarray(f_now[:3], float), self.p.f_min, self.p.f_max)
        self.t_last = None

    def state7(self, x):
        n = quat_to_rot(x[IDX_Q]).T @ E3
        w = x[IDX_W]
        return np.array([w[0], w[1], w[2], n[0], n[1], x[2], x[5]])

    def __call__(self, t, x):
        s = self.state7(x)
        e = s - self.base.x_trim
        e[5] -= self.z_ref
        if self.motor_states:
            e = np.concatenate((e, self.f_est - self.eq.f[:3]))
        u3 = np.clip(self.eq.f[:3] - self.K @ e, self.p.f_min, self.p.f_max)
        if self.motor_states:
            dt = 0.0 if self.t_last is None else t - self.t_last
            self.f_est = self.f_est + dt / self.p.sigma_mot * (u3 - self.f_est)
            self.t_last = t
        return np.array([u3[0], u3[1], u3[2], 0.0])


@dataclass
class SpinUpThenLQR:
    """Mueller & D'Andrea (2014, Sec. V-D) flight strategy: after the failure is
    known, fly on the two opposing rotors (1, 3) to build up yaw rate, and enable
    the relaxed-hover LQR once |w| exceeds w_switch (10 rad/s in the paper)."""
    p: QuadParams
    lqr: FailureLQR
    w_switch: float = 10.0
    spinning_up: bool = True

    def reset(self, f_now):
        self.spinning_up = True
        self.lqr.reset(f_now)

    def __call__(self, t, x):
        if self.spinning_up and np.linalg.norm(x[IDX_W]) < self.w_switch:
            f13 = self.p.weight / 2.0
            u = np.array([f13, 0.0, f13, 0.0])  # rotor 2 stopped: two-rotor spin-up
            self.lqr.reset(np.array([f13, self.p.f_min, f13]))
            self.lqr.t_last = t
            return u
        self.spinning_up = False
        return self.lqr(t, x)


# ---------------------------------------------------------------- supervisor
@dataclass
class DelaySupervisor:
    """Rotor 4 fails at t_fail; the failure is detected tau seconds later.

    Before detection the healthy controller keeps running (its rotor-4 command
    is lost); after detection the failure-mode controller takes over.
    """
    healthy: HealthyLQR
    failure: object  # FailureLQR or SpinUpThenLQR (anything with reset() and __call__)
    t_fail: float = 0.0
    tau: float = 0.0
    switched: bool = False

    def alive(self, t):
        return np.array([True, True, True, t < self.t_fail])

    def mode(self, t):
        return "failure" if t >= self.t_fail + self.tau else "healthy"

    def __call__(self, t, x):
        if self.mode(t) == "healthy":
            return self.healthy(t, x)
        if not self.switched:
            self.failure.reset(x[IDX_F])
            self.switched = True
        return self.failure(t, x)
