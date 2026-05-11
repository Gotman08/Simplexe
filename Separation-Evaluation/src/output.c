#include "output.h"
#include "common.h"

#include <stdio.h>
#include <string.h>

void output_afficher_probleme_ukp(const ProblemeUKP *p, NiveauVerbosite v) {
    if (v < NIVEAU_NORMAL) return;
    printf("Probleme UKP : %s\n", p->nom_instance ? p->nom_instance : "(sans nom)");
    printf("  Nombre d'objets : %d\n", p->n_variables);
    printf("  Capacite : %d\n", p->capacite);
    if (v >= NIVEAU_VERBOSE) {
        printf("  Objets (volume, utilite) :\n");
        for (int j = 0; j < p->n_variables; ++j) {
            printf("    x%d : (%d, %d)\n", j + 1, p->volumes[j], p->utilites[j]);
        }
    }
}

void output_afficher_probleme_tsp(const ProblemeTSP *p, NiveauVerbosite v) {
    if (v < NIVEAU_NORMAL) return;
    printf("Probleme TSP : %s\n", p->nom_instance ? p->nom_instance : "(sans nom)");
    printf("  Nombre de sommets : %d\n", p->n_sommets);
    if (v >= NIVEAU_VERBOSE && p->n_sommets <= 20) {
        printf("  Matrice de distances :\n");
        for (int i = 0; i < p->n_sommets; ++i) {
            printf("    ");
            for (int j = 0; j < p->n_sommets; ++j) printf("%4ld ", p->distances[i][j]);
            printf("\n");
        }
    }
}

void output_afficher_solution_ukp(const ProblemeUKP    *p,
                                  const SolutionUKP    *s,
                                  const StatistiquesBB *stats,
                                  NiveauVerbosite       v) {
    if (v < NIVEAU_NORMAL) {
        if (s && s->valide) {
            printf("%s,%ld,%ld,%.6f,%ld,%.6f\n",
                   p->nom_instance,
                   s->utilite_totale,
                   s->volume_total,
                   stats ? stats->temps_secondes : 0.0,
                   stats ? stats->n_noeuds_generes : 0,
                   stats ? stats->lp_racine : 0.0);
        }
        return;
    }
    if (!s || !s->valide) {
        printf("Aucune solution trouvee.\n");
        return;
    }
    printf("\n=== Solution UKP ===\n");
    printf("Utilite totale : %ld\n", s->utilite_totale);
    printf("Volume utilise : %ld / %d\n", s->volume_total, p->capacite);
    if (stats && stats->lp_racine > 0.0) {
        double opt_d = (double)s->utilite_totale;
        double gap = stats->lp_racine - opt_d;
        double gap_pct = (opt_d > 0.0) ? 100.0 * gap / opt_d : 0.0;
        printf("LP racine     : %.4f (gap LP-INT = %.4f, %.4f %%)\n",
               stats->lp_racine, gap, gap_pct);
    }
    if (v >= NIVEAU_VERBOSE || p->n_variables <= 30) {
        printf("Affectation : ");
        int premier = 1;
        for (int j = 0; j < p->n_variables; ++j) {
            if (s->valeurs[j] > 0) {
                if (!premier) printf(", ");
                printf("x%d=%d", j + 1, s->valeurs[j]);
                premier = 0;
            }
        }
        printf("\n");
    }
    if (stats) {
        printf("Borne initiale : %ld\n", stats->borne_initiale);
        printf("Noeuds generes : %ld\n", stats->n_noeuds_generes);
        printf("Noeuds explores : %ld\n", stats->n_noeuds_explores);
        printf("Branches coupees : %ld\n", stats->n_branches_coupees);
        printf("Temps : %.6f s\n", stats->temps_secondes);
    }
}

void output_afficher_solution_tsp(const ProblemeTSP    *p,
                                  const SolutionTSP    *s,
                                  const StatistiquesBB *stats,
                                  NiveauVerbosite       v) {
    if (v < NIVEAU_NORMAL) {
        if (s && s->valide) {
            printf("%s,%ld,%.6f,%ld\n",
                   p->nom_instance,
                   s->longueur,
                   stats ? stats->temps_secondes : 0.0,
                   stats ? stats->n_noeuds_generes : 0);
        }
        return;
    }
    if (!s || !s->valide) {
        printf("Aucune solution trouvee.\n");
        return;
    }
    printf("\n=== Solution TSP ===\n");
    printf("Longueur du tour : %ld\n", s->longueur);
    if (v >= NIVEAU_VERBOSE || p->n_sommets <= 30) {
        printf("Tour : ");
        for (int k = 0; k < p->n_sommets; ++k) printf("%d ", s->tour[k]);
        printf("%d\n", s->tour[0]);
    }
    if (stats) {
        printf("Borne initiale : %ld\n", stats->borne_initiale);
        printf("Noeuds generes : %ld\n", stats->n_noeuds_generes);
        printf("Noeuds explores : %ld\n", stats->n_noeuds_explores);
        printf("Branches coupees : %ld\n", stats->n_branches_coupees);
        if (stats->post_traitement_2opt) {
            printf("2-opt applique : longueur passee de %ld a %ld\n",
                   stats->longueur_avant_2opt, s->longueur);
        }
        printf("Temps : %.6f s\n", stats->temps_secondes);
    }
}

int output_exporter_ukp_csv(const char           *chemin,
                            const ProblemeUKP    *p,
                            const SolutionUKP    *s,
                            const StatistiquesBB *stats) {
    FILE *f = fopen(chemin, "w");
    if (!f) return 0;
    fprintf(f, "instance,n,capacite,utilite,volume,temps_s,noeuds_generes,noeuds_explores,branches_coupees,borne_initiale,lp_racine\n");
    fprintf(f, "%s,%d,%d,%ld,%ld,%.6f,%ld,%ld,%ld,%ld,%.6f\n",
            p->nom_instance ? p->nom_instance : "?",
            p->n_variables, p->capacite,
            s ? s->utilite_totale : 0,
            s ? s->volume_total : 0,
            stats ? stats->temps_secondes : 0.0,
            stats ? stats->n_noeuds_generes : 0,
            stats ? stats->n_noeuds_explores : 0,
            stats ? stats->n_branches_coupees : 0,
            stats ? stats->borne_initiale : 0,
            stats ? stats->lp_racine : 0.0);
    fclose(f);
    return 1;
}

int output_exporter_tsp_csv(const char           *chemin,
                            const ProblemeTSP    *p,
                            const SolutionTSP    *s,
                            const StatistiquesBB *stats) {
    FILE *f = fopen(chemin, "w");
    if (!f) return 0;
    fprintf(f, "instance,n,longueur,temps_s,noeuds_generes,noeuds_explores,branches_coupees,borne_initiale,post_2opt,longueur_avant_2opt\n");
    fprintf(f, "%s,%d,%ld,%.6f,%ld,%ld,%ld,%ld,%d,%ld\n",
            p->nom_instance ? p->nom_instance : "?",
            p->n_sommets,
            s ? s->longueur : 0,
            stats ? stats->temps_secondes : 0.0,
            stats ? stats->n_noeuds_generes : 0,
            stats ? stats->n_noeuds_explores : 0,
            stats ? stats->n_branches_coupees : 0,
            stats ? stats->borne_initiale : 0,
            stats ? stats->post_traitement_2opt : 0,
            stats ? stats->longueur_avant_2opt : 0);
    fclose(f);
    return 1;
}
