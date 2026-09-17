# Analyse du POC V2.4 — ablation conjointe du catalogue SATB

## Question

Les sept règles récupérées sont-elles seulement des descriptions redondantes,
ou apportent-elles chacune une information prédictive dans un même modèle ?

Le V2.4 ajuste conjointement :

1. saut mélodique supérieur à l'octave ;
2. triton mélodique ;
3. chevauchement de voix adjacentes ;
4. octaves ou unissons parallèles ;
5. quintes parallèles ;
6. mouvement direct vers octave ou unisson ;
7. mouvement direct vers quinte.

Le socle de nuisance conserve tessiture, direction, sauts génériques, harmonie
locale et espacement lisse. Son seuil `> 12` est retiré afin que la règle de
grand saut soit mesurée explicitement.

## Gain conjoint

| Données | NLL validation socle | NLL avec sept règles | Gain |
|---|---:|---:|---:|
| Chorals authentiques | 1,355250 | 1,287062 | 0,068188 |
| Contrôle permuté | 2,462670 | 2,456363 | 0,006307 |

Le gain authentique est environ 10,8 fois le gain du contrôle. Son excès par
rapport au contrôle est `0,061881` NLL par décision.

Le contrôle n'est pas parfaitement plat : la permutation conserve
l'histogramme de hauteurs et le vocabulaire tonal de chaque pièce. Les règles
mélodiques peuvent donc encore résumer une partie de cette structure. Ce
résultat confirme pourquoi leur sélection V2.2 exigeait une encoche locale et
pas seulement un poids négatif.

## Poids conjoints sur les chorals authentiques

| Règle | Soprano | Alto | Ténor | Basse |
|---|---:|---:|---:|---:|
| Grand saut | -0,991 | -0,898 | -0,902 | -1,150 |
| Triton | -1,264 | -1,172 | -0,883 | -0,990 |
| Overlap | -1,106 | -0,824 | -0,558 | -0,531 |
| Octaves parallèles | -2,288 | -2,442 | -2,578 | -2,777 |
| Quintes parallèles | -2,232 | -2,367 | -2,132 | -2,562 |
| Direct vers octave | -1,138 | — | — | — |
| Direct vers quinte | -0,962 | — | — | — |

Toutes les règles ont le signe d'un évitement. Les mouvements directs sont
évalués sur les décisions de soprano, conformément au protocole qui les a
induits ; les zéros des voix intérieures ne sont pas des poids appris.

## Ablation individuelle

Chaque poids de règle est mis à zéro à tour de rôle sans réajuster les autres
poids. Une pénalité positive signifie que la colonne porte encore de
l'information dans le catalogue conjoint.

| Règle neutralisée | Pénalité NLL validation |
|---|---:|
| Octaves ou unissons parallèles | +0,028443 |
| Quintes parallèles | +0,025060 |
| Overlap | +0,007697 |
| Triton mélodique | +0,005871 |
| Grand saut | +0,002917 |
| Direct vers quinte | +0,000836 |
| Direct vers octave | +0,000501 |

Les sept pénalités sont positives. Les mouvements directs ont une contribution
plus faible, ce qui est cohérent avec leur portée limitée aux voix extrêmes et
leur recouvrement partiel avec les parallèles.

Dans le contrôle, les pénalités des deux parallèles sont
`+0,000048` et `-0,000045`, donc pratiquement nulles, contre `+0,053503` au
total dans les chorals authentiques.

## Ce qui est établi

1. Le petit catalogue améliore nettement la vraisemblance conditionnelle sur
   validation.
2. Aucune des sept colonnes n'est totalement redondante dans le modèle
   authentique.
3. Les deux règles de parallèles portent l'essentiel du gain propre et cet
   effet disparaît dans le contrôle permuté.
4. Les règles mélodiques capturent à la fois de l'ordre séquentiel et une part
   de structure tonale conservée par le contrôle.
5. Une base compacte de règles locales explique donc une fraction mesurable,
   mais certainement pas toute la connaissance chorale.

## Limites

- L'ablation neutralise un poids ajusté sans réestimer les autres. Elle mesure
  une contribution conditionnelle fixe, pas la capacité du modèle restant à
  compenser la règle absente.
- Les poids sont propres à chaque voix ; un futur modèle hiérarchique devrait
  partager une moyenne globale avec des écarts par voix.
- L'évaluation reste une tâche locale de choix de hauteur et non encore une
  génération chorale complète.
- Le test final reste scellé.

## Suite

La prochaine étape statistique est une ablation avec réajustement, plus chère,
au moins pour les groupes `mélodie`, `overlap`, `parallèles` et `direct`.
Ensuite, le premier véritable test des obligations demandera des faits de
statut explicites : tonalité locale, sensible, septième et cadence.
