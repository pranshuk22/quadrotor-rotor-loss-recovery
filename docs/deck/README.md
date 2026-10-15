# Slide deck: progress review

**Files**
- [`progress-review.pptx`](progress-review.pptx): PowerPoint, 16 slides (15 + 1 backup) with speaker notes, theme and sections
- [`progress-review.pdf`](progress-review.pdf): PDF export of the same deck

**Sources**
- [`build_pptx.js`](build_pptx.js): generates the .pptx with [pptxgenjs](https://gitbrent.github.io/PptxGenJS/). Figures are read from `results/figures/`.
- [`speaker-notes.md`](speaker-notes.md): the speaker notes, one section per slide.

To rebuild (Node.js with pptxgenjs installed in some folder, and LibreOffice for the PDF):

```bash
NODE_PATH=<folder>/node_modules node docs/deck/build_pptx.js
soffice --headless --convert-to pdf --outdir docs/deck docs/deck/progress-review.pptx
```

## Slide list (15 slides plus 1 backup, about 12 minutes)

The deck covers the residual Koopman work (the presented proposal). The detection-delay and certificate work is described in the report only.

| # | Slide id | Content | Figure / table used |
|---|---|---|---|
| 1 | cover | Title and team | n/a |
| 2 | timeline | What happens when a rotor fails; the relaxed hover | n/a |
| 3 | problem | Problem statement, research question, why Koopman, gap | n/a |
| 4 | model | Simulator and vehicle parameters | `rotorfail/params.py` |
| 5 | validation | Model against three published papers and flight data | `results/tables/validation_report.md` |
| 6 | equilibrium | The relaxed-hover equilibrium (E1) | `e1_rho_sweep.png` |
| 7 | structure | Controllability and observability (E2) | `e2_structure.md` |
| 8 | lqr | LQR baseline, settling times and delay margins (E3) | `e3_failed_lqr_nonlinear.png` |
| 9 | part1 | Divider: learning the mismatch | n/a |
| 10 | koopman | Three predictors, same data | n/a |
| 11 | prediction | Multi-step prediction results (E6) | `e6_multistep_error.png` |
| 12 | limits | Data efficiency and generalization (E6) | `e6_data_efficiency.png` |
| 13 | mpc | Residual Koopman MPC in closed loop (E7) | `e7_altitude.png` |
| 14 | plan | Plan up to the final presentation (31 Oct) and report (13 Nov) | `progress/task-list.md` |
| 15 | summary | Three takeaways | n/a |
| 16 | references | Backup: key references | `docs/report/references.bib` |
