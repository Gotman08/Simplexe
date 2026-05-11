#include "ukp_bb.h"
#include "common.h"
#include "timer.h"

#include <glpk.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define EPSILON 1e-6

/**
 * @brief Nœud de l'arbre de branchement UKP.
 *
 * Représente l'état d'une variable libre via ses bornes inférieures et supérieures
 * courantes (vmin[j] == vmax[j] signifie variable fixée).
 */
typedef struct {
    int *valeurs_min; /**< Bornes inférieures par variable (taille n). */
    int *valeurs_max; /**< Bornes supérieures par variable (taille n). */
} Noeud;

/**
 * @brief Pile de nœuds à explorer (parcours en profondeur).
 */
typedef struct {
    Noeud *noeuds;   /**< Tableau dynamique de nœuds. */
    int    taille;   /**< Nombre de nœuds présents. */
    int    capacite; /**< Capacité allouée. */
} PileNoeuds;

/**
 * @brief Initialise une pile vide avec une capacité par défaut.
 *
 * @param[out] p Pile à initialiser.
 */
static void pile_init(PileNoeuds *p) {
    p->taille = 0;
    p->capacite = 64;
    p->noeuds = se_xmalloc(sizeof(Noeud) * (size_t)p->capacite);
}

/**
 * @brief Empile un nœud en copiant les vecteurs de bornes (croissance géométrique).
 *
 * @param[in,out] p    Pile cible.
 * @param[in]     n    Nombre de variables (taille des vecteurs).
 * @param[in]     vmin Bornes inférieures à copier.
 * @param[in]     vmax Bornes supérieures à copier.
 */
static void pile_pousser(PileNoeuds *p, int n, const int *vmin, const int *vmax) {
    if (p->taille == p->capacite) {
        p->capacite *= 2;
        p->noeuds = se_xrealloc(p->noeuds, sizeof(Noeud) * (size_t)p->capacite);
    }
    Noeud *nd = &p->noeuds[p->taille++];
    nd->valeurs_min = se_xmalloc(sizeof(int) * (size_t)n);
    nd->valeurs_max = se_xmalloc(sizeof(int) * (size_t)n);
    memcpy(nd->valeurs_min, vmin, sizeof(int) * (size_t)n);
    memcpy(nd->valeurs_max, vmax, sizeof(int) * (size_t)n);
}

/**
 * @brief Dépile un nœud (transfert la propriété des vecteurs internes à @p dst).
 *
 * @param[in,out] p   Pile source.
 * @param[out]    dst Destination du nœud dépilé.
 * @return 1 si un nœud a été dépilé, 0 si la pile était vide.
 */
static int pile_depiler(PileNoeuds *p, Noeud *dst) {
    if (p->taille == 0) return 0;
    *dst = p->noeuds[--p->taille];
    return 1;
}

/**
 * @brief Libère la pile et tous les nœuds restants.
 *
 * @param[in,out] p Pile à libérer.
 */
static void pile_liberer(PileNoeuds *p) {
    while (p->taille > 0) {
        Noeud n = p->noeuds[--p->taille];
        free(n.valeurs_min);
        free(n.valeurs_max);
    }
    free(p->noeuds);
}

SolutionUKP *ukp_heuristique_qualite_prix(const ProblemeUKP *p) {
    int n = p->n_variables;
    int *ordre = se_xmalloc(sizeof(int) * (size_t)n);
    for (int i = 0; i < n; ++i) ordre[i] = i;

    for (int i = 0; i + 1 < n; ++i) {
        for (int j = 0; j + 1 + i < n; ++j) {
            double r1 = (p->volumes[ordre[j]]   > 0)
                      ? (double)p->utilites[ordre[j]]   / p->volumes[ordre[j]]   : 0.0;
            double r2 = (p->volumes[ordre[j+1]] > 0)
                      ? (double)p->utilites[ordre[j+1]] / p->volumes[ordre[j+1]] : 0.0;
            if (r1 < r2) {
                int tmp = ordre[j]; ordre[j] = ordre[j+1]; ordre[j+1] = tmp;
            }
        }
    }

    SolutionUKP *s = solution_ukp_creer(n);
    long volume_restant = p->capacite;
    for (int k = 0; k < n; ++k) {
        int i = ordre[k];
        if (p->volumes[i] <= 0) continue;
        int qte = (int)(volume_restant / p->volumes[i]);
        s->valeurs[i] = qte;
        s->utilite_totale += (long)qte * p->utilites[i];
        s->volume_total   += (long)qte * p->volumes[i];
        volume_restant    -= (long)qte * p->volumes[i];
    }
    s->valide = 1;
    free(ordre);
    return s;
}

/**
 * @brief Résout la relaxation continue de l'UKP sous bornes [vmin, vmax] via GLPK.
 *
 * @param[in]  p                Instance UKP.
 * @param[in]  vmin             Bornes inférieures courantes (taille n).
 * @param[in]  vmax             Bornes supérieures courantes (taille n).
 * @param[out] valeurs_obtenues Valeurs fractionnaires des variables à l'optimum LP (taille n).
 * @param[out] utilite_relaxee  Valeur de la fonction objectif à l'optimum LP.
 * @return 1 si le LP est faisable et résolu à l'optimum, 0 sinon.
 */
static int evaluer_lp(const ProblemeUKP *p,
                      const int          *vmin,
                      const int          *vmax,
                      double             *valeurs_obtenues,
                      double             *utilite_relaxee) {
    int n = p->n_variables;
    glp_prob *lp = glp_create_prob();
    glp_set_obj_dir(lp, GLP_MAX);
    glp_add_rows(lp, 1);
    glp_set_row_bnds(lp, 1, GLP_UP, 0.0, (double)p->capacite);
    glp_add_cols(lp, n);

    int    *ind = se_xmalloc(sizeof(int)    * (size_t)(n + 1));
    double *val = se_xmalloc(sizeof(double) * (size_t)(n + 1));
    for (int j = 0; j < n; ++j) {
        glp_set_obj_coef(lp, j + 1, (double)p->utilites[j]);
        if (vmin[j] == vmax[j]) {
            glp_set_col_bnds(lp, j + 1, GLP_FX, (double)vmin[j], (double)vmax[j]);
        } else {
            glp_set_col_bnds(lp, j + 1, GLP_DB, (double)vmin[j], (double)vmax[j]);
        }
        ind[j + 1] = j + 1;
        val[j + 1] = (double)p->volumes[j];
    }
    glp_set_mat_row(lp, 1, n, ind, val);

    glp_smcp param;
    glp_init_smcp(&param);
    param.msg_lev = GLP_MSG_OFF;

    int rc = glp_simplex(lp, &param);
    int faisabilite = (rc == 0 && glp_get_status(lp) == GLP_OPT);
    if (faisabilite) {
        *utilite_relaxee = glp_get_obj_val(lp);
        for (int j = 0; j < n; ++j) {
            valeurs_obtenues[j] = glp_get_col_prim(lp, j + 1);
        }
    }

    glp_delete_prob(lp);
    free(ind);
    free(val);
    return faisabilite;
}

/**
 * @brief Renvoie l'indice de la première variable de valeur fractionnaire.
 *
 * @param[in] n       Nombre de variables.
 * @param[in] valeurs Valeurs courantes (issues du LP relaxé).
 * @return Indice de la première composante non entière, ou -1 si toutes sont entières.
 */
static int trouver_variable_fractionnaire(int n, const double *valeurs) {
    for (int j = 0; j < n; ++j) {
        double partie_entiere;
        double frac = modf(valeurs[j], &partie_entiere);
        if (frac > EPSILON && frac < 1.0 - EPSILON) return j;
    }
    return -1;
}

SolutionUKP *ukp_branch_and_bound(const ProblemeUKP *p,
                                  StatistiquesBB    *stats,
                                  NiveauVerbosite    verbosite) {
    Chronometre chrono;
    timer_demarrer(&chrono);

    int n = p->n_variables;
    SolutionUKP *meilleure = ukp_heuristique_qualite_prix(p);
    long borne = meilleure->utilite_totale;
    if (stats) stats->borne_initiale = borne;

    if (verbosite >= NIVEAU_NORMAL) {
        printf("Heuristique qualite-prix : utilite = %ld\n", borne);
    }

    int *vmin_init = se_xcalloc((size_t)n, sizeof(int));
    int *vmax_init = se_xcalloc((size_t)n, sizeof(int));
    for (int j = 0; j < n; ++j) {
        vmin_init[j] = 0;
        vmax_init[j] = (p->volumes[j] > 0) ? p->capacite / p->volumes[j] : 0;
    }

    PileNoeuds pile;
    pile_init(&pile);
    pile_pousser(&pile, n, vmin_init, vmax_init);

    long n_generes  = 1;
    long n_explores = 0;
    long n_coupes   = 0;
    int  premier_lp = 1;

    double *valeurs = se_xmalloc(sizeof(double) * (size_t)n);

    glp_term_out(GLP_OFF);

    while (pile.taille > 0) {
        Noeud noeud;
        pile_depiler(&pile, &noeud);
        ++n_explores;

        double utilite_lp = 0.0;
        int faisable = evaluer_lp(p, noeud.valeurs_min, noeud.valeurs_max, valeurs, &utilite_lp);

        if (premier_lp && faisable) {
            if (stats) stats->lp_racine = utilite_lp;
            premier_lp = 0;
        }

        if (verbosite >= NIVEAU_VERBOSE) {
            printf("S%ld : eval LP = %.4f (borne = %ld)\n", n_explores, utilite_lp, borne);
        }

        if (!faisable || (long)floor(utilite_lp + EPSILON) <= borne) {
            ++n_coupes;
            free(noeud.valeurs_min);
            free(noeud.valeurs_max);
            continue;
        }

        int frac = trouver_variable_fractionnaire(n, valeurs);
        if (frac < 0) {
            long utilite_int = 0;
            long volume_int  = 0;
            for (int j = 0; j < n; ++j) {
                int v = (int)(valeurs[j] + 0.5);
                utilite_int += (long)v * p->utilites[j];
                volume_int  += (long)v * p->volumes[j];
            }
            if (volume_int <= p->capacite && utilite_int > borne) {
                borne = utilite_int;
                meilleure->utilite_totale = utilite_int;
                meilleure->volume_total   = volume_int;
                for (int j = 0; j < n; ++j) {
                    meilleure->valeurs[j] = (int)(valeurs[j] + 0.5);
                }
                meilleure->valide = 1;
                if (verbosite >= NIVEAU_NORMAL) {
                    printf("Mise a jour de la borne : %ld\n", borne);
                }
            }
            free(noeud.valeurs_min);
            free(noeud.valeurs_max);
            continue;
        }

        int max_val = noeud.valeurs_max[frac];
        for (int v = max_val; v >= noeud.valeurs_min[frac]; --v) {
            int *nmin = se_xmalloc(sizeof(int) * (size_t)n);
            int *nmax = se_xmalloc(sizeof(int) * (size_t)n);
            memcpy(nmin, noeud.valeurs_min, sizeof(int) * (size_t)n);
            memcpy(nmax, noeud.valeurs_max, sizeof(int) * (size_t)n);
            nmin[frac] = v;
            nmax[frac] = v;
            pile_pousser(&pile, n, nmin, nmax);
            ++n_generes;
            free(nmin);
            free(nmax);
        }

        free(noeud.valeurs_min);
        free(noeud.valeurs_max);
    }

    free(valeurs);
    free(vmin_init);
    free(vmax_init);
    pile_liberer(&pile);

    if (stats) {
        stats->n_noeuds_generes  = n_generes;
        stats->n_noeuds_explores = n_explores;
        stats->n_branches_coupees = n_coupes;
        stats->temps_secondes    = timer_temps_ecoule(&chrono);
    }

    return meilleure;
}
