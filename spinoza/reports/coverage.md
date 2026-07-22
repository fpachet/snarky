# Couverture de l'Éthique III

## État au 22 juillet 2026

| Couche | Couverture | Statut |
|---|---:|---|
| Préface | 1 / 1 | texte importé |
| Définitions initiales | 3 / 3 | texte importé |
| Postulats | 2 / 2 | texte importé |
| Propositions | 59 / 59 | texte et structure importés |
| Définitions d'affects | 48 / 48 | texte importé |
| Définition générale des affects | 1 / 1 | texte importé |
| Manifestes de théorèmes | 59 / 59 | créés |
| Preuves historiques exécutables | 4 / 4 | reproduites |
| Propositions prouvées symboliquement | 32 / 59 | en cours |

`source_imported` signifie que l'unité textuelle, ses sous-sections et ses
références numériques candidates sont disponibles. Cela ne signifie pas que sa
formalisation logique a été validée.

Le fichier texte continu `sources/ethique_III_appuhn_1913.txt` est contrôlé
contre le corpus structuré : chaque énoncé et chaque section importée doit y
figurer, et les tests comptent exactement 59 propositions et 48 définitions
d'affects.

## Ordre de poursuite

1. E3P01–E3P32 : formalisation systématique exécutable achevée.
2. E3P33–E3P36 : réciprocité, gloire et souvenir de la jouissance.
3. E3P37–E3P44 : désir, haine et transformation de la haine en amour.
4. E3P45–E3P52 : transfert social, association et étonnement.
5. E3P53–E3P59 : considération de soi, envie, diversité et affects actifs.

Pour chaque proposition, le fichier `theorems/E3Pxx.yaml` doit passer de
`source_imported` à `candidate`, puis à `proved`, `not_proved` documenté ou
`proved_with_interpretative_rules`. La règle réutilisable correspondant à une
proposition n'est activée qu'après sa preuve et reste interdite pendant le test
de cette même proposition.
