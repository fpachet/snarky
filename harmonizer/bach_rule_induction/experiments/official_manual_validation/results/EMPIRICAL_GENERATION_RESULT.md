# Génération sous budgets empiriques du manuel

## Protocole

La recherche reprend le soprano et le rythme du BWV 108.6, mais aucune note
d'alto, ténor ou basse. Elle combine les facteurs MLE V29, le facteur de cycle
V32, l'ablation de contraintes V33 et le nouveau profil `bach_empirical`.

Les 18 seuils marginaux sont appris au quantile 95 % sur 251 chorals. Les cinq
budgets de famille sont calibrés sur le même train puis contrôlés sur 50
chorals de validation. Le test de 51 chorals n'a servi ni au seuil ni à la
promotion. L'acceptation simultanée vaut 94,0 % sur train, 96,0 % sur
validation et 86,3 % sur test.

## Recherche

- solution trouvée en 301 nœuds ;
- 69 backtracks ;
- 5 branches rejetées par les budgets du manuel ;
- score MLE moyen `-0,755610`, au-dessus du plancher `-1,367214` ;
- aucun croisement de voix adjacent.

La propagation compilée rejette immédiatement les sauts et répétitions dont
le dépassement est irréversible. Toute solution terminale subit ensuite
l'audit Snarky complet : la compilation n'est donc pas un second modèle.

## Effet par rapport à V33

| Critère | V33 | Nouvelle génération | Seuil train |
|---|---:|---:|---:|
| saut maximal ténor | 16 | 12 | 12 |
| répétition maximale alto | 8 | 8 | 6 |
| répétition maximale ténor | 6 | 6 | 6 |
| répétition maximale basse | 4 | 3 | 3 |
| nombre total de budgets dépassés | 3 | 1 | au plus 2 |
| dépassements dans la famille répétition | 2 | 1 | au plus 1 |

La nouvelle partition satisfait donc le profil empirique gelé. Elle conserve
une répétition d'alto atypique, car le corpus autorise un dépassement isolé
dans cette famille. Il serait méthodologiquement incorrect de changer ce
seuil après écoute de cette seule génération. La prochaine expérience devra
comparer plusieurs générations ou apprendre un facteur local expliquant le
contexte des répétitions, sans transformer arbitrairement le quantile en zéro.

## Artefacts

- MusicXML : `harmonizer/generated/official_manual_empirical_bwv108_6.musicxml` ;
- MIDI : `harmonizer/generated/official_manual_empirical_bwv108_6.mid` ;
- MP3 : `harmonizer/generated/official_manual_empirical_bwv108_6.mp3`, piano
  acoustique explicite.
