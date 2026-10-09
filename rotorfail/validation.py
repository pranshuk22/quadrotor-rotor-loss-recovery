"""Independent implementation of the general multicopter model of Mueller & D'Andrea,
IJRR 2016 ("Relaxed hover solutions for multicopters"), Sec. 2, eqs. (1)-(8).

Written separately from `dynamics.py` (different variables: propeller speeds instead of
thrusts) so the two can be cross-checked:
  * with the IJRR effects switched on (thrust from propeller speed relative to the AIR,
    quadratic drag torque), it reproduces the published IJRR hover solutions (Sec. 5.2);
  * with them switched off (thrust from speed relative to the body, linear yaw drag),
    it must coincide with `dynamics.body_rate_derivative` (the ICRA 2014 model).
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import fsolve

from .params import G

E3 = np.array([0.0, 0.0, 1.0])
# rotor positions (unit arm): 1 front (+x), 2 (+y), 3 (-x), 4 right (-y)
ARM_DIRS = np.array([[1.0, 0, 0], [0, 1.0, 0], [-1.0, 0, 0], [0, -1.0, 0]])
# propeller handedness: 1, 3 spin with negative speed in normal hover
HAND = np.array([-1.0, 1.0, -1.0, 1.0])


@dataclass(frozen=True)
class GeneralMulticopter:
    m: float = 0.50
    l: float = 0.17
    I_B: tuple = (2.7e-3, 2.7e-3, 5.2e-3)      # body inertia WITHOUT propellers (IJRR eq. 28)
    I_Pzz: float = 1.5e-5                       # propeller inertia about its axis (eq. 29)
    kf: float = 6.41e-6                         # |kappa_f|, N s^2/rad^2
    ktau: float = 1.1e-7                        # kappa_tau, N m s^2/rad^2 (eq. 5)
    Kd: tuple = (0.7e-4, 0.7e-4, 1.4e-4)        # quadratic drag, N m s^2/rad^2 (eq. 30)
    air_relative: bool = True                   # thrust from (Omega + r) instead of Omega
    drag: str = "quadratic"                     # "quadratic" (eq. 8) or "linear_yaw"
    gamma: float = 0.0                          # linear yaw drag (only for drag="linear_yaw")
    prop_inertia_accel: bool = True             # keep the I_P w_dot term of eq. (3) (ICRA neglects it)

    def thrusts(self, Omega, w):
        s = Omega + (w[2] if self.air_relative else 0.0)
        return HAND * self.kf * s * np.abs(s)            # eq. (4), sign of kappa_f = handedness

    def reaction_torques(self, Omega, w):
        s = Omega + (w[2] if self.air_relative else 0.0)
        return -self.ktau * s * np.abs(s)                # eq. (5)

    def drag_torque(self, w):
        if self.drag == "quadratic":
            return -np.linalg.norm(w) * np.asarray(self.Kd) * w   # eq. (8), diagonal K_d
        return np.array([0.0, 0.0, -self.gamma * w[2]])

    def angular_acceleration(self, w, Omega):
        """Solve eq. (3) for w_dot with constant propeller speeds (Omega_dot = 0)."""
        IB = np.diag(self.I_B)
        IP = np.diag([0.0, 0.0, self.I_Pzz])
        f = self.thrusts(Omega, w)
        tau = sum(np.cross(self.l * ARM_DIRS[i], E3) * f[i] for i in range(4))
        tau = tau + E3 * np.sum(self.reaction_torques(Omega, w)) + self.drag_torque(w)
        h = IB @ w + sum(IP @ (w + Om * E3) for Om in Omega)
        # I_B w_dot + sum_i I_P w_dot = tau - w x h  (I_P w_dot kept here: exact eq. 3)
        lhs = IB + 4 * IP if self.prop_inertia_accel else IB
        return np.linalg.solve(lhs, tau - np.cross(w, h))

    def hover_rates(self, Omega, guess=(0.0, 0.0, 20.0)):
        """Constant body rates for constant propeller speeds (eq. 3 with w_dot = 0)."""
        # w = 0 is the kink of the quadratic drag |w| w; test it directly before iterating
        if np.linalg.norm(self.angular_acceleration(np.zeros(3), Omega)) < 1e-9:
            return np.zeros(3)
        sol, info, ier, msg = fsolve(lambda w: self.angular_acceleration(w, Omega), np.asarray(guess, float),
                                     full_output=True, xtol=1e-12)
        if ier != 1:
            raise RuntimeError(msg)
        return sol

    def vertical_force_ratio(self, Omega, w):
        """f_Sigma * n_z / (m g), with n = w / |w| (or z_B when w = 0); 1 at a hover solution."""
        n = E3 if np.linalg.norm(w) < 1e-9 else w / np.linalg.norm(w) * np.sign(w[2])
        return float(np.sum(self.thrusts(Omega, w)) * n[2] / (self.m * G))


def ijrr_speeds(abs_speeds):
    """IJRR reports Omega = (-Omega_P1, Omega_P2, -Omega_P3, Omega_P4); return signed speeds."""
    return HAND * np.asarray(abs_speeds, float)


# Published hover solutions, IJRR 2016 Sec. 5.2, eqs. (31)-(50)
IJRR_CASES = {
    "no failure": dict(Omega=(438, 438, 438, 438), w=(0.0, 0.0, 0.0)),
    "rotor 4 failed": dict(Omega=(585, 362, 585, 0), w=(0.2, 4.3, 19.5)),
    "rotors 2, 4 failed (opposing)": dict(Omega=(643, 0, 643, 0), w=(0.0, 0.0, 24.5)),
    "rotors 3, 4 failed (adjacent)": dict(Omega=(1067, 218, 0, 0), w=(26.0, 0.0, 23.3)),
    "rotors 2, 3, 4 failed": dict(Omega=(1103, 0, 0, 0), w=(28.0, -1.6, 24.5)),
}
