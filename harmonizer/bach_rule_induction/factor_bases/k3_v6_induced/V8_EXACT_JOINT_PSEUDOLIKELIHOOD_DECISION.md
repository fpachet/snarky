# V8 — pseudo-vraisemblance exacte et décision générative

## Rectification

La première V8 utilisait bien la somme de tous les facteurs dans son softmax,
mais seulement pour le noyau K3 centré sur la note prédite. Le sampler
rythmique remplace une attaque et toute sa tenue, puis recompte tous les noyaux
K3 dont l'énergie change. Les activations étaient donc identiques, mais leur
portée et leur multiplicité ne l'étaient pas.

Cette expérience corrige cette asymétrie. Pour chaque attaque authentique de
Bach et chaque hauteur candidate, elle construit exactement le même monde
contrefactuel que Gibbs :

1. remplacement de toute la tenue ;
2. énumération de tous les centres K3 affectés ;
3. application des portées par décision, voix, bloc vertical ou transition ;
4. somme séparée des 48 comptes factoriels ;
5. softmax et apprentissage conjoint des 48 poids.

Un test vérifie désormais que

\[
S_{\mathrm{apprentissage}}(c)
= S_{\mathrm{Gibbs}}(c)
\]

pour chaque candidat, à la précision flottante.

## Corpus

L'expérience complète utilise :

- 251 chorals de train, soit 53 604 attaques/tenues ;
- 50 chorals de validation, soit 10 414 attaques/tenues ;
- les 46 hauteurs candidates pour chaque choix ;
- les voix alto, ténor et basse réellement générées ;
- le soprano et les états de bord fixes ;
- 48 facteurs appris simultanément ;
- aucun choral du test réservé.

Le cache exact contient les scores de base et les comptes factoriels de chaque
monde candidat. Il permet de réapprendre les poids sans relire les partitions.

## Pseudo-vraisemblance exacte

Les modèles antérieurs sont réévalués sur les mêmes conditionnelles exactes :

| Poids | NLL validation exacte |
|---|---:|
| V6 conditionnelle centrale | 1,039394 |
| Iteration 2 générative | 1,014606 |
| Première V8 centrale | 0,989966 |
| **V8 exacte complète** | **0,829642** |

La NLL train de V8 exacte est `0,814610`. L'optimum de validation est atteint
à l'étape 80 sur 100. L'écart train/validation reste limité.

## Effet du correctif sur la génération

Sur les dix mêmes chorals, trois graines et 30 sweeps, la première V8 centrale
produisait :

- `7,04 %` de grands sauts à la basse ;
- `42,62 %` de demi-tons ;
- `15,40 %` de notes de basse hors gamme naturelle globale.

Avec les portées exactes et le corpus complet, ces valeurs deviennent :

- `21,46 %` de grands sauts ;
- `27,64 %` de demi-tons ;
- `7,43 %` de notes hors gamme.

Bach donne respectivement `27,87 %`, `25,00 %` et `7,14 %`. Le défaut
catastrophique provenait donc bien en grande partie du décalage entre les
sommes apprises et générées.

## Audit court complet

Sur 50 chorals de validation, trois graines et 6 sweeps, V8 exacte est plus
proche de Bach sur 3 diagnostics sur 10. Elle améliore certains diagnostics
harmoniques, mais reste trop conservatrice à la basse :

- grands sauts : Bach `26,76 %`, V8 `20,91 %` ;
- demi-tons : Bach `25,67 %`, V8 `27,62 %` ;
- répétitions : Bach `3,37 %`, V8 `6,24 %`.

## Audit long

Sur dix chorals, trois graines et 30 sweeps, V8 exacte n'est plus proche que
sur 1 diagnostic sur 10 face à Iteration 2. Elle devient notamment :

- trop triadique : `57,10 %` contre `50,87 %` chez Bach ;
- insuffisamment dissonante sur les blocs faibles : `0,8948` contre `1,0323` ;
- encore trop pauvre en grands sauts : `21,46 %` contre `27,87 %`.

Les écarts du taux triadique et des dissonances faibles excluent zéro à 95 %.

## Conclusion

Le correctif de portée est **validé et devient obligatoire** pour tout nouvel
apprentissage. Il répare la majeure partie de la basse aberrante et garantit
que la pseudo-vraisemblance optimise les véritables conditionnelles de
l'énergie Gibbs.

Les poids V8 exacts ne sont cependant **pas promus comme générateur**.
Iteration 2 reste le checkpoint génératif. Le résidu ne peut plus être
attribué à un mauvais comptage : il mesure maintenant réellement l'écart entre
une excellente prédiction conditionnelle locale et les moments de la
distribution stationnaire sous une structure factorielle imparfaite.

La prochaine étape est donc l'objectif hybride prévu :

\[
\mathcal L_{\mathrm{exact\ PL}}(\theta)
+ \lambda\,
\|M_{\mathrm{Gibbs}}(\theta)-M_{\mathrm{Bach}}\|^2
\]

Tous les poids resteront appris conjointement. Le second terme devra corriger
principalement les grands sauts, les répétitions, le taux triadique et les
dissonances faibles, avec une région de confiance autour de l'optimum exact.

## Exemple d'écoute

- [MP3](../../../generated/v8_exact_joint_pl_listening/v8_exact_joint_pl_bwv108_6.mp3)
- [MusicXML MuSES](../../../generated/v8_exact_joint_pl_listening/v8_exact_joint_pl_bwv108_6.musicxml)
- [MIDI](../../../generated/v8_exact_joint_pl_listening/v8_exact_joint_pl_bwv108_6.mid)

L'exemple utilise BWV 108.6, son soprano et son rythme, la graine `5517` et
`30` sweeps. Il est expérimental et non promu.
