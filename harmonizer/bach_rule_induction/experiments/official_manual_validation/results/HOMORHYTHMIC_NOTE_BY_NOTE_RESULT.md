# Harmonisation homorythmique note à note

## Protocole

- soprano imposé : `bach/bwv48.3`, sélectionné dans `train251` ;
- 36 attaques, toutes partagées par soprano, alto, ténor et basse ;
- mêmes durées dans les quatre voix ;
- un choix Snarky conjoint `(alto, tenor, bass)` par note du soprano ;
- aucun squelette, état harmonique caché, degré ou enchaînement d'accords
  imposé ;
- plages vocales apprises sur le corpus ;
- blocs verticaux filtrés par vocabulaire observable ;
- relations locales entre positions successives : pas de quintes ou octaves
  parallèles, pas de chevauchement, pas de quinte directe externe, au plus
  trois basses identiques consécutives ;
- l'ordre de branchement favorise mouvement conjoint et notes communes, mais
  ne modifie pas l'ensemble des solutions admissibles.

## Résultats

| Vocabulaire | Composition verticale | Nœuds | Backtracks | Audit `bach_empirical` |
|---|---:|---:|---:|---:|
| standard | 14 triades consonantes, 17 septièmes, 1 triade diminuée, 4 incomplètes | 40 | 3 | accepté, 1 dépassement |
| triades | 23 triades consonantes, 9 diminuées, 4 incomplètes | 42 | 5 | accepté, 0 dépassement |
| consonant | 23 majeures, 10 mineures, 3 incomplètes | 39 | 2 | accepté, 1 dépassement |

Pour les variantes `triades` et `consonant` :

- quintes parallèles : `0` ;
- octaves parallèles : `0` ;
- croisements et chevauchements : `0` ;
- plus longue répétition de basse : `1` ;
- déficit de mouvement conjoint de basse : respectivement `0.0571` et
  `0.0857`, très inférieur au seuil Bach gelé `0.49495`.

La variante consonante a un seul dépassement métrique non bloquant :
`unresolved_suspension_ratio=1`. Cette métrique détecte aussi certaines
configurations de quartes au-dessus de la basse ; elle ne signifie pas qu'une
septième a été autorisée, car le vocabulaire consonant les exclut toutes.

## Interprétation

L'expérience démontre qu'une harmonisation complète sans squelette est
possible avec la granularité demandée. Elle ne démontre pas encore que le
style de Bach est reproduit : le score MLE exact des 137 facteurs a été différé
car son évaluateur Python prend plusieurs minutes par feuille. Les exports sont
donc des candidats satisfaisant les contraintes locales et l'audit manuel
indépendant, pas encore des solutions certifiées au-dessus du seuil MLE.

L'ablation verticale indique la suite : conserver la ligne de base consonante,
puis réintroduire une famille dissonante à la fois avec ses règles locales de
préparation et résolution. En parallèle, l'évaluateur de facteurs doit être
compilé ou vectorisé avant de reconnecter le seuil global au backtrack.
