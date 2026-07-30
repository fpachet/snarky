# V17 — différences finies appariées du sampler

Chaque candidat est réellement ajouté au modèle avec un petit poids.
V13 et sa perturbation utilisent la même pièce, le même état initial et
le même flux pseudo-aléatoire. Aucun gradient d'équilibre n'est supposé.

- Split : `train`.
- Pièces : `8`.
- Graines : `[10103, 20207]`.
- Horizon : `6` balayages.
- Candidats : `2`.
- Test réservé chargé : `false`.

| Rang | Candidat | Pas | Résidu relatif | Toutes graines | Gardes |
|---:|---|---:|---:|---|---|
| 9 | `any_pair_arrival_abs_class_same_sign(all_voices)=10` | -0.075000 | 0.838 | false | true |
| 12 | `any_voice_adjacent_abs_class(all_voices)=6` | -0.075000 | 0.963 | false | false |

Une amélioration sur ce petit écran train n'admet pas encore le
facteur. Les survivants doivent être répliqués sur 32 pièces, trois
graines et aux horizons 6 et 30 avant tout refit exact borné.
