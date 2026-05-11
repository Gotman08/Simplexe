# Projet CHPS_0805 — Optimisation combinatoire (TSP & UKP)

Implémentation comparative de deux méthodes de résolution exacte pour le
**problème du Voyageur de Commerce (TSP)** et le **problème du Sac à Dos
Généralisé (UKP)** :

1. **Séparation-Évaluation (Branch & Bound)** — application C unifiée,
   utilisant **GLPK** pour la relaxation LP de l'UKP et **Prim/ACPM** pour
   la borne du TSP. Consolidation des **TP3** et **TP5** du cours.
2. **OR-Tools** — application Python unifiée, utilisant **`pywraplp`**
   (CBC) pour l'UKP et **`pywrapcp.RoutingModel`** (PATH_CHEAPEST_ARC +
   GUIDED_LOCAL_SEARCH) pour le TSP.

Le projet inclut également :
- une étude expérimentale comparative complète (CSV + courbes log-log) ;
- des visualisations publication-ready (tour TSP avec gradient, sac à dos
  avec jauge de remplissage) ;
- un script global de pipeline (`scripts/run_all.sh`).

## Structure

```
Simplexe/
├── README.md                                 ← ce fichier
├── Sujet.txt, Modaliter.txt, TP3.txt, TP5.txt
├── Fichiers tests - Sac à dos-20260510/        instances UKP
├── Fichiers tests - Voyageur de commerce-20260510/  instances TSP
├── Separation-Evaluation/                    application C  (cf. son README)
├── OR-Tools/                                 application Python (cf. son README)
├── Resultats/                                sorties générées (créées au runtime)
│   ├── benchmarks/                           CSV + panneau récap (1 rep)
│   ├── benchmarks_pousses/                   CSV bruts + agrégés + boxplots + scaling (multi-rep)
│   ├── visualisations/                       PNG : tours TSP, sacs à dos
│   ├── solutions/                            CSV individuels par instance
│   └── logs/
├── Romeo/                                    kit de déploiement HPC URCA
│   ├── job_benchmark.sbatch                  SLURM job (4h, 8 CPU, 16 GB)
│   ├── deploy.sh                             rsync local -> Romeo
│   ├── fetch_results.sh                      rsync Romeo -> local
│   └── README.md
└── scripts/
    ├── run_all.sh                            pipeline rapide (1 rep)
    ├── run_benchmark_pousse.sh               benchmark exhaustif (multi-rep)
    └── make_plots.py                         régénère les figures à partir des CSV
```

## Démarrage rapide

```bash
# 1. Compiler le solveur C (GLPK requis : sudo apt install libglpk-dev)
cd Separation-Evaluation && make && cd ..

# 2. Installer les dépendances Python
pip install -r OR-Tools/requirements.txt

# 3. Test rapide sur les petites instances
./Separation-Evaluation/bin/solveur --probleme ukp \
    --fichier "Fichiers tests - Sac à dos-20260510/prob_sac_1.txt"
python3 OR-Tools/main.py --probleme tsp \
    --fichier "Fichiers tests - Voyageur de commerce-20260510/pd_5.tsp" --visu

# 4. Pipeline complet (compile + benchmark + figures)
bash scripts/run_all.sh
```

Les résultats apparaissent dans `Resultats/benchmarks/` (CSV + panneau
récapitulatif PNG) et `Resultats/visualisations/` (tours TSP et solutions
de sac à dos en PNG haute résolution).

## Documentation détaillée

- [Separation-Evaluation/README.md](Separation-Evaluation/README.md) — application C : compilation, CLI, algorithmes
- [OR-Tools/README.md](OR-Tools/README.md) — application Python : installation, CLI, visualisations

## Reproduire les résultats du rapport

### Mode rapide (Parties 1+2, ~10 min)

```bash
bash scripts/run_all.sh                  # Parties 1 et 2 (instances obligatoires)
bash scripts/run_all.sh --grands         # ajoute pd_59, canada_4663, usa_13509,
                                         # prob_sac_2000, prob_sac_20000 (Partie 3)
```

### Mode benchmark exhaustif (multi-rep, boxplots, scaling, ~1-2 h)

```bash
bash scripts/run_benchmark_pousse.sh                    # Parties 1+2
bash scripts/run_benchmark_pousse.sh --inclure-grands   # + Partie 3
bash scripts/run_benchmark_pousse.sh --inclure-grands --reps-petits 10
```

Sortie : `Resultats/benchmarks_pousses/`
- `ukp_brut.csv`, `tsp_brut.csv` — une ligne par exécution (instance × méthode × rep)
- `ukp_agrege_temps.csv`, `tsp_agrege_temps.csv` — médiane/min/max/stddev par (instance × méthode)
- `panneau_principal.png` — temps + nœuds × UKP + TSP en log-log
- `boxplot_temps_ukp.png`, `boxplot_temps_tsp.png` — variabilité par instance
- `scaling_ukp.png`, `scaling_tsp.png` — courbes de scaling avec barres d'erreur min/max
- `qualite_relative.png` — ratio valeur(BB) / valeur(OR-Tools) par instance

### Sur Romeo (URCA HPC)

```bash
# Depuis ton poste local
export ROMEO_USER=tonlogin
bash Romeo/deploy.sh        # rsync vers Romeo
ssh $ROMEO_USER@romeo.univ-reims.fr
cd ~/chps0805
sbatch Romeo/job_benchmark.sbatch    # lance le benchmark exhaustif

# Une fois termine, rapatrie les resultats
bash Romeo/fetch_results.sh
```

Voir [Romeo/README.md](Romeo/README.md) pour le détail.

Toutes les figures du rapport sont régénérables depuis les CSV via :
```bash
python3 scripts/make_plots.py
```

## Compatibilité

- **Linux / WSL** : cible primaire (validation de l'évaluation).
- **macOS** : devrait fonctionner après `brew install glpk`.
- **Windows** : la partie Python fonctionne nativement ; la partie C
  nécessite WSL (la chaîne de build suppose un environnement POSIX).

## Conformité au sujet

- ✅ Application C unifiée (un seul exécutable, paramétrable par CLI).
- ✅ Application Python unifiée (un seul `main.py`, paramétrable par CLI).
- ✅ `Makefile`, `Readme` par application, structure d'archive conforme à `Modaliter.txt`.
- ✅ Tests sur l'ensemble des instances obligatoires (`prob_sac_1..5`,
      `prob_sac_10..30`, `graphe_12..15`, `pd_5..pd_22`, `pd_59`).
- ✅ Distances TSPLIB95 strictement conformes (`nint(sqrt(...))`).
- ✅ Étude expérimentale comparative (temps + nœuds) avec courbes.

## Contributions personnelles (bonus)

- Heuristique du plus proche voisin + post-traitement **2-opt** pour le TSP.
- Heuristique qualité-prix (tri glouton optimisé) pour l'UKP.
- Visualisations matplotlib publication-ready (tour avec gradient
  d'orientation, sac à dos avec jauge interactive, panneau benchmark
  log-log).
- Mode silencieux côté C pour intégration directe dans le pipeline Python.
