# OR-Tools — Application Python

Implémentation unifiée des méthodes **OR-Tools** (Google) pour résoudre :
- le **problème du Sac à Dos Généralisé (UKP)** via `pywraplp` (CBC) ;
- le **problème du Voyageur de Commerce (TSP)** via `pywrapcp.RoutingModel`.

L'application gère également la **visualisation** des solutions (tours TSP,
sac à dos animé d'une jauge de remplissage) et le **benchmark croisé** avec
le binaire C de la partie Séparation-Évaluation.

## Prérequis (Linux / WSL)

```bash
sudo apt-get install -y python3 python3-pip
cd OR-Tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Sous Windows, remplacer `source .venv/bin/activate` par `.\.venv\Scripts\activate`.

## Utilisation

```bash
python main.py --probleme {ukp|tsp} --fichier <chemin> [options]
```

| Option                   | Effet                                                        |
|--------------------------|--------------------------------------------------------------|
| `-p, --probleme`         | `ukp` ou `tsp` (auto-détection du format)                    |
| `-f, --fichier`          | Chemin de l'instance                                         |
| `-t, --timeout`          | Timeout en secondes (défaut : 10)                            |
| `--visu`                 | Génère un PNG de la solution dans `Resultats/visualisations` |
| `--export DIR`           | Exporte un CSV dans `DIR/`                                   |
| `--benchmark`            | Lance la batterie complète (1 rep par instance) et trace les courbes |
| `--benchmark-pousse`     | Benchmark exhaustif (multi-rep, boxplots, scaling, qualité relative) |
| `--reps-petits/moyens/grands` | Nb de répétitions par catégorie (def : 5 / 3 / 2)       |
| `--inclure-grands`       | Inclut les très grandes instances (Partie 3)                 |
| `--binaire-c PATH`       | Chemin du solveur C (par défaut : `../Separation-Evaluation/bin/solveur`) |
| `--visualize TYPE FICHIER` | Visualisation rapide (`ukp` ou `tsp`)                      |

### Exemples

```bash
# Petit UKP (TP3) — résultat attendu : utilité = 13
python main.py --probleme ukp --fichier "../Fichiers tests - Sac à dos-20260510/prob_sac_1.txt"

# Petit TSP (TP5) avec visualisation du tour
python main.py --probleme tsp \
    --fichier "../Fichiers tests - Voyageur de commerce-20260510/graphe_12.txt" \
    --visu

# Visualisation du sac à dos (graphique : objets retenus + jauge)
python main.py --visualize ukp "../Fichiers tests - Sac à dos-20260510/prob_sac_5.txt"

# Benchmark croisé Branch & Bound (C) ↔ OR-Tools (Python)
python main.py --benchmark
python main.py --benchmark --inclure-grands --timeout 120

# Benchmark EXHAUSTIF (multi-répétitions, timeouts adaptatifs, boxplots, scaling)
python main.py --benchmark-pousse                       # Parties 1+2
python main.py --benchmark-pousse --inclure-grands      # + Partie 3 (jusqu'à 4h)
python main.py --benchmark-pousse --reps-petits 10 --reps-moyens 5 --reps-grands 3
```

## Architecture

```
OR-Tools/
├── main.py                CLI argparse unifié
├── requirements.txt
├── config.ini.example
└── src/
    ├── __init__.py
    ├── parsers.py         Parsers UKP (LP / direct) et TSP (graphe / TSPLIB95)
    ├── distances.py       Distance EUC_2D conforme TSPLIB95 (nint sqrt)
    ├── timer.py           Chronomètre perf_counter
    ├── ukp_solver.py      pywraplp (CBC) : variables IntVar, max
    ├── tsp_solver.py      pywrapcp.RoutingModel : PATH_CHEAPEST_ARC + GLS
    ├── visualization.py   matplotlib : tours, sac à dos visuel, courbes
    └── benchmark.py       Batterie complète, écriture CSV, panneau récap
```

## Visualisations

### Tour TSP (`tracer_tour_tsp`)

- Scatter des villes + tour fermé en superposition.
- Gradient de couleur le long du parcours (orientation du tour visible d'un coup d'œil).
- Marqueur ★ orange sur la ville de départ.
- Annotations index (1..N) si N ≤ 60.
- Pour N > 1000 (`canada_4663.tsp`, `usa_13509.tsp`) : style adaptatif (lignes très fines, points minuscules, pas d'annotations).
- Pour les graphes sans coordonnées (`graphe_12..15.txt`) : disposition circulaire.

### Sac à dos (`tracer_solution_ukp`)

- Bar chart horizontal : un objet par ligne, trié par `utilité / volume` décroissant.
- Vert pour les objets retenus, gris translucide pour les écartés.
- Largeur des barres = volume total occupé par l'objet (`valeur × volume unitaire`).
- Panneau latéral : jauge de remplissage du sac (% capacité utilisée) + compteur d'objets pris / total.
- Bandeau récapitulatif : utilité totale, volume utilisé, espace résiduel.

### Courbes de benchmark (`tracer_panneau_benchmark`)

- Panneau 2 × 2 : temps UKP, temps TSP, nœuds UKP, nœuds TSP.
- Échelles log sur X et Y.
- Deux courbes par graphique : Branch & Bound (C) vs OR-Tools (Python).

## Notes

- Le binaire C n'est appelé qu'en mode `--benchmark` (mode silencieux,
  une ligne CSV par exécution). Si le binaire est absent, seules les
  données OR-Tools sont écrites — utile pour l'usage purement Python.
- Les très grandes instances (`usa_13509.tsp`, `prob_sac_20000.txt`)
  ne convergent pas toujours vers l'optimum dans le timeout : OR-Tools
  retourne la meilleure solution faisable trouvée. Documenter cela
  dans le rapport conformément au sujet.

## ⚠ Avertissement sur OR-Tools/CBC pour l'UKP

L'audit qualité du benchmark exhaustif (`Resultats/benchmarks_pousses/ANALYSE.md`)
a révélé que **CBC peut renvoyer des solutions sous-optimales avec statut
`OPTIMAL` sur certaines instances UKP « plates »** — typiquement quand les
utilités sont quasi-uniformes par rapport aux volumes (ratio ≈ constant).

Cas confirmés sur le jeu de tests :

| Instance       | DP / BB (vrai opt) | OR-Tools (CBC) | Écart |
|----------------|--------------------|----------------|-------|
| `prob_sac_20`  | 125 950            | 125 942        | −8    |
| `prob_sac_25`  | 285 935            | 285 934        | −1    |

SCIP et BOP donnent également des résultats sous-optimaux (mais différents).
**Recommandation** : pour les instances UKP suspectes, croiser systématiquement
le résultat avec le BB « maison » via `--benchmark-pousse` (audit automatique)
ou avec une DP de référence si la taille le permet (`n × capacité < 10⁷`).
