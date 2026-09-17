# V22 — parité du RuleGroup Snarky

- Statut : `PASS`.
- Décisions K3 : `128`.
- Alternatives par décision : `46`.
- Facteurs : `43`.
- Groupe : `k3_v22_shared_root_motion`.
- Erreur maximale des contributions factorielles : `1.776e-15`.
- Erreur maximale des scores locaux : `0.000e+00`.
- Erreur maximale des probabilités : `0.000e+00`.

Le générateur utilise le même évaluateur compilé pour éviter
le coût d'une matérialisation de faits à chaque candidate. Ce
test établit que ses activations et sommes sont exactement
celles du programme `FACTOR` Snarky sur l'échantillon.
