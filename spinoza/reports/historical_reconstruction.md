# Reconstruction historique de Spinolog

## Périmètre

La source historique est la présentation de Michel Gondran,
`docs/Gondran.ppt`, datée de 2006 et décrivant un travail réalisé en 1987 avec
Fabrice Cavarretta, d'abord en SNARK puis en BOOJUM. Les diapositives 10 à 12
présentent la base ; les diapositives 14 à 17 détaillent E3P19, E3P21, E3P22 et
E3P33.

La reconstruction compte 21 règles exécutables. Elle conserve séparément deux
formes non exécutables et n'ajoute pas silencieusement de sémantique pour
`Créer(z)`.

## Résultats reproduits

| Théorème | Cas | But | Profondeur minimale |
|---|---|---|---:|
| E3P19 | destruction | `(x0 est triste)` | 2 |
| E3P19 | conservation | `(x0 est joyeux)` | 2 |
| E3P21 | joie | `(x0 est joyeux)` | 2 |
| E3P21 | tristesse | `(x0 est triste)` | 2 |
| E3P22 | joie causée | `(x0 aime z0)` | 3 |
| E3P22 | tristesse causée | `(x0 hait z0)` | 3 |
| E3P33 | réciprocité | `(x0 s_efforce_que (y0 aime x0))` | 5 |

Les profondeurs comptent les étapes de règles, les hypothèses étant à la
profondeur zéro. Les contextes `imagine` et `s_efforce_que` restent des
triplets imbriqués ; aucune règle ne transforme `x imagine P` en `P`.

## Chaînes principales

E3P19 :

```text
x0 aime y0
→ x0 imagine (y0 affecte_de_joie x0)
+ x0 imagine (y0 est inexistant)
→ x0 est triste
```

E3P22 :

```text
x0 aime y0
→ x0 imagine (y0 affecte_de_joie x0)
+ x0 imagine (z0 affecte_de_joie y0)
→ x0 imagine (z0 affecte_de_joie x0)
→ x0 aime z0
```

E3P33 :

```text
x0 aime y0
→ x0 imagine (y0 affecte_de_joie x0)
→ x0 s_efforce_que (y0 est existant)
→ x0 s_efforce_que (y0 est joyeux)
→ x0 s_efforce_que (x0 affecte_de_joie y0)
→ x0 s_efforce_que (y0 aime x0)
```

## Divergences et engagements interprétatifs

1. La « définition spinozienne de l'amour » de la diapositive 10 est une
   compilation de E3P13S, pas sa formulation littérale.
2. Les réciproques P13/1/2 sont plus fortes que le texte et sont donc marquées
   `stronger_than_source`.
3. P22/1 généralise les affects en une transitivité avec produit des signes.
   Cette algèbre est une construction du modèle historique.
4. La preuve de E3P33 n'utilise jamais l'hypothèse `est_semblable_a`. La base
   historique prouve donc une implication strictement plus forte que l'énoncé.
5. La dernière étape de E3P33 applique P13/2/2 sous `s_efforce_que`, tandis que
   la règle imprimée est sous `imagine`. L'implémentation emploie une règle
   distincte d'origine `historical_interpretation`.
6. P13/2/2, telle qu'imprimée, contient `y` uniquement dans la conclusion ;
   elle ne peut être exécutée sans création de témoin ou correction.
7. P21/1 appelle `Créer(z)`. Faute de sémantique historique suffisante et
   d'action de création bornée dans Snarky, elle reste explicitement bloquée.

## Comparaison au texte

La traduction Appuhn confirme les conclusions des quatre propositions. E3P21
ajoute toutefois que l'intensité de l'affect varie avec celle de la chose aimée,
dimension quantitative absente du modèle. Les démonstrations textuelles
invoquent des propositions antérieures et des scolies ; la base historique les
compile souvent en une seule règle. Le catalogue distingue donc l'attribution
textuelle de la forme opérationnelle réellement testée.
