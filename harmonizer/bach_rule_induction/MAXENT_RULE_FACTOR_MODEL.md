# Modèle MaxEnt factoriel à règles pour les chorals

## Statut

Proposition méthodologique faisant suite à la boucle V5.12–V5.16.

Cette note ne déclare pas les poids V5.16 comme un modèle MaxEnt final. Elle
définit la représentation probabiliste qui devrait précéder toute nouvelle
compilation des règles apprises dans Snarky.

## 1. Problème

Les expériences actuelles manipulent trois objets différents qui ne doivent pas
être confondus :

1. les statistiques observées dans Bach ;
2. les paramètres appris d'un modèle probabiliste ;
3. les poids opérationnels utilisés par un `CHOICE` Snarky.

Un pourcentage comme « 25,73 % des mouvements de basse sont des demi-tons »
est une statistique de corpus. Un poids appris comme `-0,45` est une
contribution logarithmique. Un poids de `CHOICE` est une quantité positive
utilisée pour ordonner ou échantillonner les alternatives encore possibles.

La confusion de ces niveaux peut produire une génération incorrecte même si
les conditionnelles locales semblent bonnes. V5.12–V5.13 en ont fourni un
exemple : un même potentiel de sonorité était additionné une fois par voix
attaquant simultanément. Une sonorité commune pouvait recevoir jusqu'à quatre
fois son poids appris.

Le modèle probabiliste doit donc posséder une définition indépendante du
moteur de choix.

## 2. Modèle MaxEnt global

Soit :

- `X` : toutes les hauteurs variables du choral ;
- `C` : le contexte fixé, notamment soprano, rythme, métrique, tonique et mode
  déclarés ;
- `F_r(X,C)` : le compte global des occurrences de la règle ou feature `r` ;
- `theta_r` : le paramètre appris de cette feature.

Le modèle maximum-entropie est :

```text
P_theta(X=x | C)
    = exp(sum_r theta_r F_r(x,C)) / Z_theta(C)
```

avec :

```text
Z_theta(C)
    = sum_x exp(sum_r theta_r F_r(x,C))
```

La fonction d'énergie équivalente est :

```text
E_theta(x,C) = -sum_r theta_r F_r(x,C)
```

La distribution est donc définie sur des harmonisations complètes, et non par
une succession ad hoc de `CHOICE`.

## 3. Une règle est une feature MaxEnt

Une interaction entre deux notes est un cas particulier de règle.

Exemple pairwise vertical :

```text
F_fifth(X) =
    sum_t indicator(interval_class(bass_t, soprano_t) = 7)
```

Exemple pairwise mélodique :

```text
F_bass_semitone(X) =
    sum_t indicator(abs(bass_t - bass_previous_attack(t)) = 1)
```

Une règle K3 est un facteur d'ordre supérieur :

```text
F_resolution(X) =
    sum_t indicator(
        dissonance_at(t)
        and stepwise_resolution_at(t+1)
    )
```

Une trajectoire de sonorités est également une feature :

```text
F_transition(X) =
    sum_t indicator(
        bass_pcset(t) = {0,3,6,8}
        and bass_pcset(t+1) = {0,4,7}
    )
```

Le MaxEnt n'oppose donc pas « interactions entre notes » et « règles ». Les
interactions pairwise constituent le premier niveau du catalogue ; les règles
lisibles peuvent porter sur des facteurs pairwise ou d'ordre supérieur.

## 4. Portée et instanciation

Chaque template de règle doit déclarer :

- les variables consultées ;
- les blocs K3 consultés ;
- son mode d'instanciation ;
- la quantité numérique qu'il retourne ;
- son identité canonique.

Exemples d'instanciation :

```text
once_per_voice_attack
once_per_voice_pair_and_block
once_per_vertical_block
once_per_k3_kernel
once_per_phrase_boundary
```

Deux conséquences sont obligatoires :

1. un facteur commun de sonorité est compté une seule fois par bloc vertical ;
2. l'exposition du facteur dans plusieurs conditionnelles ne crée pas plusieurs
   copies dans l'énergie conjointe.

L'identité d'une instance peut être représentée par :

```text
(rule_id, piece_id, central_offset, voice_scope)
```

ou, pour une sonorité commune :

```text
(rule_id, piece_id, central_offset)
```

Cette identité doit être testable et inspectable.

## 5. Contraintes, interdictions et obligations

### 5.1 Contraintes absolues

Une harmonisation illégale possède une probabilité nulle :

```text
P(X=x | C) = 0
```

Dans l'énergie, cela correspond théoriquement à `+infinity`. Dans Snarky, il
est plus simple d'éliminer l'alternative du domaine avant tout tirage.

### 5.2 Interdictions statistiques

Une interdiction souple est une feature dont le paramètre est négatif :

```text
theta_r < 0
```

Chaque occurrence réduit le poids relatif de l'harmonisation sans l'annuler.

### 5.3 Obligations et licences positives

Une obligation statistique ou une configuration favorisée possède :

```text
theta_r > 0
```

Elle peut représenter :

- une résolution normalement attendue ;
- une licence positive autorisant une dissonance ;
- une trajectoire harmonique caractéristique ;
- une configuration plus fréquente que ne le prédit le modèle courant.

Un apprentissage limité aux gradients négatifs produit une harmonie trop
consonante. V5.12 a montré qu'interdictions et licences positives doivent être
apprises conjointement.

## 6. Moments empiriques et poids

Le pourcentage observé d'une feature est son moment empirique :

```text
mu_r_data = E_Bach[F_r]
```

Le modèle possède le moment :

```text
mu_r_model = E_model[F_r]
```

Le gradient de log-vraisemblance est :

```text
dL / dtheta_r = E_Bach[F_r] - E_model[F_r]
```

L'objectif MaxEnt cherche donc :

```text
E_model[F_r] ~= E_Bach[F_r]
```

Le paramètre `theta_r` est le multiplicateur de Lagrange qui permet de
rapprocher ces moments. Il n'est pas le pourcentage observé.

Par exemple :

```text
theta_r = -0.45
```

correspond isolément au multiplicateur d'odds :

```text
exp(-0.45) ~= 0.64
```

Il ne signifie ni « probabilité 45 % » ni « réduction absolue de 45 points ».

## 7. Interactions entre règles

Dans un modèle log-linéaire simple, les contributions s'additionnent :

```text
score(X) = sum_r theta_r F_r(X,C)
```

Deux règles peuvent être statistiquement dépendantes tout en restant
indépendantes dans leur définition et leur exécution.

Si l'effet conjoint de deux faits n'est pas additif, il faut créer une feature
de conjonction explicite :

```text
F_interaction =
    indicator(rule_context_A and rule_context_B)
```

Cette interaction doit payer un coût descriptif supérieur. Elle n'est retenue
que si elle apporte un gain tenu à part suffisant. Cela évite de cacher une
table opaque d'interactions derrière des règles prétendument indépendantes.

## 8. Rôle exact de `CHOICE`

`CHOICE` doit être une opération d'inférence, pas la définition du modèle.

Pour rééchantillonner la variable `X_i`, seuls les facteurs dont la portée
contient `i` peuvent changer. Pour chaque alternative `a` :

```text
local_score(a)
    = sum_{factor g containing i}
        theta_type(g) f_g(X_i=a, X_-i, C)
```

La conditionnelle Gibbs est :

```text
P(X_i=a | X_-i,C)
    = softmax_a(local_score(a))
```

Le pont Snarky peut matérialiser :

```text
positive_weight(a)
    = exp(local_score(a) - max_b local_score(b))
```

puis exécuter :

```text
CHOICE (note $time pitch $pitch) WEIGHT $weight
FROM
    (note $time candidate_pitch $pitch)
    (note $time candidate_weight SEQ[$pitch $weight])
END_CHOICE
```

Le `WeightedRandomChoicePolicy` normalise implicitement les poids positifs des
alternatives restantes. Si une contrainte dure élimine une note, les poids des
notes encore légales sont renormalisés.

Pour une recherche déterministe, les mêmes poids peuvent ordonner les
alternatives. Cette procédure ne transforme cependant pas une recherche avec
backtracking en modèle autorégressif : la distribution globale MaxEnt reste la
référence.

## 9. Représentation déclarative proposée

Exemple de mouvement de basse :

```yaml
id: learned-bass-semitone
scope:
  blocks: [previous, current]
  voices: [bass]

feature:
  type: indicator
  condition:
    absolute_melodic_interval: 1

factor:
  grounding: once_per_bass_attack
  parameter: -0.73

evidence:
  bach_moment: 0.2259
  model_moment_before: 0.3857
  train_support: 1842
  validation_support: 381
```

Exemple de sonorité :

```yaml
id: learned-bass-pcset-0-3-6-8-weak
scope:
  blocks: [current]
  voices: [soprano, alto, tenor, bass]

feature:
  type: indicator
  condition:
    bass_relative_pcset: [0, 3, 6, 8]
    metric_status: weak

factor:
  grounding: once_per_vertical_block
  parameter: -0.41

evidence:
  bach_moment: 0.0320
  model_moment_before: 0.0577
```

Exemple de résolution K3 :

```yaml
id: learned-dissonance-step-resolution
scope:
  blocks: [previous, current, following]
  voices: [target, reference]

feature:
  type: indicator
  condition:
    central_interval_class: 11
    target_resolves_by_step: true

factor:
  grounding: once_per_voice_pair_and_k3
  parameter: 0.62
```

Les champs `evidence` documentent la règle mais ne participent pas directement
au calcul de l'énergie.

## 10. Hiérarchie expérimentale

Trois familles emboîtées doivent être apprises et comparées.

### M0 — marges

- registre par voix ;
- classe relative à la tonique globale ;
- mode déclaré ;
- position métrique.

M0 ne représente aucune interaction entre notes.

### M1 — MaxEnt pairwise

- intervalles verticaux entre couples de voix ;
- mouvements mélodiques entre attaques successives ;
- directions conjointes de deux voix ;
- répétitions attaquées ;
- interactions pairwise conditionnées par métrique.

M1 mesure ce qu'un modèle MaxEnt classique d'interactions entre couples peut
déjà expliquer.

### M2 — MaxEnt à règles K3

- résolution et préparation ;
- trajectoires de sonorités ;
- notes de passage, broderies et anticipations ;
- conjonctions courtes et lisibles ;
- statuts harmoniques explicites justifiés indépendamment.

La comparaison `M1` contre `M2` répond directement à la question scientifique :
les règles musicales d'ordre supérieur apportent-elles une information
significative au-delà des seules interactions pairwise ?

## 11. Apprentissage

Le protocole proposé est :

1. apprendre M0 ;
2. ajouter les facteurs pairwise de M1 et ajuster conjointement tous les poids ;
3. rechercher les résidus de moments sous M1 ;
4. proposer des règles K3 courtes pour ces résidus ;
5. ajuster M2 par chaînes persistantes ;
6. appliquer une régularisation L1, group lasso ou un coût MDL ;
7. fusionner les features identiques au lieu d'empiler des deltas de poids ;
8. geler le modèle avant validation générative ;
9. conserver le test scellé jusqu'au protocole final.

La pseudo-vraisemblance conditionnelle peut initialiser les paramètres :

```text
sum_i log P(X_i = bach_i | X_-i, C)
```

Mais la sélection finale destinée à la génération doit utiliser les moments de
chaînes persistantes ou une autre approximation de la vraisemblance globale.

## 12. Régularisation et intelligibilité

L'intelligibilité impose des contraintes de modèle :

- peu de templates actifs ;
- portée bornée et déclarée ;
- deux ou trois conditions atomiques par règle, sauf justification ;
- coût supérieur pour une conjonction ;
- poids fusionnés pour les features identiques ;
- exemples et contre-exemples authentiques ;
- support minimal dans plusieurs chorals ;
- effet mesurable après réajustement des autres poids ;
- validation sur des pièces jamais consultées pour la sélection.

Une table complète de toutes les transitions possibles pourrait améliorer la
vraisemblance, mais ne constituerait pas nécessairement une théorie lisible.
Elle doit servir de modèle plafond ou de générateur de résidus, non de base
symbolique finale.

## 13. Tests nécessaires

Le moteur factoriel doit vérifier :

1. une instance de facteur possède une identité canonique ;
2. une sonorité à quatre attaques n'est comptée qu'une fois ;
3. une feature mélodique est comptée pour chaque attaque concernée ;
4. le score local d'un candidat égale la différence exacte des énergies
   globales ;
5. le calcul vectorisé égale l'énumération scalaire des mondes ;
6. la conditionnelle normalisée somme à un ;
7. les contraintes dures donnent une probabilité nulle ;
8. l'échantillonnage est reproductible pour une graine donnée ;
9. la fréquence empirique d'un petit modèle énumérable rejoint sa distribution
   exacte ;
10. les poids compilés dans `CHOICE` reproduisent la même conditionnelle que le
    moteur factoriel.

## 14. Migration depuis V5.16

V5.16 doit être conservée comme résultat expérimental, mais ses poids ne sont
pas encore la base MaxEnt finale.

La migration proposée est :

1. geler les artefacts et mesures V5.16 ;
2. transformer chaque prédicat en template de facteur avec une portée et un
   mode d'instanciation explicites ;
3. fusionner les corrections additives V5.14–V5.16 par feature ;
4. reconstruire M0 depuis le train ;
5. apprendre M1 depuis zéro ;
6. mesurer les résidus génératifs de M1 ;
7. réintroduire seulement les règles K3 justifiées pour former M2 ;
8. comparer M0, M1, M2 et DeepBach ;
9. compiler le modèle gelé dans Snarky ;
10. vérifier que `CHOICE` reproduit les conditionnelles du modèle, sans devenir
    leur source sémantique.

La prochaine implémentation ne devrait donc pas ajouter directement une
nouvelle pondération à V5.16. Elle devrait d'abord introduire le modèle de
facteurs canonique et son banc de tests.
