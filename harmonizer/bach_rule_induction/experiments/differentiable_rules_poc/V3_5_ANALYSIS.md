# Analyse du POC V3.5 — contenu harmonique de la clause survivante

## Question

Le V3.4 retient une clause numérique :

```text
mode majeur
AND voix == alto
AND classe_source_alto == 11
AND classe_source_basse == 2
AND classe_cible_basse == 4
→ alto_cible == alto_source + 1
```

Son interprétation postérieure était un proxy de `vii°6→I6`. Le V3.5 vérifie
cette lecture avec les ensembles complets de classes des quatre voix. Ces
ensembles n'ont participé ni à la génération ni à la sélection des clauses
V3.1–V3.4.

L'audit est indépendant du vocabulaire du mineur, mais reste postérieur sur les
mêmes ensembles train et validation. Il ne constitue donc pas un nouveau test
confirmatoire.

## Résultat

L'hypothèse exacte compare :

```text
source : {2, 5, 11}   # vii°6 avec basse 2
cible  : {0, 4, 7}    # I6 avec basse 4
```

| Split | Contexte numérique | `vii°6→I6` exact | Résolution dans le sous-ensemble exact |
|---|---:|---:|---:|
| train | 54 | 41 | 41/41 |
| validation | 19 | 12 | 12/12 |

La cible est exactement l'ensemble de tonique `{0,4,7}` dans 45/54 cas train
et 19/19 cas validation. La source est exactement `{2,5,11}` dans 46/54 et
12/19 cas.

## La clause est plus large que son premier nom

La classification est `PITCH_CLASS_PROXY_PARTIAL`, et non
`PITCH_CLASS_PROXY_CONFIRMED`. L'accord exact ne couvre que 76 % des
occurrences train et 63 % des occurrences validation.

Les signatures sources restantes contiennent notamment :

- `{2,5,7,11}`, compatible avec un accord de dominante septième sur basse `2`;
- `{2,7,11}`, autre état incomplet ou orné de fonction dominante ;
- quelques ensembles chromatiques ou avec notes de passage.

La clause numérique semble donc capter une famille plus générale de
résolutions à basse `2→4`, dont `vii°6→I6` est le noyau le plus fréquent, et
non un accord unique.

## Les exceptions soutiennent néanmoins le noyau exact

Au train :

| Sous-ensemble | Résolutions | Exceptions | Taux |
|---|---:|---:|---:|
| progression exacte | 41 | 0 | 1,000 |
| autres signatures | 6 | 7 | 0,462 |

Le test exact de Fisher unilatéral donne `p = 9,689 × 10⁻⁶`. Cette p-valeur
est descriptive : l'hypothèse harmonique a été formulée après la sélection.
Sur validation, toutes les 19 occurrences résolvent, ce qui empêche de
contraster les deux sous-ensembles.

## Conclusion

L'étiquette `vii°6→I6` est correcte pour un sous-ensemble central et sans
exception observée, mais elle n'est pas équivalente à la clause apprise. Cette
distinction évite de transformer une corrélation numérique plus générale en
règle d'accord artificiellement étroite.

La suite devra comparer au moins deux formulations :

1. la clause chromatique courte apprise ;
2. sa spécialisation harmonique exacte `vii°6→I6`.

Leur gain propre, leur coût descriptif et leurs exceptions seront mesurés dans
la même ablation conjointe avant toute compilation Snarky.
