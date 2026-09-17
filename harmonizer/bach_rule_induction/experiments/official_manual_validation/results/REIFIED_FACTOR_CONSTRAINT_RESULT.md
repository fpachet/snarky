# Accords réifiés, facteurs purs et contraintes propagées

## Question expérimentale

Peut-on harmoniser chaque note d'un soprano imposé, sans squelette harmonique,
en utilisant Snarky comme moteur de choix et de backtrack, tout en séparant
strictement les trois couches suivantes ?

1. les règles dérivent des diagnostics lisibles ;
2. les contraintes retirent des valeurs ou rejettent une branche ;
3. les facteurs appris pondèrent les choix sans ajouter de faits.

## Architecture V40

Chaque attaque du soprano définit une variable dont le domaine est l'ensemble
des réalisations `(alto, ténor, basse)` formant un accord autorisé. La qualité,
la fondamentale et le renversement sont des attributs déterministes de ces
quatre notes : il n'existe aucun état harmonique latent et aucun squelette
préalable.

Les règles à deux positions sont compilées une seule fois en matrices de
support. Une propagation par cohérence d'arcs retire les accords sans support ;
les retraits deviennent des faits `rejected_reified_chord` appartenant à la
branche et sont donc correctement annulés lors d'un backtrack. La règle de
suspension utilise une fenêtre de trois accords et filtre le troisième choix
dès que la fenêtre est complète.

Pour chaque accord candidat, le moteur évalue en batch les conditionnelles K3
qui deviennent décidables. Leur somme est l'incrément exact de
pseudo-vraisemblance. Les cinq poids du manuel sont lus depuis
`official_manual.factors` et ajoutés sur les transitions nouvellement décidées.
Ces facteurs restent purs : aucune activation ne déclenche une règle.

Enfin, les critères globaux utilisent des bornes optimistes. Par exemple, pour
le taux de mouvement conjoint, toutes les transitions encore inconnues sont
supposées conjointes. Si même ce meilleur cas ne peut plus atteindre
l'enveloppe de Bach, le candidat est rejeté immédiatement.

## Résultats

### Profil `bach_empirical` — V38

- solution en 84 nœuds et 19 backtracks ;
- 12 795 candidats rejetés par les bornes du manuel ;
- 61 choix guidés par K3 et 63 par les facteurs du manuel ;
- profil empirique satisfait.

Ce profil révèle cependant une faiblesse de son méta-budget : il autorise deux
métriques hors seuil quelle que soit l'amplitude du dépassement. V38 contient
donc encore sept octaves parallèles. Il s'agit d'une limite explicite du profil
d'acceptation, pas d'une absence de détection.

### Profil `pedagogical_strict` — V40

- solution en 65 nœuds et un backtrack ;
- 11 818 valeurs retirées par propagation ;
- 33 candidats écartés par les filtres locaux, dont la suspension ternaire ;
- 60 choix guidés par les facteurs K3 ;
- zéro violation dans les douze familles du manuel ;
- zéro dépassement des budgets empiriques lors de l'audit final.

Avant le filtre ternaire, V39 atteignait 500 nœuds et 430 backtracks : toutes
les branches échouaient tardivement sur la même suspension. Après compilation
de cette règle locale, V40 ne demande plus qu'un backtrack. Cette comparaison
montre directement l'intérêt de propager les règles locales au lieu de les
auditer seulement sur une partition complète.

## Artefacts d'écoute

- [MusicXML V40](../../../../generated/two_loop_full_bwv108_6_v40_reified_strict_window.musicxml)
- [MIDI piano V40](../../../../generated/two_loop_full_bwv108_6_v40_reified_strict_window.mid)
- [MP3 piano V40](../../../../generated/two_loop_full_bwv108_6_v40_reified_strict_window.mp3)
- [Résultat JSON V40](../../../factor_bases/k3_v6_induced/two_loop_full_generation_v40_reified_strict_window.json)

## Limite restante

Zéro violation du manuel est une condition vérifiable, pas une preuve que le
résultat sonne comme Bach. L'écoute de V40 doit maintenant déterminer si le
vocabulaire d'accords consonants est trop restrictif ou si certaines règles
positives (direction de phrase, cadence, diversité harmonique) manquent encore.

## Correctif V42 : accords complets et frontières apprises

L'écoute de V40 a révélé que le premier bloc ne contenait que les classes de
hauteur si et ré. Il était accepté par la table générique des « triades
incomplètes », alors que l'analyse interne renvoyait `quality = -1` et
`root_degree = -1`. De plus, aucune fenêtre K3 n'étant complète au premier
choix, un tri lexicographique départageait silencieusement les candidats.

V42 ferme ces deux failles :

- chaque candidat doit contenir au moins trois classes de hauteur et posséder
  exactement une qualité et une fondamentale nommées ;
- les accords incomplets sont exclus tant qu'une omission explicite n'est pas
  représentée dans le langage ;
- un modèle catégoriel de frontière est ajusté sur `train251`, sans validation
  ni test, et retire systématiquement la pièce harmonisée de ses comptes ;
- le modèle porte sur qualité, degré de fondamentale, renversement et
  espacements des trois voix inférieures par rapport au soprano ;
- le premier et le dernier `CHOICE` doivent présenter une dispersion d'énergie
  strictement positive, sinon la génération s'arrête avec une erreur.

Sur BWV 108.6, V42 commence par une triade complète de si mineur à l'état
fondamental et termine par une triade complète de si majeur, comme Bach. Les 63
blocs sont des accords nommés à trois classes de hauteur. Ce correctif ne règle
pas encore la mauvaise conduite mélodique des voix intérieures ; il supprime
uniquement l'admission et le choix arbitraire observés à la frontière.

- [MusicXML V42](../../../../generated/two_loop_full_bwv108_6_v42_complete_boundary_voicing.musicxml)
- [MP3 piano V42](../../../../generated/two_loop_full_bwv108_6_v42_complete_boundary_voicing.mp3)
- [Résultat JSON V42](../../../factor_bases/k3_v6_induced/two_loop_full_generation_v42_complete_boundary_voicing.json)
