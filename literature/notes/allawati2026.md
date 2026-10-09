# Al Lawati & Akhtar (2026): Quasi-Static Fault-Tolerant Feedback Control of a Quadrotor under Rotor Failure with Provable Safety Guarantees

**arXiv:** 2609.23918  **Local PDF:** `../papers/AlLawati2026_QuasiStaticFTC_arXiv2609.23918.pdf`  **Read depth:** partial (abstract, intro, assumptions checked in text). Code: gradslab.github.io/quasistatic-ftc

## What it does
- Nonlinear quasi-static feedback that stabilizes the path-following (zero-dynamics) manifold for a single-rotor-failure quadrotor.
- Guarantees: path invariance, plus local exponential convergence under conditions. Simulated in Drake.

## Key assumption (verified in text, lines ~55–58)
- "the design of an FDI scheme is not addressed here; instead, we assume the availability of a **reliable FDI module and an instantaneous transition** of the ..." controller.
- No saturation or motor lag in the theory.

## Use in v4
- Example of guarantee-bearing work that **assumes zero detection delay**, which supports C1.
- Note: a secondary summary of this paper wrongly said it handles detection delay and LPV. **It does not.**
