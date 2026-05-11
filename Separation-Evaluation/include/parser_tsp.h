#ifndef SE_PARSER_TSP_H
#define SE_PARSER_TSP_H

#include "common.h"

/**
 * @brief Formats d'entrée reconnus pour une instance TSP.
 */
typedef enum {
    TSP_FORMAT_GRAPHE,   /**< Format interne "graphe_N.txt" (matrice directe). */
    TSP_FORMAT_TSPLIB95, /**< Format TSPLIB 95 (NODE_COORD_SECTION, EDGE_WEIGHT_SECTION). */
    TSP_FORMAT_INCONNU   /**< Format non identifié. */
} FormatTSP;

/**
 * @brief Détecte le format d'un fichier d'instance TSP par inspection de son contenu.
 *
 * @param[in] chemin Chemin du fichier à inspecter.
 * @return Format reconnu ou TSP_FORMAT_INCONNU.
 */
FormatTSP    parser_tsp_detecter_format(const char *chemin);

/**
 * @brief Lit un fichier d'instance TSP (format auto-détecté).
 *
 * @param[in] chemin Chemin du fichier d'entrée.
 * @return Instance allouée (à libérer par probleme_tsp_liberer()), ou NULL en cas d'erreur.
 */
ProblemeTSP *parser_tsp_lire(const char *chemin);

#endif
