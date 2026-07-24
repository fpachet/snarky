# Analyse harmonique inspirée de MusES

La thèse décrit deux familles de règles : formation d'accords à partir de
notes, puis analyse de leur succession. Ce noyau exécutable reproduit cette
séparation.

Le premier groupe calcule les intervalles modulo 12 à partir de hauteurs MIDI.
Le deuxième matérialise avec `COLLECT` l'ensemble des notes et reconnaît une
triade majeure ou mineure. Le dernier utilise `WINDOW` pour lier la séquence
ordonnée `SEQ[chord_1 chord_2 chord_3]`, puis reconnaît une progression
`ii–V–I`.

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
intervalles modulo 12, `COLLECT` produit les ensembles finis de notes et
`FiniteSequence`/`WINDOW` représentent les fenêtres de motifs sans type
musical ad hoc. `FRESH` pourrait nommer les accords s'ils étaient découverts
plutôt que fournis ; le scénario actuel n’en a pas besoin.

Les besoins encore ouverts sont musicaux plutôt que structurels : fenêtres de
longueur variable, métrique temporelle et gestion d'événements simultanés.
