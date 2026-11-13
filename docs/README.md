# Documentation

EE650 course project: fault-tolerant control of a quadrotor after complete rotor loss. The submission studies residual Koopman MPC (the proposal as presented). Work on certified fault-detection-delay budgets was explored and is not part of the submission (see the root README).

## Deliverables

| Item | Location |
|---|---|
| **Detailed project report (LaTeX, 54 pages)** | [`report/report.pdf`](report/report.pdf) · source [`report/report.tex`](report/report.tex) · bibliography [`report/references.bib`](report/references.bib) |
| **Slide deck, final presentation (19 slides + 1 backup)** | [`deck/final-presentation.pptx`](deck/final-presentation.pptx) · [`deck/final-presentation.pdf`](deck/final-presentation.pdf) · [`deck/speaker-notes.md`](deck/speaker-notes.md) · build script [`deck/build_pptx.js`](deck/build_pptx.js) (the October progress review is kept as `deck/progress-review-oct.*`) |

## Technical documentation

| # | Document | What it covers |
|---|---|---|
| 1 | [Project overview](01-project-overview.md) | Problem, aims, status, headline results, folder map |
| 2 | [Model and equations](02-model-and-equations.md) | Conventions, equations of motion, relaxed hover, parameters, truth plants, linear models, modelling limits |
| 3 | [Validation](03-validation.md) | All tests, comparisons with three papers, gaps and their explanations, flight-data gap |
| 4 | [Analysis and control](04-analysis-and-control.md) | Controllability/observability tools, LQR and supervisors, success criterion, idle-thrust bound, exploratory LMI certificate |
| 5 | [Koopman models and MPC](05-koopman-and-mpc.md) | Data generation, the three predictors, MPC formulation, results, open items |
| 6 | [Experiments](06-experiments.md) | V0, E1 to E3, E6 to E8g (and the exploratory scripts): set-up, outputs, runtime, key results, comparability notes |
| 7 | [Code reference](07-code-reference.md) | Module-by-module contents, controller interface, conventions |
| 8 | [Reproducibility](08-reproducibility.md) | Environment, commands, seeds, where numbers come from |

## Related folders (outside `docs/`)
- `proposal/`: the full proposal (all content of the presented proposal; the detection-delay additions are marked as explored, not submitted), novelty and claims, work plan
- `progress/`: status (done / not done), task list, presentation plan, review reports
- `literature/`: literature review, search log, per-paper notes, links to the papers
- `history/`: earlier versions of the proposal and the changelog
