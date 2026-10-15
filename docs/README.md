# Documentation

EE650 course project: fault-tolerant control of a quadrotor after complete rotor loss. The work combines residual Koopman MPC (the proposal as presented) with certified fault-detection-delay budgets (added after the proposal).

## Deliverables

| Item | Location |
|---|---|
| **Detailed project report (LaTeX, about 53 pages)** | [`report/report.pdf`](report/report.pdf) · source [`report/report.tex`](report/report.tex) · bibliography [`report/references.bib`](report/references.bib) |
| **Slide deck, progress review (15 slides + 1 backup, residual Koopman work)** | [`deck/progress-review.pptx`](deck/progress-review.pptx) · [`deck/progress-review.pdf`](deck/progress-review.pdf) · details in [`deck/`](deck/README.md) |

## Technical documentation

| # | Document | What it covers |
|---|---|---|
| 1 | [Project overview](01-project-overview.md) | Problem, aims, status, headline results, folder map |
| 2 | [Model and equations](02-model-and-equations.md) | Conventions, equations of motion, relaxed hover, parameters, truth plants, linear models, modelling limits |
| 3 | [Validation](03-validation.md) | All tests, comparisons with three papers, gaps and their explanations, flight-data gap |
| 4 | [Analysis, control and certification](04-analysis-and-control.md) | Controllability/observability tools, LQR and supervisors, success criterion, idle-thrust bound, LMI certificate, planned LPV method |
| 5 | [Koopman models and MPC](05-koopman-and-mpc.md) | Data generation, the three predictors, MPC formulation, results, open items |
| 6 | [Experiments](06-experiments.md) | V0, E1–E7: set-up, outputs, runtime, key results, comparability notes |
| 7 | [Code reference](07-code-reference.md) | Module-by-module contents, controller interface, conventions |
| 8 | [Reproducibility](08-reproducibility.md) | Environment, commands, seeds, where numbers come from |

## Related folders (outside `docs/`)
- `proposal/`: the full proposal (all content of the presented proposal plus the detection-delay question), novelty and claims, work plan
- `progress/`: status (done / not done), task list, presentation plan, review reports
- `literature/`: literature review, search log, per-paper notes, links to the papers
- `history/`: earlier versions of the proposal and the changelog
