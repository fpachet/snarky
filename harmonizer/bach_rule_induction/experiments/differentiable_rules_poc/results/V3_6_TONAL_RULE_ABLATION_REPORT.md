# POC V3.6 — ablation du proxy tonal et de son noyau harmonique

## Protocole

- Tâche conditionnelle : choix de la note d'alto.
- Même baseline numérique que V3.1–V3.4.
- Quatre modèles sont réajustés depuis zéro.
- Bootstrap par chorals entiers à poids ajustés fixes, 1 000 réplications.
- Le test final reste scellé.
- Chorals authentiques.

## Couverture des colonnes

| Colonne | Train | Validation |
|---|---:|---:|
| `TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4` | 47/54 | 19/19 |
| `TONAL_EXACT_VII6_TO_I6` | 41/43 | 12/12 |

## Modèles réajustés

| Modèle | Colonnes | NLL validation | NLL contexte proxy | NLL contexte harmonique | Poids |
|---|---|---:|---:|---:|---|
| baseline | — | 1.276210 | 1.554141 | 1.873731 | — |
| proxy | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4 | 1.269022 | 0.274217 | 0.359860 | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4=2.670 |
| harmonic | TONAL_EXACT_VII6_TO_I6 | 1.270669 | 0.575794 | 0.307652 | TONAL_EXACT_VII6_TO_I6=2.852 |
| both | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4, TONAL_EXACT_VII6_TO_I6 | 1.268457 | 0.178155 | 0.126670 | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4=1.857, TONAL_EXACT_VII6_TO_I6=2.015 |

## Comparaisons et ablations réajustées

| Comparaison | Gain NLL validation | Bootstrap validation, médiane [95 %] | P(gain > 0) |
|---|---:|---:|---:|
| `baseline_to_proxy` | +0.00718776 | +0.00714494 [+0.00379055 ; +0.01086561] | 1.000 |
| `baseline_to_harmonic` | +0.00554117 | +0.00534753 [+0.00237130 ; +0.00924601] | 1.000 |
| `baseline_to_both` | +0.00775281 | +0.00758213 [+0.00383191 ; +0.01218803] | 1.000 |
| `proxy_to_both_harmonic_increment` | +0.00056505 | +0.00057502 [-0.00000829 ; +0.00115683] | 0.972 |
| `harmonic_to_both_proxy_increment` | +0.00221164 | +0.00217244 [+0.00094326 ; +0.00377523] | 1.000 |
