#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *se_xmalloc(size_t taille) {
    void *p = malloc(taille);
    if (!p) {
        fprintf(stderr, "Erreur d'allocation memoire (%zu octets)\n", taille);
        exit(EXIT_FAILURE);
    }
    return p;
}

void *se_xcalloc(size_t nb, size_t taille) {
    void *p = calloc(nb, taille);
    if (!p) {
        fprintf(stderr, "Erreur d'allocation memoire (%zu * %zu octets)\n", nb, taille);
        exit(EXIT_FAILURE);
    }
    return p;
}

void *se_xrealloc(void *ptr, size_t taille) {
    void *p = realloc(ptr, taille);
    if (!p) {
        fprintf(stderr, "Erreur de re-allocation memoire (%zu octets)\n", taille);
        exit(EXIT_FAILURE);
    }
    return p;
}

ProblemeUKP *probleme_ukp_creer(int n, int capacite) {
    ProblemeUKP *p = se_xmalloc(sizeof(*p));
    p->n_variables  = n;
    p->capacite     = capacite;
    p->volumes      = se_xcalloc((size_t)n, sizeof(int));
    p->utilites     = se_xcalloc((size_t)n, sizeof(int));
    p->nom_instance = NULL;
    return p;
}

void probleme_ukp_liberer(ProblemeUKP *p) {
    if (!p) return;
    free(p->volumes);
    free(p->utilites);
    free(p->nom_instance);
    free(p);
}

ProblemeTSP *probleme_tsp_creer(int n) {
    ProblemeTSP *p = se_xmalloc(sizeof(*p));
    p->n_sommets    = n;
    p->x            = se_xcalloc((size_t)n, sizeof(double));
    p->y            = se_xcalloc((size_t)n, sizeof(double));
    p->distances    = se_xmalloc((size_t)n * sizeof(long *));
    for (int i = 0; i < n; ++i) {
        p->distances[i] = se_xcalloc((size_t)n, sizeof(long));
    }
    p->nom_instance = NULL;
    return p;
}

void probleme_tsp_liberer(ProblemeTSP *p) {
    if (!p) return;
    free(p->x);
    free(p->y);
    if (p->distances) {
        for (int i = 0; i < p->n_sommets; ++i) free(p->distances[i]);
        free(p->distances);
    }
    free(p->nom_instance);
    free(p);
}

SolutionUKP *solution_ukp_creer(int n) {
    SolutionUKP *s = se_xmalloc(sizeof(*s));
    s->valeurs        = se_xcalloc((size_t)n, sizeof(int));
    s->utilite_totale = 0;
    s->volume_total   = 0;
    s->valide         = 0;
    return s;
}

void solution_ukp_liberer(SolutionUKP *s) {
    if (!s) return;
    free(s->valeurs);
    free(s);
}

SolutionTSP *solution_tsp_creer(int n) {
    SolutionTSP *s = se_xmalloc(sizeof(*s));
    s->tour     = se_xcalloc((size_t)n, sizeof(int));
    s->longueur = 0;
    s->valide   = 0;
    return s;
}

void solution_tsp_liberer(SolutionTSP *s) {
    if (!s) return;
    free(s->tour);
    free(s);
}
