# Base de règles — Éthique III

Ce dossier contient deux paliers distincts et explicitement qualifiés, ainsi
qu'un troisième chantier entièrement séparé.

## Palier A — reconstruction historique exécutable

La base [`rules/historical.rules`](rules/historical.rules) reconstruit les
diapositives 10 à 17 de `docs/Gondran.ppt`. Elle reproduit par chaînage avant :

- E3P19, destruction et conservation de la chose aimée ;
- E3P21, joie et tristesse partagées ;
- E3P22, amour et haine envers la cause imaginée d'un affect ;
- E3P33, effort pour obtenir l'amour réciproque.

Les règles ne sont pas présentées comme des traductions littérales de Spinoza.
Leur origine, les diapositives et leur degré de fidélité sont consignés dans
[`rules/rule_catalog.yaml`](rules/rule_catalog.yaml). Deux formes visibles mais
non exécutables sont conservées dans
[`rules/non_executable_rules.yaml`](rules/non_executable_rules.yaml) : l'action
`Créer(z)` et une réciproque dont la conclusion contient une variable non liée.

Chaque preuve est décrite dans son manifeste, par exemple
[`theorems/E3P19.yaml`](theorems/E3P19.yaml). Le moteur part uniquement des
hypothèses du cas et aucune règle nommée `E3Pxx_as_direct_rule` n'est autorisée.

Le rapport complet de Fabrice Cavarretta sur SpinoLog est conservé dans
[`../docs/Cavarretta-X1988-SpinozaExpertSystem.pdf`](../docs/Cavarretta-X1988-SpinozaExpertSystem.pdf).
Il fournit une base historique plus large que la présentation. Son intégration
séparée, les audits de clôture et les extensions qu'il suggère sont documentés
dans
[`reports/spinolog_1988_enrichment.md`](reports/spinolog_1988_enrichment.md).

## Palier B — toute la partie III

Le fichier [`sources/ethique_III_appuhn_1913.txt`](sources/ethique_III_appuhn_1913.txt)
permet de relire la partie III d'un seul tenant. Il est généré à partir de
[`sources/passages.json`](sources/passages.json), l'importation structurée de
la traduction Appuhn (1913) :

- 1 préface ;
- 3 définitions ;
- 2 postulats ;
- 59 propositions, avec démonstrations, corollaires et scolies ;
- 48 définitions d'affects ;
- 1 définition générale des affects.

Les 59 fichiers `theorems/E3P01.yaml` à `theorems/E3P59.yaml` rendent la suite
du travail incrémentale et vérifiable. Dans cette couche historique, les quatre
cas reconstruits depuis la présentation sont `proved` ; les autres manifestes
indiquent encore ce qui manque. Le modèle systématique possède son propre état
d'avancement. Une proposition ne doit devenir exécutable qu'après validation
de ses hypothèses, de son but et des règles antérieures qu'elle mobilise.

Le graphe [`reports/dependency_graph.json`](reports/dependency_graph.json)
exporte les références numériques détectées dans le texte. Ce sont des
`reference_candidate`, car les renvois « proposition précédente », « même
proposition » et les références aux définitions exigent encore une
normalisation éditoriale.

## Exécution

Depuis la racine du dépôt :

```sh
uv run --extra dev pytest tests/test_spinoza_ethics_iii.py
```

Pour exécuter un cas depuis Python :

```python
from pathlib import Path

from snarky.spinoza import run_case

result = run_case(Path("spinoza"), "E3P22", "amour")
assert result.proved
assert result.proof_depths == (3,)
```

## Régénération du corpus

Après avoir enregistré localement le HTML de la page Wikisource référencée
dans `sources/bibliography.yaml` :

```sh
python scripts/import_ethics_iii.py source.html spinoza/sources/passages.json
python scripts/export_ethics_iii_text.py \
  spinoza/sources/passages.json spinoza/sources/ethique_III_appuhn_1913.txt
python scripts/generate_spinoza_theorems.py \
  spinoza/sources/passages.json spinoza/theorems
python scripts/export_spinoza_dependencies.py \
  spinoza/sources/passages.json spinoza/reports/dependency_graph.json
```

L'importeur vérifie les cardinalités attendues et stocke le SHA-256 du HTML.
La régénération des théorèmes préserve les quatre fixtures historiques dans le
script générateur.

## Palier C — reconstruction systématique

Le dossier [`systematic`](systematic/README.md) reprend la formalisation à
partir des définitions, postulats et dépendances explicites. Il ne charge pas
les règles historiques. Les fragments exécutables couvrent désormais
E3P01–E3P59 et rendent visibles les ponts importés des parties I et II.

Cette couverture comprend notamment le conatus, les affects primitifs,
l'imagination et la mémoire, les affects temporels, l'amour et la haine, leur
transmission qualitative, l'envie, l'orgueil, la surestime et la mésestime. Les
efforts d'affirmer et de nier conservent explicitement leur contenu et leur
cible au lieu d'être réduits à `EXISTANT` ou `INEXISTANT`. E3P27–E3P32
ajoutent l'imitation affective, l'approbation sociale, la considération de soi,
l'accord affectif et la rivalité pour une possession exclusive. E3P33–E3P36
ajoutent la réciprocité amoureuse, l'intensité qualitative de la gloire, le
triangle de jalousie et le désir des circonstances d'une jouissance passée.
E3P37–E3P40 ajoutent l'intensité qualitative du désir et de la haine, la peur
d'un mal plus grand, l'inhibition de l'action, la colère et la vengeance.
E3P41–E3P44 ajoutent l'amour réciproque, la gratitude, la cruauté,
l'ingratitude et la transformation de la haine en amour. L'affect initial et
l'affect réciproque restent distincts, et la victoire de l'amour conserve
l'histoire affective au lieu de la nier rétroactivement.
E3P45–E3P48 ajoutent transfert triangulaire, généralisation sous un nom de
classe ou de nation, joie mêlée de tristesse et réattribution causale. Les
écarts de E3P45, E3P47 et E3P48 avec SpinoLog sont rendus exécutables comme
contre-cas ou provenance interprétative explicite.

E3P49–E3P52 ajoutent la comparaison qualitative des affects à motif égal,
les présages issus d'associations affectives, la variabilité individuelle et
temporelle, puis l'attention prolongée et les familles de l'étonnement et du
mépris. L'absence d'alternative associative reste un fait positif.

E3P53–E3P56 relient la considération de soi aux affections corporelles,
représentent explicitement le « seulement » des contenus qui posent la
puissance, distinguent humilité, amour-propre, envie et vénération, puis
construisent les espèces affectives selon la nature de leurs objets.

E3P57–E3P59 achèvent les propositions : les différences d'essence
individualisent les affects, les idées adéquates produisent joie et désir
actifs, et la tristesse active est explicitement exclue. Le dernier scolie
formalise fermeté, générosité, dégoût, lassitude et troubles corporels.

Dix rapports décrivent les derniers jalons et leur comparaison avec Gondran
et Cavarretta :

- [`systematic/reports/milestone_e3p19_e3p22.md`](systematic/reports/milestone_e3p19_e3p22.md) ;
- [`systematic/reports/tranche_e3p23_e3p26.md`](systematic/reports/tranche_e3p23_e3p26.md) ;
- [`systematic/reports/tranche_e3p27_e3p32.md`](systematic/reports/tranche_e3p27_e3p32.md) ;
- [`systematic/reports/tranche_e3p33_e3p36.md`](systematic/reports/tranche_e3p33_e3p36.md) ;
- [`systematic/reports/tranche_e3p37_e3p40.md`](systematic/reports/tranche_e3p37_e3p40.md) ;
- [`systematic/reports/tranche_e3p41_e3p44.md`](systematic/reports/tranche_e3p41_e3p44.md) ;
- [`systematic/reports/tranche_e3p45_e3p48.md`](systematic/reports/tranche_e3p45_e3p48.md) ;
- [`systematic/reports/tranche_e3p49_e3p52.md`](systematic/reports/tranche_e3p49_e3p52.md) ;
- [`systematic/reports/tranche_e3p53_e3p56.md`](systematic/reports/tranche_e3p53_e3p56.md) ;
- [`systematic/reports/tranche_e3p57_e3p59.md`](systematic/reports/tranche_e3p57_e3p59.md).

La suite de tests comprend actuellement 89 tests réussis. Les 59 propositions
sont toutes exécutables. Le prochain chantier distinct est l'intégration
systématique des 48 définitions finales des affects. Le
[`plan de modélisation`](systematic/reports/roadmap.md) décrit l'ordre complet
jusqu'à E3P59 et aux définitions finales des affects.
