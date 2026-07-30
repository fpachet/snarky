# V20C — décision sur les transitions de fondamentales nommées

## Pourquoi ce test n'est pas V13

V13 représentait la transition entre deux **notes de basse** relatives à la
tonique. V20C représente la transition entre deux **fondamentales d'accords
analysés**. L'audit train-only confirme que la différence n'est pas
cosmétique :

- `58,33 %` des arêtes ont deux analyses nommées uniques ;
- parmi elles, `67,58 %` des transitions de fondamentales diffèrent des
  transitions de basses, principalement à cause des renversements ;
- 42 cellules ont au moins 100 occurrences dans au moins 10 chorals.

La famille franchit donc la barrière de nouveauté et de couverture.

## Protocole

La grammaire engendre symétriquement les `2 × 12 × 12 = 288` transitions de
degrés en modes majeur et mineur. Les grands marginaux observés dans l'audit
ne sont pas copiés dans la base. La sélection conserve :

- la pseudo-vraisemblance conditionnelle exacte ;
- le réajustement conjoint des poids ;
- le budget de 30 colonnes ;
- la règle finale d'une erreur standard ;
- les mêmes 32 chorals de structure et 10 de validation que V20B.

La qualité, la métrique et le renversement ne sont pas ajoutés à la
transition : V20C teste une seule interaction de complexité 4.

## Résultat

**Aucune transition de fondamentale nommée n'est sélectionnée parmi les
trente colonnes.**

La base retenue contient les mêmes 19 règles que V20B et obtient exactement la
même NLL moyenne de validation par pièce : `0,820487`. Les trente étapes de la
frontière qualité–complexité sont elles aussi identiques à V20B.

Les forts enrichissements marginaux comme `7 → 0` existent bien dans le
corpus, mais ils n'apportent pas de gain conditionnel suffisant une fois les
profils tonals, les statuts verticaux et les règles de conduite des voix déjà
présents.

## Décision

- La famille de transitions nommées est **rejetée sous cette forme**.
- Aucun pli de stabilité supplémentaire n'est lancé : il répéterait cinq fois
  un résultat sans transition sélectionnée.
- Aucun réajustement complet et aucune génération ne sont produits : ils
  seraient identiques à V20B.
- La transition ne sera pas sauvée en abaissant après coup sa complexité ou
  son seuil de support.
- Le test réservé reste fermé.

V20C ne remet pas en cause les quatre statuts verticaux robustes de V20B. Il
montre seulement que les fausses notes ne se corrigent pas par une table
pairwise de progressions de fondamentales relative à la tonalité globale.
