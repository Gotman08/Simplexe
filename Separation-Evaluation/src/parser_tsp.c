#include "parser_tsp.h"
#include "common.h"
#include "tsplib.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIGNE_MAX 65536

static char *trim(char *s) {
    while (*s && isspace((unsigned char)*s)) ++s;
    char *fin = s + strlen(s);
    while (fin > s && isspace((unsigned char)fin[-1])) --fin;
    *fin = '\0';
    return s;
}

static char *extraire_nom(const char *chemin) {
    const char *base = strrchr(chemin, '/');
#ifdef _WIN32
    const char *base_win = strrchr(chemin, '\\');
    if (base_win && base_win > base) base = base_win;
#endif
    base = base ? base + 1 : chemin;
    char *copie = se_xmalloc(strlen(base) + 1);
    strcpy(copie, base);
    char *point = strrchr(copie, '.');
    if (point) *point = '\0';
    return copie;
}

FormatTSP parser_tsp_detecter_format(const char *chemin) {
    FILE *f = fopen(chemin, "r");
    if (!f) return TSP_FORMAT_INCONNU;

    char ligne[LIGNE_MAX];
    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0' || *l == '#') continue;
        fclose(f);
        if (strncmp(l, "n_sommets", 9) == 0)  return TSP_FORMAT_GRAPHE;
        if (strncmp(l, "NAME",      4) == 0)  return TSP_FORMAT_TSPLIB95;
        if (strncmp(l, "TYPE",      4) == 0)  return TSP_FORMAT_TSPLIB95;
        if (strncmp(l, "DIMENSION", 9) == 0)  return TSP_FORMAT_TSPLIB95;
        return TSP_FORMAT_INCONNU;
    }
    fclose(f);
    return TSP_FORMAT_INCONNU;
}

static ProblemeTSP *parser_tsp_lire_graphe(FILE *f, const char *chemin) {
    char ligne[LIGNE_MAX];
    int  n = -1;
    int  oriente = 0;
    int  value = 1;
    int  dans_aretes = 0;
    ProblemeTSP *p = NULL;

    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0') continue;

        if (sscanf(l, "n_sommets %d", &n) == 1) {
            p = probleme_tsp_creer(n);
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) p->distances[i][j] = (i == j) ? 0 : -1;
            }
            continue;
        }
        if (sscanf(l, "oriente %d", &oriente) == 1) continue;
        if (sscanf(l, "value %d", &value) == 1) continue;
        if (strncmp(l, "DEBUT_DEF_ARETES", 16) == 0) { dans_aretes = 1; continue; }
        if (strncmp(l, "FIN_DEF_ARETES",   14) == 0) { dans_aretes = 0; continue; }

        if (dans_aretes && p) {
            int u, v;
            long w = 1;
            int champs = sscanf(l, "%d %d %ld", &u, &v, &w);
            if (champs >= 2 && u >= 0 && v >= 0 && u < n && v < n) {
                p->distances[u][v] = w;
                if (!oriente) p->distances[v][u] = w;
            }
        }
    }

    if (!p) {
        fprintf(stderr, "Format graphe invalide : %s\n", chemin);
        return NULL;
    }

    long max_w = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (p->distances[i][j] > max_w) max_w = p->distances[i][j];
        }
    }
    long inaccessible = (max_w + 1) * (long)n + 1;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i != j && p->distances[i][j] < 0) p->distances[i][j] = inaccessible;
        }
        p->x[i] = (double)i;
        p->y[i] = 0.0;
    }

    p->nom_instance = extraire_nom(chemin);
    return p;
}

static ProblemeTSP *parser_tsp_lire_tsplib(FILE *f, const char *chemin) {
    char ligne[LIGNE_MAX];
    int  n = -1;
    char type_arete[64] = "EUC_2D";
    int  dans_coords = 0;
    ProblemeTSP *p = NULL;

    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0') continue;

        if (!dans_coords) {
            if (sscanf(l, "DIMENSION : %d", &n) == 1
             || sscanf(l, "DIMENSION: %d", &n) == 1
             || sscanf(l, "DIMENSION %d", &n) == 1) {
                continue;
            }
            if (strstr(l, "EDGE_WEIGHT_TYPE")) {
                char *deuxpoints = strchr(l, ':');
                if (deuxpoints) {
                    sscanf(deuxpoints + 1, " %63s", type_arete);
                }
                continue;
            }
            if (strncmp(l, "NODE_COORD_SECTION", 18) == 0) {
                if (n <= 0) {
                    fprintf(stderr, "DIMENSION manquante avant NODE_COORD_SECTION : %s\n", chemin);
                    return NULL;
                }
                p = probleme_tsp_creer(n);
                dans_coords = 1;
                continue;
            }
            if (strncmp(l, "EOF", 3) == 0) break;
        } else {
            if (strncmp(l, "EOF", 3) == 0) break;
            int    idx;
            double x, y;
            if (sscanf(l, "%d %lf %lf", &idx, &x, &y) == 3) {
                int i = idx - 1;
                if (i >= 0 && i < n) {
                    p->x[i] = x;
                    p->y[i] = y;
                }
            }
        }
    }

    if (!p) {
        fprintf(stderr, "Format TSPLIB95 invalide : %s\n", chemin);
        return NULL;
    }
    if (strcmp(type_arete, "EUC_2D") != 0) {
        fprintf(stderr,
                "Avertissement : EDGE_WEIGHT_TYPE = %s, seul EUC_2D est strictement supporte.\n",
                type_arete);
    }

    tsplib_calculer_matrice(n, p->x, p->y, p->distances);
    p->nom_instance = extraire_nom(chemin);
    return p;
}

ProblemeTSP *parser_tsp_lire(const char *chemin) {
    FormatTSP fmt = parser_tsp_detecter_format(chemin);
    if (fmt == TSP_FORMAT_INCONNU) {
        fprintf(stderr, "Format TSP non reconnu : %s\n", chemin);
        return NULL;
    }
    FILE *f = fopen(chemin, "r");
    if (!f) {
        fprintf(stderr, "Impossible d'ouvrir : %s\n", chemin);
        return NULL;
    }
    ProblemeTSP *p = (fmt == TSP_FORMAT_GRAPHE)
                   ? parser_tsp_lire_graphe(f, chemin)
                   : parser_tsp_lire_tsplib(f, chemin);
    fclose(f);
    return p;
}
