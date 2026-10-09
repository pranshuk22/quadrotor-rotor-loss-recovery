# Project History

The files in this folder are kept unchanged as archives. File paths mentioned inside them refer to the old flat layout (`plan.md`, `research/`, `plan-v2-koopman-backup.md`), which was reorganized on 2026-10-09.

| Version | File | Date | Core idea | Outcome |
|---|---|---|---|---|
| v1 | `v1-proposal-koopman.pdf` (was `project-proposal.pdf`) | before 2026-10-09 | Physics-informed residual Koopman (EDMDc) MPC on the Mueller–D'Andrea spin model | Revised after instructor feedback that Koopman control for quadrotors/faults already exists |
| v2 | `v2-plan-koopman.md` (was `plan-v2-koopman-backup.md`) | 2026-10-09 | Same, with headline "residual enlarges the region where a linear predictor is valid" | Dropped as the core: mainly an ML contribution, weak EE650 fit |
| v3 | `v3-plan-certified-recoverability.md` (was `plan.md`) | 2026-10-09 | Certified recoverable set (LMI) for relaxed-hover LQR + delay map + observability | Narrowed: a local certificate at r_eq cannot contain hover-onset states; four loosely connected claims |
| v4 | `v4-proposal-delay-budget.md`, `v4-novelty-and-claims.md`, `v4-work-plan.md` | 2026-10-09 | Certified fault-detection-delay budget τ\*, with a capture set robust over the spin-up yaw rate | Merged into v5 as RQ2 |
| **v5** | `../proposal/` | 2026-10-10 | **Merged:** the presented proposal PDF in full (RQ1, residual Koopman MPC) + the delay-budget certification (RQ2), linked by evaluating every capture controller by τ\* | **Current** |

## Known issues in the v1 PDF (fix if it is ever resubmitted)
- "Lee et al. 2024, Koopman FT-MPC" looks misattributed. The IET CTA paper is by Bakhtiaridoust et al.
- Sections 6–7 are missing (it jumps from §5 to §8).
- "Linear and time-invariant" holds only in Mueller & D'Andrea's reduced-attitude body-fixed coordinates.
- Todde et al. 2026 exists (ICUAS 2026, read in full; see `../literature/notes/todde2026.md`).
