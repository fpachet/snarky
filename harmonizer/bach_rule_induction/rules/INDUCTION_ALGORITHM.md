# Algorithme d'induction de règles locales

## Objectif

Apprendre à partir des chorals une petite base de règles :

- locales sur un voisinage borné ;
- structurellement indépendantes ;
- exprimées avec des faits musicaux intelligibles ;
- sélectionnées pour leur pouvoir prédictif tenu à part ;
- compilables en Snarky ;
- évaluées sur une frontière qualité–complexité.

Le premier objectif n'est pas de découvrir une règle inconnue, mais de
redécouvrir à l'aveugle des règles existantes selon le protocole
[`KNOWN_RULE_RECOVERY.md`](KNOWN_RULE_RECOVERY.md).

## 1. Un exemple est une décision, pas une note isolée

Pour chaque attaque de chaque voix, on masque la hauteur choisie par Bach et on
énumère les hauteurs localement candidates. Toutes les candidates associées à
une même position forment un **groupe de décision** :

```text
opportunity_id = (choral, position, voix)

candidate C4   chosen = false
candidate D4   chosen = false
candidate E4   chosen = true
candidate F4   chosen = false
```

Les candidates non choisies ne sont pas étiquetées comme fautes. Le modèle
apprend seulement à classer le choix observé devant les autres possibilités.
Cela évite de confondre « Bach n'a pas choisi cette note ici » et « cette note
est interdite ».

Le premier essai conserve le rythme et les positions d'attaque du corpus. Il
ne prédit que la hauteur. L'ambitus de chaque voix définit le domaine initial ;
les règles à redécouvrir ne doivent pas servir à préfiltrer les candidates.

## 2. Faits primitifs

Chaque couple `(opportunité, candidate)` reçoit des faits calculés dans la
fenêtre locale `t-1, t, t+1`.

### Faits mélodiques

- voix ;
- hauteur et classe de hauteur candidates ;
- degré relatif à la tonalité locale ;
- intervalle depuis la note précédente ;
- intervalle vers la note suivante lorsqu'elle est fixée ;
- amplitude et direction de chaque mouvement ;
- attaque ou continuation.

### Faits verticaux

- ordre des quatre voix ;
- intervalle avec chacune des autres voix ;
- classe de chaque intervalle ;
- intervalle de la même paire à la position précédente ;
- directions relatives de deux voix.

### Faits de statut

- position métrique ;
- fermata ;
- tonalité locale et mode ;
- accord, renversement et rôle harmonique lorsque leur provenance est
  disponible ;
- statut cadentiel ou structurel explicitement défini.

Un fait peut être dérivé, par exemple
`same_nonzero_direction(upper, lower)`, s'il possède une définition générale
et testable. Il ne doit pas encoder la règle cible. Sont donc interdits pendant
la redécouverte :

```text
creates_parallel_fifth
violates_voice_overlap
must_resolve_leading_tone
```

La complexité des faits dérivés est comptée dans le coût descriptif total.

### Variante forte : invention des faits dérivés

Le benchmark principal ne doit pas nécessairement fournir les intervalles
nommés ni les relations de mouvement. La variante forte part de :

- hauteurs numériques ;
- différences de hauteurs ;
- ordre, égalité, signe, valeur absolue et modulo ;
- identité des voix et positions temporelles.

Elle apprend d'abord des clauses sur ces primitives. Lorsque plusieurs clauses
symétriques réutilisent le même sous-terme, une passe MDL peut proposer un
prédicat dérivé anonyme, défini symboliquement et réutilisable. Le nom
musicologique n'est attribué qu'après l'expérience aveugle.

Le premier prototype de ce mécanisme se trouve dans
[`../experiments/differentiable_rules_poc/`](../experiments/differentiable_rules_poc/).

## 3. Langage des clauses

Une clause est un détecteur booléen local :

```text
source_interval_class == perfect_fifth
AND target_interval_class == perfect_fifth
AND same_nonzero_direction == true
```

Pour le MVP :

- une à trois conditions musicales ;
- variables typées : voix, position, hauteur, intervalle, statut ;
- aucune référence à un identifiant de choral ;
- aucune dépendance `règle → règle` ;
- constantes relatives privilégiées aux hauteurs absolues ;
- ordre canonique des conditions afin d'éliminer les doublons syntaxiques.

Une clause peut favoriser ou défavoriser une candidate. Son poids statistique
ne détermine pas encore son statut musical.

## 4. Modèle conditionnel additif

Chaque règle `r` est une feature binaire et reçoit un poids `w_r`. Pour une
candidate `c` dans un contexte `x` :

```text
score(c | x) = Σ_r w_r × r(x, c)
```

La probabilité conditionnelle est :

```text
P(c | x) =
    exp(score(c | x))
    / Σ_c' exp(score(c' | x))
```

La somme du dénominateur porte uniquement sur les candidates de la même
opportunité. Un poids positif exprime une préférence ; un poids négatif exprime
un évitement.

Les modalités humaines sont ensuite canoniquement représentées par un prédicat
de violation :

```text
FORBID(A, B)   : violation = A AND B
REQUIRE(A, B)  : violation = A AND NOT B
AVOID(A, B)    : même forme avec pénalité souple
PREFER(A, B)   : éviter ou déclasser les alternatives à B
```

La découverte statistique recherche donc les deux queues des marginaux
conditionnels : une probabilité proche de zéro propose une interdiction, une
probabilité proche de un propose une obligation. Ces probabilités sont
normalisées par les candidates effectivement disponibles dans chaque groupe de
décision.

L'apprentissage minimise :

```text
perte conditionnelle sur train
+ λ1 × somme des valeurs absolues des poids
+ λd × longueur descriptive des clauses et des faits
```

La pénalisation `L1` annule les règles inutiles. Le coût descriptif favorise une
clause courte et un fait simple lorsqu'ils expliquent autant de données qu'une
formulation plus complexe.

## 5. Recherche des clauses par beam search

Une énumération exhaustive devient rapidement combinatoire. Le générateur
utilise un beam search borné.

### Profondeur 1

Évaluer chaque littéral atomique admissible :

```text
target_interval_class == perfect_fifth
melodic_delta > octave
target_degree == 1
```

### Profondeur 2

Conserver les meilleures clauses et ajouter un littéral compatible :

```text
source_interval_class == perfect_fifth
AND target_interval_class == perfect_fifth
```

### Profondeur 3

Étendre une dernière fois :

```text
source_interval_class == perfect_fifth
AND target_interval_class == perfect_fifth
AND same_nonzero_direction == true
```

Une clause est éliminée si :

- son support en pièces est inférieur au seuil ;
- ses conditions sont contradictoires ;
- elle couvre les mêmes cas qu'une clause plus courte ;
- elle est une spécialisation sans gain de sa règle parente ;
- elle reproduit une règle déjà sélectionnée ;
- elle utilise un fait interdit ou non enregistré.

La propriété descendante du support permet un élagage de type Apriori : si une
clause est trop rare, toutes ses spécialisations le seront également.

## 6. Column generation

Le beam search est inséré dans une boucle de génération de colonnes :

```text
R = {}

répéter:
    calculer les probabilités et résidus du modèle R
    chercher la clause r* donnant le meilleur gain pénalisé sur train
    si aucune clause admissible n'améliore le modèle:
        arrêter
    ajouter r* à R
    réestimer conjointement tous les poids
    supprimer les poids nuls et les clauses dominées
    mesurer la nouvelle base sur validation
```

Le score de recherche d'une clause est :

```text
gain de log-vraisemblance conditionnelle
- pénalité de longueur
- pénalité de faible support
- pénalité de redondance
```

Cette procédure cherche à chaque tour la règle qui explique le mieux les
erreurs résiduelles. Elle limite naturellement la duplication : une règle déjà
expliquée apporte peu de gain supplémentaire.

## 7. Séparation train, validation et test

- `train` sert à proposer les clauses et estimer leurs poids ;
- `validation` sert à choisir le nombre de règles, les pénalités et le coude de
  la frontière qualité–complexité ;
- `test` reste fermé jusqu'au gel de l'algorithme, des faits et du catalogue.

Le bootstrap et les intervalles d'incertitude regroupent par choral. Les
transpositions et événements d'une même pièce ne sont jamais traités comme des
observations indépendantes.

## 8. Redécouverte d'une règle connue

Pour les quintes parallèles, la recherche devrait évoluer ainsi :

```text
target_interval_class == perfect_fifth
```

Clause trop générale, puis :

```text
source_interval_class == perfect_fifth
AND target_interval_class == perfect_fifth
```

Clause encore incomplète, puis :

```text
source_interval_class == perfect_fifth
AND target_interval_class == perfect_fifth
AND same_nonzero_direction == true
```

La candidate finale devrait recevoir un poids négatif important. Après
apprentissage, ses verdicts sont comparés à `R-PARALLEL-002` sur :

- les opportunités de `validation` ;
- un domaine fini de transitions SATB générées exhaustivement ;
- les cas limites des tests Snarky existants.

Une concordance sémantique compte comme récupération même si les deux textes
ne sont pas identiques.

## 9. Passage du poids au statut musical

Le cycle de vie technique et la force musicale sont séparés.

```text
CANDIDATE → SUPPORTED → COMPILED → ACCEPTED → FROZEN
```

Le poids suggère seulement une interprétation initiale :

- effet stable mais modéré : candidat `PREFER` ;
- confirmation élevée avec exceptions caractérisées : candidat `NORMALLY` ;
- régularité descriptive sans gain génératif : `OBSERVED` ;
- contrainte `MUST` : certification distincte, jamais simple seuil de poids.

Une absence dans le corpus ne suffit pas à déclarer une interdiction.

## 10. Compilation Snarky

Une règle statistique sélectionnée produit une `RuleCard`, puis une règle
exécutable :

```text
RULE R_LEARNED_PARALLEL_FIFTH
WHEN
    source_interval_class == perfect_fifth
    target_interval_class == perfect_fifth
    same_nonzero_direction == true
THEN
    ADD violation
END
```

La `RuleCard` conserve :

- clause humaine et clause normalisée ;
- poids et signe ;
- support en événements et en pièces ;
- gain sur `train` et `validation` ;
- intervalle d'incertitude ;
- exemples, exceptions et contre-exemples ;
- résultat d'ablation ;
- version du registre de faits et du corpus.

## 11. Paramètres initiaux du MVP

Valeurs de départ à confirmer avant ouverture de `validation` :

| Paramètre | Valeur initiale |
|---|---:|
| fenêtre | `t-1, t, t+1` |
| longueur maximale | 3 conditions |
| largeur du beam | 200 |
| support minimal | 10 chorals distincts |
| règles actives maximales | 30 |
| arrêt | 3 tours sans amélioration du coude |

Ces valeurs sont des budgets d'intelligibilité, pas des vérités musicales.
Elles seront publiées avec chaque expérience.

## 12. Baselines algorithmiques

Le système principal combine beam search, MaxEnt conditionnel sparse et
génération de colonnes. Deux comparaisons sont utiles :

1. règles d'association de type Apriori, simples mais incapables de modéliser
   correctement le choix entre candidates ;
2. programmation logique inductive, par exemple Popper, adaptée aux verdicts
   binaires mais moins naturelle lorsque les alternatives non choisies ne sont
   pas nécessairement fautives.

Les trois méthodes doivent utiliser le même registre de faits, le même partage
par pièce et les mêmes règles cachées.

## 13. Artefacts attendus

```text
corpus/opportunities.*       groupes de décisions et candidates
features/registry.*          définitions des faits primitifs
experiments/*/config.*       budgets et hyperparamètres
experiments/*/candidates.*   clauses explorées et scores
experiments/*/frontier.*     frontière qualité–complexité
rules/*.yaml                 RuleCards retenues
rules/learned/*.rules        compilation Snarky
```

Chaque campagne doit être déterministe à graine, manifeste et configuration
identiques.
