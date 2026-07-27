# Statuts tonals primitifs

## Portée actuelle

Le corpus historique contient exactement une tonalité notée par choral. Les
quatre parties portent toujours la même indication et aucune modulation de
signature n'est encodée. Le terme `local` désigne donc provisoirement la
tonalité globale déclarée par la partition.

Cette approximation est acceptable pour un premier benchmark de redécouverte,
mais ne représente pas les tonicisations ni les modulations sans changement
de signature.

## `global_key_tonic_pc`

- **Domaine :** entier `0..11`.
- **Définition :** classe MIDI de la tonique de l'objet `music21.key.Key`
  déclaré dans les quatre parties.
- **Provenance :** MusicXML historique, sans analyse automatique.
- **Valeur manquante :** la pièce est exclue de l'expérience tonale.

## `global_key_mode`

- **Domaine :** `major | minor`.
- **Définition :** mode déclaré par le même objet tonal.
- **Provenance :** MusicXML historique.

## `tonic_relative_semitone`

```text
(midi_pitch - global_key_tonic_pc) modulo 12
```

- **Domaine :** entier `0..11`.
- **Interprétation :** distance chromatique à la tonique.
- **Attention :** ce n'est pas encore un degré diatonique orthographié.

## `leading_tone`

```text
tonic_relative_semitone == 11
```

Le statut est vrai pour la note située un demi-ton sous la tonique, y compris
la sensible altérée du mode mineur. Il est calculé sans consulter la note
suivante et n'encode donc pas sa résolution.

## `resolves_up_by_semitone`

```text
next_midi_pitch == current_midi_pitch + 1
```

Ce fait décrit le résultat d'une décision et ne doit pas être fourni comme
contexte au mineur. La première expérience l'utilise comme conclusion
candidate, testée symétriquement pour les douze classes relatives.

## Ce qui manque encore

- orthographe originale et degré diatonique complet ;
- tonalité locale inférée lors des tonicisations ;
- rôle harmonique de l'accord source ;
- statut cadentiel ;
- exceptions de résolution dans les voix intérieures ;
- distinction note structurelle / ornementale.

Ces faits seront ajoutés seulement si les exceptions du premier scan montrent
qu'ils séparent des cas autrement indiscernables.

## Premier ajout guidé par les exceptions

Le V3.2 a sélectionné le contexte numérique :

```text
voix == ténor
AND classe_source_voix == 11
AND classe_source_basse == 7
AND classe_cible_basse == 8
```

La résolution vaut `25/25` au train et `11/11` en validation dans les chorals
mineurs, contre `0/8` et `0/2` dans les chorals majeurs. Le V3.3 ajoute donc
`global_key_mode` à la clause, sans inventer de feature harmonique opaque.

Ce cas constitue le premier exemple complet de la boucle :

```text
règle agrégée → exceptions structurées → statut minimal explicite
→ règle plus précise
```
