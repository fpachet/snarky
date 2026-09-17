# POC V2.4 — ablation conjointe du catalogue SATB

## Protocole

- Train : 251 chorals / 68491 décisions.
- Validation : 50 chorals / 13249 décisions.
- Test réservé : 51 chorals, non ouvert.
- Contrôle nul : choix mélangés par choral et par voix.
- Sept règles lisibles sont ajustées conjointement.

## Gain conjoint

| Modèle | NLL train | NLL validation |
|---|---:|---:|
| Socle de nuisance | 2.456296 | 2.462670 |
| Socle + sept règles | 2.449877 | 2.456363 |

Gain NLL validation : `0.006307`.

## Poids par voix

| Règle | Soprano | Alto | Ténor | Basse |
|---|---:|---:|---:|---:|
| `R-MELODY-001` | -0.945 | -0.776 | -0.893 | -0.411 |
| `R-MELODY-002` | -0.819 | -0.581 | -0.609 | -0.474 |
| `R-OVERLAP-001` | -0.203 | -0.210 | -0.139 | -0.027 |
| `R-PARALLEL-001` | 0.046 | -0.137 | 0.003 | 0.032 |
| `R-PARALLEL-002` | 0.107 | 0.000 | -0.021 | -0.045 |
| `R-DIRECT-001` | -0.045 | 0.000 | 0.000 | 0.000 |
| `R-DIRECT-002` | 0.067 | 0.000 | 0.000 | 0.000 |

## Ablation par neutralisation d'un poids

Les autres poids restent fixes : cette mesure isole l'information
portée par chaque colonne dans le modèle conjoint.

| Règle neutralisée | NLL validation | Pénalité |
|---|---:|---:|
| `R-MELODY-002` | 2.463088 | +0.006725 |
| `R-OVERLAP-001` | 2.458791 | +0.002427 |
| `R-MELODY-001` | 2.458069 | +0.001706 |
| `R-PARALLEL-001` | 2.456411 | +0.000048 |
| `R-DIRECT-001` | 2.456392 | +0.000029 |
| `R-DIRECT-002` | 2.456352 | -0.000011 |
| `R-PARALLEL-002` | 2.456318 | -0.000045 |
