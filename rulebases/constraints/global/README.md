# Contraintes globales `NVALUE` et `ALL_DIFFERENT`

Cette base montre deux contraintes globales directement dans les prémisses
Snarky. Elles filtrent les domaines d'instanciation avant le matching, sans
appeler un solveur externe et sans introduire de choix ou de backtracking.

```text
NVALUE $count OF SEQ[$first $second $third]
ALL_DIFFERENT SEQ[$first $second $third]
```

Le premier scénario fixe `$count` à 1. Une première variable vaut `red` et
les deux autres hésitent entre `red` et `blue` : la propagation conserve
uniquement `SEQ[red red red]`.

Le second scénario forme un ensemble de Hall : les deux premières variables
ont le domaine `{1, 2}`, tandis que la troisième possède `{1, 2, 3}`.
`ALL_DIFFERENT` retire donc 1 et 2 du troisième domaine avant la jointure et
produit les deux permutations valides.

```sh
uv run python -m rulebases.runner constraints/global --trace
```

## Intérêt

- valider une interface générique de propagateur global ;
- tester les bornes de `NVALUE` et les ensembles de Hall bornés ;
- comparer chaque stratégie au matcher naïf, qui reste l'oracle sémantique ;
- préparer un futur langage de choix et de backtracking sans le cacher dans
  les conclusions Python.

`NVALUE` établit une borne inférieure sûre depuis les valeurs déjà forcées et
une borne supérieure depuis l'union des domaines. Les cas serrés `N = 1` et
`N = nombre de variables` déclenchent respectivement une intersection globale
et la propagation `ALL_DIFFERENT`.

`ALL_DIFFERENT` applique les singletons puis les ensembles de Hall de taille
au plus trois. Ce niveau couvre les paires et triplets utiles à Sudoku. Une
consistance généralisée par couplage biparti pourra être ajoutée au même
protocole si un benchmark montre que ce coût est amorti.
