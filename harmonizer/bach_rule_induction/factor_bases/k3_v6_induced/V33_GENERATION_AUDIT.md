# V33 — audit de l'ablation par contraintes fortes

Même BWV 108.6, même soprano, même rythme, même modèle V29 et mêmes
facteurs séquentiels V32. V33 ajoute seulement deux interdictions
contextuelles : `triad_plus_unlicensed` et `other_unlicensed` sur
les blocs forts.

## Résultat principal

| Système | Non licenciés forts | Triadiques | Forts non triadiques | Dissonances fortes |
|---|---:|---:|---:|---:|
| Bach | 1 / 25 | 56.122 % | 26.923 % | 0.462 |
| V29 | 3 / 25 | 43.878 % | 46.154 % | 0.808 |
| V32 | 5 / 25 | 40.816 % | 57.692 % | 1.077 |
| V33 | 0 / 25 | 42.857 % | 50.000 % | 0.885 |

## Cycles ABAB

| Voix | Bach | V29 | V32 | V33 |
|---|---:|---:|---:|---:|
| Alto | 3.226 % | 16.129 % | 4.839 % | 1.613 % |
| Tenor | 0.000 % | 13.235 % | 4.412 % | 4.412 % |
| Bass | 0.000 % | 13.333 % | 1.111 % | 0.000 % |

## Recherche

- Nœuds : `298`.
- Backtracks : `66`.
- Alternatives retirées directement : `71`.
- Rejets par propagation en avant : `1481`.
- Score : `-0.779027` pour un seuil de `-1.367214`.

## Statut scientifique

Cette expérience est une ablation stricte, pas une nouvelle règle
de Bach : le corpus contient lui-même ces deux statuts. Son rôle
est de vérifier si leur suppression explique causalement les
mauvaises sonorités de V32. Une version promouvable devra remplacer
l'interdiction absolue par une enveloppe ou un budget appris.

## Écoute

- MusicXML : `harmonizer/generated/two_loop_full_v33_bwv108_6.musicxml`
- MIDI : `harmonizer/generated/two_loop_full_v33_bwv108_6.mid`
- MP3, piano acoustique : `harmonizer/generated/two_loop_full_v33_bwv108_6.mp3`

## Décision

L'ablation est causalement positive : les cinq statuts visés
disparaissent, les dissonances fortes baissent de `1,077` à
`0,885` par bloc et les blocs forts non triadiques de `57,69 %`
à `50 %`. La propagation à un pas réduit la recherche à 298
nœuds et permet 66 backtracks effectifs.

Elle n'est toutefois pas promue. Bach contient ces statuts à un
taux global de `10,999 %` dans le train et en contient un dans
BWV 108.6. La prochaine version devra apprendre un budget de
groupe conditionnel à la longueur et laisser Snarky choisir où
dépenser ce budget, tout en maintenant un plancher harmonique
séparé.
