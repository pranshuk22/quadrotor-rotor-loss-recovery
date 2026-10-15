# Detailed project report (LaTeX)

- `report.pdf`: compiled report (about 53 pages), written for readers without a control background: every term is explained and listed in a glossary
- `report.tex`: main file; the sections are in `sections/` (one file per section, plus appendices for the glossary, symbols and reproducibility)
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
