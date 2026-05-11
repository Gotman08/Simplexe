# Déploiement et exécution sur Romeo (URCA HPC)

Procédure complète pour déployer le projet sur le supercalculateur Romeo de l'URCA et lancer le benchmark exhaustif.

## Prérequis

- Compte URCA actif et accès SSH au cluster Romeo
- Modules disponibles sur Romeo : `gcc`, `python3.10+`, `glpk` (à charger via `module load`)
- Variables d'environnement (à définir avant de lancer `deploy.sh`) :

```bash
export ROMEO_USER=tonlogin           # ex : nicolas.maranoni
export ROMEO_HOST=romeo.univ-reims.fr
export ROMEO_DEST=/home/$ROMEO_USER/chps0805
```

## 1. Déployer le code

Depuis ton poste local (avec le projet à plat) :

```bash
bash Romeo/deploy.sh
```

Le script utilise `rsync` pour pousser tout le projet vers Romeo, en excluant les binaires et résultats locaux.

## 2. Soumettre le job

Connexion SSH puis soumission via SLURM :

```bash
ssh $ROMEO_USER@$ROMEO_HOST
cd $ROMEO_DEST

# Vérifier les modules disponibles (adapter au besoin)
module avail gcc python glpk

# Soumettre le job (4h, 8 CPU, 16 GB)
sbatch Romeo/job_benchmark.sbatch
```

Le job script (`Romeo/job_benchmark.sbatch`) :
- compile la partie C (`Separation-Evaluation/bin/solveur`) ;
- crée un venv Python avec OR-Tools ;
- lance le benchmark exhaustif (`--benchmark-pousse --inclure-grands`) avec :
  - 5 répétitions sur les petites instances (n ≤ 30) ;
  - 3 répétitions sur les moyennes (n ≤ 100) ;
  - 2 répétitions sur les grandes (n > 100) ;
- timeouts adaptatifs par taille (10 s à 600 s) ;
- mesures temps + nœuds + qualité de solution + RAM ;
- génère CSV détaillés et figures (panneau, boxplots, scaling).

## 3. Suivre l'exécution

```bash
# Voir l'état du job
squeue -u $ROMEO_USER

# Suivre la sortie en direct
tail -f logs/bench_<JOB_ID>.out
```

## 4. Récupérer les résultats

Une fois le job terminé, depuis ton poste local :

```bash
bash Romeo/fetch_results.sh
```

Les résultats arrivent dans `Resultats_romeo/` :

```
Resultats_romeo/
├── benchmarks_pousses/
│   ├── ukp_brut.csv                # une ligne par exécution (méthode × instance × rep)
│   ├── ukp_agrege.csv              # médiane / min / max / écart-type par (méthode × instance)
│   ├── tsp_brut.csv
│   ├── tsp_agrege.csv
│   ├── panneau_principal.png       # 4 axes log-log : temps + nœuds × UKP + TSP
│   ├── boxplot_temps_ukp.png       # variabilité du temps par instance
│   ├── boxplot_temps_tsp.png
│   ├── scaling_ukp.png             # courbe de scalabilité avec barres d'erreur
│   ├── scaling_tsp.png
│   └── qualite_relative.png        # quotient solution_BB / solution_OR
├── visualisations/                 # tours TSP + sacs UKP
└── benchmarks/                     # benchmark "rapide" (gardé en complément)
```

## Empreinte mémoire & ressources

| Tâche                                       | RAM pic    | Durée typique |
|---------------------------------------------|------------|---------------|
| Compilation C                               | < 100 MB   | < 30 s        |
| Benchmark UKP (toutes instances obligatoires) | < 200 MB | ~5 min        |
| BB sur prob_sac_20000 (timeout 300 s)        | < 1 GB    | 5 min × 2     |
| OR-Tools sur prob_sac_20000                  | < 200 MB  | < 1 s         |
| OR-Tools sur usa_13509 (timeout 180 s)       | ~2 GB     | 3 min × 2     |
| Génération de toutes les figures             | < 500 MB  | < 30 s        |
| **Total job exhaustif (—inclure-grands)**    | ~2 GB pic | **1-2 h**     |

Le job SLURM réserve 16 GB et 8 CPU pour absorber les variations.

## Adapter aux modules de Romeo

Si Romeo a besoin de modules spécifiques :

```bash
# dans job_benchmark.sbatch, decommente et adapte :
module load gcc/13.3.0
module load python/3.12
module load glpk/5.0
```

Pour découvrir les modules disponibles :

```bash
ssh $ROMEO_USER@$ROMEO_HOST
module avail gcc python glpk
```

## Tester en local (équivalent WSL)

Pour reproduire la même charge sans Romeo :

```bash
bash scripts/run_benchmark_pousse.sh --inclure-grands
```

Le script local utilise les mêmes paramètres que le job SLURM.

## Dépannage

| Problème                          | Solution                                                          |
|-----------------------------------|-------------------------------------------------------------------|
| `ssh: Permission denied`          | Vérifier la clef SSH (`ssh-add ~/.ssh/id_rsa`) et l'accès URCA    |
| `glpk.h: No such file or directory` | `module load glpk` ou `apt install libglpk-dev` (admin)        |
| `ModuleNotFoundError: ortools`    | `OR-Tools/.venv/bin/pip install -r OR-Tools/requirements.txt`    |
| Job tué (OOM)                     | Augmenter `#SBATCH --mem=32G` dans `job_benchmark.sbatch`         |
| Job timeout                       | Augmenter `#SBATCH --time=08:00:00` ou retirer `--inclure-grands` |
