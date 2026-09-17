# V6 — suite d'écoute de l'apprentissage des poids

## Protocole

Les quatre générations utilisent exactement :

- `bach/bwv108.6` ;
- le soprano, le rythme, les tenues et les blocs de bord de Bach ;
- la graine `1729` ;
- `30` sweeps Gibbs ;
- les mêmes 30 facteurs ;
- le même rendu piano FluidSynth.

Seuls les poids changent. L'exemple permet d'entendre une trajectoire
d'apprentissage, mais il ne remplace pas les audits multi-chorals et
multi-graines.

## Fichier continu

[`05_v6_learning_suite.mp3`](../../../../generated/v6_learning_suite/05_v6_learning_suite.mp3)
enchaîne :

| Début | Version | Rôle |
|---:|---|---|
| `0:00.00` | Bach original | référence |
| `0:41.65` | V6 conditionnel | poids appris sur les choix authentiques |
| `1:23.30` | V6 moments train64 | contraste `E_Bach[f]−E_Gibbs[f]` |
| `2:04.95` | V6 multivarié, itération 1 | projection de dix diagnostics |
| `2:46.60` | V6 multivarié, itération 2 | Jacobien réestimé, pas borné à `0,15` |

Un silence de `1,5` seconde sépare les versions. Chaque extrait dure
`40,15` secondes et respecte `♩=84`.

## Extraits séparés

- [Bach original](../../../../generated/v6_learning_suite/00_bach_original.mp3)
- [V6 conditionnel](../../../../generated/v6_learning_suite/01_v6_conditional.mp3)
- [V6 moments train64](../../../../generated/v6_learning_suite/02_v6_train64_moments.mp3)
- [V6 multivarié, itération 1](../../../../generated/v6_learning_suite/03_v6_multimetric_iteration1.mp3)
- [V6 multivarié, itération 2](../../../../generated/v6_learning_suite/04_v6_multimetric_iteration2.mp3)

Le SoundFont disponible ne contient pas le programme General MIDI `choir`.
FluidSynth lui substitue donc le même piano dans les cinq extraits. Cette
substitution est constante et ne biaise pas leur comparaison.

## Exemple final

- [MusicXML MuSES](../../../../generated/v6_learning_suite/04_v6_multimetric_iteration2.musicxml)
- [MusicXML avec mise en page source](../../../../generated/v6_learning_suite/04_v6_multimetric_iteration2_source_layout.musicxml)
- [MIDI](../../../../generated/v6_learning_suite/04_v6_multimetric_iteration2.mid)
- [MP3](../../../../generated/v6_learning_suite/04_v6_multimetric_iteration2.mp3)

## Ce que montre cet exemple unique

| Mesure | Bach | Conditionnel | Moments 64 | Multi 1 | Itération 2 |
|---|---:|---:|---:|---:|---:|
| Demi-tons de basse | 29,35 % | 47,83 % | 30,43 % | 32,61 % | 25,00 % |
| Répétitions de basse | 0,00 % | 3,26 % | 4,35 % | 3,26 % | 6,52 % |
| Basse hors gamme globale | 15,05 % | 22,58 % | 11,83 % | 12,90 % | 7,53 % |
| Blocs triadiques | 56,12 % | 43,88 % | 41,84 % | 35,71 % | 41,84 % |
| Dissonances par bloc fort | 0,462 | 0,462 | 0,808 | 0,538 | 0,462 |
| Dissonances par bloc faible | 0,875 | 1,167 | 1,125 | 1,194 | 1,181 |

L'itération 2 corrige ici les dissonances fortes et les mouvements
chromatiques de basse, mais produit davantage de répétitions de basse et
reste trop dissonante sur temps faible. L'amélioration n'est donc pas
monotone sur chaque tirage.

## Quel modèle est « le meilleur » ?

L'itération 2 est le meilleur checkpoint **génératif global** disponible :
sur 50 chorals, elle réduit de cinq à deux le nombre de diagnostics dont
l'écart avec Bach est stable. Elle n'est cependant pas un modèle final :

- le modèle conditionnel conserve la meilleure NLL locale (`1,048935`,
  contre `1,241166` pour l'itération 2) ;
- deux résidus génératifs subsistent sur l'audit large ;
- un tirage isolé peut régresser sur certaines mesures ;
- le test final reste scellé ;
- la comparaison contrôlée avec DeepBach reste à exécuter.

## Optimisations suivantes

1. Sérialiser les chaînes persistantes entre itérations pour éviter un nouveau
   burn-in complet.
2. Apprendre et auditer avec un contrat explicite de mélange Gibbs, puis
   vérifier la convergence à plusieurs profondeurs.
3. Automatiser les petits pas et l'arrêt train par région de confiance, sans
   choisir une nouvelle correction après lecture répétée de la validation.
4. Traiter l'apprentissage comme un problème multiobjectif : qualité
   générative, NLL conditionnelle et amplitude des déplacements.
5. Stabiliser le Jacobien par analyse de conditionnement, ridge et bootstrap
   avant de conclure qu'une feature manque.
6. N'étendre la grammaire que si un résidu robuste n'est pas contrôlable par
   les 30 facteurs. Les deux candidats actuels sont la répétition attaquée de
   basse et l'empreinte `{0,3,6,8}` sur temps faible.
7. Comparer le checkpoint gelé à Bach et DeepBach sur le même banc
   multi-graines, avec audit automatique et écoute en aveugle.
