# Combinaisons et actions itérées

Cette petite base montre la sémantique complète de `COMBINATIONS` et
`FOR EACH` sur un exemple directement exécutable.

Un atelier possède trois candidats :

```text
[alice bob chloe]
```

`COMBINATIONS` engendre les trois binômes possibles sous forme de séquences.
Une prémisse ordinaire `$pair compatible true` filtre les choix : seuls
`alice`–`bob` et `bob`–`chloe` sont déclarés compatibles. `FOR EACH`
matérialise ensuite les deux membres de chaque binôme retenu.

```snarky
RULE generate_compatible_pairs
WHEN
    ($workshop candidates $candidates)
    COMBINATIONS $pair SIZE 2 FROM $candidates
    ($pair compatible true)
THEN
    ADD ($pair kind working_pair)
    ADD ($pair workshop $workshop)
    FOR EACH $member IN $pair
        ADD ($pair member $member)
    END_FOR_EACH
END
```

Exécution :

```sh
uv run python -m rulebases.runner small/combinations_foreach --trace
```

## Intérêt

- génération locale de choix finis dans une prémisse ;
- filtrage des choix par des faits ordinaires ;
- préservation de l'ordre dans `FiniteSequence` ;
- répétition atomique d'un bloc d'actions ;
- provenance reliant chaque binôme au fait de candidats et à son fait de
  compatibilité.

L'exemple reste volontairement minimal. Le cas d'usage plus substantiel visé
est celui des naked triples de Sudoku. Il demandera en complément les
prémisses générales `MEMBER` et `SIZE`, décrites dans
[`docs/constraints_propagation_and_search.md`](../../../docs/constraints_propagation_and_search.md).
