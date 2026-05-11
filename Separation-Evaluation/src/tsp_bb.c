#include "tsp_bb.h"
#include "common.h"
#include "timer.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INFINI_LONG LONG_MAX

/**
 * @brief Nœud de l'arbre de branchement TSP.
 *
 * Le branchement procède par interdiction d'arêtes : @c interdites est une
 * matrice n×n stockée linéairement (interdites[i*n+j] == 1 ⇔ arête (i,j) bannie).
 */
typedef struct {
    char  *interdites; /**< Matrice symétrique n×n d'arêtes interdites (linéarisée). */
    long   evaluation; /**< Borne inférieure 1-arbre associée à ce nœud. */
    int    profondeur; /**< Profondeur dans l'arbre de recherche. */
} EtatNoeud;

/**
 * @brief Tas-min indexé par EtatNoeud::evaluation (parcours best-first).
 */
typedef struct {
    EtatNoeud **donnees;  /**< Tableau dynamique de pointeurs vers les nœuds. */
    int         taille;   /**< Nombre de nœuds présents. */
    int         capacite; /**< Capacité allouée. */
} TasMin;

/**
 * @brief Initialise un tas-min vide avec une capacité par défaut.
 *
 * @param[out] t Tas à initialiser.
 */
static void tas_init(TasMin *t) {
    t->taille = 0;
    t->capacite = 64;
    t->donnees = se_xmalloc(sizeof(EtatNoeud *) * (size_t)t->capacite);
}

static void tas_echanger(TasMin *t, int i, int j) {
    EtatNoeud *tmp = t->donnees[i];
    t->donnees[i]  = t->donnees[j];
    t->donnees[j]  = tmp;
}

/**
 * @brief Remonte l'élément à l'indice @p i vers la racine pour rétablir l'invariant tas-min.
 *
 * @param[in,out] t Tas.
 * @param[in]     i Indice de départ.
 */
static void tas_remonter(TasMin *t, int i) {
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (t->donnees[i]->evaluation < t->donnees[parent]->evaluation) {
            tas_echanger(t, i, parent);
            i = parent;
        } else break;
    }
}

/**
 * @brief Descend l'élément à l'indice @p i vers les feuilles pour rétablir l'invariant tas-min.
 *
 * @param[in,out] t Tas.
 * @param[in]     i Indice de départ.
 */
static void tas_descendre(TasMin *t, int i) {
    for (;;) {
        int g = 2 * i + 1, d = 2 * i + 2, min = i;
        if (g < t->taille && t->donnees[g]->evaluation < t->donnees[min]->evaluation) min = g;
        if (d < t->taille && t->donnees[d]->evaluation < t->donnees[min]->evaluation) min = d;
        if (min == i) break;
        tas_echanger(t, i, min);
        i = min;
    }
}

/**
 * @brief Insère un nœud dans le tas (la propriété est transférée au tas).
 *
 * @param[in,out] t Tas cible.
 * @param[in]     e Nœud à insérer (libéré ultérieurement par tas_extraire ou tas_liberer).
 */
static void tas_inserer(TasMin *t, EtatNoeud *e) {
    if (t->taille == t->capacite) {
        t->capacite *= 2;
        t->donnees = se_xrealloc(t->donnees, sizeof(EtatNoeud *) * (size_t)t->capacite);
    }
    t->donnees[t->taille++] = e;
    tas_remonter(t, t->taille - 1);
}

/**
 * @brief Extrait le nœud de plus petite évaluation.
 *
 * @param[in,out] t Tas source.
 * @return Nœud extrait (propriété transférée à l'appelant), ou NULL si le tas est vide.
 */
static EtatNoeud *tas_extraire(TasMin *t) {
    if (t->taille == 0) return NULL;
    EtatNoeud *e = t->donnees[0];
    t->donnees[0] = t->donnees[--t->taille];
    if (t->taille > 0) tas_descendre(t, 0);
    return e;
}

/**
 * @brief Libère le tas et tous les nœuds restants.
 *
 * @param[in,out] t Tas à libérer.
 */
static void tas_liberer(TasMin *t) {
    while (t->taille > 0) {
        EtatNoeud *e = t->donnees[--t->taille];
        free(e->interdites);
        free(e);
    }
    free(t->donnees);
}

static long arete_poids(const ProblemeTSP *p, int i, int j, const char *interdites) {
    if (interdites && interdites[i * p->n_sommets + j]) return INFINI_LONG;
    return p->distances[i][j];
}

SolutionTSP *tsp_heuristique_plus_proche_voisin(const ProblemeTSP *p, int sommet_depart) {
    int  n = p->n_sommets;
    SolutionTSP *s = solution_tsp_creer(n);
    char *visite = se_xcalloc((size_t)n, sizeof(char));

    s->tour[0]       = sommet_depart;
    visite[sommet_depart] = 1;

    for (int k = 1; k < n; ++k) {
        int  courant = s->tour[k - 1];
        int  meilleur = -1;
        long meilleur_poids = INFINI_LONG;
        for (int j = 0; j < n; ++j) {
            if (!visite[j] && p->distances[courant][j] < meilleur_poids) {
                meilleur_poids = p->distances[courant][j];
                meilleur = j;
            }
        }
        if (meilleur < 0) { s->valide = 0; free(visite); return s; }
        s->tour[k] = meilleur;
        visite[meilleur] = 1;
        s->longueur += meilleur_poids;
    }
    s->longueur += p->distances[s->tour[n - 1]][s->tour[0]];
    s->valide = 1;
    free(visite);
    return s;
}

/**
 * @brief Calcule la borne 1-arbre : ACPM sur {1,...,n-1} + deux plus courtes arêtes incidentes au sommet 0.
 *
 * @param[in] p          Instance TSP.
 * @param[in] interdites Matrice n×n linéarisée d'arêtes bannies (peut être NULL).
 * @return Borne inférieure du TSP sous les contraintes d'interdiction, ou INFINI_LONG si infaisable.
 */
static long evaluer_acpm_avec_sommet_zero(const ProblemeTSP *p, const char *interdites) {
    int n = p->n_sommets;
    if (n < 2) return 0;

    long *cle = se_xmalloc(sizeof(long) * (size_t)n);
    char *dans_arbre = se_xcalloc((size_t)n, sizeof(char));
    for (int i = 0; i < n; ++i) cle[i] = INFINI_LONG;
    cle[1] = 0;
    long total = 0;
    int  aretes_ajoutees = 0;

    for (int it = 0; it + 1 < n; ++it) {
        int  meilleur = -1;
        long min_cle = INFINI_LONG;
        for (int j = 1; j < n; ++j) {
            if (!dans_arbre[j] && cle[j] < min_cle) {
                min_cle = cle[j];
                meilleur = j;
            }
        }
        if (meilleur < 0) { free(cle); free(dans_arbre); return INFINI_LONG; }
        dans_arbre[meilleur] = 1;
        if (it > 0) {
            total += min_cle;
            ++aretes_ajoutees;
        }
        for (int v = 1; v < n; ++v) {
            if (!dans_arbre[v]) {
                long w = arete_poids(p, meilleur, v, interdites);
                if (w < cle[v]) cle[v] = w;
            }
        }
    }

    free(cle);
    free(dans_arbre);

    if (aretes_ajoutees < n - 2) return INFINI_LONG;

    long min1 = INFINI_LONG, min2 = INFINI_LONG;
    for (int j = 1; j < n; ++j) {
        long w = arete_poids(p, 0, j, interdites);
        if (w < min1) { min2 = min1; min1 = w; }
        else if (w < min2) { min2 = w; }
    }
    if (min1 >= INFINI_LONG || min2 >= INFINI_LONG) return INFINI_LONG;
    return total + min1 + min2;
}

/**
 * @brief Extrait les arêtes du 1-arbre (n-2 arêtes ACPM + 2 arêtes incidentes au sommet 0).
 *
 * @param[in]  p          Instance TSP.
 * @param[in]  interdites Matrice d'arêtes bannies (peut être NULL).
 * @param[out] aretes_u   Extrémités gauches (taille ≥ n+2).
 * @param[out] aretes_v   Extrémités droites (taille ≥ n+2).
 * @param[out] n_aretes   Nombre d'arêtes effectivement écrites.
 * @return 1 si le 1-arbre est constructible, 0 si infaisable.
 */
static int extraire_aretes_acpm(const ProblemeTSP *p, const char *interdites,
                                int *aretes_u, int *aretes_v, int *n_aretes) {
    int n = p->n_sommets;
    long *cle = se_xmalloc(sizeof(long) * (size_t)n);
    int  *parent = se_xmalloc(sizeof(int) * (size_t)n);
    char *dans_arbre = se_xcalloc((size_t)n, sizeof(char));
    for (int i = 0; i < n; ++i) { cle[i] = INFINI_LONG; parent[i] = -1; }
    cle[1] = 0;
    *n_aretes = 0;

    for (int it = 0; it + 1 < n; ++it) {
        int  meilleur = -1;
        long min_cle = INFINI_LONG;
        for (int j = 1; j < n; ++j) {
            if (!dans_arbre[j] && cle[j] < min_cle) { min_cle = cle[j]; meilleur = j; }
        }
        if (meilleur < 0) { free(cle); free(parent); free(dans_arbre); return 0; }
        dans_arbre[meilleur] = 1;
        if (parent[meilleur] != -1) {
            aretes_u[*n_aretes] = parent[meilleur];
            aretes_v[*n_aretes] = meilleur;
            ++(*n_aretes);
        }
        for (int v = 1; v < n; ++v) {
            if (!dans_arbre[v]) {
                long w = arete_poids(p, meilleur, v, interdites);
                if (w < cle[v]) { cle[v] = w; parent[v] = meilleur; }
            }
        }
    }

    int u_min1 = -1, u_min2 = -1;
    long min1 = INFINI_LONG, min2 = INFINI_LONG;
    for (int j = 1; j < n; ++j) {
        long w = arete_poids(p, 0, j, interdites);
        if (w < min1) { min2 = min1; u_min2 = u_min1; min1 = w; u_min1 = j; }
        else if (w < min2) { min2 = w; u_min2 = j; }
    }
    if (u_min1 >= 0) { aretes_u[*n_aretes] = 0; aretes_v[*n_aretes] = u_min1; ++(*n_aretes); }
    if (u_min2 >= 0) { aretes_u[*n_aretes] = 0; aretes_v[*n_aretes] = u_min2; ++(*n_aretes); }

    free(cle);
    free(parent);
    free(dans_arbre);
    return 1;
}

/**
 * @brief Teste si un multi-graphe à n arêtes forme un cycle hamiltonien (tous degrés à 2).
 *
 * @param[in]  n        Nombre de sommets.
 * @param[in]  aretes_u Extrémités gauches.
 * @param[in]  aretes_v Extrémités droites.
 * @param[in]  n_aretes Nombre d'arêtes.
 * @param[out] degres   Tableau de travail (taille n).
 * @return 1 si c'est un cycle hamiltonien, 0 sinon.
 */
static int est_cycle_hamiltonien(int n, const int *aretes_u, const int *aretes_v, int n_aretes,
                                 int *degres) {
    if (n_aretes != n) return 0;
    memset(degres, 0, sizeof(int) * (size_t)n);
    for (int k = 0; k < n_aretes; ++k) {
        ++degres[aretes_u[k]];
        ++degres[aretes_v[k]];
    }
    for (int i = 0; i < n; ++i) {
        if (degres[i] != 2) return 0;
    }
    return 1;
}

/**
 * @brief Reconstitue l'ordre de visite d'un cycle hamiltonien à partir de sa liste d'arêtes.
 *
 * @param[in]  n        Nombre de sommets.
 * @param[in]  aretes_u Extrémités gauches (n arêtes formant un cycle).
 * @param[in]  aretes_v Extrémités droites.
 * @param[out] tour     Permutation des sommets dans l'ordre du cycle (taille n).
 * @return Toujours 1 (échec impossible si le cycle est valide en entrée).
 */
static int reconstruire_tour(int n, const int *aretes_u, const int *aretes_v, int *tour) {
    int **adj = se_xmalloc(sizeof(int *) * (size_t)n);
    int  *deg = se_xcalloc((size_t)n, sizeof(int));
    for (int i = 0; i < n; ++i) adj[i] = se_xcalloc(2, sizeof(int));
    for (int k = 0; k < n; ++k) {
        int u = aretes_u[k], v = aretes_v[k];
        if (deg[u] < 2) adj[u][deg[u]++] = v;
        if (deg[v] < 2) adj[v][deg[v]++] = u;
    }
    int prec = -1, courant = 0;
    for (int k = 0; k < n; ++k) {
        tour[k] = courant;
        int suivant = (adj[courant][0] != prec) ? adj[courant][0] : adj[courant][1];
        prec = courant;
        courant = suivant;
    }
    for (int i = 0; i < n; ++i) free(adj[i]);
    free(adj);
    free(deg);
    return 1;
}

/**
 * @brief Renvoie le sommet de plus fort degré strictement supérieur à 2 dans le 1-arbre.
 *
 * Utilisé pour choisir la variable de branchement : une arête incidente à ce sommet
 * sera bannie dans chaque sous-problème.
 *
 * @param[in]  n        Nombre de sommets.
 * @param[in]  aretes_u Extrémités gauches.
 * @param[in]  aretes_v Extrémités droites.
 * @param[in]  n_aretes Nombre d'arêtes.
 * @param[out] degres   Tableau de travail (taille n).
 * @return Indice du sommet à brancher, ou -1 si aucun sommet n'a un degré > 2.
 */
static int trouver_sommet_degre_sup_2(int n, const int *aretes_u, const int *aretes_v,
                                      int n_aretes, int *degres) {
    memset(degres, 0, sizeof(int) * (size_t)n);
    for (int k = 0; k < n_aretes; ++k) { ++degres[aretes_u[k]]; ++degres[aretes_v[k]]; }
    int meilleur = -1, deg_max = 2;
    for (int i = 0; i < n; ++i) {
        if (degres[i] > deg_max) { deg_max = degres[i]; meilleur = i; }
    }
    return meilleur;
}

void tsp_appliquer_2opt(const ProblemeTSP *p, SolutionTSP *s) {
    int n = p->n_sommets;
    int ameliore = 1;
    while (ameliore) {
        ameliore = 0;
        for (int i = 0; i + 1 < n; ++i) {
            for (int k = i + 1; k < n; ++k) {
                int a = s->tour[i];
                int b = s->tour[(i + 1) % n];
                int c = s->tour[k];
                int d = s->tour[(k + 1) % n];
                if (a == c || a == d || b == c || b == d) continue;
                long avant = p->distances[a][b] + p->distances[c][d];
                long apres = p->distances[a][c] + p->distances[b][d];
                if (apres < avant) {
                    int g = i + 1, h = k;
                    while (g < h) {
                        int tmp = s->tour[g]; s->tour[g] = s->tour[h]; s->tour[h] = tmp;
                        ++g; --h;
                    }
                    s->longueur -= (avant - apres);
                    ameliore = 1;
                }
            }
        }
    }
}

SolutionTSP *tsp_branch_and_bound(const ProblemeTSP *p,
                                  StatistiquesBB    *stats,
                                  NiveauVerbosite    verbosite,
                                  int                active_2opt) {
    Chronometre chrono;
    timer_demarrer(&chrono);

    int n = p->n_sommets;
    SolutionTSP *meilleure = tsp_heuristique_plus_proche_voisin(p, 0);
    long borne = meilleure->longueur;
    if (stats) stats->borne_initiale = borne;

    if (verbosite >= NIVEAU_NORMAL) {
        printf("Heuristique plus proche voisin : longueur = %ld\n", borne);
    }

    EtatNoeud *racine = se_xmalloc(sizeof(EtatNoeud));
    racine->interdites = se_xcalloc((size_t)n * (size_t)n, sizeof(char));
    racine->evaluation = evaluer_acpm_avec_sommet_zero(p, racine->interdites);
    racine->profondeur = 0;

    TasMin tas;
    tas_init(&tas);
    tas_inserer(&tas, racine);

    long n_generes  = 1;
    long n_explores = 0;
    long n_coupes   = 0;

    int *aretes_u = se_xmalloc(sizeof(int) * (size_t)(n + 2));
    int *aretes_v = se_xmalloc(sizeof(int) * (size_t)(n + 2));
    int *degres   = se_xmalloc(sizeof(int) * (size_t)n);

    while (tas.taille > 0) {
        EtatNoeud *e = tas_extraire(&tas);
        ++n_explores;

        if (e->evaluation >= borne) {
            ++n_coupes;
            free(e->interdites);
            free(e);
            continue;
        }

        int n_aretes = 0;
        if (!extraire_aretes_acpm(p, e->interdites, aretes_u, aretes_v, &n_aretes)) {
            ++n_coupes;
            free(e->interdites);
            free(e);
            continue;
        }

        if (est_cycle_hamiltonien(n, aretes_u, aretes_v, n_aretes, degres)) {
            if (e->evaluation < borne) {
                borne = e->evaluation;
                reconstruire_tour(n, aretes_u, aretes_v, meilleure->tour);
                meilleure->longueur = borne;
                meilleure->valide = 1;
                if (verbosite >= NIVEAU_NORMAL) {
                    printf("Mise a jour de la borne : %ld\n", borne);
                }
            }
            free(e->interdites);
            free(e);
            continue;
        }

        int sommet = trouver_sommet_degre_sup_2(n, aretes_u, aretes_v, n_aretes, degres);
        if (sommet < 0) { free(e->interdites); free(e); continue; }

        for (int k = 0; k < n_aretes; ++k) {
            int u = aretes_u[k], v = aretes_v[k];
            if (u != sommet && v != sommet) continue;

            EtatNoeud *fils = se_xmalloc(sizeof(EtatNoeud));
            fils->interdites = se_xmalloc((size_t)n * (size_t)n);
            memcpy(fils->interdites, e->interdites, (size_t)n * (size_t)n);
            fils->interdites[u * n + v] = 1;
            fils->interdites[v * n + u] = 1;
            fils->profondeur = e->profondeur + 1;
            fils->evaluation = evaluer_acpm_avec_sommet_zero(p, fils->interdites);
            ++n_generes;

            if (fils->evaluation < borne) {
                tas_inserer(&tas, fils);
            } else {
                ++n_coupes;
                free(fils->interdites);
                free(fils);
            }
        }

        free(e->interdites);
        free(e);
    }

    free(aretes_u);
    free(aretes_v);
    free(degres);
    tas_liberer(&tas);

    if (stats) {
        stats->n_noeuds_generes  = n_generes;
        stats->n_noeuds_explores = n_explores;
        stats->n_branches_coupees = n_coupes;
        stats->longueur_avant_2opt = meilleure->longueur;
        stats->post_traitement_2opt = 0;
    }

    if (active_2opt && meilleure->valide && n >= 4) {
        long avant = meilleure->longueur;
        tsp_appliquer_2opt(p, meilleure);
        if (stats && meilleure->longueur < avant) stats->post_traitement_2opt = 1;
    }

    if (stats) stats->temps_secondes = timer_temps_ecoule(&chrono);

    return meilleure;
}
