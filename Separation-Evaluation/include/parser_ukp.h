#ifndef SE_PARSER_UKP_H
#define SE_PARSER_UKP_H

#include "common.h"

/**
 * @brief Formats d'entrée reconnus pour une instance UKP.
 */
typedef enum {
    UKP_FORMAT_LP,      /**< Format LP type GLPK (Maximize / Subject To / Bounds). */
    UKP_FORMAT_DIRECT,  /**< Format direct (capacité + listes volumes/utilités). */
    UKP_FORMAT_INCONNU  /**< Format non identifié. */
} FormatUKP;

/**
 * @brief Détecte le format d'un fichier d'instance UKP par inspection de son contenu.
 *
 * @param[in] chemin Chemin du fichier à inspecter.
 * @return Format reconnu ou UKP_FORMAT_INCONNU.
 */
FormatUKP    parser_ukp_detecter_format(const char *chemin);

/**
 * @brief Lit un fichier d'instance UKP (format auto-détecté).
 *
 * @param[in] chemin Chemin du fichier d'entrée.
 * @return Instance allouée (à libérer par probleme_ukp_liberer()), ou NULL en cas d'erreur.
 */
ProblemeUKP *parser_ukp_lire(const char *chemin);

#endif
