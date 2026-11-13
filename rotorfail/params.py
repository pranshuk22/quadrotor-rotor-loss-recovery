"""Vehicle parameters.

Default values are the Hummingbird-based quadrocopter of Mueller & D'Andrea,
ICRA 2014, Sec. V-A (literature/papers/MuellerDAndrea2014_ICRA_PropellerLoss.pdf).

Rotor layout and sign conventions follow the same paper (Fig. 2, eqs. 8-14):
  rotor 1 at +x, rotor 2 at +y, rotor 3 at -x, rotor 4 at -y (body frame, z up).
  tau_res = ( l (f2 - f4),  l (f3 - f1),  kappa_tau (f1 - f2 + f3 - f4) - gamma r )
  propellers 1 and 3 spin with negative speed, 2 and 4 with positive speed.
"""
from dataclasses import dataclass, field

import numpy as np

G = 9.81  # m/s^2, gravity magnitude; inertial z axis points up


@dataclass(frozen=True)
class QuadParams:
    m: float = 0.50              # kg
    l: float = 0.17              # m, arm length
    Ixx_T: float = 3.2e-3        # kg m^2, total (body + propellers) inertia about x and y
    Izz_T: float = 5.5e-3        # kg m^2, total inertia about z
    Izz_P: float = 1.5e-5        # kg m^2, single propeller inertia about its axis
    Ixx_P: float = 0.0           # kg m^2, neglected (as in the paper)
    kappa_f: float = 6.41e-6     # N s^2 / rad^2, thrust = kappa_f * w^2
    kappa_tau: float = 1.69e-2   # N m / N, reaction torque per unit thrust
    gamma: float = 2.75e-3       # N m s / rad, yaw drag torque coefficient
    f_min: float = 0.2           # N, per-rotor thrust limits (working rotors)
    f_max: float = 3.8           # N
    sigma_mot: float = 0.015     # s, first-order motor time constant
    # Truth-plant effect absent from the nominal model: rotor thrust efficiency drops with
    # body rate, eta = 1 - thrust_loss * |w|^2 (M&D 2014 observed less thrust while spinning).
    thrust_loss: float = 0.0     # s^2 / rad^2
    # +1 / -1: sign of propeller angular velocity for rotors 1..4
    prop_sign: tuple = (-1.0, 1.0, -1.0, 1.0)
    # Optional truth-plant effects of Mueller & D'Andrea (IJRR 2016), off by default (the published ICRA 2014 model):
    # air_relative: thrust from the propeller speed relative to the AIR (Omega + r), f = kappa_f (Omega + r)|Omega + r|;
    # quad_drag: quadratic drag torque -|w| Kd w (diagonal Kd, N m s^2/rad^2) in place of the linear yaw drag gamma r.
    air_relative: bool = False
    quad_drag: tuple | None = None

    @property
    def Ixx_B(self) -> float:
        return self.Ixx_T - 4.0 * self.Ixx_P

    @property
    def Izz_B(self) -> float:
        return self.Izz_T - 4.0 * self.Izz_P

    @property
    def I_B(self) -> np.ndarray:
        return np.diag([self.Ixx_B, self.Ixx_B, self.Izz_B])

    @property
    def I_T(self) -> np.ndarray:
        return np.diag([self.Ixx_T, self.Ixx_T, self.Izz_T])

    @property
    def weight(self) -> float:
        return self.m * G

    def prop_speeds(self, f: np.ndarray) -> np.ndarray:
        """Signed propeller speeds (rad/s) from thrusts (N), f = kappa_f w^2."""
        f = np.maximum(np.asarray(f, dtype=float), 0.0)
        return np.asarray(self.prop_sign) * np.sqrt(f / self.kappa_f)

    def thrust_efficiency(self, w: np.ndarray) -> float:
        return max(0.0, 1.0 - self.thrust_loss * float(np.dot(w, w)))

    def effective_thrust(self, f: np.ndarray, r: float) -> np.ndarray:
        """Thrust produced when the propeller speed is taken relative to the air (IJRR 2016, eq. 4); a stopped rotor
        produces nothing. Identity when `air_relative` is off."""
        if not self.air_relative:
            return f
        f = np.asarray(f, dtype=float)
        s = self.prop_speeds(f) + r
        return np.where(f > 0.0, np.asarray(self.prop_sign) * self.kappa_f * s * np.abs(s), 0.0)

    def body_torque(self, f: np.ndarray, r: float, w: np.ndarray | None = None) -> np.ndarray:
        """Resultant body torque from rotor thrusts and yaw drag, eq. (8),(9),(11). With `quad_drag` set the drag
        torque is -|w| Kd w on all axes (needs w) instead of the linear yaw drag."""
        f1, f2, f3, f4 = f
        if self.quad_drag is not None:
            drag = -np.linalg.norm(w) * np.asarray(self.quad_drag) * w
            return np.array([self.l * (f2 - f4), self.l * (f3 - f1), self.kappa_tau * (f1 - f2 + f3 - f4)]) + drag
        return np.array([
            self.l * (f2 - f4),
            self.l * (f3 - f1),
            self.kappa_tau * (f1 - f2 + f3 - f4) - self.gamma * r,
        ])


DEFAULT = QuadParams()


def truth_family(name: str = "A", base: QuadParams = DEFAULT) -> QuadParams:
    """Truth plants with effects/parameter errors that the nominal model does not have.

    A: training family. B: held-out family (different magnitudes, for generalization tests).
    "A+" / "B+": A / B plus the IJRR effects (air-relative thrust, quadratic drag; task K11).
    """
    from dataclasses import replace
    if name in ("A+", "B+"):
        return replace(truth_family(name[0], base), air_relative=True, quad_drag=(0.7e-4, 0.7e-4, 1.4e-4), gamma=0.0)
    if name == "A":
        return replace(base, thrust_loss=1.5e-4, Ixx_T=base.Ixx_T * 1.08, Izz_T=base.Izz_T * 0.95,
                       sigma_mot=0.020)
    if name == "B":
        return replace(base, thrust_loss=2.5e-4, Ixx_T=base.Ixx_T * 0.94, Izz_T=base.Izz_T * 1.06,
                       sigma_mot=0.012)
    raise ValueError(name)


def random_family(rng, base: QuadParams = DEFAULT) -> QuadParams:
    """Domain-randomized truth plant for training (one draw per episode).

    Ranges cover family A but not family B (B stays an extrapolation test):
    thrust_loss in [0, 2e-4], I_xx x [0.96, 1.10], I_zz x [0.93, 1.03], sigma_mot in [15, 22] ms.
    """
    from dataclasses import replace
    return replace(base, thrust_loss=rng.uniform(0.0, 2.0e-4),
                   Ixx_T=base.Ixx_T * rng.uniform(0.96, 1.10),
                   Izz_T=base.Izz_T * rng.uniform(0.93, 1.03),
                   sigma_mot=rng.uniform(0.015, 0.022))
