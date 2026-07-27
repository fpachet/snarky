# V5-K3-CLEAN — premier cycle d'induction

## Protocole

- Base musicale initiale vide.
- Une note masquée et trois blocs verticaux consécutifs.
- Domaine commun de hauteurs dérivé du seul train.
- Aucun manifeste ni fichier de règles V1–V4 chargé.
- Sélection des colonnes sur le gradient résiduel du train.
- Les noms musicologiques ne sont appliqués qu'après sélection.

## Corpus

- Train : `251` chorals, `68263` décisions.
- Validation : `50` chorals, `13202` décisions.
- Ancien test : `51` chorals non chargés.
- Domaine commun train : MIDI `36` à `81`.
- Choix validation hors domaine : `0`.

## Modèle

- NLL validation registre seul : `2.594465`.
- Meilleure NLL validation : `1.900371`.
- Gain : `0.694095`.
- Règles locales retenues : `12`.

| # | Clause numérique | Poids | z au moment de la sélection | Modalité |
|---:|---|---:|---:|---|
| 1 | `abs_step_from_previous_gt(v0)=2` | -1.812709 | -120.225 | évitement |
| 2 | `abs_step_from_previous_gt(v1)=2` | -1.551374 | -115.229 | évitement |
| 3 | `abs_step_from_previous_gt(v2)=2` | -1.625284 | -113.762 | évitement |
| 4 | `abs_step_from_previous_gt(v3)=2` | -1.616616 | -108.875 | évitement |
| 5 | `abs_step_to_next_gt(v3)=2` | -1.701348 | -94.538 | évitement |
| 6 | `abs_step_to_next_gt(v2)=2` | -1.617854 | -83.513 | évitement |
| 7 | `abs_step_to_next_gt(v1)=2` | -1.532327 | -78.830 | évitement |
| 8 | `abs_step_to_next_gt(v0)=2` | -1.670821 | -63.832 | évitement |
| 9 | `central_ordered_gap_le(v2,v1)=2` | -1.577571 | -51.035 | évitement |
| 10 | `central_ordered_gap_le(v1,v0)=2` | -1.661928 | -49.806 | évitement |
| 11 | `central_ordered_gap_le(v1,v2)=2` | -1.700309 | -60.300 | évitement |
| 12 | `central_pair_abs_class(v3,v2)=0` | +0.956926 | +49.229 | préférence |

## Benchmark externe après gel

- `melodic_class_6` : `non retrouvé`
- `preserved_pair_class_0` : `non retrouvé`
- `preserved_pair_class_7` : `non retrouvé`
- `arrival_pair_class_0` : `non retrouvé`
- `arrival_pair_class_7` : `non retrouvé`
- `previous_or_central_order_boundary` : `non retrouvé`

Ce benchmark ne change ni les colonnes ni les poids. Les absences sont
des résultats négatifs du premier budget, pas des motifs d'ajustement
manuel.
