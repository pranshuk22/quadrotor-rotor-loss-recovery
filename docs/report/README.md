# Progress Report 1 (LaTeX)

- `report.pdf`: compiled report (15 pages)
- `report.tex`: source
- `references.bib`: bibliography (30 entries; all papers cited in the proposal and the work so far)
- `figures/`: copies of `results/figures/*.png` used by the report

## Build

```bash
cd docs/report
tectonic -X compile report.tex          # installed at /opt/homebrew/bin/tectonic
# or, with a full TeX Live:  latexmk -pdf report.tex
```

If the experiments are re-run, copy the new figures first: `cp ../../results/figures/*.png figures/`.

## Notes on references
Entries with `note = {... to be verified}` carry details not yet checked against the primary source. These are the two attributions the proposal itself flagged ("Lee et al. 2024") and two papers whose author lists were not available to us. BibTeX warns "empty author" for the two author-less entries; this is expected.
