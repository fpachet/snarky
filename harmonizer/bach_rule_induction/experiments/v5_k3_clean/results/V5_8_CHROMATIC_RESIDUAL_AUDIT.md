# V5.8 — audit des chromaticismes résiduels

Les classes dites rares sont définies mécaniquement par une fréquence
d'apprentissage inférieure à `2.00 %`,
séparément pour chaque voix et chaque mode. Il ne s'agit donc pas d'une
liste de notes chromatiques écrite à la main.

Le taux observé est le nombre d'attaques authentiques classées rares
divisé par toutes les décisions d'attaque internes des quatre voix. Comme
plusieurs classes ont chacune une fréquence train inférieure au seuil,
leur taux cumulé sur validation peut dépasser 2 %.

Le jeu de test scellé n'est ni chargé ni consulté.

## Calibration conditionnelle sur validation

| Périmètre | Décisions | Observé | Attendu par V5.7 | Écart | z |
|---|---:|---:|---:|---:|---:|
| Ensemble | 13202 | 3.780 % | 2.364 % | +1.416 pp | +11.41 |
| voice=Soprano | 2787 | 3.229 % | 2.012 % | +1.217 pp | +4.81 |
| voice=Alto | 3436 | 3.492 % | 2.209 % | +1.284 pp | +5.37 |
| voice=Tenor | 3426 | 4.495 % | 2.892 % | +1.603 pp | +6.06 |
| voice=Bass | 3553 | 3.800 % | 2.279 % | +1.520 pp | +6.50 |
| metric=0 | 2761 | 5.143 % | 2.801 % | +2.343 pp | +7.90 |
| metric=1 | 4640 | 3.987 % | 2.301 % | +1.686 pp | +8.24 |
| metric=2 | 2785 | 3.124 % | 2.100 % | +1.024 pp | +3.97 |
| metric=3 | 3016 | 2.818 % | 2.303 % | +0.515 pp | +2.01 |
| mode=major | 7244 | 4.086 % | 2.817 % | +1.269 pp | +6.96 |
| mode=minor | 5958 | 3.407 % | 1.812 % | +1.595 pp | +9.81 |

## Formes locales des choix rares authentiques

| Statut dans le noyau K3 | Nombre | Part des choix rares |
|---|---:|---:|
| `incoming_step` | 409 | 81.96 % |
| `immediate_step_resolution` | 278 | 55.71 % |
| `immediate_neighbor` | 105 | 21.04 % |
| `immediate_passing` | 123 | 24.65 % |
| `no_incoming_step` | 90 | 18.04 % |
| `short_note_no_step_resolution` | 58 | 11.62 % |

## Résidus des interactions candidates

| Interaction | Observé | Attendu | Écart | z |
|---|---:|---:|---:|---:|
| `incoming_step` | 3.402 % | 2.196 % | +1.206 pp | +9.68 |
| `immediate_step_resolution` | 3.527 % | 2.133 % | +1.393 pp | +9.21 |
| `immediate_neighbor` | 7.692 % | 2.800 % | +4.892 pp | +11.73 |
| `immediate_passing` | 4.579 % | 3.006 % | +1.574 pp | +5.19 |
| `no_incoming_step` | 0.682 % | 0.364 % | +0.318 pp | +6.21 |
| `short_note_no_step_resolution` | 0.667 % | 0.467 % | +0.200 pp | +2.82 |
| `strong_metric` | 2.965 % | 2.206 % | +0.759 pp | +4.18 |
| `weak_metric` | 4.418 % | 2.487 % | +1.931 pp | +11.40 |

## Décision méthodologique

V5.7 sous-estime significativement les choix rares authentiques dans ses conditionnelles. Une pénalisation chromatique globale serait donc contraire au corpus. Il faut tester si la chaîne de Gibbs amplifie ces choix ou si l'écart aperçu sur BWV 108.6 est propre à cette pièce.

L'audit porte sur les choix authentiques et leurs alternatives locales.
La prochaine étape séparée est une campagne Gibbs multi-chorals, qui
mesurera une éventuelle amplification propre à la génération.
