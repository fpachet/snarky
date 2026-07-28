# V7 — décision sur les facteurs résiduels

## Modèle à six facteurs

Deux candidates stables par famille sont ajoutées au socle V6 :

- basse : seconde entrante et saut supérieur à deux demi-tons ;
- contexte vertical : intervalle 7 sur bloc fort et intervalle 8 sur bloc
  faible ;
- trajectoire : `{0,4,7} → {0,4,7,10}` et répétition de `{0,3,6,8}`.

Les 30 poids V6 restent gelés. La MAE des six moments train passe de
`0,045283` à `0,005009` et la NLL conditionnelle validation de `1,241166` à
`1,225843`.

L'audit génératif rejette néanmoins le modèle :

- à 6 sweeps, les grands sauts de basse diminuent de `4,30 points` par rapport
  à l'itération 2 et passent sous Bach ;
- à 30 sweeps, la diminution atteint `5,53 points`.

Les deux facteurs de basse encodent deux vues fortement redondantes de la même
préférence et surcontraignent conjointement le mouvement.

## Ablation V7-Sonority

Les deux facteurs de basse sont retirés. À 6 sweeps sur 50 chorals × 3 graines,
sept diagnostics sur dix se rapprochent de Bach :

- accords forts non triadiques : résidu `+0,02575 → −0,00108` ;
- dissonances fortes : `+0,03954 → −0,00039` ;
- dissonances faibles : `−0,09400 → −0,06194`.

À 30 sweeps, cependant, les quatre facteurs deviennent trop consonants et trop
triadiques : seulement trois diagnostics sur dix se rapprochent de Bach.
L'ablation brute n'est pas promue.

## Refit des quatre facteurs

Les quatre poids sont ensuite réappris séparément sur train. La MAE atteint
`0,005749`, mais les poids plus élevés déplacent indirectement la basse. Le
screening à 6 sweeps échoue avant campagne complète : les grands sauts
augmentent de `4,06 points` sur les dix pièces de développement.

## Décision

**Aucun modèle V7 n'est promu. L'itération 2 reste la référence.**

Le résultat scientifique est néanmoins positif :

1. les facteurs métriques et de transition contrôlent effectivement les
   accords étranges ;
2. leurs effets ne sont pas indépendants du mouvement de basse ;
3. un apprentissage par moments séparés double-compte certaines préférences ;
4. la prochaine méthode doit apprendre le petit groupe conjointement avec une
   pénalisation des diagnostics latéraux, ou utiliser une mise à jour
   multivariée réguliarisée incluant basse et harmonie.

## Paire d'écoute

Deux générations sur BWV 108.6 utilisent le même soprano, rythme, bord,
graine `5517` et `30` sweeps :

- [Itération 2 — MP3](../../../generated/v7_listening_comparison/01_iteration2_bwv108_6.mp3)
- [V7-Sonority expérimental — MP3](../../../generated/v7_listening_comparison/02_v7_sonority_bwv108_6.mp3)
- [Itération 2 — MusicXML](../../../generated/v7_listening_comparison/01_iteration2_bwv108_6.musicxml)
- [V7-Sonority — MusicXML](../../../generated/v7_listening_comparison/02_v7_sonority_bwv108_6.musicxml)

Cette paire sert à comprendre qualitativement l'effet des quatre facteurs.
Elle ne contredit pas leur rejet statistique à l'horizon long.
