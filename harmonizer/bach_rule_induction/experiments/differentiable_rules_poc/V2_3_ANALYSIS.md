# Analyse du POC V2.3 — parallèles dans les six paires de voix

## Résultat

Le POC V2.3 teste uniformément les douze classes d'intervalle pour le patron :

```text
classe_source == k
AND classe_cible == k
AND mouvements_de_même_signe_non_nul
→ éviter
```

Avec un budget de deux règles, les classes retenues sont exactement `0` et
`7`. Après dévoilement des noms musicologiques, elles correspondent aux
octaves ou unissons parallèles et aux quintes parallèles. Le contrôle permuté
ne sélectionne aucune classe. Le test final de 51 chorals reste scellé.

## Extension par rapport au V1

Le V1 avait observé ces patrons uniquement entre soprano et basse. Le V2.3 les
recherche maintenant dans les six paires :

```text
S-A, S-T, S-B, A-T, A-B, T-B
```

Chaque décision d'une voix énumère ses candidates dans la tessiture DeepBach.
Pour chacune des trois autres voix, le programme calcule les classes source et
cible ainsi que les signes des deux mouvements. Il n'utilise ni le terme
*parallèle*, ni les classes expertes `0/7`, ni les verdicts Snarky.

## Résidus conditionnels

| Classe | z train | z validation | Bootstrap validation, médiane [95 %] |
|---:|---:|---:|---:|
| 0 | -48,430 | -21,588 | -21,560 [-23,154 ; -19,864] |
| 7 | -45,585 | -20,314 | -20,364 [-22,027 ; -18,610] |

Les taux observés sont `0,00648` contre `0,10894` attendu pour la classe `0`
sur train, et `0,01428` contre `0,10650` pour la classe `7`. Le signe du
bootstrap est négatif dans 100 % des 1 000 réplications de train et de
validation.

## Critère de parcimonie

Le contraste entre classes voisines utilisé pour le triton n'est pas adapté :
les classes `1` et `11` sont elles-mêmes presque absentes dans ce contexte. Le
V2.3 emploie donc :

```text
z train <= -10
AND z validation <= -5
AND P_bootstrap(z validation < 0) >= 0,95
→ classer par gain résiduel
→ conserver au plus deux classes
```

Ces seuils exploratoires sont plus stricts que ceux du V2.2, car l'agrégation
sur six paires donne un support beaucoup plus grand. Ils conservent `0/7` sur
le corpus complet et sur le smoke test de vingt pièces.

Avec les seuils plus permissifs du V2.2, le contrôle nul produisait une fausse
alerte sur la classe `4`. Le seuil familial strict la rejette. Dans le contrôle
final, les z de `0` sont `-0,668/-0,836` et ceux de `7`
`+0,365/-0,624`.

## Comparaison avec Snarky

La comparaison postérieure énumère 1 130 364 états locaux valides par classe
dans les six paires de tessitures. Les formules numériques apprises ont zéro
désaccord avec :

- `R-PARALLEL-001` pour la classe `0` ;
- `R-PARALLEL-002` pour la classe `7`.

Les deux résultats sont donc classés `RECOVERED_EQUIVALENT` sur ce domaine.

## Ce qui est établi

1. Les patrons du V1 se généralisent aux voix intérieures.
2. La notion anonyme de mouvement de même signe est réutilisable dans une
   nouvelle campagne.
3. Les classes `0/7` dominent fortement les dix autres classes sous un budget
   de deux règles.
4. Le contrôle permuté ne sélectionne aucune classe avec le protocole final.
5. Les deux formules sont équivalentes aux règles Snarky cachées sur le
   domaine fini testé.

## Limites et suite

- Le seuil familial a été ajusté pendant cette phase exploratoire ; il doit
  être gelé avant l'ouverture du test.
- Une paire qui attaque simultanément peut contribuer aux décisions des deux
  voix. Une analyse de sensibilité doit dédupliquer ces attaques.
- Les exceptions authentiques et leur contexte métrique ou harmonique ne sont
  pas encore analysés.
- Le prochain jalon est une ablation conjointe : ajuster les six règles de
  niveau A dans un même modèle, quantifier leur gain propre et leur
  redondance, puis seulement ajouter les premiers statuts tonals nécessaires
  aux obligations.
