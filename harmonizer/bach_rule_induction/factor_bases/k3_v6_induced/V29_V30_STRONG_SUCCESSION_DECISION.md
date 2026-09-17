# V29–V30 — décision sur les successions fortes

## V29 : succession forte × arrivée de basse

V29 définit une partition de 36 cellules sur les blocs forts : trois types de
sonorité précédente, trois types de sonorité courante et quatre tailles de
mouvement de basse. Une seule cellule est active par alternative.

Les `36/36` cellules dépassent les seuils de couverture sur 32 chorals et
1 039 blocs forts représentatifs. La confirmation gelée à `λ=0,6` sur 50
chorals donne :

- gain NLL moyen : `+0,011500` ;
- intervalle bootstrap 95 % : `[+0,008226 ; +0,014722]` ;
- chorals améliorés : `43/50`.

V29 est donc confirmé comme facteur explicatif local. Sa génération complète
est cependant un compromis :

| Mesure | Bach | V28 | V29 |
|---|---:|---:|---:|
| Blocs triadiques | 56,12 % | 45,92 % | 43,88 % |
| Blocs forts non triadiques | 26,92 % | 42,31 % | 46,15 % |
| Dissonances fortes | 0,462 | 0,808 | 0,808 |
| Demi-tons de basse | 29,35 % | 60,87 % | 47,83 % |
| Basse hors gamme naturelle | 15,05 % | 30,11 % | 26,88 % |

V29 réduit nettement le chromatisme de basse et ramène les sonorités fortes
véritablement résiduelles de quatre à trois. Il remplace néanmoins une partie
des triades par des accords nommés non consonants. Il n'est donc pas déclaré
meilleur modèle génératif sur la seule base de cette pièce.

## V30 : rôle fort résiduel × qualité de résolution

V30 croise les huit statuts résiduels forts V24 avec une résolution binaire.
Les `16/16` cellules sont couvertes sur les 181 blocs forts résiduels du train.

Le meilleur candidat de découverte, `λ=0,3`, n'est pas retenu :

- gain NLL moyen : `+0,000556` ;
- intervalle bootstrap 95 % : `[-0,003615 ; +0,004918]` ;
- chorals améliorés : `4/10`.

V30 est conservé comme résultat négatif reproductible. Il n'est ni exporté
dans la base factorielle canonique ni généré.

## Conclusion

Le succès prédictif de V29 et son résultat génératif mixte montrent que la
pseudo-vraisemblance locale et la qualité d'une solution complète doivent
rester deux critères distincts. La prochaine hypothèse devra raffiner la
classe `other_named_sonority` — notamment accords de septième communs contre
accords altérés — sans réintroduire une table de transitions illisible.

## Artefacts

- [Couverture V29](V29_STRONG_SUCCESSION_COVERAGE.md)
- [Confirmation V29](V29_STRONG_SUCCESSION_CONFIRMATION50.md)
- [Génération V29](TWO_LOOP_FULL_GENERATION_V29.md)
- [Audit génératif V29](V29_SNARKY_GENERATION_AUDIT.md)
- [Couverture V30](V30_JOINT_STRONG_RESOLUTION_COVERAGE.md)
- [Modèle de découverte V30](V30_JOINT_STRONG_RESOLUTION_MODEL.md)
