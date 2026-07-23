# Mutations et prémisses existentielles

Snarky supporte une mémoire de travail mutable au moyen de `REMOVE`, ainsi que
les prémisses corrélées `EXISTS` et `NOT EXISTS`. Ces fonctionnalités sont des
`MODERN_EXTENSION` conçues pour les systèmes de production et validées par le
cas d’étude Sudoku.

## Suppression d’un fait

La syntaxe de `REMOVE` est symétrique à celle de `ADD` :

```text
RULE consume
WHEN
    ($item state pending)
THEN
    REMOVE ($item state pending)
    ADD ($item state done)
END
```

Un statut explicite peut être indiqué après une apostrophe. Retirer un fait
absent est une non-opération déterministe.

Toutes les actions d’une activation sont d’abord instanciées. Elles sont
ensuite appliquées dans leur ordre textuel avant que le moteur teste une
condition d’arrêt ou sélectionne une autre activation.

## Journal de mutations

Chaque ajout ou retrait effectif produit un `InferenceEvent` contenant :

- un numéro de séquence ;
- le type `add` ou `remove` ;
- le fait concerné ;
- le groupe et la règle ;
- la substitution ;
- les faits prémisses ;
- le cycle.

Le journal est conservé même lorsqu’un fait quitte la mémoire. Il permet donc
de rejouer une résolution et d’expliquer une élimination, contrairement à une
simple photographie du point fixe.

`GroupRunResult` expose `added_facts`, `removed_facts`, `events`, `changed` et
`mutation_count`. Le mode `FIRST_CHANGE` s’arrête après toute mutation
effective, ajout ou retrait.

## Réfaction et index

Une suppression est enregistrée dans l’index partagé puis appliquée en lot
avant l’instanciation suivante. Une désynchronisation non incrémentale provoque
toujours une reconstruction sûre. Les stratégies naïve, indexée et semi-naïve
conservent ainsi les mêmes résultats observables.

La réfraction est liée à l’activation continûment valide :

- retirer un fait support expire les activations qui en dépendaient ;
- ajouter un fait ne réévalue que les activations négatives dont une prémisse
  peut matcher sa signature ;
- un bloc `NOT EXISTS` réduit à une prémisse factuelle installe implicitement
  un bloqueur corrélé : le fait ajouté expire directement les seules
  substitutions qu’il bloque, sans réinstancier la règle entière ;
- les blocs négatifs composés conservent une réévaluation exhaustive indexée,
  utilisée comme chemin de repli sémantiquement sûr ;
- une activation ayant cessé d’exister peut donc redevenir éligible plus
  tard.

Cette sémantique est plus générale qu’une mémorisation permanente du couple
`(règle, substitution)`.

## `EXISTS` et `NOT EXISTS`

Un bloc existentiel contient une conjonction locale :

```text
RULE single_candidate
WHEN
    ($cell candidate $value)
    NOT EXISTS
        ($cell candidate $other)
        $other != $value
    END_EXISTS
THEN
    ADD ($cell solved $value)
END
```

Les variables liées avant le bloc sont visibles à l’intérieur. Les variables
introduites dans le bloc sont locales et ne peuvent pas être utilisées après
`END_EXISTS`. Dans un bloc existentiel, une comparaison utilisant une variable
qui n’a pas encore été liée est rejetée au parsing ou à la construction de la
règle. Au niveau principal, le comportement historique est conservé : une
comparaison prématurée échoue simplement lors de l’instanciation.

`EXISTS` conserve les faits de son premier témoin déterministe dans les
supports de provenance. `NOT EXISTS` ne crée aucune liaison et ne confond pas
l’absence avec le statut explicite `INEXISTANT`.

Les résultats de recherche de témoin sont mémorisés pour un snapshot exact de
la mémoire de travail. Tout ajout ou retrait effectif invalide ce cache.

Les constructeurs Python équivalents sont `exists(...)` et
`not_exists(...)`.

## Limites

`REMOVE` porte sur un fait ground exactement instancié. Snarky ne fournit pas
encore :

- de modification partielle d’un terme ;
- de création de symboles frais ;
- de vérité conditionnelle ou de retour arrière ;
- de maintenance automatique des justifications d’un fait dérivé lorsque ses
  prémisses sont retirées.

Le journal conserve l’histoire, mais il ne constitue pas encore un système
complet de maintenance de vérité.
