# Date du lendemain

Cette base calcule la date qui suit une date donnée en séparant les étapes
qu'emploierait un raisonnement humain :

1. déterminer la longueur du mois courant ;
2. avancer dans le mois, changer de mois ou changer d'année ;
3. publier les trois composantes du résultat.

Le scénario fourni calcule d'abord que 2024 est bissextile, puis le lendemain
du 29 février 2024 et obtient le 1er mars 2024.

## Intérêt

Ce n'est pas seulement un test de calcul. La base exerce les groupes de règles,
les résultats intermédiaires, `LET`, les comparaisons et le contrôle par point
fixe. Elle constitue un exemple compact de résolution explicable.

```sh
uv run python -m rulebases.runner thesis/tomorrow_date
```

## Extension utilisée

La base utilise désormais le prédicat entier
`DIVISIBLE $year BY 4|100|400`. Le fait `(2024 leap true)` est entièrement
dérivé par les règles ; il n'est plus fourni dans les données.

`FRESH` permettrait aussi de nommer plusieurs requêtes simultanées, mais il
n'est pas nécessaire au scénario actuel : `current` et `tomorrow` sont des
identifiants explicites.
