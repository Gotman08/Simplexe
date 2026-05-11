#ifndef SE_TSP_BB_H
#define SE_TSP_BB_H

#include "common.h"

/**
 * @brief Construction d'un tour TSP par heuristique du plus proche voisin.
 *
 * @param[in] p              Instance TSP (matrice de distances renseignée).
 * @param[in] sommet_depart  Indice du sommet initial.
 * @return Tour admissible (à libérer par solution_tsp_liberer()).
 */
SolutionTSP *tsp_heuristique_plus_proche_voisin(const ProblemeTSP *p, int sommet_depart);

/**
 * @brief Résout le TSP par séparation-évaluation avec borne 1-arbre (ACPM enraciné en sommet 0).
 *
 * Le tour initial est fourni par tsp_heuristique_plus_proche_voisin().
 *
 * @param[in]  p            Instance TSP.
 * @param[out] stats        Compteurs et temps remplis pendant l'exploration (peut être NULL).
 * @param[in]  verbosite    Niveau de trace stdout.
 * @param[in]  active_2opt  Si non nul, applique tsp_appliquer_2opt() en post-traitement.
 * @return Tour optimal (à libérer par l'appelant).
 */
SolutionTSP *tsp_branch_and_bound(const ProblemeTSP *p,
                                  StatistiquesBB    *stats,
                                  NiveauVerbosite    verbosite,
                                  int                active_2opt);

/**
 * @brief Améliore un tour en place par échanges 2-opt jusqu'à un optimum local.
 *
 * @param[in]     p Instance TSP de référence.
 * @param[in,out] s Tour à améliorer (longueur mise à jour).
 */
void         tsp_appliquer_2opt(const ProblemeTSP *p, SolutionTSP *s);

#endif
