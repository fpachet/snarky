# Analyse du POC V3.2 — raffinements locaux de la sensible

## Recherche

La prémisse fixe est la classe source `11` trouvée par V3.1. Le programme
énumère ensuite, sans étiquette harmonique :

```text
voix_sujet × classe_basse_source × classe_basse_cible
```

Les 432 clauses ont au plus quatre conditions lisibles :

```text
voix == v
AND classe_relative(source_voix) == 11
AND classe_relative(source_basse) == b0
AND classe_relative(cible_basse) == b1
→ préférer source_voix + 1
```

Le gradient résiduel compare la résolution choisie par Bach à sa probabilité
dans la baseline conditionnelle. Le test final reste scellé.

## Résultat

Quatre contextes passent simultanément les seuils de support, confirmation et
z sur train et validation. Le même sélecteur n'en retient aucun dans le
contrôle permuté.

| Voix | Basse | Résolution train | Résolution validation | z validation |
|---|---:|---:|---:|---:|
| alto | `2→0` | 83/92 | 27/28 | 4,429 |
| alto | `2→4` | 49/56 | 19/19 | 8,050 |
| ténor | `7→8` | 25/33 | 11/13 | 2,305 |
| soprano | `7→0` | 89/123 | 22/25 | 4,214 |

## Interprétation postérieure

Les états SATB conservés dans le JSON rendent les patrons inspectables. Ils
correspondent à des proxys numériques de progressions familières :

- soprano, basse `7→0` : dominante vers tonique, souvent cadentielle ;
- alto, basse `2→0` : accord de sensible au premier renversement vers tonique
  en position fondamentale ;
- alto, basse `2→4` : accord de sensible au premier renversement vers tonique
  au premier renversement ;
- ténor, basse `7→8` : signal agrégé dont l'audit révèle une dépendance
  majeure au mode.

Le mot *proxy* est essentiel. La clause ne teste pas encore les deux autres
classes de l'accord : elle ne doit donc pas être rebaptisée accord ou cadence
avant une vérification harmonique complète.

## Diagnostic de feature

Le quatrième patron fournit exactement la boucle recherchée pour inventer un
statut intelligible :

| Mode | Train | Validation |
|---|---:|---:|
| majeur | 0/8 | 0/2 |
| mineur | 25/25 | 11/11 |

La règle agrégée cache donc deux comportements opposés. La feature minimale
n'est pas un embedding opaque, mais le statut déjà défini
`global_key_mode`. V3.3 réexécute la recherche en l'ajoutant explicitement à
la prémisse.

## Limites

- un seul contrôle nul ne calibre pas encore le maximum des 432 statistiques ;
- les seuils sont exploratoires ;
- la tonalité reste globale et ignore les tonicisations ;
- les analyses d'accord sont postérieures et ne font pas partie de la
  sélection ;
- les répétitions internes à un choral augmentent le nombre d'occurrences,
  même si le bootstrap rééchantillonne des pièces entières.
