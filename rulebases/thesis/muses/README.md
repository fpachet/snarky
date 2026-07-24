# Analyse harmonique inspirée de MusES

La thèse décrit deux familles de règles : formation d'accords à partir de
notes, puis analyse de leur succession. Ce noyau exécutable reproduit cette
séparation.

Le premier groupe calcule les intervalles modulo 12 à partir de hauteurs MIDI.
Le deuxième matérialise avec `COLLECT` l'ensemble des notes et reconnaît une
triade majeure ou mineure. Le dernier reconnaît une progression `ii–V–I` dans
trois accords liés par `next`.

## Intérêt

- deux niveaux de représentation, notes puis accords ;
- appel ordonné de groupes de règles ;
- reconnaissance de motifs dans une séquence ;
- provenance d'une analyse musicale de haut niveau.

```sh
uv run python -m rulebases.runner thesis/muses
```

## Extensions utilisées et besoin restant

Les hauteurs ne sont plus normalisées manuellement : `%` calcule les
intervalles modulo 12, et `COLLECT` produit les ensembles finis de notes.
Une version musicale plus complète demanderait encore un type natif de
séquence avec fenêtres de motifs. `FRESH` pourrait nommer les accords si ceux-ci
étaient découverts plutôt que fournis ; le scénario actuel n’en a pas besoin.

Ces opérateurs seraient généraux et serviraient aussi à l'analyse de textes,
de traces et de séries temporelles symboliques.
