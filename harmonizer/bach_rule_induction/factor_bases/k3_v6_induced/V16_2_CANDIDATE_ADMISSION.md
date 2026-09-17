# V16 — admission hybride des candidats

Chaque colonne du top-K a un poids nul dans les chaînes. Sa covariance
avec les dix diagnostics estime l'effet local qu'aurait le petit pas
conditionnel proposé. Un candidat n'est admissible que si cet effet est
stable entre graines et non régressif pour la distance générative.

- Graines indépendantes : `3`.
- Pas maximal : `0.15`.
- Cosinus inter-graines minimal : `0.5`.
- Régression maximale tolérée par graine : `2.0 %`.
- Amélioration ensemble minimale : `5.0 %`.
- Candidats admissibles : `1`.
- Candidat proposé : `9`.

| Rang | Candidat | Pas | cos min | Résidu ensemble | Admis |
|---:|---|---:|---:|---:|---|
| 1 | `central_pair_abs_class_metric_target_rearticulated(v1,v2)=7,1` | +0.150000 | -0.328 | 1.001 | false |
| 2 | `three_block_sign_shape(v1)=0,-1` | +0.150000 | -0.420 | 1.001 | false |
| 3 | `abs_step_to_next_gt(v1)=1` | +0.150000 | -0.583 | 0.990 | false |
| 4 | `central_pair_abs_class(v1,v3)=5` | -0.150000 | +0.512 | 1.005 | false |
| 5 | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.150000 | +0.666 | 0.992 | false |
| 6 | `central_pair_abs_class(v0,v3)=3` | +0.150000 | -0.428 | 0.988 | false |
| 7 | `central_pair_abs_class(v2,v1)=7` | +0.150000 | -0.195 | 1.014 | false |
| 8 | `abs_class_from_previous(v3)=0` | +0.150000 | +0.909 | 0.970 | false |
| 9 | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.150000 | +0.765 | 0.946 | true |
| 10 | `central_pair_abs_class(v3,v0)=3` | +0.150000 | -0.307 | 0.993 | false |
| 11 | `central_pair_abs_class_metric_target_rearticulated(v1,v0)=1,1` | +0.150000 | -0.753 | 1.001 | false |
| 12 | `any_voice_adjacent_abs_class(all_voices)=6` | -0.150000 | +0.600 | 0.972 | false |

L'admission est locale : le candidat proposé doit encore être ajouté,
réajusté conjointement par pseudo-vraisemblance exacte, puis soumis à
un nouvel audit génératif. Le test réservé reste fermé.
