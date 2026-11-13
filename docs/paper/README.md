# Short paper (summary)

`paper.pdf` is a 3-page summary of the work in IEEE two-column format. It is a summary, not a full paper: the complete method, all experiments, the limitations and the reproduction instructions are in the report (`../report/report.pdf`). Every number in it comes from a file under `results/` and is checked by `experiments/audit_numbers.py`.

- `paper.tex`: source
- `figures/`: copies of five figures from `results/figures/`

## Build

```bash
cd docs/paper
tectonic -X compile paper.tex
```
