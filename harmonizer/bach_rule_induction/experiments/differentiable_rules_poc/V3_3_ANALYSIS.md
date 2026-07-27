# Analyse du POC V3.3 — le mode comme statut explicite

## Changement minimal

V3.3 ne change ni la conclusion, ni le modèle de gradient, ni les classes
tonales. Il ajoute seulement `global_key_mode` à la prémisse et énumère :

```text
mode × voix × classe_basse_source × classe_basse_cible
```

Les 864 candidats restent locaux, indépendants et directement traduisibles en
clauses Snarky. Le seuil de support train descend de 30 à 20 pour ne pas
éliminer mécaniquement les strates de mode ; tous les autres seuils sont ceux
de V3.2.

## Résultat

Sept clauses sont retenues sur les chorals authentiques, aucune sur le contrôle
permuté.

| Mode | Voix | Basse | Résolution train | Résolution validation | Interprétation postérieure |
|---|---|---:|---:|---:|---|
| mineur | alto | `2→0` | 49/49 | 12/12 | `vii°6 → i` proxy |
| mineur | ténor | `7→8` | 25/25 | 11/11 | cadence rompue `V → VI` proxy |
| mineur | soprano | `7→0` | 32/34 | 11/11 | `V → i` proxy |
| majeur | ténor | `5→4` | 24/26 | 9/10 | `V4/2 → I6` proxy |
| majeur | alto | `2→4` | 47/54 | 19/19 | `vii°6 → I6` proxy |
| majeur | alto | `2→0` | 34/43 | 15/16 | `vii°6 → I` proxy |
| mineur | alto | `7→3` | 19/28 | 6/8 | résolution trompeuse `V → III` proxy |

Le patron qui motivait la nouvelle feature est maintenant correctement
séparé : `ténor + basse 7→8` n'est retenu qu'en mineur. Le mode a donc amélioré
à la fois la précision et l'intelligibilité de la règle.

## Ce que le système a réellement découvert

La recherche n'a pas reçu les symboles `V`, `vii°6`, `I6`, cadence parfaite ou
cadence rompue. Elle a trouvé des conjonctions de classes chromatiques et de
voix. Les noms de progressions ont été proposés seulement après inspection des
états SATB enregistrés.

Le résultat est plus précis que l'aphorisme pédagogique « la sensible monte » :
il quantifie les contextes locaux où cette résolution approche l'obligation,
sépare les voix et met en évidence une interaction de mode. Il ne prouve pas
encore une nouvelle loi musicale ; il montre qu'une petite grammaire de faits
explicites peut reconstruire des contextes harmoniques sans les encoder
directement.

## Statut scientifique

Les sept clauses restent `CANDIDATE_REFINEMENT` :

- le signe bootstrap est positif dans au moins 95 % des réplications, mais
  certains intervalles à 95 % recouvrent zéro et les supports restent faibles ;
- une seule permutation n'est pas une calibration familiale suffisante ;
- les proxys d'accord doivent être comparés à une analyse harmonique
  indépendante ;
- les seuils et le budget doivent être gelés avant le test final ;
- aucune règle n'est encore compilée dans l'harmoniseur de production.

Le [V3.4](V3_4_ANALYSIS.md) a depuis effectué cette calibration sur 49
permutations complètes. Une seule des sept clauses survit à 5 % après
correction familiale : `majeur + alto + basse 2→4`, avec `p = 0,02`. Les six
autres restent des hypothèses descriptives.
