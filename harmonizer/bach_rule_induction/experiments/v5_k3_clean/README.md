# V5-K3-CLEAN

Expérience clean-room fondée sur une seule hypothèse musicale structurelle :
les règles portent sur trois blocs verticaux consécutifs.

Le dossier ne charge aucun fichier de `rules/` ni aucun manifeste de
`rule_bases/historical` ou `rule_bases/learned`.

## Composants

- `k3.py` : représentation du corpus, catalogue numérique, gradient et Gibbs ;
- `run_induction.py` : construction du corpus et génération de colonnes ;
- `run_gibbs_diagnostic.py` : génération dense avec le modèle appris ;
- `run_k3_ablation.py` : retrait d'une règle et réajustement des autres ;
- `run_k3_null_max_calibration.py` : calibration familiale de la première règle ;
- `run_rhythmic_gibbs.py` : génération des hauteurs sur une grille polyphonique
  réelle d'attaques et de tenues ;
- `run_contextual_induction.py` : réinduction depuis zéro avec tonalité,
  métrique, répétitions attaquées et fingerprints verticaux ;
- `run_contextual_generation_comparison.py` : comparaison contrôlée
  Bach/V5.5/V5.6/V5.7 sur le même soprano et le même rythme ;
- `run_chromatic_residual_audit.py` : calibration conditionnelle des classes
  tonales empiriquement rares sur validation ;
- `run_multichoral_generation_audit.py` : campagne Gibbs reproductible sur
  plusieurs chorals et plusieurs graines ;
- `run_chromatic_loop_comparison.py` : décision avant/après et protocole V5.9 ;
- `run_generative_moment_calibration.py` : calibration de huit règles maximum
  par contraste de moments Bach−Gibbs sur train ;
- `run_v5_9_comparison.py` : validation appariée V5.7/V5.8/V5.9 et retour sur
  BWV 108.6 ;
- `run_generative_residual_audit.py` : second tour sur les licences restantes
  et les interactions avec les empreintes verticales locales ;
- `local_tonality.py` : HMM transposable et apprentissage EM d'un statut tonal
  latent à partir des noyaux K3 ;
- `run_local_tonality_poc.py` : ajustement train et évaluation tenue à part ;
- `run_local_tonality_sensitivity.py` : robustesse à la persistance du statut ;
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
- [`V5_3_K3_REFIT_ABLATION.md`](results/V5_3_K3_REFIT_ABLATION.md), contribution
  conditionnelle de chaque règle après réajustement des onze autres ;
- [`V5_4_K3_FIRST_COLUMN_NULL_MAX.md`](results/V5_4_K3_FIRST_COLUMN_NULL_MAX.md),
  calibration de la première découverte contre le maximum des faux signaux ;
- [`V5_5_K3_RHYTHMIC_GIBBS.md`](results/V5_5_K3_RHYTHMIC_GIBBS.md), premier
  choral avec croches, doubles-croches et tenues par voix ;
- [`V5_6_K3_CONTEXTUAL_REINDUCTION.md`](results/V5_6_K3_CONTEXTUAL_REINDUCTION.md),
  redécouverte numérique des principales sonorités triadiques ;
- [`V5_7_K3_CONTEXTUAL_REINDUCTION.md`](results/V5_7_K3_CONTEXTUAL_REINDUCTION.md),
  raffinement tonal et répétition attaquée par voix ;
- [`V5_7_CONTEXTUAL_GENERATION_COMPARISON.md`](results/V5_7_CONTEXTUAL_GENERATION_COMPARISON.md),
  mesure avant/après des défauts observés dans la partition ;
- [`V5_8_CHROMATIC_RESIDUAL_AUDIT.md`](results/V5_8_CHROMATIC_RESIDUAL_AUDIT.md),
  contraste entre choix rares observés et attendus sur validation ;
- [`V5_8_MULTICHORAL_GENERATION_AUDIT.md`](results/V5_8_MULTICHORAL_GENERATION_AUDIT.md),
  première campagne générative V5.7 sur 20 chorals ;
- [`V5_8_CHROMATIC_LOOP_COMPARISON.md`](results/V5_8_CHROMATIC_LOOP_COMPARISON.md),
  rejet génératif de V5.8 et définition du gradient V5.9 ;
- [`V5_9_GENERATIVE_CALIBRATION.md`](results/V5_9_GENERATIVE_CALIBRATION.md),
  poids appris par les chaînes persistantes sur train ;
- [`V5_9_GENERATIVE_VALIDATION_COMPARISON.md`](results/V5_9_GENERATIVE_VALIDATION_COMPARISON.md),
  promotion expérimentale de V5.9 après validation multi-chorals ;
- [`V5_10_GENERATIVE_RESIDUAL_AUDIT.md`](results/V5_10_GENERATIVE_RESIDUAL_AUDIT.md),
  clôture négative des licences simples et verticales ;
- [`V5_11_LOCAL_TONALITY_HMM.md`](results/V5_11_LOCAL_TONALITY_HMM.md),
  validation du statut tonal latent ;
- [`V5_11_LOCAL_TONALITY_SENSITIVITY.md`](results/V5_11_LOCAL_TONALITY_SENSITIVITY.md),
  robustesse à trois probabilités de persistance ;
- `v5_1_k3_compact_model.json`, modèle complet pour le Gibbs.

Le protocole complet est
[`../../V5_K3_CLEAN_PROTOCOL.md`](../../V5_K3_CLEAN_PROTOCOL.md), et les
expériences remplacées comme axe principal sont résumées dans
[`../../EXPERIMENT_HISTORY.md`](../../EXPERIMENT_HISTORY.md).
