# Analyse du POC V3.6 — proxy tonal ou règle harmonique ?

## Question

La seule clause V3.4 survivant à la correction familiale est un proxy
numérique court :

```text
mode majeur
AND voix == alto
AND classe_source_alto == 11
AND classe_source_basse == 2
AND classe_cible_basse == 4
→ alto_cible == alto_source + 1
```

V3.5 a montré qu'une majorité de ses occurrences observées correspondent à
`vii°6→I6`. V3.6 demande si cette spécialisation harmonique explique tout le
signal, ou si le proxy plus large contient encore de l'information.

Quatre modèles sont donc réajustés depuis zéro avec la même baseline :

1. baseline seule ;
2. baseline + proxy numérique ;
3. baseline + spécialisation harmonique ;
4. baseline + les deux colonnes.

## Une colonne harmonique sans regarder la réponse

La signature source exacte est `{2,5,11}` et la cible candidate `{0,4,7}`,
avec basse `2→4`. Pour chaque note candidate de l'alto, le code la substitue
dans l'accord cible et recalcule sa signature. La note d'alto réellement
choisie n'entre donc pas dans la prémisse.

Cette définition donne 43 opportunités harmoniques au train, dont 41
résolutions. Le V3.5 n'en comptait que 41 parce que son audit postérieur
filtrait les progressions dont la **cible observée** était déjà `I6`. Les deux
chiffres répondent à des questions différentes ; `41/43` est le taux pertinent
pour une règle utilisable par le modèle.

Comme toute pseudo-vraisemblance de type DeepBach, l'expérience conditionne
néanmoins l'alto sur les trois autres voix observées au même instant. Elle
n'évalue pas encore une génération SATB autonome.

## Résultats authentiques

| Colonne | Train | Validation |
|---|---:|---:|
| proxy numérique | 47/54 | 19/19 |
| `vii°6→I6` candidat-dépendant | 41/43 | 12/12 |

| Modèle | NLL validation | Contexte proxy | Contexte harmonique |
|---|---:|---:|---:|
| baseline | 1,276210 | 1,554141 | 1,873731 |
| proxy | 1,269022 | 0,274217 | 0,359860 |
| harmonique | 1,270669 | 0,575794 | 0,307652 |
| les deux | **1,268457** | **0,178155** | **0,126670** |

Les deux poids restent positifs dans le modèle conjoint :

```text
proxy numérique     1,857
spécialisation      2,015
```

Le modèle conjoint gagne `0,007753` de NLL de validation sur la baseline. Le
bootstrap de 1 000 rééchantillonnages par choral, à poids ajustés fixes, donne
une médiane de `0,007582` et un intervalle à 95 % `[0,003832 ; 0,012188]`.

## Qui apporte quoi ?

| Ajout | Gain NLL validation | Bootstrap médian [95 %] | P(gain > 0) |
|---|---:|---:|---:|
| proxy à la baseline | 0,007188 | 0,007145 [0,003791 ; 0,010866] | 1,000 |
| harmonique à la baseline | 0,005541 | 0,005348 [0,002371 ; 0,009246] | 1,000 |
| harmonique au proxy | 0,000565 | 0,000575 [-0,000008 ; 0,001157] | 0,972 |
| proxy à l'harmonique | 0,002212 | 0,002172 [0,000943 ; 0,003775] | 1,000 |

Le proxy n'est donc pas un simple substitut imparfait de `vii°6→I6` : il
conserve un apport propre net lorsque la spécialisation est déjà présente.
La réciproque est plus fragile. La spécialisation améliore ponctuellement le
proxy, mais son intervalle bootstrap touche pratiquement zéro.

Le résultat favorise une représentation hiérarchique intelligible :

```text
règle générale locale
  résolution ascendante de l'alto dans le contexte basse 2→4 majeur

spécialisation plus forte
  lorsque l'état candidat forme exactement vii°6→I6
```

Ces clauses sont imbriquées et corrélées ; elles ne doivent pas être présentées
comme deux lois indépendantes.

## Contrôle nul

Après permutation intra-pièce des choix d'alto, les trois gains principaux de
validation sont compris entre `0,000044` et `0,000219`. Leurs intervalles
bootstrap traversent tous zéro. L'ajout de la spécialisation au proxy devient
même négatif (`-0,000127`).

Ce contrôle ciblé ne remplace pas la calibration familiale V3.4 à 49
permutations. Il montre seulement que le contraste d'ablation observé n'est
pas reproduit par ce jeu de réponses mélangées.

## Décision

- conserver le proxy numérique comme règle candidate principale ;
- conserver `vii°6→I6` comme spécialisation explicative et colonne candidate,
  mais pas encore comme règle dure autonome ;
- ne pas ouvrir le test final ;
- ajouter ensuite des statuts harmoniques candidats-dépendants pour déterminer
  si une notion plus générale de fonction dominante vers tonique remplace
  proprement le proxy sans multiplication des clauses.

## Limites

- La validation a déjà servi au processus itératif V3.1–V3.6 et au suivi de
  l'ajustement ; elle n'est plus un test confirmatoire.
- Le bootstrap rééchantillonne les pertes à poids fixes et ne réajuste pas les
  modèles dans chaque réplication.
- Une seule permutation ciblée est comparée ici.
- La tonalité est globale, sans analyse des tonicisations locales.
- Les ensembles de classes décrivent des accords, mais pas leur fonction dans
  tous les contextes.

Les artefacts canoniques sont le
[`rapport authentique`](results/V3_6_TONAL_RULE_ABLATION_REPORT.md), le
[`rapport nul`](results/V3_6_TONAL_RULE_ABLATION_NULL_REPORT.md) et leurs
fichiers JSON associés.
