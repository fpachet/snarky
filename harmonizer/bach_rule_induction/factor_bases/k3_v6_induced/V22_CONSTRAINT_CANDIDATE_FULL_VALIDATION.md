# V22 — validation élargie des contraintes candidates

Les interdictions exactes découvertes sur 32/10 chorals sont réévaluées
directement sur toutes les décisions des 251 chorals de train et des
50 de validation. Le test réservé reste fermé.

## Résumé

- Candidats exacts issus de la structure : `88`.
- Toujours sans exception sur train et validation : `40`.
- Décisions train/validation : `68263/13202`.

## Familles survivantes

| Famille | Candidats |
|---|---:|
| `direct_arrival_interval` | 4 |
| `melodic_large_or_rare_interval` | 12 |
| `named_harmonic_exclusion` | 1 |
| `parallel_preserved_interval` | 2 |
| `voice_order_and_minimum_spacing` | 21 |

## Candidats exacts les mieux couverts

| Famille | Prédicat | Train occasions | Validation occasions |
|---|---|---:|---:|
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ 0 demi-tons au bloc central | 18044 | 3553 |
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ 1 demi-tons au bloc central | 18044 | 3553 |
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ -1 demi-tons au bloc central | 18043 | 3552 |
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ -2 demi-tons au bloc central | 18042 | 3552 |
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ -1 demi-tons au bloc précédent | 18042 | 3549 |
| `voice_order_and_minimum_spacing` | basse et soprano : écart ordonné ≤ -2 demi-tons au bloc précédent | 18040 | 3549 |
| `melodic_large_or_rare_interval` | ténor : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 17948 | 3426 |
| `melodic_large_or_rare_interval` | ténor : mouvement depuis la note précédente supérieur à 12 demi-tons | 17948 | 3426 |
| `voice_order_and_minimum_spacing` | ténor et soprano : écart ordonné ≤ -1 demi-tons au bloc central | 17946 | 3425 |
| `voice_order_and_minimum_spacing` | ténor et soprano : écart ordonné ≤ -2 demi-tons au bloc central | 17944 | 3425 |
| `melodic_large_or_rare_interval` | alto : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 17637 | 3436 |
| `melodic_large_or_rare_interval` | alto : mouvement depuis la note précédente supérieur à 12 demi-tons | 17637 | 3436 |
| `voice_order_and_minimum_spacing` | alto et basse : écart ordonné ≤ -1 demi-tons au bloc central | 17620 | 3432 |
| `voice_order_and_minimum_spacing` | alto et basse : écart ordonné ≤ -2 demi-tons au bloc central | 17620 | 3432 |
| `voice_order_and_minimum_spacing` | alto et basse : écart ordonné ≤ -2 demi-tons au bloc précédent | 17619 | 3433 |
| `melodic_large_or_rare_interval` | soprano : intervalle depuis la note précédente de classe 11 (septième majeure modulo l’octave) | 14634 | 2787 |
| `melodic_large_or_rare_interval` | soprano : mouvement depuis la note précédente supérieur à 12 demi-tons | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et ténor : écart ordonné ≤ -1 demi-tons au bloc central | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et ténor : écart ordonné ≤ -2 demi-tons au bloc central | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ 0 demi-tons au bloc central | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ 1 demi-tons au bloc central | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ 0 demi-tons au bloc précédent | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ 1 demi-tons au bloc précédent | 14634 | 2787 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ -1 demi-tons au bloc central | 14618 | 2783 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ -2 demi-tons au bloc central | 14618 | 2783 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ -1 demi-tons au bloc précédent | 14617 | 2785 |
| `voice_order_and_minimum_spacing` | soprano et basse : écart ordonné ≤ -2 demi-tons au bloc précédent | 14616 | 2785 |
| `direct_arrival_interval` | ténor avec basse : arrive par mouvement direct sur la classe d’intervalle 1 | 14008 | 2709 |
| `melodic_large_or_rare_interval` | ténor : intervalle vers la note suivante de classe 11 (septième majeure modulo l’octave) | 12634 | 2358 |
| `melodic_large_or_rare_interval` | ténor : mouvement vers la note suivante supérieur à 12 demi-tons | 12634 | 2358 |
| `melodic_large_or_rare_interval` | alto : intervalle vers la note suivante de classe 11 (septième majeure modulo l’octave) | 12183 | 2379 |
| `melodic_large_or_rare_interval` | alto : mouvement vers la note suivante supérieur à 12 demi-tons | 12183 | 2379 |
| `direct_arrival_interval` | alto avec ténor : arrive par mouvement direct sur la classe d’intervalle 1 | 10994 | 2196 |
| `direct_arrival_interval` | basse avec ténor : arrive par mouvement direct sur la classe d’intervalle 1 | 10774 | 2145 |
| `direct_arrival_interval` | ténor avec alto : arrive par mouvement direct sur la classe d’intervalle 1 | 10422 | 1977 |
| `melodic_large_or_rare_interval` | soprano : intervalle vers la note suivante de classe 11 (septième majeure modulo l’octave) | 7288 | 1328 |
| `melodic_large_or_rare_interval` | soprano : mouvement vers la note suivante supérieur à 12 demi-tons | 7288 | 1328 |
| `parallel_preserved_interval` | au moins une paire de voix : conserve l’intervalle de classe 11 par mouvement direct non nul | 1215 | 215 |
| `parallel_preserved_interval` | au moins une paire de voix : conserve l’intervalle de classe 1 par mouvement direct non nul | 1023 | 184 |
| `named_harmonic_exclusion` | bloc central : septième majeure sur fondamentale à 2 demi-tons de la tonique | 734 | 153 |

Ces candidats ne sont toujours pas des contraintes logiques. Les
seuils emboîtés, les deux orientations d'une paire de voix et les
prédicats impliqués par une règle plus générale doivent être
fusionnés avant toute compilation en filtre dur.
