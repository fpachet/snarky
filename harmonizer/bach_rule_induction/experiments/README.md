# Experiments

Une expérience devra être entièrement décrite par une configuration versionnée
et produire des résultats machine-readable.

Elle enregistrera notamment :

- manifeste et partition du corpus ;
- versions des systèmes et du catalogue de règles ;
- graines et nombre d'échantillons ;
- informations conditionnées à l'entrée ;
- critères d'exclusion préenregistrés ;
- sorties brutes, métriques et classification des désaccords.

Le jeu de test final reste fermé jusqu'au gel des features, règles et métriques
principales.

## Premier POC différentiable

[`differentiable_rules_poc/`](differentiable_rules_poc/) apprend des clauses
locales depuis les hauteurs du corpus historique. Le gradient de la
vraisemblance conditionnelle guide la recherche, puis une compression
symbolique propose des prédicats locaux réutilisables. Le premier résultat
retrouve notamment les patrons numériques correspondant aux quintes et octaves
parallèles, sans exposer ces noms pendant l'apprentissage.
