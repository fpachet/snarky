# POC V3.6 — ablation du proxy tonal et de son noyau harmonique

## Protocole

- Tâche conditionnelle : choix de la note d'alto.
- Même baseline numérique que V3.1–V3.4.
- Quatre modèles sont réajustés depuis zéro.
- Bootstrap par chorals entiers à poids ajustés fixes, 1 000 réplications.
- Le test final reste scellé.
- Contrôle nul ciblé par permutation.

## Couverture des colonnes

| Colonne | Train | Validation |
|---|---:|---:|
| `TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4` | 13/54 | 4/19 |
| `TONAL_EXACT_VII6_TO_I6` | 12/43 | 2/12 |

## Modèles réajustés

| Modèle | Colonnes | NLL validation | NLL contexte proxy | NLL contexte harmonique | Poids |
|---|---|---:|---:|---:|---|
| baseline | — | 2.353139 | 1.920359 | 1.967338 | — |
| proxy | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4 | 2.352920 | 1.874680 | 1.929464 | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4=1.058 |
| harmonic | TONAL_EXACT_VII6_TO_I6 | 2.353095 | 1.906426 | 1.944237 | TONAL_EXACT_VII6_TO_I6=1.354 |
| both | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4, TONAL_EXACT_VII6_TO_I6 | 2.353047 | 1.897603 | 1.941233 | TONAL_PROXY_MAJOR_ALTO_BASS_2_TO_4=0.145, TONAL_EXACT_VII6_TO_I6=1.166 |

## Comparaisons et ablations réajustées

| Comparaison | Gain NLL validation | Bootstrap validation, médiane [95 %] | P(gain > 0) |
|---|---:|---:|---:|
| `baseline_to_proxy` | +0.00021890 | +0.00018829 [-0.00067065 ; +0.00117391] | 0.659 |
| `baseline_to_harmonic` | +0.00004447 | +0.00001305 [-0.00043001 ; +0.00062682] | 0.519 |
| `baseline_to_both` | +0.00009226 | +0.00007832 [-0.00038630 ; +0.00072510] | 0.603 |
| `proxy_to_both_harmonic_increment` | -0.00012663 | -0.00011916 [-0.00084820 ; +0.00059758] | 0.369 |
| `harmonic_to_both_proxy_increment` | +0.00004779 | +0.00004336 [-0.00004856 ; +0.00016134] | 0.796 |
