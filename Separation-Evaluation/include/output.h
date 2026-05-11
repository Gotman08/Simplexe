#ifndef SE_OUTPUT_H
#define SE_OUTPUT_H

#include "common.h"

/**
 * @brief Affiche sur stdout les caractéristiques d'une instance UKP.
 *
 * @param[in] p Instance à décrire.
 * @param[in] v Niveau de détail (NIVEAU_SILENT supprime l'affichage).
 */
void output_afficher_probleme_ukp(const ProblemeUKP *p, NiveauVerbosite v);

/**
 * @brief Affiche sur stdout les caractéristiques d'une instance TSP.
 *
 * @param[in] p Instance à décrire.
 * @param[in] v Niveau de détail (NIVEAU_SILENT supprime l'affichage).
 */
void output_afficher_probleme_tsp(const ProblemeTSP *p, NiveauVerbosite v);

/**
 * @brief Affiche sur stdout une solution UKP et les statistiques associées.
 *
 * @param[in] p     Instance résolue.
 * @param[in] s     Solution trouvée.
 * @param[in] stats Statistiques de l'exécution.
 * @param[in] v     Niveau de détail.
 */
void output_afficher_solution_ukp(const ProblemeUKP    *p,
                                  const SolutionUKP    *s,
                                  const StatistiquesBB *stats,
                                  NiveauVerbosite       v);

/**
 * @brief Affiche sur stdout une solution TSP et les statistiques associées.
 *
 * @param[in] p     Instance résolue.
 * @param[in] s     Solution trouvée.
 * @param[in] stats Statistiques de l'exécution.
 * @param[in] v     Niveau de détail.
 */
void output_afficher_solution_tsp(const ProblemeTSP    *p,
                                  const SolutionTSP    *s,
                                  const StatistiquesBB *stats,
                                  NiveauVerbosite       v);

/**
 * @brief Exporte au format CSV une instance UKP, sa solution et ses statistiques.
 *
 * @param[in] chemin Chemin du fichier CSV à écrire (écrasement).
 * @param[in] p      Instance.
 * @param[in] s      Solution.
 * @param[in] stats  Statistiques d'exécution.
 * @return 0 en cas de succès, valeur non nulle en cas d'erreur d'écriture.
 */
int output_exporter_ukp_csv(const char           *chemin,
                            const ProblemeUKP    *p,
                            const SolutionUKP    *s,
                            const StatistiquesBB *stats);

/**
 * @brief Exporte au format CSV une instance TSP, sa solution et ses statistiques.
 *
 * @param[in] chemin Chemin du fichier CSV à écrire (écrasement).
 * @param[in] p      Instance.
 * @param[in] s      Solution.
 * @param[in] stats  Statistiques d'exécution.
 * @return 0 en cas de succès, valeur non nulle en cas d'erreur d'écriture.
 */
int output_exporter_tsp_csv(const char           *chemin,
                            const ProblemeTSP    *p,
                            const SolutionTSP    *s,
                            const StatistiquesBB *stats);

#endif
