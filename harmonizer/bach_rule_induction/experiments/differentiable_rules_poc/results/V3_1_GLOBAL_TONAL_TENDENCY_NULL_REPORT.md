# POC V3.1 — première obligation tonale

## Audit des statuts

- 352/352 chorals ont une tonalité unique et cohérente dans les quatre voix.
- Modes : `{'major': 176, 'minor': 176}`.
- Aucun changement de signature détecté.
- La tonalité locale est provisoirement la tonalité globale notée.
- Le test final reste scellé.
- Contrôle nul par permutation.

## Scan des douze classes relatives à la tonique

Conclusion testée uniformément : `candidate == previous + 1`.

| Classe source | z train | z validation | Pic local train/val. | Taux observé/attendu val. | Bootstrap val. médian [95 %] | P(z val. > 0) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -11.907 | -6.939 | -1.052 / -1.389 | 0.0072 / 0.0335 | -7.031 [-8.604 ; -4.981] | 0.000 |
| 1 | -1.402 | -1.935 | 0.200 / -0.107 | 0.0505 / 0.1103 | -1.918 [-3.287 ; -0.149] | 0.021 |
| 2 | 3.818 | 2.081 | 0.571 / 1.615 | 0.0692 / 0.0575 | 1.981 [-1.334 ; 5.240] | 0.886 |
| 3 | -6.887 | -5.085 | -0.907 / -2.313 | 0.0048 / 0.0379 | -5.093 [-6.045 ; -3.981] | 0.000 |
| 4 | 8.211 | 3.146 | 1.251 / 1.702 | 0.1005 / 0.0754 | 3.150 [0.369 ; 5.806] | 0.987 |
| 5 | -11.542 | -3.874 | -1.588 / -1.097 | 0.0157 / 0.0333 | -3.904 [-5.747 ; -1.860] | 0.000 |
| 6 | 6.449 | 2.621 | 1.031 / 0.940 | 0.1895 / 0.1268 | 2.518 [0.028 ; 5.178] | 0.976 |
| 7 | 1.369 | -2.984 | 0.082 / -0.341 | 0.0325 / 0.0450 | -3.015 [-5.176 ; -0.700] | 0.005 |
| 8 | -6.089 | -1.751 | -0.221 / -0.073 | 0.0421 / 0.0609 | -1.772 [-3.301 ; 0.033] | 0.028 |
| 9 | -8.007 | -1.920 | -0.427 / -0.273 | 0.0432 / 0.0564 | -1.846 [-3.930 ; 0.192] | 0.038 |
| 10 | 1.172 | 2.251 | 0.154 / 0.269 | 0.0453 / 0.0309 | 2.252 [-0.423 ; 5.033] | 0.952 |
| 11 | 16.097 | 6.968 | 0.906 / 1.067 | 0.1881 / 0.1152 | 6.854 [4.310 ; 9.784] | 1.000 |

## Sélection

- Classes retenues : `[]`.

## Statut sémantique

`MISSING_CONTEXT_FOR_EQUIVALENCE` : la classe numérique peut être
comparée à la sensible, mais le modèle ne possède pas encore le rôle
harmonique de l'accord source ni les exceptions cadentielles de
`R-LEADING-001`.
