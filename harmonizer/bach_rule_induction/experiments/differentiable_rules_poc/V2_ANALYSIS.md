# Analyse du POC V2.1 — génération de colonnes résiduelle

## Résultat principal

Le POC V2.1 isole les deux règles de mouvement direct recherchées après avoir
absorbé les effets généraux de hauteur cible, de direction et d'amplitude du
saut.

Le mineur ne reçoit toujours ni les noms d'intervalle, ni un prédicat
`direct_motion`, ni les verdicts Snarky. Il réutilise seulement le prédicat
anonyme de même signe non nul inventé par le V1, puis teste uniformément les
douze classes numériques.

Le raffinement de famille retient exactement les classes `0` et `7` :

```text
abs(candidate_s-current_b) % 12 == 0
AND abs(candidate_s-prev_s) > 2
AND LEARNED_PREDICATE_001
→ éviter
```

```text
abs(candidate_s-current_b) % 12 == 7
AND abs(candidate_s-prev_s) > 2
AND LEARNED_PREDICATE_001
→ éviter
```

Après dévoilement sémantique, ces deux classes correspondent aux arrivées par
mouvement direct sur octave ou unisson, et sur quinte parfaite.

## Changement algorithmique

Le V1 classait d'abord les clauses par leur marginal global. Le V2 ajuste un
socle de 21 effets numériques simples, puis répète :

```text
calculer P(candidate | contexte) avec le catalogue courant
→ calculer le résidu choix_de_Bach - P
→ chercher la conjonction courte au meilleur gain conditionnel pénalisé
→ ajouter une colonne
→ réestimer conjointement tous les poids avec Adam et L1
→ sélectionner le meilleur préfixe sur validation
```

Pour une clause booléenne, sa masse prédite dans une opportunité est `q`. La
courbure diagonale utilisée par la recherche est `q(1-q)` et le gain local de
log-vraisemblance est approché par `g²/(2h)`. Le score soustrait un coût de
description et un coût de redondance avec les colonnes déjà retenues.

La recherche générale autorise simultanément préférences et évitements. Une
branche complémentaire `avoid` vérifie le comportement lorsque seules les
queues négatives sont proposées.

## Corpus et séparation

- 352 chorals et 20 350 décisions disponibles ;
- train : 246 pièces et 14 436 décisions ;
- validation : 53 pièces et 3 029 décisions ;
- test : 53 pièces toujours scellées ;
- 22 candidates de soprano par décision, hauteurs MIDI `60..81`.

Le programme V2 ne possède volontairement aucune option permettant d'ouvrir le
test.

## Qualité et parcimonie

| Modèle | NLL validation | Clauses actives |
|---|---:|---:|
| Socle de main effects | 1,736939 | 20 après élagage |
| Meilleur préfixe de 12 colonnes | 1,628203 | 32 |
| Après raffinement direct | 1,625642 | 34 |
| Contrôle nul final | 2,643938 | 30 |

Le V1 conservait 52 clauses actives pour une NLL de validation de `1,970562`.
La comparaison porte sur la même tâche et le même partage, mais le V2 dispose
d'un socle numérique plus systématique. Le gain ne doit donc pas être attribué
à la seule génération de colonnes ; l'ablation du socle reste à faire.

## Isolement du mouvement direct

Avant le raffinement de famille, les résidus sont :

| Classe | z train marginal | z validation marginal | z train résiduel | z validation résiduel |
|---:|---:|---:|---:|---:|
| 0 | -18,335 | -8,715 | -6,239 | -3,889 |
| 7 | -14,804 | -7,444 | -3,161 | -2,491 |

Les autres classes peuvent avoir un résidu important sur train, mais ne
franchissent pas simultanément les seuils identiques :

```text
z train <= -3
AND z validation <= -2
```

Le système sélectionne donc `[0, 7]` parmi les douze classes, sans règle
spécifique à ces deux valeurs. Après ajustement conjoint :

| Classe | Poids |
|---:|---:|
| 0 | -1,345 |
| 7 | -0,568 |

Leur ajout réduit la NLL de validation de `1,628718` à `1,625642`. Après
ajustement, leurs résidus se rapprochent de zéro, ce qui est le comportement
attendu d'une colonne expliquant l'effet.

## Comparaison postérieure avec Snarky

Les règles apprises sont comparées à `R-DIRECT-001` et `R-DIRECT-002` seulement
après l'induction. Le comparateur énumère 301 401 états locaux valides par
classe, avec la soprano au-dessus de la basse à la source et à la cible.

| Classe | États positifs appris | États positifs Snarky | Désaccords |
|---:|---:|---:|---:|
| 0 | 9 972 | 9 972 | 0 |
| 7 | 9 324 | 9 324 | 0 |

Sur ce domaine local borné, les deux résultats sont donc classés
`RECOVERED_EQUIVALENT`. Cette équivalence concerne le comportement logique de
la clause, pas encore son statut normatif définitif.

## Contrôles

### Mélange intra-pièce

Le contrôle nul conserve l'histogramme des choix de soprano de chaque pièce
mais détruit les relations locales.

| Classe | z train résiduel | z validation résiduel |
|---:|---:|---:|
| 0 | -1,871 | -0,840 |
| 7 | +2,434 | -0,157 |

Aucune classe ne franchit les deux seuils et aucun raffinement direct n'est
ajouté.

### Recherche limitée aux évitements

Dans la branche `avoid`, les troisième et quatrième colonnes retrouvées sont :

```text
source_class == 0 AND target_class == 0 AND same_nonzero_sign
source_class == 7 AND target_class == 7 AND same_nonzero_sign
```

Cette branche retrouve donc de nouveau les octaves et quintes parallèles avant
le raffinement du mouvement direct. Une fois ces parallèles absorbées, les
résidus propres au mouvement direct deviennent plus faibles ; cela montre
pourquoi il faut distinguer les deux familles malgré leur recouvrement.

## Ce qui est établi

1. La notion anonyme de même direction découverte au V1 est réutilisable.
2. Une génération de colonnes guidée par le résidu réduit la duplication et
   améliore fortement la vraisemblance tenue à part.
3. La famille locale « arrivée après saut en même direction » distingue
   automatiquement `0` et `7` des dix autres classes.
4. Ces deux clauses sont extensionnellement équivalentes aux règles Snarky de
   mouvement direct sur le domaine valide testé.
5. La sélection disparaît dans le contrôle nul.
6. Le premier critère de redécouverte atteint désormais quatre familles du
   niveau A : grand saut, octaves parallèles, quintes parallèles et mouvements
   directs.

## Limites

1. `LEARNED_PREDICATE_001` est hérité du V1 ; le V2 ne réexécute pas son
   invention à chaque tour.
2. La forme de famille « classe cible + saut + même signe » est engendrée
   uniformément, mais elle constitue déjà un biais de langage. Les valeurs
   `0` et `7`, elles, ne sont pas privilégiées.
3. Les seuils de raffinement sont sélectionnés au stade exploratoire. Ils
   doivent être préenregistrés avant toute ouverture du test.
4. Le bootstrap par pièce et le regroupement des variantes de chorals restent
   à implémenter.
5. Les douze interactions générales retenues comprennent plusieurs
   préférences encore sans interprétation musicale.
6. Seules les voix extrêmes sont modélisées et les candidates ne sont pas
   encore filtrées par toutes les contraintes de tessiture et de croisement.
7. L'équivalence avec Snarky est démontrée sur les états locaux valides bornés,
   pas sur les candidates où les voix seraient croisées.
8. Le test final reste fermé : le résultat est confirmé sur validation, mais
   pas encore gelé.

## Prochaine expérience

Le POC V2.2 doit étendre le même moteur aux quatre voix et aux paires
adjacentes pour rechercher le chevauchement, le triton mélodique et les
parallèles intérieures. Avant cela, il faut :

1. préenregistrer les seuils et budgets du V2 ;
2. ajouter un bootstrap groupé par choral ;
3. regrouper les variantes d'une même mélodie avant le partage ;
4. compiler les deux règles retrouvées en `RuleCard`, en pointant vers les
   règles Snarky déjà équivalentes plutôt qu'en les dupliquant.
