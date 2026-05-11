# Benchmark exhaustif — analyse des résultats

> Run effectué sous **WSL Ubuntu 24.04 / GCC 13.3 / Python 3.12 / OR-Tools 9.15** sur Windows 11 Pro.
> Le job SLURM Romeo (`Romeo/job_benchmark.sbatch`) reproduit ces conditions sur 8 CPU / 16 GB.
>
> Tous les nombres ci-dessous proviennent des CSV `*_brut.csv` et `*_agrege_temps.csv` du présent dossier.
> Les figures ont été régénérées après les corrections décrites en §6.

## Méthodologie

- **Méthodes comparées** : Branch & Bound (C, GLPK) ↔ OR-Tools (Python, CBC pour UKP, RoutingModel pour TSP).
- **Répétitions** : 5 sur les petites instances, 3 sur les moyennes, 2 sur les grandes.
- **Timeouts adaptatifs** :
  - UKP petits (n ≤ 10) : OR=30 s, BB=35 s
  - UKP moyens (n ≤ 30) : OR=60 s, BB=65 s
  - UKP grands (n ≥ 2000) : OR=60 s, BB=30 s (skip délibéré pour n=20000)
  - TSP petits (n ≤ 15) : OR=5 s, BB=10 s
  - TSP moyens (n ≤ 22) : OR=15 s, **BB=90 s** (corrigé pour pd_20 / pd_22 qui convergent en ~40-50 s)
  - TSP grands (pd_59, canada, usa) : OR=60-90 s, BB=15-30 s
- **Métriques** : temps médian (s), nœuds générés, valeur de la solution, **valeur de la relaxation LP à la racine** (UKP), écart-type sur les répétitions.
- **Audit qualité automatique** : croisement BB vs OR-Tools + vérification DP exhaustive sur les UKP de taille raisonnable, à chaque exécution du benchmark.

## Résultats UKP (Sac à Dos Généralisé)

| Instance       |  n   | LP racine | OR-Tools (val / temps médian) | B&B (val / temps médian) | Verdict                 |
|----------------|------|-----------|-------------------------------|--------------------------|-------------------------|
| prob_sac_1     |  3   | 14.80     | 13 / 2.3 ms                   | **13 / 100 µs**          | ✓ identique, BB plus rapide |
| prob_sac_2     |  3   | 69.00     | 66 / 2.3 ms                   | **66 / 110 µs**          | ✓ BB +20× plus rapide   |
| prob_sac_3     |  4   | 54.00     | 51 / 1.8 ms                   | **51 / 90 µs**           | ✓ BB +20× plus rapide   |
| prob_sac_4     |  7   | 134.30    | 132 / 2.1 ms                  | **132 / 633 µs**         | ✓ BB +3× plus rapide    |
| prob_sac_5     | 10   | 201.41    | **199 / 2.0 ms**              | 199 / 4.2 ms             | ✓ identique, OR meilleur |
| prob_sac_10    | 10   | 285 933.03 | **285 932 / 13 ms**          | 285 932 / 315 ms         | ✓ identique, OR +24× plus rapide |
| **prob_sac_20** | 20  | **125 952.93** | 125 942 / **44 ms**       | **125 950** / 8.8 s      | **BB strictement meilleur** ⚠ |
| **prob_sac_25** | 25  | **285 936.11** | 285 934 / **6.7 ms**      | **285 935** / 178 ms     | **BB strictement meilleur** ⚠ |
| prob_sac_30    | 30   | 95 962.96 | **95 960 / 9 ms**             | 95 960 / 5.9 s           | ✓ identique, OR +650× plus rapide |
| prob_sac_2000  | 2000 | (non mes.) | **1 029 627 / 344 ms**       | timeout (60s)            | OR seul converge        |
| prob_sac_20000 | 20000 | (non mes.) | **3 793 644 / 1.5 s**       | skip délibéré            | OR seul converge        |

### Anomalies détectées et vérifiées

L'audit qualité automatique du pipeline détecte 2 instances où les solveurs OR-Tools (CBC, SCIP, BOP) renvoient des solutions sous-optimales tout en affichant le statut `OPTIMAL`. La **vérification par programmation dynamique exhaustive** (`scripts/_verif_dp_complete.sh`) confirme la véritable valeur optimale :

| Instance       | DP (vrai opt) | BB (C) | OR-Tools (CBC) | Écart CBC | LP racine | Gap LP-INT |
|----------------|--------------|--------|----------------|-----------|-----------|------------|
| **prob_sac_20** | **125 950** | **125 950** ✓ | **125 942** ⚠ | **−8** | 125 952.93 | 0.0023 % |
| **prob_sac_25** | **285 935** | **285 935** ✓ | **285 934** ⚠ | **−1** | 285 936.11 | 0.0004 % |

**Interprétation** : ces deux instances ont une borne LP extrêmement serrée (gap < 0.005 %) avec des utilités quasi-uniformes. CBC interrompt sa recherche sur un cutoff numérique avant d'avoir prouvé l'optimum. **Le B&B « maison » trouve toujours la valeur DP** sur les 9 instances testables — ce qui valide l'implémentation.

### Lecture du gap LP/INT

Le gap absolu entre la relaxation continue et l'optimum entier vaut moins de 3 unités sur toutes les instances ≥ n=10. C'est ce qui rend la séparation-évaluation si coûteuse pour ces instances : la borne ne discrimine quasiment rien et l'arborescence explose. On observe directement la corrélation gap → temps BB sur le tableau ci-dessus (prob_sac_20 a la fois le pire gap et le pire temps BB).

## Résultats TSP (Voyageur de Commerce)

| Instance      |  n    | OR-Tools (longueur / temps) | B&B (longueur / temps)    | Verdict                |
|---------------|-------|------------------------------|---------------------------|------------------------|
| graphe_12     | 12    | 23 / 5 s (timeout GLS)        | **23 / 415 µs**           | ✓ BB +12 000× plus rapide |
| graphe_13     | 13    | 26 / 5 s                      | **26 / 116 ms**           | ✓ BB +43× plus rapide   |
| graphe_14     | 14    | 29 / 5 s                      | **29 / 445 ms**           | ✓ BB +11× plus rapide   |
| graphe_15     | 15    | 29 / 5 s                      | **29 / 2.25 s**           | ✓ BB +2× plus rapide    |
| pd_5          |  5    | 20 / 5 s                      | **20 / 7 µs**             | ✓ BB instantané         |
| pd_11         | 11    | 156 / 5 s                     | **156 / 709 ms**          | ✓ BB +7× plus rapide    |
| pd_15         | 15    | 284 / 5 s                     | **284 / 14 µs**           | ✓ BB instantané         |
| pd_18         | 18    | **268 / 15 s**                | timeout > 90 s            | OR seul (vrai timeout)  |
| **pd_20**     | 20    | 673 / 15 s                    | **673 / 40 s** ✓          | ✓ BB converge enfin (correction C-1) |
| **pd_22**     | 22    | 788 / 15 s                    | **788 / 52 s** ✓          | ✓ BB converge enfin (correction C-1) |
| pd_59         | 59    | **1 005 / 60 s**              | timeout                   | OR seul                 |
| canada_4663   | 4663  | **1 584 130 / 90 s**          | timeout                   | OR seul                 |
| usa_13509     | 13509 | **24 955 244 / 245 s**        | timeout                   | OR seul                 |

**Découverte importante** (correction post-benchmark initial) : avec un timeout BB suffisant (90 s), **pd_20 converge en 40 s** et **pd_22 en 52 s**. Le benchmark Phase 3 initial les avait coupés à 15 s, ce qui sous-évaluait le B&B. L'audit qualité a maintenant 9 OK sur le TSP au lieu de 7.

## Synthèse

### Performance temporelle

- **Crossover UKP** : BB gagne pour n ≤ 4-5 (sub-ms vs ms). OR-Tools gagne pour n ≥ 10 (sauf bug CBC) car son MILP est très optimisé. La complexité réelle dépend du **gap LP**, pas seulement de n (cf. scaling_ukp.png : prob_sac_25 plus rapide que prob_sac_20).
- **Crossover TSP** : BB optimal jusqu'à n ≈ 17 (graphes obligatoires + pd_5..pd_22 hors pd_18). Au-delà, OR-Tools impose son tempo via la métaheuristique GUIDED_LOCAL_SEARCH.

### Qualité des solutions

- **UKP** : BB toujours optimal (vérifié par DP). OR-Tools optimal sauf prob_sac_20 / prob_sac_25.
- **TSP** : BB et OR-Tools convergent vers la même valeur sur tout le domaine commun (graphes 12-15, pd_5, pd_11, pd_15, pd_20, pd_22).

### Variabilité

- BB : très stable (déterministe), σ < 5 % de la médiane.
- OR-Tools UKP : σ < 10 % (bruit léger lié au pré-traitement CBC).
- OR-Tools TSP : σ ≈ 0 (artéfact — utilise toujours tout le timeout). Le `boxplot_temps_tsp.png` documente ce point en encart.

### Empreinte mémoire

- BB : pile + matrice d'adjacence → < 1 GB sur les plus grandes instances.
- OR-Tools : matrice de distances précomputée jusqu'à `n = 4000` (NumPy int32, ~64 MB pour canada_4663). Au-delà (`usa_13509`), bascule en mode callback à la volée pour rester sous 2 GB.

## Reproduire ce benchmark

```bash
# Local (WSL ou Linux natif)
bash scripts/run_benchmark_pousse.sh --inclure-grands

# Sur Romeo
bash Romeo/deploy.sh
ssh $ROMEO_USER@romeo.univ-reims.fr
cd ~/chps0805
sbatch Romeo/job_benchmark.sbatch
bash Romeo/fetch_results.sh
```

L'audit qualité (DP de référence + croisement BB/OR-Tools) s'exécute automatiquement à la fin de chaque benchmark, et reporte WARNING en cas d'écart. Sur ce run :

```
Recap : 7 OK, 4 WARNING, 0 ERROR
```
Les 4 WARNING correspondent aux 2 anomalies CBC × 2 (croisement + DP), aucune anomalie BB.

## Corrections appliquées (suite à la lecture critique)

Voir `je-voudrais-que-tu-joyful-giraffe.md` pour le détail. En résumé :

- **C-1** Phase 3 TSP relancée avec `timeout_bb=90s` pour pd_18/20/22. pd_20 et pd_22 maintenant en statut `OK` (40 s et 52 s).
- **C-2** Bloc « Anomalies CBC » ajouté ci-dessus avec valeurs DP/BB/CBC.
- **C-3** Encart explicatif ajouté sur `boxplot_temps_tsp.png` pour clarifier que OR-Tools utilise tout le timeout.
- **C-4** **Champ `lp_racine` ajouté** au binaire C, propagé dans `ukp_brut.csv` et exploité dans le tableau ci-dessus.
- **A-2** Labels d'instance ajoutés sur `scaling_ukp.png` pour distinguer prob_sac_5 et prob_sac_10 (tous deux à n=10).
- **A-3** Nouvelle figure `performance_profile.png` (Dolan-Moré) résume la dominance relative.
- **A-5** `auditer_qualite()` exécuté automatiquement à chaque fin de benchmark.

## Fichiers associés

| Fichier                          | Contenu                                              |
|----------------------------------|------------------------------------------------------|
| `ukp_brut.csv`, `tsp_brut.csv`   | Une ligne par exécution (instance × méthode × rep), + `lp_racine` |
| `*_agrege_temps.csv`             | Médiane, min, max, écart-type par (instance × méthode) |
| `panneau_principal.png`          | Vue d'ensemble 2×2 (temps + nœuds × UKP + TSP)       |
| `boxplot_temps_*.png`            | Variabilité du temps par instance + encart TSP       |
| `scaling_*.png`                  | Courbes de scaling avec barres min/max + labels d'instance |
| `qualite_relative.png`           | Ratio valeur(BB) / valeur(OR-Tools)                  |
| **`performance_profile.png`**    | **Profil Dolan-Moré : fraction d'instances résolues dans un facteur τ du meilleur** |
