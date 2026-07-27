# Third-party material and redistribution audit

This inventory records provenance separately from permission. A citation,
download URL, or use as a research oracle does not by itself grant
redistribution rights.

All external corpora and historical documents are excluded from Snarky's
Python source and wheel distributions. A public tagged repository release is
also blocked wherever the table says `review required`.

## Historical documents

| Local path | Identification | Recorded terms | Decision |
|---|---|---|---|
| `docs/481057722-Intelligence-artificielle-Resolution-de-problemes-par-lhomme-et-la-machine-by-Jean-Louis-Lauriere-z-lib-org-pdf.pdf` | Jean-Louis Laurière, *Intelligence Artificielle - Résolution de problèmes par l'Homme et la machine*, 485 pages; PDF metadata dated 2009 | No redistribution terms recorded; file origin is not an authoritative publisher URL | Internal reference only; exclude from distributions and tagged releases pending a legitimate source and permission review |
| `docs/6-SNARK2-4p.pdf` | Bernard Espinasse, *Programmation Déclarative: SNARK 2*, 2004, 13-page four-slides-per-page handout | No redistribution terms recorded | Internal reference only; exclude pending author or publisher permission |
| `docs/Cavarretta-X1988-SpinozaExpertSystem.pdf` | Fabrice Cavarretta, *SpinoLog*, École Polytechnique X85, supervised by Michel Gondran, 49-page scan | No redistribution terms recorded | Internal Spinoza reference only; exclude pending permission |
| `docs/Gondran.ppt` | Michel Gondran, *Modélisation de l'Éthique de Spinoza dans le langage Snark de Jean-Louis Laurière*, 2006 presentation | No redistribution terms recorded | Internal Spinoza reference only; exclude pending permission |
| `docs/RC12628-Ebcioglu-CHORAL.pdf` | Kemal Ebcioğlu, *Report on the CHORAL Project: An Expert System for Harmonizing Four-Part Chorales*, IBM Research Report RC 12628, 20 March 1987, 328 pages; SHA-256 `1e15961a4855bb8b6610fe5fc1c5db6bfdddf54f6129f36cee5f5a7d26643d8c`; source `global-supercomputing.com/people/kemal.ebcioglu/pdf/RC12628.pdf` | The scan contains an IBM limited-distribution notice anticipating transfer of copyright; no current redistribution permission has been established despite public hosting on the author's site | Internal harmony research reference only; exclude from Python distributions and tagged public releases pending rights review |
| `docs/Satisfaction_de_contraintes_et_programmation_par_o.pdf` | Pierre Roy, doctoral thesis, *Satisfaction de contraintes et programmation par objets*, Université Paris 6, defended 21 December 1998, 232 pages | No redistribution terms or authoritative repository URL recorded | Internal CSP/harmony reference only; exclude pending repository or author rights verification |

`docs/Shal.doc` is a local, ignored document and is not tracked or
distributed.

## External rulebase corpora

Exact revisions, selected paths, archive hashes, and source URLs are in
[`third_party/test_rulebases/manifest.yaml`](third_party/test_rulebases/manifest.yaml).

| Corpus | Revision/source | Recorded terms | Repository decision |
|---|---|---|---|
| W3C N3 | `b975fc59...`, `github.com/w3c/N3` | W3C Test Suite License and W3C Software and Document License bundled in the selected tree | Retain for research testing with notices; exclude from Python distributions |
| W3C RIF 1.22 | official W3C BLD/Core/PRD archives with SHA-256 hashes | Upstream W3C software-license URL recorded; no local license copy in the imported snapshot | Review notices before any corpus release; exclude from Python distributions |
| CLIPS 6.4.2 | official SourceForge example and feature-test archives with SHA-256 hashes | Upstream project declares MIT; no license file is bundled with the selected archives | Add authoritative license notice before any corpus release; exclude from Python distributions |
| ChaseBench | `7427e1c1...`, `github.com/dbunibas/chasebench` | No license found in the imported revision | Review required; do not include in a tagged release |
| rbench | `1dda8ded...`, `gitlab.informatik.uni-halle.de/brass/rbench` | No license found in the imported revision | Review required; do not include in a tagged release |
| Soufflé | `a1303be3...`, `github.com/souffle-lang/souffle` | UPL-1.0 license and upstream notices bundled | Retain with notices for research testing; exclude from Python distributions |
| EYE | `f14729b5...`, `github.com/josd/eye` | MIT license bundled | Retain with notice for research testing; exclude from Python distributions |

The imported selections are reference inputs, not native Snarky tests and not
claims of conformance to the source systems. `scripts/fetch_test_rulebases.sh`
reproduces the selection and refuses to overwrite an existing corpus.

## DeepBach local reference

DeepBach is maintained as the autonomous sibling project
`../deepbach-reference/`, outside the Boojum repository. It contains the
complete upstream clone, unmodified snapshots of tag `v2.0`, the 2018 Keras
branch tip and the later PyTorch port, plus a separately tested compatibility
runtime.

The source declares the MIT license. The separately downloaded model and
dataset artifacts contain no sufficiently explicit standalone redistribution
notice, so they remain in the sibling project's ignored `resources/cache/`
directory. They are excluded from Boojum distributions and public releases
pending a rights and provenance review. Exact revisions, URLs, sizes and
hashes are recorded by that project's `UPSTREAM.json`; Boojum's technical
inventory remains in
[`harmonizer/bach_rule_induction/sources/DEEPBACH.md`](harmonizer/bach_rule_induction/sources/DEEPBACH.md).

## CLAIRE4 cross-language benchmark

`benchmarks/claire_n_queens.cl` and
`benchmarks/claire_talarian_filter.cl` are modified derivatives of Yves
Caseau's `test/toys/queens.cl` and `test/rules/filter.cl`, respectively, from
[`ycaseau/CLAIRE4`](https://github.com/ycaseau/CLAIRE4) at revision
`25b14968e1eef80269d56af418eda7d2ccd88cbf`. The upstream repository records
the Apache License 2.0. The local N-Queens file changes the board-size
handling, singleton propagation, assigned-conflict validation,
instrumentation, and output format. The local filter file makes the frame
count runtime-configurable, separates object preparation from inference, and
adds validation counters and machine-readable output. Both are retained only
as benchmark source, excluded from the Python wheel and source distribution,
and must not enter a tagged repository release until the upstream Apache-2.0
license text and required notices are bundled with them.

## Spinoza text

`spinoza/sources/ethique_III_appuhn_1913.txt` and
`spinoza/sources/passages.json` derive from Charles Appuhn's 1913 French
translation as transcribed by Wikisource. The source URL and retrieval date
are recorded in `spinoza/sources/bibliography.yaml`.

The age of the printed translation does not by itself settle the terms of the
online transcription or structured derivative. These files remain research
corpus material, are excluded from Python distributions, and require a
documented rights decision before a tagged corpus release.

## Generated and first-party research artifacts

- `harmonizer/generated/` contains reproducible MIDI and MusicXML outputs.
  They are ignored by Git and regenerated with
  `python -m harmonizer.example_muses`.
- `benchmarks/results/` contains tracked, machine-readable experimental
  records. It is first-party evidence, not runtime source, and is excluded
  from Python distributions.
- caches, wheels, source distributions, coverage reports, and local IDE files
  are ignored.

## Audit rule

Before adding any external artifact, record:

1. its author or originating organization;
2. an authoritative source URL and immutable revision or checksum;
3. the applicable license or permission text;
4. required notices and modification status;
5. whether it belongs in the repository, a tagged research corpus, a Python
   distribution, or only a private reference collection.

Unknown is a valid audit result, but never an implicit permission.
