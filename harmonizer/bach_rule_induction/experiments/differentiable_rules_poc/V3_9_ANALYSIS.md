# Analyse du POC V3.9 — comparaison avec DeepBach

## Générations libres

Deux générations canoniques de 160 ticks ont été auditées :

- seed 0, artefact doré déjà archivé ;
- seed 1, nouvelle exécution complète à 19 968 mises à jour.

Elles contiennent 101 attaques d'alto exploitables, mais aucune occurrence du
contexte très spécifique :

```text
alto source = classe 11
basse 2 → 4
mode majeur
```

Il est donc impossible d'estimer un taux de violation à partir de ce petit lot
libre. Le résultat correct est `0/0`, non « zéro erreur ».

## Sonde conditionnelle

Pour obtenir une comparaison ciblée, le réseau historique d'alto est interrogé
sur les 12 contextes du test Bach gelé. Il reçoit son contexte complet de 16
ticks à gauche et à droite, les trois autres voix et les métadonnées
historiques.

| Sous-ensemble | N | Résolutions Bach | Probabilité DeepBach moyenne | Résolution top-1 |
|---|---:|---:|---:|---:|
| tous | 12 | 10 | 0,9246 | 12/12 |
| `vii°6→I6` exact | 9 | 9 | 0,9351 | 9/9 |
| autres | 3 | 1 | 0,8931 | 3/3 |

La médiane globale vaut `0,9927` et la résolution est classée première dans
chaque contexte.

## Les deux exceptions sont instructives

Bach ne résout pas l'alto dans deux contextes non exacts :

| Pièce | Offset | P DeepBach résolution | P DeepBach choix de Bach |
|---|---:|---:|---:|
| `bwv359` | 53 | 0,9931 | 0,0035 |
| `bwv57.8` | 32 | 0,6863 | 0,0056 |

DeepBach a donc appris une préférence encore plus systématique que le corpus
local observé. Ces cas montrent pourquoi la formulation Snarky doit rester une
préférence graduée : transformer le patron en obligation dure effacerait des
exceptions authentiques de Bach.

## Limites

- Les poids DeepBach historiques ont été entraînés sur des augmentations du
  corpus complet, y compris les chorals aujourd'hui placés dans notre test.
  La sonde décrit le comportement du réseau ; ce n'est pas une évaluation
  indépendante de généralisation.
- Le port Keras 3 charge les tableaux de poids historiques sans conversion,
  mais sa certification numérique face à TensorFlow 1.1 reste à faire.
- Deux générations libres sont insuffisantes pour un phénomène aussi rare.

## Conséquence pour la boucle d'apprentissage

DeepBach n'indique pas ici une feature manquante : il connaît très fortement la
tendance. En revanche, ses désaccords avec les deux exceptions de Bach
fournissent exactement les cas à analyser pour découvrir un statut futur
expliquant quand la norme peut être suspendue.
