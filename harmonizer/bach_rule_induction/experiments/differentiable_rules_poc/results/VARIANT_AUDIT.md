# Audit des variantes et partage groupé

## Résultat

- Ancien partage : 246/53/53.
- Nouveau partage conservateur : 251/50/51.
- Groupes de soprano dupliqués : 10 (21 pièces).
- Groupes de soprano traversant l'ancien partage : 6.
- Groupes traversant le nouveau partage : 0.
- Le nouveau test contient 51 pièces, toutes déjà réservées au test historique et jamais promues depuis train ou validation.

## Définition d'une variante

Deux pièces appartiennent au même groupe lorsque la suite exacte des
durées quantifiées et des intervalles mélodiques de soprano est
identique. La hauteur absolue est ignorée, ce qui rend le test invariant
par transposition. Pour la tâche soprano-conditionnée, cette définition
est volontairement plus prudente qu'une identité de l'harmonisation.

## Déplacements conservateurs

| Pièce | Ancien | Nouveau |
|---|---|---|
| `bach/bwv176.6` | validation | train |
| `bach/bwv20.7` | validation | train |
| `bach/bwv244.15` | test | train |
| `bach/bwv244.54` | validation | train |
| `bach/bwv327` | test | validation |
| `bach/bwv398` | validation | train |

## Groupes qui traversaient l'ancien partage

- `bach/bwv176.6` (validation), `bach/bwv280` (train)
- `bach/bwv197.7-a` (train), `bach/bwv398` (validation)
- `bach/bwv20.11` (train), `bach/bwv20.7` (validation)
- `bach/bwv244.15` (test), `bach/bwv244.17` (train), `bach/bwv244.44` (train)
- `bach/bwv244.54` (validation), `bach/bwv270` (train)
- `bach/bwv326` (validation), `bach/bwv327` (test)

Le test est construit sans consulter aucune métrique de modèle. Un
groupe est déplacé vers la partition la plus anciennement exposée :
`train` avant `validation`, puis `test`. Aucun élément anciennement
vu en train ou validation ne peut donc entrer dans le nouveau test.
