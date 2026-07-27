# POC V2.4 — ablation conjointe du catalogue SATB

## Protocole

- Train : 251 chorals / 68491 décisions.
- Validation : 50 chorals / 13249 décisions.
- Test réservé : 51 chorals, non ouvert.
- Données authentiques.
- Sept règles lisibles sont ajustées conjointement.

## Gain conjoint

| Modèle | NLL train | NLL validation |
|---|---:|---:|
| Socle de nuisance | 1.345111 | 1.355250 |
| Socle + sept règles | 1.282853 | 1.287062 |

Gain NLL validation : `0.068188`.

## Poids par voix

| Règle | Soprano | Alto | Ténor | Basse |
|---|---:|---:|---:|---:|
| `R-MELODY-001` | -0.991 | -0.898 | -0.902 | -1.150 |
| `R-MELODY-002` | -1.264 | -1.172 | -0.883 | -0.990 |
| `R-OVERLAP-001` | -1.106 | -0.824 | -0.558 | -0.531 |
| `R-PARALLEL-001` | -2.288 | -2.442 | -2.578 | -2.777 |
| `R-PARALLEL-002` | -2.232 | -2.367 | -2.132 | -2.562 |
| `R-DIRECT-001` | -1.138 | 0.000 | 0.000 | 0.000 |
| `R-DIRECT-002` | -0.962 | 0.000 | 0.000 | 0.000 |

## Ablation par neutralisation d'un poids

Les autres poids restent fixes : cette mesure isole l'information
portée par chaque colonne dans le modèle conjoint.

| Règle neutralisée | NLL validation | Pénalité |
|---|---:|---:|
| `R-PARALLEL-001` | 1.315505 | +0.028443 |
| `R-PARALLEL-002` | 1.312122 | +0.025060 |
| `R-OVERLAP-001` | 1.294758 | +0.007697 |
| `R-MELODY-002` | 1.292932 | +0.005871 |
| `R-MELODY-001` | 1.289979 | +0.002917 |
| `R-DIRECT-002` | 1.287898 | +0.000836 |
| `R-DIRECT-001` | 1.287563 | +0.000501 |
