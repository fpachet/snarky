# V27–V28 — décision sur la trajectoire et le mouvement de basse

## V27 : rôle harmonique prioritaire

V27 partitionne chaque bloc en dix statuts : basse d'accord nommé, note du
squelette consonant, passage ou broderie diatonique/chromatique, résolution
préparée/attaquée, autre note diatonique/chromatique.

Les dix cellules sont toutes testables. La confirmation terminale à
`λ=0,6`, sur 50 chorals de validation, donne :

- gain NLL moyen : `+0,007331` ;
- intervalle bootstrap 95 % : `[+0,004941 ; +0,009671]` ;
- chorals améliorés : `40/50`.

Le groupe est donc conditionnellement confirmé. Sa génération réduit les
demi-tons de basse de `81,52 %` à `73,91 %`, mais dégrade légèrement les
mesures verticales. L'audit révèle la cause : le statut « basse d'accord
nommé » masque le mouvement chromatique qui mène à cette note.

## V28 : mouvement indépendant de l'accord

V28 conserve V27 et ajoute une seconde partition indépendante de huit états :
tenue, répétition attaquée, demi-ton de passage/broderie, demi-ton résolu,
demi-ton non résolu, ton entier, petit saut et grand saut.

Le cas critique est vérifié explicitement : une basse peut activer à la fois
« note d'accord » dans V27 et « mouvement chromatique » dans V28. Les poids
sont appris conjointement ; aucune catégorie n'est interdite.

La confirmation terminale de `λ=0,6` sur 50 chorals donne :

- gain NLL moyen : `+0,006836` au-dessus de V27 ;
- intervalle bootstrap 95 % : `[+0,004376 ; +0,009328]` ;
- chorals améliorés : `39/50`.

## Génération Snarky

La première recherche V28 rencontre une contrainte V22 tardive. Un
préfiltrage de domaine retire les alternatives dont la violation K3 est déjà
décidable. La recherche complète termine alors en 801 nœuds :

- 551 domaines vides et 551 backtracks ;
- 10 536 alternatives retirées avant `CHOICE` ;
- score moyen `−0,597431`, seuil strict `−1,394179`.

| Mesure | Bach | V26 | V27 | V28 |
|---|---:|---:|---:|---:|
| Blocs triadiques | 56,12 % | 39,80 % | 38,78 % | 45,92 % |
| Blocs forts non triadiques | 26,92 % | 53,85 % | 53,85 % | 42,31 % |
| Dissonances fortes | 0,462 | 0,885 | 1,000 | 0,808 |
| Demi-tons de basse | 29,35 % | 81,52 % | 73,91 % | 60,87 % |
| Basse hors gamme naturelle | 15,05 % | 40,86 % | 39,78 % | 30,11 % |

V28 est retenu comme nouveau meilleur modèle de cette boucle. Il améliore
simultanément sa cible de basse et les mesures harmoniques, mais l'écart avec
Bach reste matériel. La prochaine induction devra étudier les transitions
d'accord fortes et les grands sauts de basse manquants, sans modifier V28
après écoute.

## Artefacts

- [Couverture V27](V27_BASS_TRAJECTORY_COVERAGE.md)
- [Confirmation V27](V27_BASS_TRAJECTORY_CONFIRMATION50.md)
- [Confirmation V28](V28_BASS_MOTION_CONFIRMATION50.md)
- [Audit des générations](V28_SNARKY_GENERATION_AUDIT.md)
- [Génération V28](TWO_LOOP_FULL_GENERATION_V28.md)
