# K3-V29-STRONG-SUCCESSION-GROUP-1 — groupe exhaustif de sonorités résiduelles

Les 36 cellules sont apprises simultanément au-dessus du socle gelé. Elles ne dupliquent aucun
accord nommé unique et forment une partition mutuellement exclusive.

| Candidat | λ | NLL validation/pièce | Gain apparié | IC bootstrap 95 % | Chorals améliorés |
|---|---:|---:|---:|---:|---:|
| socle V28 réajusté | — | 0.767133 | — | — | — |
| groupe V29 succession forte λ=0.6 | 0.6 | 0.755650 | +0.011484 | [+0.004051, +0.018474] | 9/10 | **← retenu**
| groupe V29 succession forte λ=0.3 | 0.3 | 0.751802 | +0.015331 | [+0.004790, +0.025092] | 9/10 |
| groupe V29 succession forte λ=0.1 | 0.1 | 0.750936 | +0.016197 | [+0.004577, +0.026774] | 9/10 |
| groupe V29 succession forte λ=0.03 | 0.03 | 0.750614 | +0.016520 | [+0.004583, +0.027320] | 9/10 |
| groupe V29 succession forte λ=0 | 0 | 0.750483 | +0.016650 | [+0.004559, +0.027599] | 9/10 |

- Sélection : `groupe V29 succession forte λ=0.6`.
- Groupe retenu sur ce découpage : `true`.

## Poids du candidat retenu

| Statut | Poids |
|---|---:|
| `consonant_scaffold__to__consonant_scaffold__with__repeated_bass` | -0.0840 |
| `consonant_scaffold__to__consonant_scaffold__with__semitone_arrival` | +0.3051 |
| `consonant_scaffold__to__consonant_scaffold__with__whole_tone_arrival` | -0.2964 |
| `consonant_scaffold__to__consonant_scaffold__with__skip_or_leap_arrival` | +0.2674 |
| `consonant_scaffold__to__other_named_sonority__with__repeated_bass` | +0.1603 |
| `consonant_scaffold__to__other_named_sonority__with__semitone_arrival` | -0.1667 |
| `consonant_scaffold__to__other_named_sonority__with__whole_tone_arrival` | +0.0562 |
| `consonant_scaffold__to__other_named_sonority__with__skip_or_leap_arrival` | +0.2720 |
| `consonant_scaffold__to__residual_sonority__with__repeated_bass` | -0.0229 |
| `consonant_scaffold__to__residual_sonority__with__semitone_arrival` | +0.0506 |
| `consonant_scaffold__to__residual_sonority__with__whole_tone_arrival` | +0.2186 |
| `consonant_scaffold__to__residual_sonority__with__skip_or_leap_arrival` | -0.2417 |
| `other_named_sonority__to__consonant_scaffold__with__repeated_bass` | +0.2287 |
| `other_named_sonority__to__consonant_scaffold__with__semitone_arrival` | +0.2956 |
| `other_named_sonority__to__consonant_scaffold__with__whole_tone_arrival` | +0.1788 |
| `other_named_sonority__to__consonant_scaffold__with__skip_or_leap_arrival` | +0.0716 |
| `other_named_sonority__to__other_named_sonority__with__repeated_bass` | +0.3413 |
| `other_named_sonority__to__other_named_sonority__with__semitone_arrival` | -0.3124 |
| `other_named_sonority__to__other_named_sonority__with__whole_tone_arrival` | +0.3019 |
| `other_named_sonority__to__other_named_sonority__with__skip_or_leap_arrival` | -0.2684 |
| `other_named_sonority__to__residual_sonority__with__repeated_bass` | -0.0716 |
| `other_named_sonority__to__residual_sonority__with__semitone_arrival` | +0.3240 |
| `other_named_sonority__to__residual_sonority__with__whole_tone_arrival` | -0.2944 |
| `other_named_sonority__to__residual_sonority__with__skip_or_leap_arrival` | +0.0070 |
| `residual_sonority__to__consonant_scaffold__with__repeated_bass` | +0.1010 |
| `residual_sonority__to__consonant_scaffold__with__semitone_arrival` | -0.3001 |
| `residual_sonority__to__consonant_scaffold__with__whole_tone_arrival` | -0.2284 |
| `residual_sonority__to__consonant_scaffold__with__skip_or_leap_arrival` | -0.2261 |
| `residual_sonority__to__other_named_sonority__with__repeated_bass` | -0.0800 |
| `residual_sonority__to__other_named_sonority__with__semitone_arrival` | -0.2770 |
| `residual_sonority__to__other_named_sonority__with__whole_tone_arrival` | -0.3256 |
| `residual_sonority__to__other_named_sonority__with__skip_or_leap_arrival` | -0.3100 |
| `residual_sonority__to__residual_sonority__with__repeated_bass` | -0.2533 |
| `residual_sonority__to__residual_sonority__with__semitone_arrival` | -0.1271 |
| `residual_sonority__to__residual_sonority__with__whole_tone_arrival` | +0.2246 |
| `residual_sonority__to__residual_sonority__with__skip_or_leap_arrival` | +0.1787 |

Ces coefficients sont des contributions conjointes. Un statut rare
ou absent n'est pas promu en contrainte dure par cette expérience.
