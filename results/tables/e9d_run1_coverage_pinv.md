> Run 1 of `experiments/e9d_certified_delay.py` (commit before the coverage fix). Kept for the record: the coverage statistics of this run are invalid. The hand-over map has exactly zero sensitivity to the horizontal velocity and the yaw angle of the pre-failure state (the capture coordinates do not depend on them), and the pseudo-inverse used to measure the normalised excess amplified numerical noise in those directions (excess factors up to 4.6e8). The containment results below (centre scaling, beta, tau*) do not use the pseudo-inverse and stand; the coverage section was recomputed in the next run with a relative rank tolerance.

# E9d: reachable hand-over sets, containment and the certified delay budget

X0 = 99 % ellipsoid of the E4 pre-failure distribution, scaled by gamma; nominal plant. Choices fixed in the docstring of `experiments/e9d_certified_delay.py`. 'rigorous' certificates (remainder-inclusive) are certified; 'LPV' certificates are certified for the quasi-LPV model only (see E9b and E9c). beta >= 1 means the whole hand-over set is inside; 'out (alpha_c)' means the centre of the hand-over set is outside C and alpha_c is the scaling of the centre onto the boundary.

## Undetected phase: affine LTI ellipsoid (proposal method) against 1000 nonlinear samples (gamma = 1)

| tau (ms) | fraction of samples inside the LTI ellipsoid | worst normalised excess | worst orthogonal residual |
|---|---|---|---|
| 10 | 0.988 | 1.004 | 1.27e-01 |
| 30 | 0.917 | 1.045 | 1.60e-01 |
| 60 | 0.603 | 1.360 | 2.03e-01 |

Saturation classification of rotors 1 to 3 over the propagated set (support function; 'clear' = all rotors unsaturated at all controller samples):

| tau (ms) | gamma 0.0 | gamma 0.1 | gamma 0.25 | gamma 0.5 | gamma 1.0 |
|---|---|---|---|---|---|
| 0 | clear | clear | clear | clear | ambiguous |
| 5 | clear | clear | clear | clear | ambiguous |
| 10 | clear | clear | clear | clear | ambiguous |
| 15 | clear | clear | clear | clear | ambiguous |
| 20 | clear | clear | clear | ambiguous | ambiguous |
| 25 | clear | clear | clear | ambiguous | ambiguous |
| 30 | clear | clear | clear | ambiguous | ambiguous |
| 35 | clear | clear | clear | ambiguous | ambiguous |
| 40 | clear | clear | clear | ambiguous | ambiguous |
| 45 | clear | clear | clear | ambiguous | ambiguous |
| 50 | clear | clear | clear | ambiguous | ambiguous |
| 55 | clear | clear | clear | ambiguous | ambiguous |
| 60 | clear | clear | ambiguous | ambiguous | ambiguous |
| 80 | saturated | ambiguous | ambiguous | ambiguous | ambiguous |
| 100 | saturated | ambiguous | ambiguous | ambiguous | ambiguous |
| 130 | saturated | ambiguous | ambiguous | ambiguous | ambiguous |

## Coverage of the hand-over sets by 1000 or 100 nonlinear samples (gamma = 1, f_spin = 2.95 N)

| w_sw | tau (ms) | samples | handed over | inside the linearised set | worst excess | worst orth. residual | hand-over sample window | jitter (max abs, first sample vs interpolated) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 0 | 1000 | 1000 | 0.140 | 13.344 | 1.38e-01 | 301 to 424 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 6 | 5 | 100 | 100 | 0.000 | 2351210.910 | 1.12e-06 | 310 to 407 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 6 | 10 | 100 | 100 | 0.000 | 293429.509 | 1.21e-07 | 307 to 405 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 6 | 15 | 100 | 100 | 0.000 | 120406.169 | 1.49e-07 | 301 to 408 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 6 | 20 | 1000 | 1000 | 0.000 | 187939.253 | 6.38e-07 | 283 to 427 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 25 | 100 | 100 | 0.000 | 77239.758 | 3.54e-07 | 277 to 412 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 30 | 100 | 100 | 0.000 | 298118.651 | 4.39e-06 | 263 to 414 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 35 | 100 | 100 | 0.000 | 311227.921 | 1.07e-05 | 247 to 416 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 40 | 100 | 100 | 0.000 | 190616.520 | 1.39e-05 | 231 to 418 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 6 | 45 | 100 | 100 | 0.000 | 348515.269 | 4.93e-05 | 213 to 420 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 50 | 100 | 100 | 0.000 | 131363.675 | 4.47e-05 | 195 to 422 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 6 | 55 | 100 | 100 | 0.000 | 525753.195 | 2.24e-04 | 174 to 424 | 0.019 | linearised set misses samples (sampling-based after inflation) |
| 6 | 60 | 1000 | 1000 | 0.000 | 450779422.214 | 2.98e-01 | 79 to 443 | 0.029 | linearised set misses samples (sampling-based after inflation) |
| 6 | 80 | 100 | 100 | 0.000 | 284677924.184 | 4.22e-01 | 93 to 434 | 0.028 | linearised set misses samples (sampling-based after inflation) |
| 6 | 100 | 100 | 100 | 0.000 | 427035741.595 | 4.26e-01 | 100 to 443 | 0.059 | linearised set misses samples (sampling-based after inflation) |
| 6 | 130 | 100 | 100 | 0.000 | 457743623.537 | 6.78e-02 | 130 to 454 | 0.027 | linearised set misses samples (sampling-based after inflation) |
| 8 | 0 | 100 | 100 | 0.050 | 36.190 | 8.24e-02 | 452 to 544 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 5 | 100 | 100 | 0.000 | 1884395.063 | 7.87e-11 | 451 to 544 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 10 | 100 | 100 | 0.000 | 99407.680 | 6.12e-11 | 449 to 542 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 15 | 100 | 100 | 0.000 | 221285.612 | 6.72e-09 | 445 to 544 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 20 | 100 | 100 | 0.000 | 118694.325 | 1.01e-10 | 438 to 547 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 25 | 100 | 100 | 0.000 | 96252.588 | 4.30e-11 | 429 to 549 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 30 | 100 | 100 | 0.000 | 95597.989 | 3.90e-11 | 420 to 551 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 35 | 100 | 100 | 0.000 | 861866.245 | 1.42e-10 | 411 to 554 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 40 | 100 | 100 | 0.000 | 66396.053 | 2.65e-09 | 402 to 556 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 45 | 100 | 100 | 0.000 | 606896.050 | 2.28e-08 | 392 to 558 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 50 | 100 | 100 | 0.000 | 246995.878 | 6.32e-08 | 383 to 560 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 8 | 55 | 100 | 100 | 0.000 | 133783.889 | 6.38e-09 | 376 to 563 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 60 | 100 | 100 | 0.000 | 1100429.197 | 7.52e-08 | 368 to 565 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 80 | 100 | 100 | 0.000 | 611111.303 | 3.44e-08 | 345 to 575 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 100 | 100 | 100 | 0.000 | 2225099.097 | 1.59e-07 | 338 to 585 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 8 | 130 | 100 | 100 | 0.000 | 6301592.437 | 1.17e-06 | 325 to 598 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 10 | 0 | 1000 | 1000 | 0.016 | 113.086 | 8.36e-02 | 584 to 705 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 5 | 100 | 100 | 0.000 | 165844.913 | 6.68e-11 | 599 to 690 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 10 | 100 | 100 | 0.000 | 634351.318 | 2.73e-10 | 597 to 688 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 15 | 100 | 100 | 0.000 | 116534.666 | 8.89e-11 | 595 to 690 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 20 | 1000 | 1000 | 0.000 | 2048717.465 | 5.21e-10 | 583 to 711 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 25 | 100 | 100 | 0.000 | 850368.697 | 5.93e-10 | 584 to 695 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 30 | 100 | 100 | 0.000 | 207233.119 | 7.06e-11 | 577 to 698 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 10 | 35 | 100 | 100 | 0.000 | 94184.222 | 5.48e-11 | 570 to 700 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 10 | 40 | 100 | 100 | 0.000 | 325068.493 | 9.14e-11 | 563 to 703 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 10 | 45 | 100 | 100 | 0.000 | 373430.624 | 8.94e-11 | 556 to 705 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 10 | 50 | 100 | 100 | 0.000 | 101568.439 | 7.03e-11 | 550 to 708 | 0.017 | linearised set misses samples (sampling-based after inflation) |
| 10 | 55 | 100 | 100 | 0.000 | 899063.091 | 6.75e-10 | 545 to 710 | 0.018 | linearised set misses samples (sampling-based after inflation) |
| 10 | 60 | 1000 | 1000 | 0.000 | 479821.047 | 3.52e-10 | 515 to 726 | 0.021 | linearised set misses samples (sampling-based after inflation) |
| 10 | 80 | 100 | 100 | 0.000 | 254851.079 | 1.05e-10 | 528 to 723 | 0.019 | linearised set misses samples (sampling-based after inflation) |
| 10 | 100 | 100 | 100 | 0.000 | 1617394.876 | 8.75e-10 | 527 to 733 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 10 | 130 | 100 | 100 | 0.000 | 161520.847 | 1.09e-10 | 524 to 748 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 12 | 0 | 100 | 100 | 0.010 | 140.101 | 5.36e-02 | 756 to 846 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 5 | 100 | 100 | 0.000 | 128390.434 | 4.72e-11 | 756 to 847 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 10 | 100 | 100 | 0.000 | 60971.786 | 4.99e-11 | 756 to 846 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 15 | 100 | 100 | 0.000 | 47738.300 | 2.04e-11 | 754 to 848 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 20 | 100 | 100 | 0.000 | 100848.697 | 3.57e-11 | 750 to 850 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 25 | 100 | 100 | 0.000 | 71481.421 | 4.47e-11 | 745 to 852 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 30 | 100 | 100 | 0.000 | 186798.635 | 2.13e-10 | 740 to 855 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 35 | 100 | 100 | 0.000 | 394199.810 | 3.08e-10 | 735 to 858 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 40 | 100 | 100 | 0.000 | 53377.053 | 4.62e-11 | 729 to 860 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 12 | 45 | 100 | 100 | 0.000 | 84471.876 | 5.97e-11 | 724 to 863 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 50 | 100 | 100 | 0.000 | 104485.936 | 5.16e-11 | 719 to 865 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 12 | 55 | 100 | 100 | 0.000 | 202711.483 | 2.22e-10 | 715 to 868 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 60 | 100 | 100 | 0.000 | 106041.391 | 8.98e-11 | 712 to 871 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 12 | 80 | 100 | 100 | 0.000 | 97539.553 | 3.87e-11 | 704 to 881 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 12 | 100 | 100 | 100 | 0.000 | 46400.433 | 3.40e-11 | 705 to 892 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 12 | 130 | 100 | 100 | 0.000 | 53863.445 | 3.05e-11 | 705 to 907 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 14 | 0 | 100 | 100 | 0.000 | 6038957332549.768 | 8.40e-05 | 926 to 1017 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 5 | 100 | 100 | 0.000 | 33550.054 | 2.15e-11 | 927 to 1017 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 10 | 100 | 100 | 0.000 | 60499.475 | 2.16e-11 | 927 to 1017 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 15 | 100 | 100 | 0.000 | 18804.347 | 2.03e-11 | 925 to 1018 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 20 | 100 | 100 | 0.000 | 343335.059 | 6.68e-11 | 923 to 1020 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 25 | 100 | 100 | 0.000 | 24871.163 | 4.61e-11 | 919 to 1023 | 0.011 | linearised set misses samples (sampling-based after inflation) |
| 14 | 30 | 100 | 100 | 0.000 | 28418.788 | 1.67e-11 | 914 to 1026 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 14 | 35 | 100 | 100 | 0.000 | 3237118.015 | 4.65e-09 | 909 to 1028 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 14 | 40 | 100 | 100 | 0.000 | 36571.161 | 2.09e-11 | 905 to 1031 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 14 | 45 | 100 | 100 | 0.000 | 83752.146 | 1.36e-10 | 900 to 1034 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 14 | 50 | 100 | 100 | 0.000 | 62985.545 | 5.62e-11 | 896 to 1036 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 14 | 55 | 100 | 100 | 0.000 | 53863.683 | 5.08e-11 | 893 to 1039 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 14 | 60 | 100 | 100 | 0.000 | 62782.061 | 1.07e-10 | 891 to 1042 | 0.014 | linearised set misses samples (sampling-based after inflation) |
| 14 | 80 | 100 | 100 | 0.000 | 97491.854 | 1.47e-10 | 885 to 1053 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 14 | 100 | 100 | 100 | 0.000 | 11225.393 | 8.10e-12 | 887 to 1064 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 14 | 130 | 100 | 100 | 0.000 | 62015.354 | 7.03e-11 | 889 to 1079 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 16 | 0 | 100 | 100 | 0.000 | 294.540 | 3.97e-02 | 1112 to 1203 | 0.010 | linearised set misses samples (sampling-based after inflation) |
| 16 | 5 | 100 | 100 | 0.000 | 36051.977 | 1.52e-11 | 1114 to 1204 | 0.010 | linearised set misses samples (sampling-based after inflation) |
| 16 | 10 | 100 | 100 | 0.000 | 43459.589 | 1.96e-11 | 1114 to 1203 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 16 | 15 | 100 | 100 | 0.000 | 417321.979 | 3.77e-10 | 1112 to 1205 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 16 | 20 | 100 | 100 | 0.000 | 18608.916 | 2.29e-11 | 1110 to 1207 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 16 | 25 | 100 | 100 | 0.000 | 11119.917 | 1.70e-11 | 1107 to 1209 | 0.016 | linearised set misses samples (sampling-based after inflation) |
| 16 | 30 | 100 | 100 | 0.000 | 18005.448 | 2.35e-11 | 1102 to 1212 | 0.017 | linearised set misses samples (sampling-based after inflation) |
| 16 | 35 | 100 | 100 | 0.000 | 23994.958 | 1.84e-11 | 1098 to 1215 | 0.019 | linearised set misses samples (sampling-based after inflation) |
| 16 | 40 | 100 | 100 | 0.000 | 126434.509 | 4.57e-11 | 1094 to 1218 | 0.018 | linearised set misses samples (sampling-based after inflation) |
| 16 | 45 | 100 | 100 | 0.000 | 12782.366 | 1.59e-11 | 1090 to 1220 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 16 | 50 | 100 | 100 | 0.000 | 3758.505 | 4.18e-12 | 1086 to 1223 | 0.023 | linearised set misses samples (sampling-based after inflation) |
| 16 | 55 | 100 | 100 | 0.000 | 19165.626 | 9.94e-12 | 1083 to 1226 | 0.022 | linearised set misses samples (sampling-based after inflation) |
| 16 | 60 | 100 | 100 | 0.000 | 52266.280 | 2.92e-11 | 1081 to 1228 | 0.022 | linearised set misses samples (sampling-based after inflation) |
| 16 | 80 | 100 | 100 | 0.000 | 44371.647 | 3.89e-11 | 1078 to 1240 | 0.024 | linearised set misses samples (sampling-based after inflation) |
| 16 | 100 | 100 | 100 | 0.000 | 162021.719 | 1.33e-10 | 1080 to 1251 | 0.023 | linearised set misses samples (sampling-based after inflation) |
| 16 | 130 | 100 | 100 | 0.000 | 3448.408 | 3.42e-12 | 1083 to 1266 | 0.024 | linearised set misses samples (sampling-based after inflation) |
| 18 | 0 | 1000 | 1000 | 0.000 | 880358087636.999 | 7.57e-06 | 1303 to 1424 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 18 | 5 | 100 | 100 | 0.000 | 15352.148 | 1.61e-11 | 1319 to 1409 | 0.012 | linearised set misses samples (sampling-based after inflation) |
| 18 | 10 | 100 | 100 | 0.000 | 14122.551 | 3.61e-11 | 1319 to 1409 | 0.013 | linearised set misses samples (sampling-based after inflation) |
| 18 | 15 | 100 | 100 | 0.000 | 11602.584 | 2.11e-11 | 1318 to 1411 | 0.015 | linearised set misses samples (sampling-based after inflation) |
| 18 | 20 | 1000 | 1000 | 0.000 | 16602.797 | 8.30e-12 | 1307 to 1431 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 18 | 25 | 100 | 100 | 0.000 | 18019.682 | 3.39e-11 | 1313 to 1415 | 0.021 | linearised set misses samples (sampling-based after inflation) |
| 18 | 30 | 100 | 100 | 0.000 | 10488.166 | 1.44e-11 | 1309 to 1418 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 18 | 35 | 100 | 100 | 0.000 | 6796.167 | 1.85e-11 | 1305 to 1421 | 0.020 | linearised set misses samples (sampling-based after inflation) |
| 18 | 40 | 100 | 100 | 0.000 | 18900.072 | 4.38e-11 | 1301 to 1423 | 0.024 | linearised set misses samples (sampling-based after inflation) |
| 18 | 45 | 100 | 100 | 0.000 | 16632.175 | 1.47e-11 | 1297 to 1426 | 0.027 | linearised set misses samples (sampling-based after inflation) |
| 18 | 50 | 100 | 100 | 0.000 | 24442.414 | 1.89e-11 | 1293 to 1429 | 0.023 | linearised set misses samples (sampling-based after inflation) |
| 18 | 55 | 100 | 100 | 0.000 | 48879.998 | 4.88e-11 | 1291 to 1431 | 0.030 | linearised set misses samples (sampling-based after inflation) |
| 18 | 60 | 1000 | 1000 | 0.000 | 6972677.493 | 4.88e-09 | 1273 to 1446 | 0.030 | linearised set misses samples (sampling-based after inflation) |
| 18 | 80 | 100 | 100 | 0.000 | 20328.913 | 1.52e-11 | 1286 to 1445 | 0.026 | linearised set misses samples (sampling-based after inflation) |
| 18 | 100 | 100 | 100 | 0.000 | 43931.581 | 5.30e-11 | 1288 to 1456 | 0.026 | linearised set misses samples (sampling-based after inflation) |
| 18 | 130 | 100 | 100 | 0.000 | 305002.416 | 2.93e-10 | 1292 to 1472 | 0.026 | linearised set misses samples (sampling-based after inflation) |

## Certified delay budget

Largest relative disagreement between the LMI and the trust-region evaluation of beta over all cases: 0.00e+00.

### Capture controller: LQR; certificate tier: rigorous

| f_spin (N) | w_sw (rad/s) | gamma | state at tau = 0 | tau* |
|---|---|---|---|---|
| 2.95 | 6 | 0.0 | centre outside, alpha_c = 0.0017 | does not exist |
| 2.95 | 6 | 0.1 | centre outside, alpha_c = 0.0017 | does not exist |
| 2.95 | 6 | 0.25 | centre outside, alpha_c = 0.0017 | does not exist |
| 2.95 | 6 | 0.5 | centre outside, alpha_c = 0.0017 | does not exist |
| 2.95 | 6 | 1.0 | centre outside, alpha_c = 0.0017 | does not exist |
| 2.95 | 8 | 0.0 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.95 | 8 | 0.1 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.95 | 8 | 0.25 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.95 | 8 | 0.5 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.95 | 8 | 1.0 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 6 | 0.0 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 6 | 0.1 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 6 | 0.25 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 6 | 0.5 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 6 | 1.0 | centre outside, alpha_c = 0.0018 | does not exist |
| 2.45 | 8 | 0.0 | centre outside, alpha_c = 0.0015 | does not exist |
| 2.45 | 8 | 0.1 | centre outside, alpha_c = 0.0015 | does not exist |
| 2.45 | 8 | 0.25 | centre outside, alpha_c = 0.0015 | does not exist |
| 2.45 | 8 | 0.5 | centre outside, alpha_c = 0.0015 | does not exist |
| 2.45 | 8 | 1.0 | centre outside, alpha_c = 0.0015 | does not exist |

### Capture controller: redesigned; certificate tier: rigorous

| f_spin (N) | w_sw (rad/s) | gamma | state at tau = 0 | tau* |
|---|---|---|---|---|

### Capture controller: LQR; certificate tier: LPV

| f_spin (N) | w_sw (rad/s) | gamma | state at tau = 0 | tau* |
|---|---|---|---|---|
| 2.95 | 6 | 0.0 | centre outside, alpha_c = 0.0986 | does not exist |
| 2.95 | 6 | 0.1 | centre outside, alpha_c = 0.0986 | does not exist |
| 2.95 | 6 | 0.25 | centre outside, alpha_c = 0.0986 | does not exist |
| 2.95 | 6 | 0.5 | centre outside, alpha_c = 0.0986 | does not exist |
| 2.95 | 6 | 1.0 | centre outside, alpha_c = 0.0986 | does not exist |
| 2.95 | 8 | 0.0 | centre outside, alpha_c = 0.1772 | does not exist |
| 2.95 | 8 | 0.1 | centre outside, alpha_c = 0.1772 | does not exist |
| 2.95 | 8 | 0.25 | centre outside, alpha_c = 0.1772 | does not exist |
| 2.95 | 8 | 0.5 | centre outside, alpha_c = 0.1772 | does not exist |
| 2.95 | 8 | 1.0 | centre outside, alpha_c = 0.1772 | does not exist |
| 2.95 | 10 | 0.0 | centre outside, alpha_c = 0.1466 | does not exist |
| 2.95 | 10 | 0.1 | centre outside, alpha_c = 0.1466 | does not exist |
| 2.95 | 10 | 0.25 | centre outside, alpha_c = 0.1466 | does not exist |
| 2.95 | 10 | 0.5 | centre outside, alpha_c = 0.1466 | does not exist |
| 2.95 | 10 | 1.0 | centre outside, alpha_c = 0.1466 | does not exist |
| 2.95 | 12 | 0.0 | centre outside, alpha_c = 0.3160 | does not exist |
| 2.95 | 12 | 0.1 | centre outside, alpha_c = 0.3160 | does not exist |
| 2.95 | 12 | 0.25 | centre outside, alpha_c = 0.3160 | does not exist |
| 2.95 | 12 | 0.5 | centre outside, alpha_c = 0.3160 | does not exist |
| 2.95 | 12 | 1.0 | centre outside, alpha_c = 0.3160 | does not exist |
| 2.95 | 14 | 0.0 | centre outside, alpha_c = 0.2660 | does not exist |
| 2.95 | 14 | 0.1 | centre outside, alpha_c = 0.2660 | does not exist |
| 2.95 | 14 | 0.25 | centre outside, alpha_c = 0.2660 | does not exist |
| 2.95 | 14 | 0.5 | centre outside, alpha_c = 0.2660 | does not exist |
| 2.95 | 14 | 1.0 | centre outside, alpha_c = 0.2660 | does not exist |
| 2.95 | 16 | 0.0 | centre outside, alpha_c = 0.3092 | does not exist |
| 2.95 | 16 | 0.1 | centre outside, alpha_c = 0.3092 | does not exist |
| 2.95 | 16 | 0.25 | centre outside, alpha_c = 0.3092 | does not exist |
| 2.95 | 16 | 0.5 | centre outside, alpha_c = 0.3092 | does not exist |
| 2.95 | 16 | 1.0 | centre outside, alpha_c = 0.3092 | does not exist |
| 2.95 | 18 | 0.0 | centre outside, alpha_c = 0.1271 | does not exist |
| 2.95 | 18 | 0.1 | centre outside, alpha_c = 0.1271 | does not exist |
| 2.95 | 18 | 0.25 | centre outside, alpha_c = 0.1271 | does not exist |
| 2.95 | 18 | 0.5 | centre outside, alpha_c = 0.1271 | does not exist |
| 2.95 | 18 | 1.0 | centre outside, alpha_c = 0.1271 | does not exist |
| 2.45 | 6 | 0.0 | centre outside, alpha_c = 0.1066 | does not exist |
| 2.45 | 6 | 0.1 | centre outside, alpha_c = 0.1066 | does not exist |
| 2.45 | 6 | 0.25 | centre outside, alpha_c = 0.1066 | does not exist |
| 2.45 | 6 | 0.5 | centre outside, alpha_c = 0.1066 | does not exist |
| 2.45 | 6 | 1.0 | centre outside, alpha_c = 0.1066 | does not exist |
| 2.45 | 8 | 0.0 | centre outside, alpha_c = 0.1494 | does not exist |
| 2.45 | 8 | 0.1 | centre outside, alpha_c = 0.1494 | does not exist |
| 2.45 | 8 | 0.25 | centre outside, alpha_c = 0.1494 | does not exist |
| 2.45 | 8 | 0.5 | centre outside, alpha_c = 0.1494 | does not exist |
| 2.45 | 8 | 1.0 | centre outside, alpha_c = 0.1494 | does not exist |
| 2.45 | 10 | 0.0 | centre outside, alpha_c = 0.1046 | does not exist |
| 2.45 | 10 | 0.1 | centre outside, alpha_c = 0.1046 | does not exist |
| 2.45 | 10 | 0.25 | centre outside, alpha_c = 0.1046 | does not exist |
| 2.45 | 10 | 0.5 | centre outside, alpha_c = 0.1046 | does not exist |
| 2.45 | 10 | 1.0 | centre outside, alpha_c = 0.1046 | does not exist |
| 2.45 | 12 | 0.0 | centre outside, alpha_c = 0.0848 | does not exist |
| 2.45 | 12 | 0.1 | centre outside, alpha_c = 0.0848 | does not exist |
| 2.45 | 12 | 0.25 | centre outside, alpha_c = 0.0848 | does not exist |
| 2.45 | 12 | 0.5 | centre outside, alpha_c = 0.0848 | does not exist |
| 2.45 | 12 | 1.0 | centre outside, alpha_c = 0.0848 | does not exist |
| 2.45 | 14 | 0.0 | centre outside, alpha_c = 0.0565 | does not exist |
| 2.45 | 14 | 0.1 | centre outside, alpha_c = 0.0565 | does not exist |
| 2.45 | 14 | 0.25 | centre outside, alpha_c = 0.0565 | does not exist |
| 2.45 | 14 | 0.5 | centre outside, alpha_c = 0.0565 | does not exist |
| 2.45 | 14 | 1.0 | centre outside, alpha_c = 0.0565 | does not exist |
| 2.45 | 16 | 0.0 | centre outside, alpha_c = 0.0687 | does not exist |
| 2.45 | 16 | 0.1 | centre outside, alpha_c = 0.0687 | does not exist |
| 2.45 | 16 | 0.25 | centre outside, alpha_c = 0.0687 | does not exist |
| 2.45 | 16 | 0.5 | centre outside, alpha_c = 0.0687 | does not exist |
| 2.45 | 16 | 1.0 | centre outside, alpha_c = 0.0687 | does not exist |
| 2.45 | 18 | 0.0 | centre outside, alpha_c = 0.0297 | does not exist |
| 2.45 | 18 | 0.1 | centre outside, alpha_c = 0.0297 | does not exist |
| 2.45 | 18 | 0.25 | centre outside, alpha_c = 0.0297 | does not exist |
| 2.45 | 18 | 0.5 | centre outside, alpha_c = 0.0297 | does not exist |
| 2.45 | 18 | 1.0 | centre outside, alpha_c = 0.0297 | does not exist |

### Capture controller: redesigned; certificate tier: LPV

| f_spin (N) | w_sw (rad/s) | gamma | state at tau = 0 | tau* |
|---|---|---|---|---|
| 2.95 | 6 | 0.0 | centre outside, alpha_c = 0.2490 | does not exist |
| 2.95 | 6 | 0.1 | centre outside, alpha_c = 0.2490 | does not exist |
| 2.95 | 6 | 0.25 | centre outside, alpha_c = 0.2490 | does not exist |
| 2.95 | 6 | 0.5 | centre outside, alpha_c = 0.2490 | does not exist |
| 2.95 | 6 | 1.0 | centre outside, alpha_c = 0.2490 | does not exist |
| 2.95 | 8 | 0.0 | centre outside, alpha_c = 0.2931 | does not exist |
| 2.95 | 8 | 0.1 | centre outside, alpha_c = 0.2931 | does not exist |
| 2.95 | 8 | 0.25 | centre outside, alpha_c = 0.2931 | does not exist |
| 2.95 | 8 | 0.5 | centre outside, alpha_c = 0.2931 | does not exist |
| 2.95 | 8 | 1.0 | centre outside, alpha_c = 0.2931 | does not exist |
| 2.95 | 10 | 0.0 | centre outside, alpha_c = 0.1965 | does not exist |
| 2.95 | 10 | 0.1 | centre outside, alpha_c = 0.1965 | does not exist |
| 2.95 | 10 | 0.25 | centre outside, alpha_c = 0.1965 | does not exist |
| 2.95 | 10 | 0.5 | centre outside, alpha_c = 0.1965 | does not exist |
| 2.95 | 10 | 1.0 | centre outside, alpha_c = 0.1965 | does not exist |
| 2.95 | 12 | 0.0 | centre outside, alpha_c = 0.4283 | does not exist |
| 2.95 | 12 | 0.1 | centre outside, alpha_c = 0.4283 | does not exist |
| 2.95 | 12 | 0.25 | centre outside, alpha_c = 0.4283 | does not exist |
| 2.95 | 12 | 0.5 | centre outside, alpha_c = 0.4283 | does not exist |
| 2.95 | 12 | 1.0 | centre outside, alpha_c = 0.4283 | does not exist |
| 2.95 | 14 | 0.0 | centre outside, alpha_c = 0.3477 | does not exist |
| 2.95 | 14 | 0.1 | centre outside, alpha_c = 0.3477 | does not exist |
| 2.95 | 14 | 0.25 | centre outside, alpha_c = 0.3477 | does not exist |
| 2.95 | 14 | 0.5 | centre outside, alpha_c = 0.3477 | does not exist |
| 2.95 | 14 | 1.0 | centre outside, alpha_c = 0.3477 | does not exist |
| 2.95 | 16 | 0.0 | centre outside, alpha_c = 0.4611 | does not exist |
| 2.95 | 16 | 0.1 | centre outside, alpha_c = 0.4611 | does not exist |
| 2.95 | 16 | 0.25 | centre outside, alpha_c = 0.4611 | does not exist |
| 2.95 | 16 | 0.5 | centre outside, alpha_c = 0.4611 | does not exist |
| 2.95 | 16 | 1.0 | centre outside, alpha_c = 0.4611 | does not exist |
| 2.95 | 18 | 0.0 | centre outside, alpha_c = 0.3663 | does not exist |
| 2.95 | 18 | 0.1 | centre outside, alpha_c = 0.3663 | does not exist |
| 2.95 | 18 | 0.25 | centre outside, alpha_c = 0.3663 | does not exist |
| 2.95 | 18 | 0.5 | centre outside, alpha_c = 0.3663 | does not exist |
| 2.95 | 18 | 1.0 | centre outside, alpha_c = 0.3663 | does not exist |
| 2.45 | 6 | 0.0 | centre outside, alpha_c = 0.1993 | does not exist |
| 2.45 | 6 | 0.1 | centre outside, alpha_c = 0.1993 | does not exist |
| 2.45 | 6 | 0.25 | centre outside, alpha_c = 0.1993 | does not exist |
| 2.45 | 6 | 0.5 | centre outside, alpha_c = 0.1993 | does not exist |
| 2.45 | 6 | 1.0 | centre outside, alpha_c = 0.1993 | does not exist |
| 2.45 | 8 | 0.0 | centre outside, alpha_c = 0.2026 | does not exist |
| 2.45 | 8 | 0.1 | centre outside, alpha_c = 0.2026 | does not exist |
| 2.45 | 8 | 0.25 | centre outside, alpha_c = 0.2026 | does not exist |
| 2.45 | 8 | 0.5 | centre outside, alpha_c = 0.2026 | does not exist |
| 2.45 | 8 | 1.0 | centre outside, alpha_c = 0.2026 | does not exist |
| 2.45 | 10 | 0.0 | centre outside, alpha_c = 0.1270 | does not exist |
| 2.45 | 10 | 0.1 | centre outside, alpha_c = 0.1270 | does not exist |
| 2.45 | 10 | 0.25 | centre outside, alpha_c = 0.1270 | does not exist |
| 2.45 | 10 | 0.5 | centre outside, alpha_c = 0.1270 | does not exist |
| 2.45 | 10 | 1.0 | centre outside, alpha_c = 0.1270 | does not exist |
| 2.45 | 12 | 0.0 | centre outside, alpha_c = 0.0700 | does not exist |
| 2.45 | 12 | 0.1 | centre outside, alpha_c = 0.0700 | does not exist |
| 2.45 | 12 | 0.25 | centre outside, alpha_c = 0.0700 | does not exist |
| 2.45 | 12 | 0.5 | centre outside, alpha_c = 0.0700 | does not exist |
| 2.45 | 12 | 1.0 | centre outside, alpha_c = 0.0700 | does not exist |
| 2.45 | 14 | 0.0 | centre outside, alpha_c = 0.0682 | does not exist |
| 2.45 | 14 | 0.1 | centre outside, alpha_c = 0.0682 | does not exist |
| 2.45 | 14 | 0.25 | centre outside, alpha_c = 0.0682 | does not exist |
| 2.45 | 14 | 0.5 | centre outside, alpha_c = 0.0682 | does not exist |
| 2.45 | 14 | 1.0 | centre outside, alpha_c = 0.0682 | does not exist |
| 2.45 | 16 | 0.0 | centre outside, alpha_c = 0.0475 | does not exist |
| 2.45 | 16 | 0.1 | centre outside, alpha_c = 0.0475 | does not exist |
| 2.45 | 16 | 0.25 | centre outside, alpha_c = 0.0475 | does not exist |
| 2.45 | 16 | 0.5 | centre outside, alpha_c = 0.0475 | does not exist |
| 2.45 | 16 | 1.0 | centre outside, alpha_c = 0.0475 | does not exist |
| 2.45 | 18 | 0.0 | centre outside, alpha_c = 0.0289 | does not exist |
| 2.45 | 18 | 0.1 | centre outside, alpha_c = 0.0289 | does not exist |
| 2.45 | 18 | 0.25 | centre outside, alpha_c = 0.0289 | does not exist |
| 2.45 | 18 | 0.5 | centre outside, alpha_c = 0.0289 | does not exist |
| 2.45 | 18 | 1.0 | centre outside, alpha_c = 0.0289 | does not exist |
