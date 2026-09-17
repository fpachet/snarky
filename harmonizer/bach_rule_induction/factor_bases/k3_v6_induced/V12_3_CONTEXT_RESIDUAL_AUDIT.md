# V12.3 — localisation des résidus contextuels

`16` chorals de train, `3` graines et `30` sweeps. Le test et la validation restent fermés.

Les tableaux classent les contextes par excès `V12.2 − Bach`. Ils ne
définissent pas encore des règles : ils localisent les interactions que
le prochain catalogue devra rendre disponibles à l'induction.

## Intervalles dissonants par paire et niveau métrique

| Contexte | Bach | V12.2 | Écart |
|---|---:|---:|---:|
| `Soprano–Bass|strong` | 2.98 % | 9.22 % | +6.24 pp |
| `Soprano–Tenor|strong` | 6.81 % | 12.41 % | +5.60 pp |
| `Alto–Tenor|strong` | 3.62 % | 8.72 % | +5.11 pp |
| `Soprano–Tenor|weak` | 13.28 % | 17.29 % | +4.00 pp |
| `Tenor–Bass|strong` | 4.68 % | 8.09 % | +3.40 pp |
| `Soprano–Bass|weak` | 15.43 % | 15.82 % | +0.39 pp |
| `Soprano–Alto|weak` | 12.01 % | 11.91 % | -0.10 pp |
| `Alto–Bass|strong` | 8.09 % | 7.16 % | -0.92 pp |
| `Alto–Tenor|weak` | 14.65 % | 12.99 % | -1.66 pp |
| `Tenor–Bass|weak` | 16.70 % | 14.91 % | -1.79 pp |
| `Alto–Bass|weak` | 15.04 % | 12.76 % | -2.28 pp |
| `Soprano–Alto|strong` | 12.13 % | 6.03 % | -6.10 pp |

## Statuts des occurrences dissonantes

| Contexte | Bach | V12.2 | Écart |
|---|---:|---:|---:|
| `Alto–Bass|strong|passing` | 10.53 % | 37.62 % | +27.10 pp |
| `Alto–Tenor|strong|passing` | 5.88 % | 31.71 % | +25.82 pp |
| `Tenor–Bass|strong|passing` | 18.18 % | 43.86 % | +25.68 pp |
| `Soprano–Alto|strong|passing` | 5.26 % | 30.59 % | +25.33 pp |
| `Alto–Tenor|weak|unresolved_nonornamental` | 3.33 % | 25.56 % | +22.23 pp |
| `Soprano–Tenor|strong|unresolved_nonornamental` | 15.62 % | 36.57 % | +20.95 pp |
| `Alto–Bass|weak|unresolved_nonornamental` | 3.25 % | 21.43 % | +18.18 pp |
| `Tenor–Bass|weak|unresolved_nonornamental` | 2.34 % | 20.09 % | +17.75 pp |
| `Tenor–Bass|strong|neighbor` | 0.00 % | 16.67 % | +16.67 pp |
| `Alto–Bass|strong|neighbor` | 5.26 % | 20.79 % | +15.53 pp |
| `Soprano–Bass|strong|passing` | 21.43 % | 36.15 % | +14.73 pp |
| `Soprano–Tenor|strong|passing` | 18.75 % | 30.86 % | +12.11 pp |
| `Soprano–Alto|weak|unresolved_nonornamental` | 8.94 % | 20.22 % | +11.28 pp |
| `Soprano–Tenor|weak|unresolved_nonornamental` | 8.09 % | 17.51 % | +9.43 pp |
| `Soprano–Bass|weak|unresolved_nonornamental` | 6.33 % | 15.02 % | +8.69 pp |

## Mouvements de basse

| Contexte | Bach | V12.2 | Écart |
|---|---:|---:|---:|
| `semitone|weak` | 21.47 % | 32.72 % | +11.25 pp |
| `outside_arrival|weak` | 9.36 % | 14.57 % | +5.21 pp |
| `large_leap|weak` | 20.55 % | 24.74 % | +4.19 pp |
| `semitone|strong` | 22.84 % | 26.94 % | +4.09 pp |
| `descending_large_leap|weak` | 9.51 % | 13.09 % | +3.58 pp |
| `outside_arrival|strong` | 6.68 % | 9.55 % | +2.87 pp |
| `ascending_large_leap|weak` | 11.04 % | 11.66 % | +0.61 pp |
| `outside_after_large_leap|weak` | 1.23 % | 1.69 % | +0.46 pp |
| `outside_after_large_leap|strong` | 1.29 % | 1.22 % | -0.07 pp |
| `descending_large_leap|strong` | 19.61 % | 16.45 % | -3.16 pp |
| `ascending_large_leap|strong` | 22.20 % | 14.22 % | -7.97 pp |
| `large_leap|strong` | 41.81 % | 30.68 % | -11.14 pp |

## Transitions tonales de basse les plus surproduites

| Contexte | Bach | V12.2 | Écart |
|---|---:|---:|---:|
| `8→9|weak` | 0.09 % | 0.99 % | +0.90 pp |
| `3→5|weak` | 0.18 % | 0.96 % | +0.78 pp |
| `0→11|weak` | 1.79 % | 2.54 % | +0.75 pp |
| `9→0|strong` | 0.00 % | 0.75 % | +0.75 pp |
| `2→0|strong` | 0.72 % | 1.34 % | +0.63 pp |
| `5→3|strong` | 0.27 % | 0.90 % | +0.63 pp |
| `3→2|weak` | 0.63 % | 1.19 % | +0.57 pp |
| `7→8|weak` | 0.81 % | 1.37 % | +0.57 pp |
| `5→0|weak` | 0.18 % | 0.72 % | +0.54 pp |
| `0→11|strong` | 0.36 % | 0.87 % | +0.51 pp |
| `2→3|weak` | 0.36 % | 0.87 % | +0.51 pp |
| `9→8|strong` | 0.00 % | 0.51 % | +0.51 pp |

## Lecture

Les excès stables doivent être traduits en familles de facteurs
dirigés et locaux : paire de voix × classe d'intervalle × métrique ×
préparation/résolution, et degré de basse × mouvement × métrique.
Le signe et le poids de chaque candidat resteront appris du corpus.
