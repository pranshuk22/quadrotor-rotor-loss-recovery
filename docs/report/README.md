# Detailed project report (LaTeX)

- `report.pdf`: compiled report (54 pages), written for readers without a control background: every term is explained and listed in a glossary
- `report.tex`: main file; the sections are in `sections/` (one file per section, plus appendices for the glossary, symbols and reproducibility)
- `references.bib`: bibliography (52 entries, of which 38 are cited in the report; the others belong to the proposal and the exploratory work)
- `figures/`: copies of `results/figures/*.png` used by the report

## Build

```bash
cd docs/report
tectonic -X compile report.tex          # installed at /opt/homebrew/bin/tectonic
# or, with a full TeX Live:  latexmk -pdf report.tex
```

If the experiments are re-run, copy the new figures first: `cp ../../results/figures/*.png figures/`.

## Notes on references
Bibliographic metadata (authors, title, venue, year, DOI) of every entry has been completed and checked; no entry carries a "to be verified" note and none lacks authors. Statements about papers that were only read in abstract form are marked as such in `sections/03-literature.tex` and in the limitations.
