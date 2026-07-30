# V22 — décision sur le groupe partagé des mouvements de fondamentale

V22 remplace la table libre V21 de 288 coefficients par une seule
règle factorielle structurée : pour chaque mode, le poids dépend
uniquement de la classe dirigée du mouvement de fondamentale. Le
groupe possède donc 24 paramètres (2 modes × 12 mouvements).

## Résultat scientifique

- Quatre folds gelés : gain NLL moyen apparié `+0.013859` sur `32` chorals hors apprentissage ; `27/32` sont améliorés.
- IC bootstrap 95 % inter-folds : `[+0.009556, +0.018245]`.
- Stabilité : corrélation minimale des poids entre folds `0.854` ; `19/24` coefficients gardent le même signe dans les quatre folds.
- Réapprentissage sur 251 chorals, validation sur 50 : `0.829956` → `0.808481`, soit un gain `+0.021475` ; `46/50` chorals améliorés.
- IC bootstrap 95 % sur les 50 chorals : `[+0.017585, +0.025329]`.

Le groupe est donc **retenu**. Contrairement à V21, le gain se
réplique dans tous les folds et sur le grand découpage réservé.
Le partage des paramètres est bien la réduction de dimension qui
manquait à l'apprentissage conjoint.

## Règle apprise, sous forme lisible

Un poids positif signifie que le mouvement rend le choix local de
Bach plus probable relativement aux autres candidats disponibles ;
un poids négatif le rend moins probable. Les poids sont centrés dans
chaque mode : ils n'ont pas de sens comme probabilités isolées.

| Mouvement de fondamentale | Majeur | Mineur |
|---|---:|---:|
| maintien | -0.256 | -0.150 |
| 2de min. ascendante | +0.337 | +0.272 |
| 2de maj. ascendante | +0.325 | +0.306 |
| 3ce min. ascendante | -0.288 | -0.148 |
| 3ce maj. ascendante | -0.249 | -0.074 |
| 4te ascendante / 5te descendante | +0.427 | +0.377 |
| triton | +0.376 | +0.346 |
| 5te ascendante / 4te descendante | +0.228 | +0.246 |
| 3ce maj. descendante | -0.338 | -0.397 |
| 3ce min. descendante | +0.283 | +0.133 |
| 2de maj. descendante | -0.353 | -0.428 |
| 2de min. descendante | -0.492 | -0.482 |

Ce tableau est une seule règle structurée, pas 24 interdictions.
Ses contributions s'ajoutent aux autres facteurs avant la
normalisation conditionnelle MaxEnt.

## Séparation avec les contraintes

L'audit indépendant des prédicats à fréquence nulle a trouvé 40
lignes sans exception sur 251 + 50 chorals. Après suppression des
orientations symétriques et seuils emboîtés, elles se regroupent en
plusieurs schémas candidats :

1. absence de croisement soprano–ténor, frontière directionnelle
   alto–basse et espacement soprano–basse supérieur à un demi-ton ;
2. absence de septième majeure mélodique et de saut supérieur à
   l'octave au soprano, alto et ténor ;
3. absence d'arrivée en mouvement direct sur une seconde mineure
   entre alto–ténor et ténor–basse ;
4. absence de seconde mineure ou septième majeure conservée par
   mouvement direct entre deux voix ;
5. absence, beaucoup plus spécifique, d'un accord de septième
   majeure sur le degré chromatique +2.

Les quatre premiers ensembles sont des candidats à formaliser puis à tester
comme contraintes. Le cinquième doit rester un facteur doux tant
qu'une analyse enharmonique et tonale n'a pas exclu un artefact de
représentation. Les 23 prédicats retenus sont compilés dans Snarky
comme filtres d'ablation pré-test, sans statut `MUST`.

## Ablation générative

Sur dix chorals de validation, même état initial faisable,
même soprano, rythme et graine :

| Mesure | Bach | Socle | V22 | V22 + contraintes |
|---|---:|---:|---:|---:|
| Blocs triadiques | 50.87 % | 49.33 % | 47.07 % | 49.23 % |
| Dissonances/bloc faible | 1.032 | 1.101 | 1.172 | 1.055 |
| Dissonances/bloc fort | 0.357 | 0.611 | 0.688 | 0.654 |
| Basse hors gamme globale | 7.14 % | 10.59 % | 11.59 % | 10.58 % |

Les contraintes récupèrent une grande partie de la qualité
triadique et des dissonances faibles perdues par V22, mais
elles ne corrigent ni les dissonances fortes ni le
chromatisme de basse. Le prochain groupe doit donc relier
statut tonal de basse, force métrique et qualité d'accord,
sans modifier rétroactivement le groupe V22.
