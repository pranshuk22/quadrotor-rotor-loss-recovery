# E8e: MPC horizon and tuning study for capture

Capture after a detection delay (E7 Part 2 protocol, exact hover start, spin-up 2.95 N). Cells: SAFE count over the six delays tau = 0, 10, ..., 60 ms (the first failing tau in brackets, '-' if none), median altitude loss over the delays (m), median CVXPY wall time per step (ms). Settings fixed in the docstring of `experiments/e8e_mpc_tuning.py`. Horizon 80 exceeds the 5 ms period by far and is an analysis result, not a real-time controller.

## Plant: nominal

| Controller | weights | H = 10 | H = 20 | H = 40 | H = 80 |
|---|---|---|---|---|---|
| MPC analytical | published | 2/6 (20 ms); 3.48 m; 3.5 ms | 2/6 (20 ms); 5.25 m; 9.6 ms | 2/6 (20 ms); 6.92 m; 47.1 ms | 2/6 (20 ms); 5.86 m; 91.9 ms |
| MPC analytical | heavy attitude | 3/6 (30 ms); 1.77 m; 3.4 ms | 3/6 (30 ms); 2.42 m; 11.2 ms | 3/6 (30 ms); 2.88 m; 47.1 ms | 3/6 (30 ms); 2.70 m; 89.1 ms |
| MPC residual | published | 2/6 (20 ms); 3.93 m; 3.4 ms | 2/6 (20 ms); 6.23 m; 7.4 ms | 2/6 (20 ms); 18.79 m; 48.3 ms | 2/6 (20 ms); 9.12 m; 96.4 ms |
| MPC residual | heavy attitude | 3/6 (30 ms); 1.85 m; 3.4 ms | 3/6 (30 ms); 2.24 m; 8.4 ms | 3/6 (30 ms); 2.53 m; 46.4 ms | 3/6 (30 ms); 2.31 m; 83.9 ms |
| Offset-free | published | 0/6 (0 ms); 96.22 m; 3.2 ms | 0/6 (0 ms); 149.31 m; 6.6 ms | 0/6 (0 ms); 220.71 m; 46.1 ms | 0/6 (0 ms); 282.56 m; 89.4 ms |
| Offset-free | heavy attitude | 1/6 (10 ms); 6.67 m; 3.4 ms | 1/6 (10 ms); 10.69 m; 10.5 ms | 1/6 (10 ms); 16.03 m; 50.0 ms | 1/6 (10 ms); 62.18 m; 122.5 ms |

## Plant: A (full)

| Controller | weights | H = 10 | H = 20 | H = 40 | H = 80 |
|---|---|---|---|---|---|
| MPC analytical | published | 2/6 (20 ms); 8.86 m; 3.4 ms | 1/6 (10 ms); 13.86 m; 6.8 ms | 1/6 (10 ms); 25.61 m; 50.4 ms | 1/6 (10 ms); 32.97 m; 84.9 ms |
| MPC analytical | heavy attitude | 2/6 (20 ms); 3.23 m; 3.2 ms | 2/6 (20 ms); 4.28 m; 8.2 ms | 2/6 (20 ms); 5.93 m; 47.3 ms | 2/6 (20 ms); 5.59 m; 96.9 ms |
| MPC residual | published | 1/6 (10 ms); 10.17 m; 3.3 ms | 1/6 (10 ms); 13.73 m; 6.2 ms | 1/6 (10 ms); 173.07 m; 48.0 ms | 1/6 (10 ms); 92.51 m; 86.9 ms |
| MPC residual | heavy attitude | 2/6 (20 ms); 3.39 m; 3.2 ms | 2/6 (20 ms); 3.70 m; 6.9 ms | 2/6 (20 ms); 4.58 m; 44.6 ms | 2/6 (20 ms); 4.27 m; 90.0 ms |
| Offset-free | published | 0/6 (0 ms); 518.22 m; 3.1 ms | 0/6 (0 ms); 445.14 m; 6.4 ms | 0/6 (0 ms); 596.33 m; 44.0 ms | 0/6 (0 ms); 726.40 m; 77.4 ms |
| Offset-free | heavy attitude | 0/6 (0 ms); 23.21 m; 3.3 ms | 0/6 (0 ms); 103.21 m; 8.9 ms | 0/6 (0 ms); 213.09 m; 49.7 ms | 0/6 (0 ms); 309.86 m; 114.6 ms |

## Long-horizon check: DARE terminal cost versus plain finite horizon (first command, 20 hand-over-like states)

| Horizon | max abs difference of the first command (N) | median (N) |
|---|---|---|
| 20 | 0.000 | 0.000 |
| 40 | 0.000 | 0.000 |
| 80 | 0.000 | 0.000 |
