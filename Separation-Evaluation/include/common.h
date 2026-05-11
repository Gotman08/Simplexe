#ifndef SE_COMMON_H
#define SE_COMMON_H

#include <stddef.h>
#include <stdio.h>

#define SE_VERSION "1.0.0"

/**
 * @brief Famille de problème combinatoire pris en charge par le solveur.
 */
typedef enum {
    PROBLEME_UKP, /**< Sac à dos 0/1 (Unbounded/0-1 Knapsack Problem). */
    PROBLEME_TSP  /**< Voyageur de commerce (Travelling Salesman Problem). */
} TypeProbleme;

/**
 * @brief Niveau de trace écrit sur stdout pendant la résolution.
 */
typedef enum {
    NIVEAU_SILENT  = 0, /**< Aucune sortie en dehors du résultat final. */
    NIVEAU_NORMAL  = 1, /**< Étapes principales et statistiques. */
    NIVEAU_VERBOSE = 2  /**< Trace détaillée de l'arbre de recherche. */
} NiveauVerbosite;

/**
 * @brief Instance d'un problème UKP 0/1.
 *
 * Les tableaux @c volumes et @c utilites sont indexés de 0 à n_variables-1
 * et possédés par la structure (libérés par probleme_ukp_liberer()).
 */
typedef struct {
    int    n_variables;  /**< Nombre d'objets candidats. */
    int    capacite;     /**< Capacité du sac. */
    int   *volumes;      /**< Volume (poids) de chaque objet. */
    int   *utilites;     /**< Utilité (valeur) de chaque objet. */
    char  *nom_instance; /**< Nom logique de l'instance (issu du fichier). */
} ProblemeUKP;

/**
 * @brief Instance d'un problème TSP symétrique.
 *
 * La matrice @c distances est de taille n_sommets × n_sommets et possédée
 * par la structure (libérée par probleme_tsp_liberer()).
 */
typedef struct {
    int     n_sommets;    /**< Nombre de villes. */
    double *x;            /**< Coordonnées x des sommets (optionnel, peut être NULL). */
    double *y;            /**< Coordonnées y des sommets (optionnel, peut être NULL). */
    long  **distances;    /**< Matrice de distances entières arrondies. */
    char   *nom_instance; /**< Nom logique de l'instance. */
} ProblemeTSP;

/**
 * @brief Solution d'une instance UKP.
 */
typedef struct {
    int    *valeurs;        /**< Vecteur 0/1 indiquant les objets sélectionnés. */
    long    utilite_totale; /**< Somme des utilités des objets retenus. */
    long    volume_total;   /**< Somme des volumes des objets retenus. */
    int     valide;         /**< Non nul si la solution est admissible. */
} SolutionUKP;

/**
 * @brief Solution d'une instance TSP (tour hamiltonien).
 */
typedef struct {
    int    *tour;     /**< Ordre de visite des sommets (taille n_sommets, sans répétition du retour). */
    long    longueur; /**< Longueur totale du tour. */
    int     valide;   /**< Non nul si le tour est admissible. */
} SolutionTSP;

/**
 * @brief Compteurs et mesures recueillis pendant un Branch & Bound.
 */
typedef struct {
    long    n_noeuds_generes;     /**< Nœuds créés (avant filtrage par borne). */
    long    n_noeuds_explores;    /**< Nœuds effectivement développés. */
    long    n_branches_coupees;   /**< Coupures par borne ou infaisabilité. */
    double  temps_secondes;       /**< Temps CPU total de l'exploration. */
    long    borne_initiale;       /**< Borne fournie par l'heuristique de départ. */
    int     post_traitement_2opt; /**< Non nul si un 2-opt a été appliqué après le BB. */
    long    longueur_avant_2opt;  /**< Longueur du tour avant post-traitement 2-opt. */
    double  lp_racine;            /**< Valeur de la relaxation continue au nœud racine. */
} StatistiquesBB;

/**
 * @brief Paramètres d'exécution issus de la ligne de commande.
 */
typedef struct {
    TypeProbleme    probleme;             /**< Famille de problème à résoudre. */
    char            fichier_entree[1024]; /**< Chemin vers l'instance. */
    char            dossier_export[1024]; /**< Dossier de sortie des CSV (vide = pas d'export). */
    NiveauVerbosite verbosite;            /**< Niveau de trace. */
    int             active_2opt;          /**< Non nul pour activer le 2-opt post-BB (TSP). */
    double          timeout_secondes;     /**< Limite de temps en secondes (0 = illimité). */
} Configuration;

/**
 * @brief malloc qui termine le programme en cas d'échec d'allocation.
 *
 * @param[in] taille Nombre d'octets à allouer.
 * @return Pointeur vers un bloc non initialisé.
 */
void          *se_xmalloc(size_t taille);

/**
 * @brief calloc qui termine le programme en cas d'échec d'allocation.
 *
 * @param[in] nb     Nombre d'éléments.
 * @param[in] taille Taille d'un élément en octets.
 * @return Pointeur vers un bloc mis à zéro.
 */
void          *se_xcalloc(size_t nb, size_t taille);

/**
 * @brief realloc qui termine le programme en cas d'échec d'allocation.
 *
 * @param[in,out] ptr    Bloc à redimensionner (peut être NULL).
 * @param[in]     taille Nouvelle taille en octets.
 * @return Pointeur vers le bloc redimensionné.
 */
void          *se_xrealloc(void *ptr, size_t taille);

/**
 * @brief Alloue une instance UKP et ses tableaux internes.
 *
 * @param[in] n        Nombre d'objets.
 * @param[in] capacite Capacité du sac.
 * @return Instance à libérer par probleme_ukp_liberer().
 */
ProblemeUKP   *probleme_ukp_creer(int n, int capacite);

/**
 * @brief Libère une instance UKP et ses tableaux.
 *
 * @param[in] p Instance à libérer (NULL toléré).
 */
void           probleme_ukp_liberer(ProblemeUKP *p);

/**
 * @brief Alloue une instance TSP avec sa matrice de distances n×n.
 *
 * @param[in] n Nombre de sommets.
 * @return Instance à libérer par probleme_tsp_liberer().
 */
ProblemeTSP   *probleme_tsp_creer(int n);

/**
 * @brief Libère une instance TSP, ses tableaux de coordonnées et sa matrice.
 *
 * @param[in] p Instance à libérer (NULL toléré).
 */
void           probleme_tsp_liberer(ProblemeTSP *p);

/**
 * @brief Alloue une solution UKP de taille n (vecteur 0/1 mis à zéro).
 *
 * @param[in] n Nombre de variables de décision.
 * @return Solution à libérer par solution_ukp_liberer().
 */
SolutionUKP   *solution_ukp_creer(int n);

/**
 * @brief Libère une solution UKP.
 *
 * @param[in] s Solution à libérer (NULL toléré).
 */
void           solution_ukp_liberer(SolutionUKP *s);

/**
 * @brief Alloue une solution TSP de taille n (tour non initialisé).
 *
 * @param[in] n Nombre de sommets.
 * @return Solution à libérer par solution_tsp_liberer().
 */
SolutionTSP   *solution_tsp_creer(int n);

/**
 * @brief Libère une solution TSP.
 *
 * @param[in] s Solution à libérer (NULL toléré).
 */
void           solution_tsp_liberer(SolutionTSP *s);

#endif
