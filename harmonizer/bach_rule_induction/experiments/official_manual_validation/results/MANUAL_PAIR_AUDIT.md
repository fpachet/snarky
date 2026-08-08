# Audit Snarky du manuel Bach

Chaque ligne compare l'extrait authentique et sa mutation pédagogique
avec le même RuleGroup et sans réajuster aucun poids.

- Contrastes réussis : `12` / `12`.
- Le split test du corpus n'est pas chargé.

| Étude | Relation | Bach | Variante | Résultat |
|---|---:|---:|---:|---:|
| rule_001_parallel_fifths | `violates` | 0 | 1 | PASS |
| rule_002_parallel_octaves | `violates` | 0 | 1 | PASS |
| rule_003_direct_fifths | `violates` | 0 | 1 | PASS |
| rule_004_voice_crossing | `violates` | 0 | 1 | PASS |
| rule_005_voice_overlap | `violates` | 0 | 1 | PASS |
| rule_006_common_notes | `satisfies` | 8 | 7 | PASS |
| rule_007_contrary_motion | `satisfies` | 2 | 1 | PASS |
| rule_008_compensated_leaps | `satisfies` | 1 | 0 | PASS |
| rule_009_dissonance_preparation | `satisfies` | 2 | 1 | PASS |
| rule_010_leading_tone | `satisfies` | 1 | 0 | PASS |
| rule_011_singable_line | `violates` | 1 | 2 | PASS |
| rule_012_active_inner_voices | `violates` | 0 | 1 | PASS |

Ce test valide la sémantique différentielle des règles, pas leur
suffisance comme théorie complète du style de Bach.
