# V25 — apprentissage génératif des licences faibles

Le vocabulaire V25 et les 65 poids V24 restent gelés. Seuls les neuf
poids faibles sont mis à jour par les moments `Bach − générateur`.

| Itération | Résiduel Bach | Résiduel généré | MAE | Norme poids |
|---:|---:|---:|---:|---:|
| 0 | 0.2488 | 0.3258 | 0.01137 | 0.0000 |
| 1 | 0.2488 | 0.3141 | 0.00956 | 0.0360 |
| 2 | 0.2488 | 0.3096 | 0.00856 | 0.0646 |
| 3 | 0.2488 | 0.3069 | 0.00826 | 0.0911 |
| 4 | 0.2488 | 0.3069 | 0.00806 | 0.1145 |
| 5 | 0.2488 | 0.3051 | 0.00816 | 0.1373 |
| 6 | 0.2488 | 0.3069 | 0.00726 | 0.1606 |
| 7 | 0.2488 | 0.3087 | 0.00836 | 0.1822 |
| 8 | 0.2488 | 0.3064 | 0.00931 | 0.2044 |

## Point d'arrêt sélectionné

L'itération `6` minimise la MAE des neuf moments sur l'échantillon d'apprentissage. Ses poids, plus modérés que ceux de la dernière itération, sont exportés.

| Statut | Bach | Généré au point d'arrêt | Poids |
|---|---:|---:|---:|
| `exact_named_ambiguous` | 0.0171 | 0.0194 | -0.0153 |
| `incomplete_consonant_triad` | 0.0261 | 0.0252 | +0.0102 |
| `triad_plus_one_ambiguous` | 0.0000 | 0.0054 | -0.0191 |
| `triad_plus_passing` | 0.0072 | 0.0063 | +0.0049 |
| `triad_plus_neighbor` | 0.0000 | 0.0014 | -0.0042 |
| `triad_plus_suspension` | 0.0090 | 0.0072 | +0.0120 |
| `triad_plus_appoggiatura` | 0.0000 | 0.0027 | -0.0069 |
| `triad_plus_unlicensed` | 0.0469 | 0.0527 | -0.0096 |
| `other_unlicensed` | 0.1424 | 0.1866 | -0.1574 |

La validation n'est jamais consultée pendant ces mises à jour.
Aucun statut n'est converti en contrainte dure.
