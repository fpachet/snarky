# Documentation

English is the publication language for the Snarky engine, API, architecture,
benchmarks, and application guides. The Spinoza corpus and its formalization
remain in French. Historical sources and quotations retain their original
language with explicit provenance.

Each document has one primary language. Existing French implementation notes
are retained as research history; they are not the publication entry point and
should not be mechanically mixed with English sections.

## Start here

- [Project status and validation map](project_status.md): completed review
  fixes, compatibility boundaries, test scopes, and remaining research work.
- [Runtime boundary tutorials](runtime_tutorial.md): executable examples of
  custom propagation, saved explanations, and factor/choice semantics.
- [Language validation and formatting](language_tooling.md): console usage
  and installation of the optional CSP companion.

## Publication guides in English

- [Architecture](architecture.md)
- [Unified redesign plan](redesign_plan.md): final objectives, runtime separation,
  migration phases, and conformance gates.
- [Redesign performance baseline](performance_baseline.md): fixed non-Bach workloads,
  fresh timings, comparison protocol, and optimization ledger.
- [Prune CSP comparison](performance_prune_2026-09-16.md): shared models, optimization,
  global constraints, independently validated Rust/Python implementation timings,
  interpretation limits and explicit coverage gaps.
- [Redesign implementation evidence](redesign_progress.md)
- [Markov constraints action plan](markov_constraints_plan.md): audited LSDB Blues,
  four scoring modes, numerical guarantees, and ordered solver improvements.
- [Boulez optimization result](performance_boulez_2026-09-16.md): exact published
  sequence regenerated without a seed, with a completed proof and paired benchmarks.
- [Markov implementation progress](markov_constraints_progress.md): corpus audit,
  exact first-order Blues optimization, and remaining acceptance gates.
- [Declarative finite model contract](finite_model_contract.md)
- [Finite model language and migration](finite_language.md)
- [Textual syntax](syntax.md)
- [Language validation and formatting](language_tooling.md)
- [Reference semantics](semantics.md)
- [Snarky Core 0.1 baseline](core_0_1_baseline.md)
- [Learned-factor language plan](learned_factor_language_plan.md)
- [Probabilistic constraint learning and exact generation](probabilistic_constraint_learning_spec.md)
- [Rule programs and sequential steps](rule_programs.md)
- [Persistent finite-domain constraints](persistent_constraints.md)
- [Finite-CSP solver optimization plan](solver_optimization_plan.md)
- [LORE, LAURE, CLAIRE, and Snarky](caseau_rules_constraints.md)
- [API stability](api_stability.md)
- [Versioning and compatibility](versioning.md)
- [Strategy lifecycle](strategy_lifecycle.md)
- [Consolidation plan](consolidation_plan.md)
- [Benchmark guide](../benchmarks/README.md)

## Applications

- [Markov constraints](markov_constraints_application.md): exact Blues and melody
  optimization, paper reproductions, control examples and performance records.
- [Finite CSP](../csp_solver/README.md)
- [Sudoku](../sudoku/README.md)
- [Four-part harmonizer](../harmonizer/README.md)
- [Rulebase catalogue](../rulebases/README.md)

The [Bach experiment](../harmonizer/bach_rule_induction/README.md) is a separate
side project, with independent corpus, learning and generation protocols.

## Focused French research notes

The following documents predate the publication-language policy. They remain
useful design records and each stays consistently French:

- rule groups, programs, mutation, arithmetic, collections, computed objects,
  conflict resolution, and global constraints;
- choice search, propagation, CSP/harmonizer milestones, and optimization
  plans;
- advanced-problem-solving and future-feature roadmaps;
- the original Codex design prompts.

When a topic graduates into the supported publication surface, write or
replace its canonical guide in English and leave historical material clearly
identified rather than producing a mixed-language document.

## Spinoza

The [Spinoza project](../spinoza/README.md), systematic atlas, source
formalization, and reports intentionally remain in French. A later English
overview may introduce the case study without translating or replacing the
French research corpus.

## External sources

PDFs, presentations, theses, and third-party rule corpora are reference
material, not automatically redistributable project documentation. Their
origin and release decision are recorded in
[the third-party audit](../THIRD_PARTY.md).
