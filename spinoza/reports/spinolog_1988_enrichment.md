# Apports du rapport SpinoLog de Cavarretta

## Source et statut

Le document source est
[`../../docs/Cavarretta-X1988-SpinozaExpertSystem.pdf`](../../docs/Cavarretta-X1988-SpinozaExpertSystem.pdf),
rapport de Fabrice Cavarretta sous la direction de Michel Gondran. La
présentation de 2006 situe le travail initial en 1987 ; le rapport décrit
explicitement son prototype comme la « version de juillet 1988 ». Le nom
`spinolog_1988` désigne donc ici la version documentée, sans trancher la date de
début du stage.

Le rapport complète la présentation de Gondran sur quatre points :

- la base de faits initiale et sa méta-ontologie ;
- les règles SpinoLog commentées avec leur origine et leurs limites ;
- les démonstrations, intermédiaires et conclusions annexes de 24 propositions ;
- un bilan explicite des simplifications et extensions souhaitables.

Cette source historique ne doit pas être confondue avec une transcription
littérale de Spinoza. Son algèbre positif/négatif, ses réciproques et certaines
règles de propagation sont des choix propres à SpinoLog.

## Correspondances avec Snarky

| SpinoLog | État dans Snarky | Décision |
|---|---|---|
| Triplets récursifs | Supportés nativement | Conserver |
| Variables portant sur une relation | Supportées par l'unification | Conserver et tester dans la couche historique |
| Chaînage avant jusqu'à saturation | Supporté | Exposer davantage la clôture obtenue |
| Trace des règles appliquées | Provenance minimale disponible | Ajouter les branches alternatives et rapports de clôture |
| Origine et explication des règles | Catalogue systématique disponible | Ajouter les pages du rapport à la provenance historique |
| Nature, signe, contraire et type de relation comme faits | Ontologie seulement partielle | Expérimenter dans une méta-ontologie séparée |
| Objet générique `QQCHOSE` | Pas de création existentielle | Préférer les témoins explicites, puis étudier des témoins frais bornés |
| Dualité Âme/Corps | Absente de SpinoLog | Déjà conservée dans le modèle systématique |
| Passé, présent et futur | Extension demandée dans le rapport | Déjà introduits pour E3P18 |
| Intensité « d'autant plus/moins » | Non représentée | Garder comme capacité future explicitement manquante |

## Enrichissement 1 — reconstruction historique SpinoLog 1988

Créer une couche autonome, distincte à la fois de `rules/historical.rules` et
du modèle systématique :

```text
spinoza/spinolog_1988/
  facts/
  rules/
  theorems/
  reports/
```

Cette couche devra transcrire :

1. les notions, leurs natures, signes et contraires ;
2. les types de relations `DEDUCTIVE`, `NON-DEDUCTIVE` et `SYMETRIQUE` ;
3. les règles de domaine P13 à P48 décrites dans le chapitre III ;
4. les règles logiques DEDUC documentées ;
5. les hypothèses, buts et intermédiaires publiés pour les 24 propositions du
   chapitre IV.

Chaque règle portera au minimum :

```yaml
origin: historical_model
source: Cavarretta1988
page: III.x
fidelity: literal | normalized | interpreted | blocked
```

Les objets créés, variables non liées, prémisses implicites et erreurs
typographiques resteront visibles. Une correction nécessaire à l'exécution
devra produire une règle distincte marquée `historical_interpretation`.

### Critère de sortie

- toutes les règles lisibles du rapport sont transcrites ou déclarées
  `blocked` ;
- chaque démonstration publiée possède un cas exécutable ou un diagnostic ;
- les résultats de la présentation de Gondran restent inchangés ;
- aucune règle SpinoLog 1988 n'est chargée par le modèle systématique.

## Enrichissement 2 — audit de la clôture déductive

SpinoLog ne vérifie pas seulement une conclusion cible. Pour E3P19, le rapport
mentionne 45 inférences et 46 faits déduits, dont plusieurs conclusions
annexes. Ces faits inattendus servent à détecter les conséquences fortes, les
boucles et les conflits du modèle.

Le lanceur de manifestes Snarky devra pouvoir publier, sans modifier le cœur du
moteur :

- le nombre de faits initiaux et dérivés ;
- le nombre de dérivations et de règles activées ;
- les faits annexes explicitement attendus ;
- les faits interdits ou contradictoires ;
- les conclusions sans rapport avec les buts ;
- les branches de preuve alternatives écartées par la provenance minimale.

Un manifeste pourra progressivement recevoir :

```yaml
closure_expectations:
  must_derive: []
  must_not_derive: []
  allowed_contradictions: []
  max_derived_facts: null
```

Le seuil `max_derived_facts` sera d'abord informatif. Il ne deviendra bloquant
qu'après stabilisation des règles afin de ne pas confondre richesse du modèle
et explosion combinatoire.

## Enrichissement 3 — méta-ontologie expérimentale

SpinoLog représente comme faits la nature, le signe, le contraire et les
propriétés logiques des relations. Ses règles DEDUC propagent ensuite
symétrie, signe et nature. Cette idée peut réduire les duplications de règles,
mais l'algèbre binaire du rapport est une hypothèse interprétative forte.

L'expérimentation devra donc rester optionnelle :

- déclarer les oppositions sans supposer que toute notion possède un contraire ;
- distinguer `contraire`, `incompatible`, `FAUX` et `INEXISTANT` ;
- déclarer explicitement les relations symétriques ou transitives ;
- ne jamais déduire une négation à partir de la seule absence d'un fait ;
- comparer les résultats produits par règles spécialisées et méta-règles.

Une méta-règle ne rejoindra le modèle systématique que si elle préserve les
preuves existantes et si sa portée textuelle est justifiée proposition par
proposition.

## Enrichissement 4 — témoins existentiels bornés

Le rapport utilise un symbole générique `QQCHOSE` pour matérialiser une cause
inconnue et recommande déjà de numéroter ces objets. La réutilisation d'un seul
symbole peut fusionner des individus qui devraient rester distincts.

Ordre proposé :

1. conserver les témoins nommés dans les manifestes systématiques ;
2. enregistrer leur rôle existentiel dans le catalogue ;
3. ajouter un générateur déterministe de témoins bornés seulement lorsqu'une
   proposition ne peut être représentée autrement ;
4. garantir qu'une même application de règle réutilise son témoin, mais que
   deux applications indépendantes ne le partagent pas ;
5. tester terminaison, reproductibilité et provenance.

## Enrichissement 5 — génération d'hypothèses et tests exploratoires

Le rapport propose un générateur d'hypothèses. Une version moderne peut être
construite comme un explorateur fini plutôt que comme une génération sans
borne :

- choisir un petit domaine d'individus et de relations autorisées ;
- produire des jeux d'hypothèses typés ;
- saturer la base ;
- regrouper les clôtures équivalentes ;
- signaler contradictions nouvelles, cycles et conclusions surprenantes ;
- conserver tout cas intéressant comme fixture reproductible.

Cette approche doit rester un outil de découverte. Elle ne remplace ni les
preuves textuelles ni les contre-cas construits proposition par proposition.

## Points philosophiques à auditer

Le rapport identifie plusieurs zones où l'exécution éclaire ou fragilise la
formalisation :

- E3P21 : la conclusion qualitative est obtenue, mais pas la variation
  d'intensité ;
- E3P27 et E3P47 : la condition de similitude et l'absence préalable de
  sentiment ne sont pas appliquées de façon uniforme ;
- E3P33 : les chaînes historiques peuvent prouver davantage que l'énoncé en
  n'utilisant pas la similitude ;
- E3P45 : la clôture produit fluctuation, stabilité, jalousie et dérision non
  demandées ;
- E3P48 : `doute`, négation et remise en cause d'un sentiment ne doivent pas
  être confondus ;
- les niveaux `AIME`, `IMAGINE(AIME)`, `SAIT(AIME)` et `DOUTE(AIME)` exigent
  des passages explicitement autorisés, jamais un aplatissement général.

Ces points deviennent des critères de revue obligatoires lors de la
formalisation systématique des propositions concernées.

## Ordre d'intégration

1. Au jalon E3P19–E3P22, ajouter les cas SpinoLog du rapport et l'audit de
   clôture en lecture seule. Ce jalon est réalisé dans
   [`../systematic/reports/milestone_e3p19_e3p22.md`](../systematic/reports/milestone_e3p19_e3p22.md) :
   les conclusions annexes servent de contre-tests, sans transcription de la
   base SpinoLog complète.
2. Avant E3P27, formaliser la typologie de la similitude et ses conditions
   d'application.
3. Avant E3P33, comparer texte, rapport 1988, présentation 2006 et modèle
   systématique.
4. Avant E3P45–E3P48, rendre visibles les conclusions annexes, contradictions
   et niveaux épistémiques.
5. Après E3P59, évaluer séparément méta-ontologie, témoins frais et génération
   d'hypothèses.

Le rapport sert ainsi à la fois de source historique, de jeu de régression et
de catalogue de questions. Il ne devient jamais une autorité textuelle se
substituant à l'Éthique.
