# V5.1 — comparaison authentique / contrôle nul

## Résultat principal

Avec douze règles, le modèle authentique réduit la NLL de validation de
`1,145342`, contre `0,106239` pour le contrôle permuté : le gain authentique
est `10,78` fois plus grand.

| Données | NLL registre seul | NLL avec 12 règles | Gain |
|---|---:|---:|---:|
| Bach authentique | 2,594465 | 1,449123 | 1,145342 |
| choix permutés dans chaque pièce et voix | 2,594465 | 2,488226 | 0,106239 |

La permutation conserve les histogrammes de hauteurs, les ambitus et une part
du contexte tonal propre à chaque choral. Elle détruit en revanche
l'association entre le choix central et son K3. Les petits effets restants
dans le contrôle ne doivent donc pas être interprétés comme des règles locales
confirmées.

## Catalogue authentique compact

Le premier prédicat général pénalise un mouvement de plus de deux demi-tons
vers l'un ou l'autre bloc voisin. Il remplace les huit spécialisations apprises
par V5.0 et fournit un modèle à la fois plus court et meilleur.

Il ne s'agit pas d'une limite dure à un ton. Son poids `-1,654188` multiplie
les odds du candidat par `exp(-1,654188) ≈ 0,191`; les sauts restent possibles
et 21,0 % des choix authentiques testables activent la règle. Une seconde
pénalité `-1,301362` s'ajoute seulement au-delà de sept demi-tons.

Les règles suivantes :

- pénalisent plusieurs classes verticales dissonantes ;
- pénalisent un écart ordonné inférieur ou égal à un demi-ton entre voix
  adjacentes ;
- ajoutent une pénalité supplémentaire aux mouvements de plus de sept
  demi-tons ;
- préfèrent la classe verticale `7` ;
- pénalisent la conservation des classes `0` et `7` lorsque deux voix se
  déplacent avec le même signe ;
- préfèrent le mouvement mélodique de classe `1`.

Après gel, les deux clauses de conservation sont équivalentes aux patrons
numériques généraux des octaves et quintes parallèles. Elles ne figurent pas
dans les douze clauses du contrôle nul.

## Limites et décisions

- Un seul contrôle permuté ne calibre pas le maximum des 791 colonnes.
- La règle spécialisée positive
  `previous_ordered_gap_le(v0,v1)=2` doit être auditée avant interprétation.
- Les classes mélodiques et verticales sont des régularités numériques ; leurs
  noms musicologiques et leurs éventuelles exceptions restent à établir.
- Le Gibbs actuel valide l'identité entre évaluateur d'apprentissage et
  évaluateur de génération sur une grille dense. Il ne traite pas encore les
  tenues d'un rythme réel comme une variable unique.

V5.1 reste donc exploratoire. La prochaine barrière est une calibration par
plusieurs permutations, suivie d'une ablation réajustée de chaque règle.
