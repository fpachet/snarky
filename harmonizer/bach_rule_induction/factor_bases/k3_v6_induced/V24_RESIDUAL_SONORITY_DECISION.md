# V24 — statuts résiduels des sonorités fortes

## Question

V23 reconnaît bien les accords nommés dont l'analyse est unique, mais ne dit
rien lorsque cette analyse échoue. Cette zone de référence contient à la fois
des sonorités légitimes — accords incomplets, retards, appoggiatures, notes de
passage — et les accords étranges encore audibles dans les générations.

V24 teste si un petit vocabulaire local, exhaustif et lisible peut distinguer
ces cas puis réduire les erreurs sans ajouter de règle historique ou experte.

## Vocabulaire gelé

Sur chaque bloc fort sans analyse V23 unique, un et un seul des huit statuts
suivants est actif :

1. analyse nommée exacte mais ambiguë ;
2. triade consonante incomplète ;
3. triade plus une note, analyse ambiguë ;
4. triade plus note de passage ou broderie ;
5. triade plus retard ;
6. triade plus appoggiature ;
7. triade plus note étrangère non licenciée ;
8. autre sonorité non licenciée.

La licence est définie uniquement dans la fenêtre K3
`précédent–courant–suivant`, avec la sémantique réelle `ATTACK/HOLD`. Le
vocabulaire est humainement défini ; les poids ne le sont pas.

L'audit des 32 chorals de structure compte 1 039 blocs forts : 858 reçoivent
l'analyse unique V23 et 181 un statut V24. Toutes les alternatives locales
possibles activent exactement un état V23 ou V24. La catégorie
`other_unlicensed` apparaît néanmoins 100 fois chez Bach : ce n'est donc pas
une interdiction absolue.

## Résultat conditionnel négatif

Le premier ajustement par pseudo-vraisemblance donne un gain trop petit. Avec
la pénalité gelée `λ=0,6`, les quatre folds produisent respectivement
`−0,002274`, `+0,000134`, `−0,000102` et `+0,000829` de gain NLL moyen, soit
`−0,000353` au total. Le groupe est rejeté comme amélioration explicative
conditionnelle stable.

Ce résultat est conservé : V24 n'est pas présenté comme une règle que la
pseudo-vraisemblance aurait redécouverte de façon robuste.

## Apprentissage génératif

Une seconde estimation garde les 57 facteurs V23 figés et apprend seulement
les huit poids V24 par gradient MaxEnt Monte-Carlo :

`gradient = fréquence_Bach − fréquence_générateur`.

La validation n'est jamais utilisée pendant les huit mises à jour. Sur les 32
chorals d'apprentissage :

- taux résiduel généré : `24,64 % → 22,04 %` ;
- cible Bach : `17,42 %` ;
- erreur absolue moyenne des huit moments : `0,01335 → 0,00938`.

Le poids dominant est celui de `other_unlicensed` (`−0,2377`). L'accord
incomplet consonant reçoit au contraire `+0,0486`. Il reste un écart
génératif : cette calibration est utile mais non convergée jusqu'à égalité des
moments.

## Validation générative

Audit tenu à part : dix chorals de validation, cinq graines par choral, six
balayages, mêmes soprano, rythme, initialisation et bords.

| Mesure | Bach | V23 | V24 |
|---|---:|---:|---:|
| Blocs triadiques | 50,87 % | 49,42 % | 50,17 % |
| Blocs forts non triadiques | 26,91 % | 35,17 % | 32,02 % |
| Dissonances par bloc fort | 0,357 | 0,596 | 0,530 |
| Dissonances par bloc faible | 1,032 | 1,081 | 1,085 |
| Basse hors gamme naturelle | 7,14 % | 11,69 % | 12,11 % |

V24 améliore donc les mesures qu'il vise, sans améliorer la basse ni les
temps faibles. Il demeure à `+5,11` points de Bach pour les blocs forts non
triadiques et à `+0,173` dissonance forte par bloc.

## Échantillonnage conjoint

Un Gibbs exact par paires de segments vocaux a été ajouté et vérifié contre
l'énumération exhaustive. Il conserve la même distribution cible ; il ne peut
donc corriger à lui seul des poids insuffisants.

Dans l'audit 10 chorals × 3 graines, une passe conjointe fait passer :

- les blocs forts non triadiques de `31,04 %` à `33,01 %` ;
- les dissonances fortes de `0,515` à `0,556`.

Cette variante est rejetée pour la génération courante. Le code reste
disponible comme diagnostic de mélange, avec une valeur par défaut nulle.

## Snarky

Le modèle retenu contient 65 facteurs : 57 hérités de V23 et huit V24. Il est
exporté comme programme `FACTOR` Snarky. Sur 128 décisions et toutes leurs
alternatives, l'erreur maximale entre Snarky et Python vaut
`8,882 × 10⁻¹⁶` pour les contributions, les scores et les probabilités.

Aucune contrainte historique ou experte n'est chargée.

## Décision

V24 est retenu comme **candidat génératif pré-test**, pas comme nouvelle loi
conditionnelle stable. C'est un résultat utile et précisément circonscrit :
un vocabulaire local lisible, pondéré par les erreurs réelles du générateur,
réduit les accords étranges sur validation, mais ne résout ni la basse
chromatique ni toutes les dissonances.

La prochaine induction doit séparer deux résidus :

1. aux temps faibles, apprendre les licences de dissonance en fonction de leur
   préparation et résolution ;
2. à la basse, apprendre une fonction locale structurée
   `note d'accord / passage / broderie / appoggiature / chromatisme fonctionnel`
   avec direction de résolution, plutôt qu'un degré tonal plat.

## Artefacts

- [Couverture V24](V24_RESIDUAL_SONORITY_COVERAGE.md)
- [Ajustement des moments](V24C_CONTRASTIVE_MOMENT_FIT.md)
- [Validation V23–V24, 10 × 5](V24C_V23_GENERATION_VALIDATION10X5_SWEEP6.md)
- [Ablation du Gibbs conjoint](V24_BLOCKED_VALIDATION10X3_SWEEP6.md)
- [Parité Snarky](V24_SNARKY_PARITY.md)
- [MusicXML BWV 108.6](../../../generated/v24_contrastive_bwv108_6_seed_22304.musicxml)
- [MP3 piano BWV 108.6](../../../generated/v24_contrastive_bwv108_6_seed_22304_piano.mp3)
