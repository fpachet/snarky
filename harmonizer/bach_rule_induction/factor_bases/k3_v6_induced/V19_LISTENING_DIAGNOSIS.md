# V19 — diagnostic après écoute

## Verdict

L'écoute experte de l'exemple BWV 108.6 signale de nombreuses fausses notes.
Ce verdict invalide toute promotion de V19 comme générateur musical, malgré
l'amélioration de plusieurs statistiques agrégées sur dix chorals.

V19 reste un résultat explicatif utile : le corpus sélectionne de manière
stable la préférence pour les triades complètes, particulièrement sur temps
fort. Mais cette règle est trop peu conditionnée pour déterminer **quelle**
triade convient à un endroit donné.

## Ce que les premières métriques ont masqué

Sur l'exemple effectivement écouté :

| Diagnostic | Bach | V19 |
|---|---:|---:|
| blocs triadiques | `56,12 %` | `47,96 %` |
| blocs forts non triadiques | `26,92 %` | `23,08 %` |
| dissonances de paires / bloc fort | `0,462` | `0,423` |
| dissonances de paires / bloc faible | `0,875` | `0,972` |
| dominante avec septième au premier renversement / bloc fort | `11,54 %` | `0 %` |
| demi-tons mélodiques à la basse | `29,35 %` | `32,61 %` |
| basse hors gamme naturelle globale | `15,05 %` | `16,13 %` |

La partition authentique contient 34 cellules chromatiques sur 392, contre 35
dans V19. Le problème n'est donc pas réductible au **nombre** de notes
chromatiques. Bach place les altérations dans des fonctions et des trajectoires
précises ; V19 ne représente que des préférences locales plus grossières.

La basse authentique emploie dix classes de hauteur dans cet extrait, tandis
que la basse V19 emploie les douze. Ce symptôme concorde avec l'impression
d'une basse chromatique sans direction.

## Cause structurelle

Le statut V19 répond seulement à :

> les quatre voix forment-elles une triade majeure ou mineure complète ?

Il ne répond pas à :

- quelle est la fondamentale ;
- quel est son degré dans la tonalité ;
- quelle qualité et quel renversement sont attendus à cet instant ;
- d'où vient l'accord et vers quel accord il se dirige ;
- quelle note chromatique est une sensible secondaire ou une altération
  fonctionnelle ;
- quelle dissonance est une note de passage, une broderie ou un retard
  correctement résolu.

Une triade chromatique arbitraire reçoit donc le même bonus de statut qu'une
tonique ou une dominante appropriée. Les profils tonals note par note ne
remplacent pas une relation harmonique entre les voix.

La pseudo-vraisemblance apprend en outre à remplacer une note au milieu d'un
contexte presque entièrement authentique. Pendant la génération, les trois
voix libres fournissent mutuellement des contextes déjà générés. Une grammaire
incomplète peut alors quitter rapidement les régions stylistiques observées
par Bach.

## Correction V20

Il ne faut pas augmenter le poids triadique ni corriger manuellement les
marginaux. La prochaine grammaire doit ajouter des **statuts déterministes et
lisibles**, puis laisser le corpus sélectionner leurs règles et leurs poids :

1. fondamentale relative à la tonique, qualité, renversement et complétude ;
2. statuts explicites des accords de septième usuels ;
3. transition de statut harmonique entre les trois blocs K3 ;
4. pour chaque note non harmonique : passage, broderie ou retard avec sa
   préparation et sa résolution ;
5. fonction chromatique de la basse conditionnée par le statut harmonique.

Ces statuts ne doivent pas être des états latents anonymes. Ils sont calculés
directement à partir des notes, de la tonalité déclarée, de la métrique et de
la fenêtre K3. Les poids restent appris par pseudo-vraisemblance sur le train.

Avant toute nouvelle écoute, V20 devra passer trois contrôles séparés :

- gain conditionnel et stabilité de structure ;
- adéquation des racines, qualités, renversements et transitions sur
  validation ;
- audit génératif multi-chorals, puis écoute experte.

Le test réservé reste fermé.
