# Version simple

Cette version conserve le premier noyau Snarky du problème. Le singe est
affamé, la caisse est près de la fenêtre et les bananes sont au centre. Quatre
règles exécutent un chemin entièrement déterminé :

1. marcher jusqu’à la caisse ;
2. pousser la caisse sous les bananes ;
3. monter sur la caisse ;
4. prendre les bananes.

```sh
uv run python -m rulebases.runner thesis/monkey_bananas/simple --trace
```

Cette base est utile comme test compact de mutations atomiques et de
provenance. Elle n’engendre aucun sous-but et n’utilise pas MEA ; ce n’est donc
pas encore un planificateur.
