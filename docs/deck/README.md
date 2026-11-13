# Slide deck

**Final presentation (RQ1, residual Koopman MPC)**
- [`final-presentation.pptx`](final-presentation.pptx): PowerPoint, 20 slides (19 + 1 backup) with speaker notes; plain white academic template
- [`final-presentation.pdf`](final-presentation.pdf): PDF export of the same deck
- [`build_pptx.js`](build_pptx.js): generates the .pptx with [pptxgenjs](https://gitbrent.github.io/PptxGenJS/). Figures are read from `results/figures/`.
- [`speaker-notes.md`](speaker-notes.md): the speaker notes, one section per slide id.

To rebuild (Node.js with pptxgenjs installed in some folder, and LibreOffice for the PDF):

```bash
NODE_PATH=<folder>/node_modules node docs/deck/build_pptx.js
soffice --headless --convert-to pdf --outdir docs/deck docs/deck/final-presentation.pptx
```

**Earlier progress review (October 2026, kept as an archive):** `progress-review-oct.pptx/.pdf`, built by `build_pptx_oct.js` from `speaker-notes-oct.md`.

## Slide list (19 slides plus 1 backup)

The deck covers the residual Koopman work (the research question of the project and the report).

| # | Slide id | Content | Figure / table used |
|---|---|---|---|
| 1 | cover | Title and team | n/a |
| 2 | rotorloss | A quadrotor that loses a rotor; the relaxed hover | n/a |
| 3 | question | Problem and research question | n/a |
| 4 | simulator | Simulator and vehicle parameters | `rotorfail/params.py` |
| 5 | validation | Model against published results and flight data | `results/tables/validation_report.md` |
| 6 | equilibrium | The relaxed-hover equilibrium (E1) | `e1_rho_sweep.png` |
| 7 | linear | Controllability and observability (E2) | `e2_structure.md` |
| 8 | lqr | LQR baseline (E3) | `e3_failed_lqr_nonlinear.png` |
| 9 | predictors | The three predictors | n/a |
| 10 | prediction | Multi-step prediction (E6) | `e6_multistep_error.png` |
| 11 | limits | Data efficiency and generalization (E6) | `e6_data_efficiency.png` |
| 12 | mpc | MPC with the residual (E7) | `e7_altitude.png` |
| 13 | offsetfree | Offset-free MPC and integral action (E8a) | `e8_altitude.png`, `e8_offset_free.md` |
| 14 | fullstate | MPC on the full-state Koopman model (E8b) | `e8_full_koopman.png` |
| 15 | adapt | Online adaptation (E8c) | `e8c_adaptive.png` |
| 16 | transient | Transient training and MPC tuning (E8d, E8e) | `e8d_spinup.png` |
| 17 | ablations | Ablations and the realistic plant (E8f, E8g) | `e8f_ablations.png` |
| 18 | hypotheses | Status of H1 to H4 | n/a |
| 19 | conclusions | Conclusions, limits, next steps | n/a |
| 20 | references | Backup: key references | `docs/report/references.bib` |
