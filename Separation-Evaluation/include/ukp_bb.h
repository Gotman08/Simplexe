#ifndef SE_UKP_BB_H
#define SE_UKP_BB_H

#include "common.h"

/**
 * @brief Heuristique gloutonne UKP triant les objets par ratio utilité/volume décroissant.
 *
 * @param[in] p Instance UKP.
 * @return Solution admissible (à libérer par solution_ukp_liberer()).
 */
SolutionUKP *ukp_heuristique_qualite_prix(const ProblemeUKP *p);

/**
 * @brief Résout l'UKP par séparation-évaluation avec borne par relaxation LP (GLPK).
 *
 * La solution initiale est fournie par ukp_heuristique_qualite_prix().
 *
 * @param[in]  p         Instance UKP.
 * @param[out] stats     Compteurs et temps remplis pendant l'exploration (peut être NULL).
 * @param[in]  verbosite Niveau de trace stdout.
 * @return Meilleure solution trouvée (à libérer par l'appelant).
 */
SolutionUKP *ukp_branch_and_bound(const ProblemeUKP *p,
                                  StatistiquesBB    *stats,
                                  NiveauVerbosite    verbosite);

#endif
