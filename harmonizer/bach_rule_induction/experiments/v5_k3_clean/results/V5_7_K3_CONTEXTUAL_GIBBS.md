# V5_7-K3-CONTEXTUAL-RHYTHMIC-GIBBS — génération sur rythme polyphonique réel

## Protocole

- Choral : `bach/bwv108.6`, appartenant au train.
- Soprano, grille d'attaques et tenues fixés.
- Alto, ténor et basse rééchantillonnés par segments d'attaque.
- `12` balayages Gibbs, graine `5517`.
- `20` règles K3 apprises, sans règle historique.
- Test fermé non chargé.

## Résultat structurel

- blocs verticaux : `98` ;
- segments d'attaque totaux : `292` ;
- segments rééchantillonnés : `223` ;
- cellules de tenue : `100` ;
- cohérence des tenues : `true` ;
- blocs avec croisement de voix : `0`.

## Durées conservées

| Voix | Histogramme en noires |
|---|---|
| Soprano | `0.25`×2, `0.5`×23, `1`×36, `2`×2 |
| Alto | `0.5`×30, `1`×33, `2`×2 |
| Tenor | `0.5`×40, `1`×30, `2`×1 |
| Bass | `0.5`×82, `1`×11 |

Le choral produit contient donc des doubles-croches (`0,25`), des
croches (`0,5`), des noires (`1`) et des blanches (`2`).

## Mouvements courts de type passage

Diagnostic purement géométrique : note centrale d'au plus une croche,
approchée et quittée dans la même direction par demi-ton ou ton.

| Voix | Bach | Généré |
|---|---:|---:|
| Soprano | 16 | 16 |
| Alto | 13 | 12 |
| Tenor | 16 | 12 |
| Bass | 36 | 25 |

## Limites

- Le rythme est ici conservé, pas encore généré.
- Le diagnostic de passage n'est pas une analyse harmonique.
- La tonalité utilisée reste la tonalité globale déclarée ; les tonicisations
  locales et degrés orthographiés restent absents.
- Les règles pondérées sont évaluées par le moteur K3 Python ; leur
  compilation dans une base Snarky apprise reste le jalon suivant.

Cette expérience valide la sémantique `ATTACK/HOLD` et l'export
MusicXML/MIDI. Elle ne constitue pas encore une comparaison qualitative
avec DeepBach.
