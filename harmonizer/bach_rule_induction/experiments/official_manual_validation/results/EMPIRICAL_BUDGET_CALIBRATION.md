# Calibration des budgets empiriques du manuel

Les seuils sont les quantiles supérieurs calculés sur les 251 chorals
d'entraînement uniquement. Un budget est promu lorsque son taux de
dépassement sur les 50 chorals de validation ne dépasse pas la borne
préenregistrée. Le test n'intervient ni dans le seuil ni dans la promotion.

- Quantile train : `0.950`.
- Dépassement validation maximal : `0.150`.
- Budgets promus : `18` / `18`.
- Acceptation conjointe train / validation / test : `0.598` / `0.720` / `0.490`.
- Budget conjoint de dépassements autorisés : `2`.
- Acceptation avec ce budget train / validation / test : `0.960` / `0.980` / `0.902`.
- Acceptation de toutes les familles train / validation / test : `0.940` / `0.960` / `0.863`.

| Métrique | Seuil | Train > | Validation > | Test > | Décision |
|---|---:|---:|---:|---:|---|
| `parallel_fifth_rate` | 0.010204 | 0.048 | 0.040 | 0.137 | PROMU |
| `parallel_octave_rate` | 0.007576 | 0.044 | 0.100 | 0.078 | PROMU |
| `direct_fifth_rate` | 0.020408 | 0.048 | 0.020 | 0.078 | PROMU |
| `voice_crossing_rate` | 0.119403 | 0.048 | 0.000 | 0.078 | PROMU |
| `voice_overlap_rate` | 0.196970 | 0.044 | 0.000 | 0.059 | PROMU |
| `unresolved_leading_tone_ratio` | 0.781250 | 0.048 | 0.020 | 0.020 | PROMU |
| `uncompensated_leap_ratio` | 1.000000 | 0.000 | 0.000 | 0.000 | PROMU |
| `unresolved_suspension_ratio` | 0.800000 | 0.048 | 0.040 | 0.039 | PROMU |
| `soprano_maximum_leap` | 12.000000 | 0.000 | 0.000 | 0.000 | PROMU |
| `alto_maximum_leap` | 12.000000 | 0.000 | 0.000 | 0.020 | PROMU |
| `tenor_maximum_leap` | 12.000000 | 0.000 | 0.000 | 0.000 | PROMU |
| `bass_maximum_leap` | 16.000000 | 0.036 | 0.020 | 0.000 | PROMU |
| `alto_longest_repeat_run` | 6.000000 | 0.036 | 0.020 | 0.039 | PROMU |
| `tenor_longest_repeat_run` | 6.000000 | 0.040 | 0.040 | 0.020 | PROMU |
| `bass_longest_repeat_run` | 3.000000 | 0.012 | 0.000 | 0.000 | PROMU |
| `alto_step_deficit` | 0.338983 | 0.048 | 0.000 | 0.118 | PROMU |
| `tenor_step_deficit` | 0.370370 | 0.048 | 0.020 | 0.039 | PROMU |
| `bass_step_deficit` | 0.494949 | 0.048 | 0.080 | 0.098 | PROMU |

## Budgets par famille

| Famille | Dépassements autorisés | Train | Validation | Test |
|---|---:|---:|---:|---:|
| `contrapuntal` | 2 | 0.996 | 1.000 | 0.961 |
| `tendency` | 1 | 0.996 | 1.000 | 1.000 |
| `leap` | 0 | 0.964 | 0.980 | 0.980 |
| `repetition` | 1 | 0.996 | 1.000 | 1.000 |
| `conjunct_motion` | 1 | 0.984 | 0.980 | 0.922 |

Les budgets sont des enveloppes statistiques de génération, pas des
interdictions musicologiques universelles. Une pièce authentique peut
donc tomber hors enveloppe, ce que mesure l'acceptation conjointe.
