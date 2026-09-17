# V10–V11 — décision sur les licences contextuelles

## V10 : gain réel mais partiel

V10 ajoute 96 conjonctions génériques aux 954 facteurs V6. Les douze classes
d'intervalle reçoivent exactement le même vocabulaire : force métrique,
réarticulation, résolution par pas, passage, broderie et voix tenue. Aucune
classe n'est pré-étiquetée consonante ou dissonante.

L'induction sélectionne spontanément trois nouveaux facteurs : passage pour
les classes 9 et 10, et classe 7 sur temps fort. Avec 30 facteurs, la NLL de
validation atteint `0,757960`, contre `0,779783` pour V9.

Les audits génératifs confirment que ce n'est pas seulement un gain prédictif :

- à 6 sweeps, les blocs forts non triadiques baissent de `45,74 %` (V9) à
  `39,85 %` (V10), et les dissonances fortes de `0,743` à `0,607` ;
- à 30 sweeps, ils baissent de `39,93 %` à `36,62 %`, et les dissonances
  fortes de `0,606` à `0,539`.

V10 n'est cependant pas promu : la basse hors gamme reste à `13,62 %` contre
`7,14 %` chez Bach, et ses demi-tons à `33,07 %` contre `25,00 %`.

## V11 : résultat négatif utile

V11 ajoute 72 facteurs dont les classes tonales rares sont définies sur le
train seulement, séparément par voix et mode, au seuil empirique de `2 %`.
Avec un budget de 30 facteurs, aucun n'est sélectionné : V11 est exactement
V10.

Un contrôle à 45 facteurs améliore la NLL à `0,711052`, mais ne sélectionne
toujours aucun facteur tonal rare. Il réintroduit en revanche les secondes
soprano–alto positives aux rangs 34 et 37. Ce candidat n'est donc pas soumis
à un audit génératif : le mécanisme déjà causal de l'échec V9 réapparaît.

## Conclusion expérimentale

Les licences locales d'intervalle sont utiles et valident la direction
représentationnelle. Le résidu chromatique montre toutefois une différence
entre deux objectifs :

- la pseudo-vraisemblance choisit les facteurs qui prédisent le mieux chaque
  décision authentique ;
- la qualité générative exige aussi que les chaînes reproduisent les moments
  globaux de Bach.

La prochaine sélection de structure devra donc combiner le gain conditionnel
exact avec un terme de dérive générative mesuré sur train. Ajouter simplement
des facteurs ou augmenter leur budget est falsifié par V11. Iteration 2 reste
le checkpoint génératif de référence ; V10 devient le meilleur diagnostic
conditionnel compact.
