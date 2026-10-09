# Search Log

Purpose: record what was searched, so novelty claims can be re-checked and defended. Re-run before submission.

## 2026-10-09 (v4 narrowing session)

| # | Query (web search) | Notable results | Takeaway |
|---|---|---|---|
| 1 | region of attraction quadrotor rotor failure LQR saturation LMI invariant set relaxed hover | Simha 2017; Sun INDI 2020; M&D relaxed hover; PMC 2025 nonlinear rotor-failure control | No LMI/saturation ROA for relaxed-hover LQR found |
| 2 | quadrotor complete rotor failure detection delay tolerance analysis recovery | Multiple-model L1 FDD (IEEE 11235993); Sun upset 2020; learning-based passive FTC (arXiv:2503.02649) | Detector delays 30–130 ms; delay named as a problem; no certified tolerance |
| 3 | Hamilton-Jacobi reachability quadrotor rotor failure recoverable set spin-up transition | General HJ / hybrid reachability for quadrotors (Gillula et al. 2011) | No HJ analysis of rotor-loss recovery found |
| 4 | observability analysis spinning quadrotor rotor failure state estimation sensors IMU yaw | Vision-based flight with rotor failure (arXiv:2102.13406); rotor-failure-aware flight (arXiv:2510.11306) | No systematic observability study; kept as course content only |
| 5 | LPV yaw rate scheduling quadrotor complete rotor loss spinning | **Stephan, Schmitt & Fichter JGCD 2018** (via descriptions) | **LPV-on-r synthesis already exists** → C2 framed as analysis/certification |
| 6 | Lanzon Freddi Longhi flight control subsequent to rotor failure | JGCD 2014: feedback linearization + H∞ loop shaping at a spinning working point | Linear baseline |
| 7 | gain-scheduled rotor failure transition spin-up parameter-dependent Lyapunov | Hybrid quad-plane incremental FTC; dual-system UAV gain-scheduled passive FTC (arXiv:2510.01044) | Nothing certifying the spin-up under saturation |
| 8 | "yaw rate" "scheduling parameter" LPV multicopter actuator loss "initial transient" | Stephan 2018 description confirmed | — |
| 9 | Stephan Schmitt Fichter LPV complete actuator loss | Bibliographic data: JGCD 41(10):2232–2246, doi:10.2514/1.G003441 | Paywalled (AIAA 403); read via the library |
| 10 | rotor failure "fault detection" delay "region of attraction" OR "recoverable set" ... | Al Lawati 2026; Sun upset; HKU AFTC | Al Lawati assumes instantaneous transition (verified in text) |
| 11 | set-theoretic FTC invariant sets admissible detection delay Seron Olaru Stoican | Stoican & Olaru 2013 book; IET CTA 2012 | General method exists → credit it |
| 12 | multirotor rotor failure maximum tolerable FDI delay reachability guarantee | AST 2024 fault-tolerant motion planning (backward reachability); controllability for rotor degradation (arXiv:1403.5986) | Planning after engagement, not delay |
| 13 | FTC "detection delay" maximum allowable, Shin Belcastro / Yang Jiang Staroswiecki | NASA Shin & Belcastro; imperfect-FDI AFTC for UAVs | General delay analysis, not rotor loss |
| 14 | Yang Ozay CDC 2017 FTC detection delay invariant | Not found (PDF link unreachable) | — |
| 15 | "Fault tolerant motion planning for a quadrotor subject to complete rotor failure" | UNIST record; AST Nov 2024 | Not overlapping |

**Primary-source verification done this session:** full-text grep/read of arXiv 2002.09425, 2609.23918, 2109.12886, 2011.07529 and 2002.07837, plus a full read of Todde et al. 2026 (local PDF). A web-tool summary of 2609.23918 claimed it handled detection delay and LPV; **the actual text contradicts that** (it assumes instantaneous transition). Always check primary text.

## Earlier sessions (from v3 notes)

- Mueller & D'Andrea ICRA 2014 / IJRR (read through §5), Simha 2017, heli-quad, Al Lawati 2026, and Sun 2020 were read for v3. Their conclusions are carried into `notes/`.
- Passive FTC for one-to-three rotor failures (arXiv:2211.12972) and LPV/polytopic LMI for partial faults: the failure-severity continuum is not a gap.

## To re-run before submission
- Queries 1, 2, 5, 10 and 12, plus: "dwell time" rotor failure quadrotor; "switching delay" fault-tolerant quadrotor LMI; "maximum allowable detection time" multirotor.
- Google Scholar: forward citations of Stephan 2018 and Sun 2020 (upset recovery).
