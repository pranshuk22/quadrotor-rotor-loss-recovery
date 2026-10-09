# Sun, Baert, Strack van Schijndel, de Visser (2020): Upset Recovery Control for Quadrotors Subjected to a Complete Rotor Failure from Large Initial Disturbances

**arXiv:** 2002.09425  **Local PDF:** `../papers/Sun2020_UpsetRecovery_arXiv2002.09425.pdf`  **Read depth:** partial (intro, contributions, AMS sections; full text extracted)

## What it does
- Cascaded controller: position/altitude loop, an attitude controller with an almost-global attraction region, and **QP control allocation** with a constraint on the "undesirable" angular velocity.
- Defines the **Attainable Moment Set (AMS)** under non-negative thrust. Some angular-rate components (ω̃) cannot be suppressed by the attainable moments.
- Validation: Monte Carlo from arbitrary attitude/rates; flight tests with the vehicle tossed by hand.

## Key quotes for v4
- "a post-failure quadrotor may be upside down and fast rotating before the FTC is triggered, because of strong wind disturbances and **delay of the fault detection module**. At this moment, existing FTC methods could fail owing to multiple reasons, such as **violation of linearization assumptions, actuator saturations**, etc."
- On prior work: LQR around the analytical equilibrium [M&D]; "To improve the stability under various yaw rates, the study in [11] employs a linear parameter varying (LPV) controller" (Stephan 2018).

## Use in v4
- **Direct motivation for C1:** names detection delay + saturation as the failure mechanism but does not quantify it.
- Empirical (Monte Carlo), no certificate; cite and differentiate.
