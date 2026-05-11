# Rapport et présentation LaTeX — CHPS_0805

Deux livrables LaTeX conformes aux modalités d'évaluation :
- **`rapport.tex`** → `rapport.pdf` (rapport écrit, 14 pages, ~10 pages de contenu)
- **`presentation.tex`** → `presentation.pdf` (slides Beamer, 26 slides, format 16:9)

## Compilation

### Prérequis Linux / WSL

```bash
sudo apt-get install -y texlive-latex-extra texlive-fonts-recommended \
                        texlive-lang-french texlive-fonts-extra
# texlive-fonts-extra fournit le theme Beamer Metropolis
```

### Build

```bash
cd rapport
make             # compile rapport.pdf ET presentation.pdf
make rapport     # compile uniquement le rapport
make slides      # compile uniquement la presentation
make view        # compile et ouvre le rapport
make slides-view # compile et ouvre la presentation
make clean       # supprime les fichiers auxiliaires
make mrproper    # supprime tout (auxiliaires + 2 PDF)
```

Variante avec `latexmk` (gestion automatique des passes) :

```bash
make latexmk     # compile rapport + presentation via latexmk
```

## Structure du document

| Section | Contenu |
|---|---|
| Page de garde | Titre, auteur, encadrant, date |
| Sommaire (TOC) | Généré automatiquement |
| 1. Introduction | Contexte, objectifs, plan |
| 2. Architecture | Structure du dépôt, applications C et Python, formats |
| 3. Séparation-Évaluation | UKP (TP3), TSP (TP5), bonus 2-opt, lp_racine |
| 4. OR-Tools | UKP via pywraplp, TSP via pywrapcp.RoutingModel |
| 5. Étude expérimentale | Méthodologie, résultats UKP/TSP, panneau, scaling, Dolan-Moré |
| 6. Anomalies | Bug CBC sur prob_sac_20/25, vérification DP |
| 7. Difficultés et améliorations | Mémoire, timeouts, trade-off warnings |
| 8. Conclusion | Synthèse |
| Annexes | Commandes, livrables |

## Figures intégrées

Les sept figures du rapport référencent les fichiers PNG du dossier `Resultats/benchmarks_pousses/` (chemins relatifs `../Resultats/...`). Si tu réorganises le dépôt, vérifie ces chemins dans `rapport.tex`.

## Personnalisation

- **Nom de l'auteur et de l'encadrant** : édite la page de garde de `rapport.tex` (rechercher `[Nom de l'étudiant]` et `[Nom de l'enseignant]`).
- **Bibliographie** : aucune référence externe pour l'instant (le rapport est autoportant). Ajouter `\bibliographystyle{plain}` + `\bibliography{biblio}` si besoin.

## Volumétrie cible

Le rapport compile à environ **10 pages** de contenu (hors page de garde et annexes), conforme à la cible de la modalité (« ne devrait pas excéder une dizaine de pages »).

---

## Présentation Beamer (`presentation.tex`)

### Thème
- **Beamer / Metropolis** en aspect ratio 16:9.
- Mêmes couleurs que le rapport (bleu primaire `#1f77b4`, orange accent `#ff7f0e`).
- ~20 slides (45 secondes par slide pour tenir 15 min de présentation orale).

### Structure (20 slides + 6 séparateurs de section automatiques = 26 pages)

| # | Slide | Contenu |
|---|---|---|
| 1 | Page de garde | Titre + auteur + URCA + CHPS_0805 |
| 2 | Plan | TOC automatique |
| 3 | Contexte | Cadre, objectifs, livrables |
| 4 | Problèmes | Définition formelle UKP & TSP |
| 5 | Architecture | Structure du dépôt, applications unifiées |
| 6 | B&B UKP (TP3) | Qualité-prix + GLPK + DFS |
| 7 | B&B TSP (TP5) | NN + ACPM + best-first + 2-opt |
| 8 | OR-Tools UKP | Snippet `pywraplp` (CBC) |
| 9 | OR-Tools TSP | Snippet `pywrapcp.RoutingModel` (GLS) |
| 10 | Méthodologie | Plan d'expérience, audit qualité |
| 11 | Résultats UKP | Tableau, crossover, anomalies |
| 12 | Panneau principal | Figure 4 axes log-log |
| 13 | Résultats TSP | Tableau (graphes + pd_X + canada + usa) |
| 14 | Visualisation tour | `tsp_pd_22_tour.png` |
| 15 | Anomalies CBC | Tableau certifié par DP exhaustive |
| 16 | Performance profile | Figure Dolan-Moré |
| 17 | Difficultés | Mémoire usa_13509, timeouts, warnings |
| 18 | Améliorations | Held-Karp, Lin-Kernighan, OpenMP |
| 19 | Conclusion | Bilan et bonnes pratiques |
| 20 | Démo + questions | Commandes pour démo live |

### Personnalisation

Le placeholder `[Nom de l'étudiant]` sur la page de garde de `presentation.tex` est à remplacer avant la soutenance.

### Conversion en PowerPoint (si nécessaire)

La modalité accepte un PDF de slides comme support de présentation. Si une version `.pptx` est exigée :

```bash
libreoffice --headless --convert-to pptx presentation.pdf
```

(La conversion altère légèrement le rendu — privilégier le PDF natif.)
