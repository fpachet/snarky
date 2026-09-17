# V32 — audit causal de la génération

Même BWV 108.6, même soprano, même rythme, même socle V29 et même
ordre de recherche. La seule différence est l'ajout des deux facteurs
séquentiels V32 appris sur le corpus.

## Cycles de deux notes attaquées

| Voix | Mesure | Bach | V29 | V32 |
|---|---|---:|---:|---:|
| Soprano | Retours ABA | 27.869 % | 27.869 % | 27.869 % |
| Soprano | Continuations ABAB | 6.667 % | 6.667 % | 6.667 % |
| Soprano | Runs ≥ 4 | 4.000 | 4.000 | 4.000 |
| Soprano | Longueur maximale | 4.000 | 4.000 | 4.000 |
| Alto | Retours ABA | 9.524 % | 25.397 % | 15.873 % |
| Alto | Continuations ABAB | 3.226 % | 16.129 % | 4.839 % |
| Alto | Runs ≥ 4 | 1.000 | 4.000 | 2.000 |
| Alto | Longueur maximale | 5.000 | 8.000 | 5.000 |
| Tenor | Retours ABA | 4.348 % | 28.986 % | 20.290 % |
| Tenor | Continuations ABAB | 0.000 % | 13.235 % | 4.412 % |
| Tenor | Runs ≥ 4 | 0.000 | 5.000 | 3.000 |
| Tenor | Longueur maximale | 3.000 | 6.000 | 4.000 |
| Bass | Retours ABA | 2.198 % | 37.363 % | 29.670 % |
| Bass | Continuations ABAB | 0.000 % | 13.333 % | 1.111 % |
| Bass | Runs ≥ 4 | 0.000 | 7.000 | 1.000 |
| Bass | Longueur maximale | 3.000 | 5.000 | 4.000 |

## Harmonie et basse

| Mesure | Bach | V29 | V32 |
|---|---:|---:|---:|
| Blocs triadiques | 56.122 % | 43.878 % | 40.816 % |
| Blocs forts non triadiques | 26.923 % | 46.154 % | 57.692 % |
| Dissonances par bloc fort | 0.462 | 0.808 | 1.077 |
| Dissonances par bloc faible | 0.875 | 0.917 | 0.972 |
| Mouvements chromatiques de basse | 29.348 % | 47.826 % | 50.000 % |
| Grands sauts de basse | 26.087 % | 1.087 % | 1.087 % |
| Basse hors gamme naturelle | 15.054 % | 26.882 % | 29.032 % |

V32 modifie `35` blocs et `45` attaques des voix inférieures par rapport à V29.

Cet audit mesure l'effet génératif ; il ne sert pas à réajuster
les poids V32.

## Écoute

- MusicXML : `harmonizer/generated/two_loop_full_v32_bwv108_6.musicxml`
- MIDI : `harmonizer/generated/two_loop_full_v32_bwv108_6.mid`
- MP3, piano acoustique :
  `harmonizer/generated/two_loop_full_v32_bwv108_6.mp3`

## Décision

Les facteurs V32 expliquent et corrigent bien le défaut séquentiel ciblé,
mais la génération V32 n'est pas promue comme meilleur modèle global. Le
choix local remplace les continuations interdites de fait par des alternatives
moins répétitives mais souvent moins harmoniques. Le prochain test doit donc
conserver ces facteurs comme groupe autonome et faire porter le backtracking
sur deux critères séparés :

1. une enveloppe de fréquence du groupe séquentiel apprise sur Bach ;
2. un plancher propre au groupe harmonique fort.

Une solution ne sera admise que si elle satisfait les deux. Cela évite qu'un
bon score global compense arbitrairement un très mauvais sous-score.
