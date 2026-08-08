# Premier audit d'une partition complète

Cet audit compare le BWV 108.6 authentique et la génération Snarky V33 qui
emploie son soprano et son rythme. Les deux partitions ont 98 tranches et sont
évaluées avec exactement la même base `official_manual`.

| Mesure | Bach authentique | Génération V33 |
|---|---:|---:|
| score des cinq facteurs actuels | 14,724 | 25,525 |
| chevauchements détectés | 6 | 1 |
| sensibles non résolues détectées | 8 | 12 |
| suspensions non résolues détectées | 16 | 26 |
| répétition maximale alto | 3 | 8 |
| répétition maximale ténor | 4 | 6 |
| saut maximal ténor | 10 | 16 |

## Interprétation

Le score factoriel actuel classe à tort V33 au-dessus de Bach. Ce n'est pas un
échec du mécanisme Snarky : seuls cinq facteurs sont pondérés, et la récompense
des résolutions de sensible domine leur somme. Les règles non pondérées
signalent pourtant deux défauts audibles de V33 : davantage de suspensions
non résolues et des répétitions beaucoup plus longues aux voix intérieures.

Le profil `pedagogical_strict` rejette les deux partitions (40 violations
dures pour V33, 41 pour Bach). C'est attendu : ce profil traite volontairement
des préférences comme des interdictions et les détecteurs de suspension et de
compensation ne connaissent pas encore toutes les exceptions contextuelles.
Il sert aux exercices stricts, pas à définir empiriquement Bach.

La conclusion correcte est donc :

1. le langage sait représenter diagnostics, facteurs purs et contradictions ;
2. le moteur sait utiliser une contradiction pour backtracker ;
3. les douze règles ont une parité différentielle de 12/12 sur le manuel ;
4. la base n'est pas encore une fonction d'acceptation complète du style.

La prochaine expérience doit calibrer sur le corpus les taux ou budgets par
longueur pour répétitions, suspensions, sauts, notes communes et mouvement
contraire, en gelant ces seuils avant l'évaluation du split test.
