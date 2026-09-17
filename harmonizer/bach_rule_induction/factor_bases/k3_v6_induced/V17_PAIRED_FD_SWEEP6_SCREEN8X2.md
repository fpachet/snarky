# V17 — différences finies appariées du sampler

Chaque candidat est réellement ajouté au modèle avec un petit poids.
V13 et sa perturbation utilisent la même pièce, le même état initial et
le même flux pseudo-aléatoire. Aucun gradient d'équilibre n'est supposé.

- Split : `train`.
- Pièces : `8`.
- Graines : `[10103, 20207]`.
- Horizon : `6` balayages.
- Candidats : `12`.
- Test réservé chargé : `false`.

| Rang | Candidat | Pas | Résidu relatif | Toutes graines | Gardes |
|---:|---|---:|---:|---|---|
| 12 | `any_voice_adjacent_abs_class(all_voices)=6` | -0.150000 | 0.773 | false | false |
| 9 | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.150000 | 0.863 | true | false |
| 7 | `central_pair_abs_class(v2,v1)=7` | +0.150000 | 0.868 | false | false |
| 4 | `central_pair_abs_class(v1,v3)=5` | -0.150000 | 0.951 | false | false |
| 11 | `central_pair_abs_class_metric_target_rearticulated(v1,v0)=1,1` | +0.150000 | 0.963 | false | true |
| 1 | `central_pair_abs_class_metric_target_rearticulated(v1,v2)=7,1` | +0.150000 | 0.995 | false | true |
| 8 | `abs_class_from_previous(v3)=0` | +0.150000 | 1.013 | false | false |
| 10 | `central_pair_abs_class(v3,v0)=3` | +0.150000 | 1.043 | false | false |
| 2 | `three_block_sign_shape(v1)=0,-1` | +0.150000 | 1.050 | false | false |
| 3 | `abs_step_to_next_gt(v1)=1` | +0.150000 | 1.133 | false | false |
| 5 | `any_voice_three_block_sign_shape(all_voices)=0,-1` | +0.150000 | 1.162 | false | false |
| 6 | `central_pair_abs_class(v0,v3)=3` | +0.150000 | 1.198 | false | false |

Une amélioration sur ce petit écran train n'admet pas encore le
facteur. Les survivants doivent être répliqués sur 32 pièces, trois
graines et aux horizons 6 et 30 avant tout refit exact borné.
