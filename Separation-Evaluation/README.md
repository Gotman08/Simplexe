# Separation-Evaluation — Application C

Implémentation unifiée des méthodes de **séparation et évaluation** (Branch & Bound) pour résoudre :
- le **problème du Sac à Dos Généralisé (UKP)** — relaxation LP via GLPK + heuristique qualité-prix ;
- le **problème du Voyageur de Commerce (TSP)** — borne par ACPM (excluant le sommet 0) + 2 plus légères arêtes incidentes au sommet 0 + heuristique du plus proche voisin.

Cette application correspond à la consolidation des **TP3** (UKP) et **TP5** (TSP) du cours `CHPS_0805`.

## Prérequis (Linux / WSL)

```bash
sudo apt-get update
sudo apt-get install -y build-essential libglpk-dev
```

- `gcc` ≥ 9
- `libglpk-dev` (l'application appelle directement l'API GLPK)
- `make`

## Compilation

```bash
cd Separation-Evaluation
make            # produit bin/solveur
```

Cibles utiles :
- `make`           → compile `bin/solveur`
- `make clean`     → supprime les fichiers objets
- `make mrproper`  → supprime objets + binaire
- `make run-test`  → exécute deux tests rapides (prob_sac_1, graphe_12)

## Utilisation

```bash
./bin/solveur --probleme {ukp|tsp} --fichier <chemin> [options]
```

| Option              | Effet                                                      |
|---------------------|------------------------------------------------------------|
| `-p, --probleme`    | `ukp` ou `tsp` (obligatoire)                               |
| `-f, --fichier`     | Chemin de l'instance (format auto-détecté, obligatoire)    |
| `-e, --export DIR`  | Exporte le résumé CSV dans `DIR/<instance>_bb.csv`         |
| `-v, --verbose`     | Affichage détaillé (matrice, tour, énumération …)          |
| `-s, --silent`      | Sortie machine (une ligne CSV) — utile pour le benchmarking |
| `--no-2opt`         | Désactive le post-traitement 2-opt sur le TSP              |
| `-h, --help`        | Affiche l'aide                                             |

### Formats d'instances supportés

| Problème | Format                       | Reconnaissance     | Exemples                                       |
|----------|------------------------------|--------------------|------------------------------------------------|
| UKP      | TP3 — programme linéaire      | `n_variables ...`  | `prob_sac_1.txt` … `prob_sac_5.txt`            |
| UKP      | Étendu — `n / c / objets`    | `n: ...` `c: ...`  | `prob_sac_10.txt` … `prob_sac_20000.txt`       |
| TSP      | TP5 — liste d'arêtes valuées | `n_sommets ...`    | `graphe_12.txt` … `graphe_15.txt`              |
| TSP      | TSPLIB95 (EUC_2D)            | `NAME / DIMENSION` | `pd_5.tsp` … `usa_13509.tsp`                   |

La distance EUC_2D suit strictement la définition TSPLIB95 :
`d(i,j) = nint(sqrt((xi-xj)² + (yi-yj)²))`.

## Exemples

```bash
# Petit UKP du TP3 (résultat attendu : utilité = 13)
./bin/solveur --probleme ukp --fichier "../Fichiers tests - Sac à dos-20260510/prob_sac_1.txt"

# Petit TSP du TP5 (verbose) — résultat attendu pour graphe_12
./bin/solveur --probleme tsp \
    --fichier "../Fichiers tests - Voyageur de commerce-20260510/graphe_12.txt" --verbose

# Export CSV pour benchmark
mkdir -p ../Resultats/solutions
./bin/solveur -p ukp -f "../Fichiers tests - Sac à dos-20260510/prob_sac_5.txt" \
              -e ../Resultats/solutions

# Mode silencieux pour scripts
./bin/solveur -p tsp -f .../pd_5.tsp -s
# Sortie : pd_5,19,0.000123,42
```

## Architecture du code

```
Separation-Evaluation/
├── Makefile
├── config.cfg.example
├── include/        Headers publics (un par module)
│   ├── common.h    Types partagés et allocateurs sûrs
│   ├── parser_ukp.h / parser_tsp.h
│   ├── tsplib.h    Distances EUC_2D (nint)
│   ├── ukp_bb.h / tsp_bb.h
│   ├── output.h    Affichage console + export CSV
│   └── timer.h     clock_gettime(CLOCK_MONOTONIC)
└── src/            Sources
    ├── common.c
    ├── parser_ukp.c   auto-détection LP / direct
    ├── parser_tsp.c   auto-détection graphe / TSPLIB95
    ├── tsplib.c       formules conformes TSPLIB95
    ├── ukp_bb.c       B&B itératif + GLPK + heuristique qualité-prix
    ├── tsp_bb.c       B&B meilleur d'abord + ACPM Prim + plus proche voisin + 2-opt
    ├── output.c       affichage et export CSV
    ├── timer.c
    └── main.c         CLI getopt_long
```

## Algorithmes

### UKP — TP3
- **Borne initiale** : heuristique qualité-prix (tri par `utilité / volume` décroissant).
- **Évaluation d'un nœud** : relaxation LP par GLPK (variables réelles bornées par les choix déjà fixés).
- **Test d'intégrité** : `modf` sur chaque valeur réelle.
- **Séparation** : variable fractionnaire identifiée → branches sur valeurs entières `0..⌊max⌋`.
- **Stratégie** : DFS itératif (pile explicite, recommandé par le TP3).

### TSP — TP5
- **Borne initiale** : heuristique du plus proche voisin depuis le sommet 0.
- **Évaluation d'un nœud** : ACPM (Prim) sur `G \ {0}` + 2 arêtes les plus légères incidentes au sommet 0.
- **Test du cycle hamiltonien** : tous les sommets de degré exactement 2.
- **Séparation** : sommet de degré > 2 → 3 fils (un par arête incidente interdite).
- **Stratégie** : meilleur-d'abord (tas binaire min-heap sur les évaluations).
- **Bonus 2-opt** : post-traitement sur la solution optimale (n'altère pas la convergence du B&B).

## Notes sur la qualité de la solution

Pour les très grandes instances (`prob_sac_2000.txt`, `prob_sac_20000.txt`,
`canada_4663.tsp`, `usa_13509.tsp`), la convergence du Branch & Bound n'est
pas garantie en temps raisonnable : le programme retourne la meilleure
solution faisable connue (heuristique d'amorçage améliorée par le 2-opt
pour le TSP). Les difficultés rencontrées sont à documenter dans le rapport.
