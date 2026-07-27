# V5-K3-CLEAN

Expérience clean-room fondée sur une seule hypothèse musicale structurelle :
les règles portent sur trois blocs verticaux consécutifs.

Le dossier ne charge aucun fichier de `rules/` ni aucun manifeste de
`rule_bases/historical` ou `rule_bases/learned`.

## Composants

- `k3.py` : représentation du corpus, catalogue numérique, gradient et Gibbs ;
- `run_induction.py` : construction du corpus et génération de colonnes ;
- `run_gibbs_diagnostic.py` : génération dense avec le modèle appris ;
- `results/` : artefacts et rapports reproductibles.

`V5.0` conserve le premier catalogue spécialisé, qui a appris huit variantes
de la même préférence mélodique. `V5.1` ajoute des prédicats invariants par
voix et symétriques dans le temps afin que la loi générale soit sélectionnée
avant d'éventuelles spécialisations.

Résultats principaux :

- [`V5_1_K3_COMPACT_REPORT.md`](results/V5_1_K3_COMPACT_REPORT.md) ;
- [`V5_1_K3_COMPACT_NULL_REPORT.md`](results/V5_1_K3_COMPACT_NULL_REPORT.md) ;
- [`V5_1_AUTHENTIC_NULL_COMPARISON.md`](results/V5_1_AUTHENTIC_NULL_COMPARISON.md) ;
- [`V5_2_FIRST_RULE_AUDIT.md`](results/V5_2_FIRST_RULE_AUDIT.md), audit du
  seuil mélodique `> 2` ;
- `v5_1_k3_compact_model.json`, modèle complet pour le Gibbs.

Le protocole complet est
[`../../V5_K3_CLEAN_PROTOCOL.md`](../../V5_K3_CLEAN_PROTOCOL.md), et les
expériences remplacées comme axe principal sont résumées dans
[`../../EXPERIMENT_HISTORY.md`](../../EXPERIMENT_HISTORY.md).
