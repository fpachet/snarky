# Décision V18 — conserver MaxEnt, recentrer l'objectif sur les règles

## Question

V17 a montré qu'un réglage des poids guidé par quelques diagnostics de
génération peut corriger un défaut et en créer d'autres. Cela ne justifie ni
l'abandon de MaxEnt, ni l'introduction d'interactions opaques entre règles.

V18 teste l'architecture suivante :

1. chaque facteur est un prédicat K3 autonome et lisible ;
2. aucune règle ne peut activer une autre règle ;
3. les poids sont appris conjointement par pseudo-vraisemblance exacte ;
4. la pénalité `L1` croît avec la longueur descriptive du prédicat ;
5. la validation choisit le premier point situé à une erreur standard du
   meilleur modèle ;
6. aucune statistique de génération ne modifie les poids.

## Catalogue

La grammaire gelée produit 954 prédicats. V18 en conserve 816 et exclut la
famille `observed_vertical_set`. Les ensembles verticaux encodés par un entier
sont prédictifs, mais leur représentation en bitset n'est pas encore une règle
qu'un musicien peut lire.

Les conjonctions internes permises définissent une seule proposition musicale.
Par exemple :

> une paire conserve une quinte juste par mouvement direct non nul.

Ce prédicat est différent d'une interaction entre deux règles déjà apprises :
il possède une définition autonome, une portée K3 et un verdict directement
testable.

## Frontière obtenue

Sur 32 chorals d'apprentissage de structure et 10 chorals de validation :

| Modèle | Règles | Complexité | NLL validation par décision |
|---|---:|---:|---:|
| Profils registre/tonalité seuls | 0 | 0 | 2,317000 |
| V18 retenu par une erreur standard | 19 | 26 | 0,875539 |
| V18 au budget maximal | 30 | 41 | 0,812174 |
| V9 avec bitsets verticaux | 30 | non comparable | 0,774130 |

Le modèle de 19 règles réduit de 62,2 % la NLL de la baseline. Le prix
provisoire de l'intelligibilité est visible : environ `0,038` NLL entre les
modèles de 30 facteurs V18 et V9, puis `0,063` supplémentaire pour ramener V18
de 30 à 19 règles.

## Connaissances récupérées

Sans traité, CHORAL ni base historique, V18 retrouve notamment :

- l'évitement progressif des grands mouvements mélodiques ;
- l'évitement très fort des unissons et quintes conservés par mouvement
  direct ;
- l'évitement des croisements de voix et des espacements presque nuls ;
- la préférence pour trois classes de hauteur distinctes ;
- la préférence pour les tierces majeures et mineures et la quinte juste ;
- l'évitement des secondes, septièmes et de certaines quartes
  basse–ténor ;
- l'évitement d'une nouvelle attaque répétant la basse précédente.

Le premier facteur ne dit pas « aucune voix ne doit dépasser un ton ». Son
poids négatif est une pénalité statistique, à laquelle s'ajoute une pénalité
spécifique au-delà d'une quinte. Un autre contexte peut donc compenser cette
pénalité.

Deux formulations demandent une analyse musicologique avant promotion :

- la préférence conditionnelle pour un mouvement adjacent chromatique ;
- le poids positif du mouvement du ténor vers la note suivante supérieur à un
  demi-ton.

Elles peuvent exprimer une véritable licence contextuelle, ou une compensation
entre colonnes corrélées. Leur lisibilité syntaxique ne suffit pas encore à en
faire une connaissance stable.

## Stabilité des poids

Les mêmes 19 règles ont été réapprises quatre fois sur 24 des 32 chorals, avec
évaluation sur les huit pièces retirées.

- 19 signes sur 19 restent identiques ;
- 19 poids sur 19 restent non nuls dans tous les replis ;
- la NLL des pièces retirées passe de `2,325–2,480` sans règles à
  `0,929–1,019` avec les règles.

Ce résultat valide la stabilité des poids **conditionnellement à la structure
de 19 règles**. Il ne démontre pas encore que la procédure redécouvrirait
exactement les mêmes 19 prédicats sur d'autres sous-corpus.

## Décision

V18 est conservé comme première base explicitement orientée vers
l'explication. Il n'est pas encore promu comme générateur et le test réservé
reste fermé.

La prochaine séquence est :

1. répéter la sélection complète des colonnes sur plusieurs sous-corpus ;
2. conserver le noyau de règles structurellement stable et caractériser les
   règles substituables d'une même famille ;
3. réapprendre ce noyau sur les 251 chorals de train et arrêter sur les 50 de
   validation ;
4. produire les RuleCards, exemples Bach et exceptions ;
5. compiler cette base seule vers Snarky ;
6. seulement alors réaliser l'audit génératif et ouvrir une fois le test
   réservé.

Cette séquence conserve le maximum de pseudo-vraisemblance comme estimateur,
mais interdit que la génération réécrive après coup l'explication.

## Résultats de la séquence complète

Les quatre réinductions 24/8, ajoutées au modèle original, produisent :

- 14 règles présentes dans 5 bases sur 5 ;
- 17 règles présentes dans au moins 4 bases sur 5 ;
- 22 règles présentes dans au moins 3 bases sur 5 ;
- un Jaccard moyen de `0,620` entre les bases sélectionnées.

Le noyau unanime de 14 règles a ensuite été gelé et réappris sur les 251
chorals de train, avec arrêt sur 50 chorals de validation :

- NLL validation sans règles : `2,406648` ;
- NLL validation du noyau : `0,981894` ;
- test de 51 chorals : toujours fermé.

Quatorze RuleCards et un programme `FACTOR` Snarky ont été exportés. La parité
sur 128 décisions K3 × 46 alternatives donne une erreur maximale de
`8,88 × 10⁻¹⁶`.

### Audit génératif externe

Une génération à 30 balayages ainsi qu'un audit sur dix chorals de validation
× trois graines ont été réalisés sans modifier les poids.

| Mesure | Bach | V13 | V18 unanime |
|---|---:|---:|---:|
| Blocs triadiques | 50,87 % | 53,03 % | 38,68 % |
| Blocs forts non triadiques | 26,91 % | 36,34 % | 53,90 % |
| Dissonances par bloc fort | 0,357 | 0,558 | 0,765 |
| Répétitions de basse | 3,71 % | 3,77 % | 5,32 % |

Le résultat est négatif pour la génération, mais précis pour l'étude : une
petite base unanimement redécouverte explique fortement les décisions locales
authentiques sans suffire à maintenir une trajectoire polyphonique libre dans
les régions du domaine rarement visitées par Bach.

Cette lacune ne doit pas être corrigée en ajustant manuellement les quatorze
poids. Elle devient une nouvelle question d'induction : quels faits et quelles
règles autonomes, probablement liés à la structure verticale et à son statut
métrique, manquent au langage explicatif actuel ?
