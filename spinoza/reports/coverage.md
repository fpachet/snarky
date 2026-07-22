# Couverture de l'Éthique III

## État au 22 juillet 2026

| Couche | Couverture | Statut |
|---|---:|---|
| Préface | 1 / 1 | texte importé |
| Définitions initiales | 3 / 3 | texte importé |
| Postulats | 2 / 2 | texte importé |
| Propositions | 59 / 59 | texte et structure importés |
| Définitions d'affects | 48 / 48 | texte importé et définitions exécutables |
| Définition générale des affects | 1 / 1 | texte importé et définition exécutable |
| Manifestes de théorèmes | 59 / 59 | créés |
| Preuves historiques exécutables | 4 / 4 | reproduites |
| Propositions prouvées symboliquement | 59 / 59 | achevé |
| Manifestes de définitions finales | 49 / 49 | achevé |
| Cas des définitions finales | 101 / 101 | 51 positifs, 50 frontières négatives |

`source_imported` signifie que l'unité textuelle, ses sous-sections et ses
références numériques candidates sont disponibles. Cela ne signifie pas que sa
formalisation logique a été validée.

Le fichier texte continu `sources/ethique_III_appuhn_1913.txt` est contrôlé
contre le corpus structuré : chaque énoncé et chaque section importée doit y
figurer, et les tests comptent exactement 59 propositions et 48 définitions
d'affects.

## État systématique

1. E3P01–E3P59 : formalisation systématique exécutable achevée.
2. E3DA01–E3DA48 : formalisation des 48 énoncés définitionnels achevée.
3. E3DA-GENERAL : définition générale exécutable achevée.
4. E3DA*-EXP : les 27 explications annexes sont atomisées et exécutables.

Chaque proposition possède maintenant un manifeste systématique `proved` ou
`proved_with_interpretative_rules`. La règle réutilisable correspondant à une
proposition n'est activée qu'après sa preuve et reste interdite pendant le test
de cette même proposition.

Chaque définition finale suit le même principe de séparation : sa règle
textuelle est testée localement, tandis que sa règle validée reste interdite
dans son propre manifeste. Les 27 sections annexes « Explication » forment une
couche distincte : 27 manifestes, 44 règles et 54 cas en assurent maintenant
la couverture exécutable sans modifier la métrique canonique 48/48.
