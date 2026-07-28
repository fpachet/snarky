# V9 — décision sur la réinduction exacte

## Décision

V9 n'est **pas promu comme générateur**. Le checkpoint génératif de référence
reste `v6_train64_multimetric_iteration2_model.json`.

Cette décision ne rejette pas la réinduction exacte. Au contraire, elle
localise la lacune suivante : la grammaire factorielle sait reconnaître des
intervalles verticaux, mais ne sait pas encore exprimer les licences
temporelles qui rendent certaines dissonances bachiennes légitimes.

## Ce qui fonctionne

- La structure repart du catalogue gelé de `954` facteurs, sans imposer les
  facteurs de V6 ou V8.
- Chaque gradient est calculé sur le monde candidat exact vu par Gibbs :
  toutes les portées K3 affectées par une substitution attaque/tenue sont
  recomptées.
- Registre, profil tonal et poids des facteurs sélectionnés sont appris
  conjointement.
- Trente facteurs suffisent à obtenir une NLL de validation de `0,779783`,
  meilleure que les `0,829642` de V8 Exact avec 48 facteurs.
- Le train (`0,784184`) et la validation (`0,779783`) restent proches.
- Le facteur de répétition attaquée à la basse reçoit spontanément un poids
  négatif fort (`-1,911294`) et corrige une partie du défaut entendu.

Ces résultats montrent que le principe central — apprendre conjointement une
petite somme de facteurs locaux intelligibles par pseudo-vraisemblance
exacte — est viable.

## Pourquoi la génération reste mauvaise

Le corpus contient réellement des secondes entre soprano et alto. Dans leur
contexte authentique, elles sont prédictives. V9 sélectionne donc :

- `central_pair_abs_class(v0,v1)=2`, poids `+0,991090` ;
- `central_pair_abs_class(v0,v1)=1`, poids `+1,442347`.

Or ces facteurs sont plats : ils ne disent pas si la dissonance est sur temps
faible ou fort, préparée, tenue, de passage, voisine, ou correctement résolue.
Une exception contextuelle observée chez Bach devient ainsi une préférence
globale dans le sampler.

Les audits confirment cette causalité :

- sur 50 chorals à 6 sweeps, les blocs forts non triadiques passent de
  `28,72 %` chez Bach à `45,74 %` avec V9 ;
- les dissonances par bloc fort passent de `0,410` à `0,743` ;
- sur 10 chorals à 30 sweeps, la basse hors gamme passe de `7,14 %` à
  `13,85 %` et les demi-tons de basse de `25,00 %` à `33,43 %`.

La pseudo-vraisemblance n'est donc pas en cause ici : elle optimise
correctement les facteurs qu'on lui donne. La grammaire confond encore
« intervalle parfois légitime » et « intervalle généralement désirable ».

## Suite falsifiable

1. Ajouter des facteurs lisibles de **licence de dissonance** :
   statut métrique, attaque ou tenue, préparation consonante, mouvement de
   passage ou voisin, direction et intervalle de résolution.
2. Conserver la fenêtre K3 et les faits observables ; aucun état harmonique
   arbitraire n'est requis.
3. Répéter la calibration nulle familiale sur les véritables mondes
   contrefactuels exacts.
4. Réinduire la structure et les poids depuis zéro.
5. N'accepter le modèle que s'il conserve le gain de NLL tout en ramenant,
   sur les audits à 6 et 30 sweeps, les moments de dissonance et de
   chromaticisme dans les intervalles de Bach.
6. Si la pseudo-vraisemblance seule laisse encore une dérive de moments,
   ajouter un terme génératif global à l'objectif, sans modifier la
   sémantique déclarative des facteurs.

## Conclusion

Oui, l'approche peut fonctionner *in fine*, mais pas avec des indicateurs
verticaux sans contexte. V9 fournit précisément l'expérience qui manquait :
le moteur, la portée exacte et l'apprentissage conjoint sont validés ; la
prochaine hypothèse à tester est une grammaire locale plus expressive, non un
retour à des règles écrites à la main.
