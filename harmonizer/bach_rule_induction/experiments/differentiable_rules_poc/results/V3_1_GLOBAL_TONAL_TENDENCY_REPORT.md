# POC V3.1 — première obligation tonale

## Audit des statuts

- 352/352 chorals ont une tonalité unique et cohérente dans les quatre voix.
- Modes : `{'major': 176, 'minor': 176}`.
- Aucun changement de signature détecté.
- La tonalité locale est provisoirement la tonalité globale notée.
- Le test final reste scellé.
- Chorals authentiques.

## Scan des douze classes relatives à la tonique

Conclusion testée uniformément : `candidate == previous + 1`.

| Classe source | z train | z validation | Pic local train/val. | Taux observé/attendu val. | Bootstrap val. médian [95 %] | P(z val. > 0) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -16.875 | -8.080 | -1.121 / -1.687 | 0.0136 / 0.0467 | -8.223 [-10.123 ; -5.748] | 0.000 |
| 1 | -0.265 | 3.447 | 0.374 / 0.988 | 0.4242 / 0.2949 | 3.482 [-0.174 ; 7.022] | 0.966 |
| 2 | 4.079 | -0.228 | 0.838 / 0.586 | 0.1384 / 0.1401 | -0.172 [-4.172 ; 3.101] | 0.472 |
| 3 | -16.540 | -6.928 | -1.719 / -1.783 | 0.0143 / 0.0679 | -6.901 [-8.406 ; -5.061] | 0.000 |
| 4 | 21.063 | 11.275 | 2.163 / 1.970 | 0.3146 / 0.1992 | 11.204 [7.074 ; 15.213] | 1.000 |
| 5 | -18.228 | -8.023 | -2.524 / -1.950 | 0.0124 / 0.0539 | -8.022 [-9.538 ; -6.636] | 0.000 |
| 6 | 17.909 | 9.218 | 1.572 / 1.381 | 0.6947 / 0.4170 | 9.197 [6.951 ; 11.363] | 1.000 |
| 7 | -1.225 | -4.408 | -0.032 / -0.506 | 0.0742 / 0.0978 | -4.524 [-7.820 ; -0.656] | 0.009 |
| 8 | -10.668 | -0.524 | -0.298 / 0.331 | 0.1242 / 0.1307 | -0.437 [-3.197 ; 2.406] | 0.365 |
| 9 | -10.831 | -5.606 | 0.392 / 0.278 | 0.0753 / 0.1225 | -5.681 [-8.206 ; -2.841] | 0.000 |
| 10 | -11.241 | -5.828 | -1.146 / -1.504 | 0.0137 / 0.0602 | -5.785 [-7.348 ; -4.236] | 0.000 |
| 11 | 34.761 | 17.093 | 1.501 / 1.895 | 0.5259 / 0.3074 | 16.958 [14.219 ; 20.106] | 1.000 |

## Sélection

- Classes retenues : `[11]`.
- Interprétation postérieure de `11` : sensible globale.

## Détail par voix sur validation

| Voix | Occurrences testables | Résolutions | Exceptions | Taux observé | Taux attendu | z |
|---|---:|---:|---:|---:|---:|---:|
| Soprano | 115 | 59 | 56 | 0.5130 | 0.2682 | 6.895 |
| Alto | 385 | 190 | 195 | 0.4935 | 0.2617 | 12.512 |
| Tenor | 208 | 115 | 93 | 0.5529 | 0.3107 | 8.488 |
| Bass | 201 | 114 | 87 | 0.5672 | 0.4142 | 5.425 |

## Statut sémantique

`MISSING_CONTEXT_FOR_EQUIVALENCE` : la classe numérique peut être
comparée à la sensible, mais le modèle ne possède pas encore le rôle
harmonique de l'accord source ni les exceptions cadentielles de
`R-LEADING-001`.
