# V24 — POC de génération par recherche Snarky

Ce POC n'utilise pas Gibbs pour générer. Les facteurs appris V24
pondèrent des variables de fenêtre K3. Les 23 prédicats V22 sans
exception en apprentissage et validation sont des contraintes
persistantes empiriques (et non des lois universelles). Snarky
alterne propagation, choix et rollback lorsque celui-ci est requis.

## Résultat

- Statut : `solved`.
- Nœuds explorés : `4`.
- Branches en échec : `0`.
- Décisions sur la branche solution : `3`.
- Événements `BACKTRACK` : `0`.
- Parcours : `depth_first`.
- Valeurs éliminées à la racine par propagation : `0`.
- Valeurs candidates avant/après propagation : `4646` / `4646`.
- Contraintes apprises persistantes : `23`.
- Instances locales de ces contraintes : `92`.
- Facteurs appris : `65`.
- Erreur maximale du score factoriel Snarky : `6.661e-16`.

Aucun retour arrière n'a été nécessaire et aucune valeur n'a été filtrée à la racine : la première branche pondérée est restée compatible jusqu'à la solution.

## Blocs

| Bloc | Offset | Métrique | Soprano | Alto | Ténor | Basse |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 1 | 71 | 66 | 62 | 47 |
| 1 | 1.00 | 3 | 71 | 66 | 62 | 47 |
| 2 | 1.50 | 0 | 71 | 66 | 62 | 47 |
| 3 | 2.00 | 1 | 71 | 59 | 59 | 47 |
| 4 | 2.50 | 0 | 71 | 59 | 59 | 47 |
| 5 | 3.00 | 2 | 78 | 66 | 62 | 59 |

## Éliminations par propagation

| Contrainte | Valeurs supprimées |
|---|---:|
| _aucune_ | 0 |

## Décisions de la solution

| # | Point de choix | Alternative | Poids |
|---:|---|---|---:|
| 1 | `apply_csp_choices:choose_csp_value:0[problem=learned_v24_snarky_harmonization,variable=v24_window_1]` | `SEQ[SEQ[71 66 62 47] SEQ[71 66 62 47] SEQ[71 66 62 47]]` | 1 |
| 2 | `apply_csp_choices:choose_csp_value:0[problem=learned_v24_snarky_harmonization,variable=v24_window_2]` | `SEQ[SEQ[71 66 62 47] SEQ[71 66 62 47] SEQ[71 59 59 47]]` | 0.502069 |
| 3 | `apply_csp_choices:choose_csp_value:0[problem=learned_v24_snarky_harmonization,variable=v24_window_3]` | `SEQ[SEQ[71 66 62 47] SEQ[71 59 59 47] SEQ[71 59 59 47]]` | 0.0026574 |

## Impasses et retours arrière

Aucune impasse n'a été rencontrée sur cette recherche.

## Limites de ce POC

Les blocs de bord sont conservés comme conditions aux limites ;
le soprano et le rythme sont donnés. Les domaines intérieurs sont
obtenus uniquement à partir des priors de registre et de tonalité
appris, sans recopier les voix intérieures de Bach.

Le petit domaine `top-pitches` est un échafaudage de validation,
pas encore la base générative finale. Une solution répétitive
indique une lacune du modèle appris ou du domaine, et non une
absence de propagation/backtracking dans Snarky.
