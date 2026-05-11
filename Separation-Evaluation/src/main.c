#define _POSIX_C_SOURCE 200809L

#include "common.h"
#include "parser_ukp.h"
#include "parser_tsp.h"
#include "ukp_bb.h"
#include "tsp_bb.h"
#include "output.h"

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void afficher_aide(const char *prog) {
    printf("Solveur de Separation-Evaluation (CHPS_0805) - v%s\n\n", SE_VERSION);
    printf("Usage : %s --probleme {ukp|tsp} --fichier <chemin> [options]\n\n", prog);
    printf("Options :\n");
    printf("  -p, --probleme {ukp|tsp}    Type de probleme a resoudre\n");
    printf("  -f, --fichier <chemin>      Fichier d'instance (format auto-detecte)\n");
    printf("  -e, --export <repertoire>   Repertoire ou exporter le resultat CSV\n");
    printf("  -v, --verbose               Affichage detaille\n");
    printf("  -s, --silent                Sortie machine (ligne CSV unique)\n");
    printf("      --no-2opt               Desactive le post-traitement 2-opt (TSP)\n");
    printf("  -h, --help                  Affiche cette aide\n");
    printf("\n");
    printf("Exemples :\n");
    printf("  %s --probleme ukp --fichier prob_sac_1.txt\n", prog);
    printf("  %s --probleme tsp --fichier graphe_12.txt --verbose\n", prog);
    printf("  %s -p tsp -f pd_5.tsp -e ../Resultats/solutions\n", prog);
}

static int chemin_concatener(char *dst, size_t taille, const char *a, const char *b) {
    int n = snprintf(dst, taille, "%s/%s", a, b);
    return (n > 0 && (size_t)n < taille) ? 1 : 0;
}

int main(int argc, char **argv) {
    Configuration cfg = {0};
    cfg.verbosite      = NIVEAU_NORMAL;
    cfg.active_2opt    = 1;
    cfg.timeout_secondes = 0.0;
    cfg.probleme       = PROBLEME_UKP;

    static struct option longopts[] = {
        {"probleme", required_argument, NULL, 'p'},
        {"fichier",  required_argument, NULL, 'f'},
        {"export",   required_argument, NULL, 'e'},
        {"verbose",  no_argument,       NULL, 'v'},
        {"silent",   no_argument,       NULL, 's'},
        {"no-2opt",  no_argument,       NULL,  1 },
        {"help",     no_argument,       NULL, 'h'},
        {0, 0, 0, 0}
    };

    int opt;
    int probleme_specifie = 0;
    int fichier_specifie  = 0;
    while ((opt = getopt_long(argc, argv, "p:f:e:vsh", longopts, NULL)) != -1) {
        switch (opt) {
        case 'p':
            if (strcmp(optarg, "ukp") == 0)      { cfg.probleme = PROBLEME_UKP; probleme_specifie = 1; }
            else if (strcmp(optarg, "tsp") == 0) { cfg.probleme = PROBLEME_TSP; probleme_specifie = 1; }
            else { fprintf(stderr, "Probleme inconnu : %s\n", optarg); return EXIT_FAILURE; }
            break;
        case 'f':
            strncpy(cfg.fichier_entree, optarg, sizeof(cfg.fichier_entree) - 1);
            fichier_specifie = 1;
            break;
        case 'e':
            strncpy(cfg.dossier_export, optarg, sizeof(cfg.dossier_export) - 1);
            break;
        case 'v': cfg.verbosite = NIVEAU_VERBOSE; break;
        case 's': cfg.verbosite = NIVEAU_SILENT;  break;
        case 1:   cfg.active_2opt = 0;            break;
        case 'h': afficher_aide(argv[0]);         return EXIT_SUCCESS;
        default:  afficher_aide(argv[0]);         return EXIT_FAILURE;
        }
    }

    if (!probleme_specifie || !fichier_specifie) {
        afficher_aide(argv[0]);
        return EXIT_FAILURE;
    }

    StatistiquesBB stats = {0};
    int code_retour = EXIT_SUCCESS;

    if (cfg.probleme == PROBLEME_UKP) {
        ProblemeUKP *p = parser_ukp_lire(cfg.fichier_entree);
        if (!p) return EXIT_FAILURE;
        output_afficher_probleme_ukp(p, cfg.verbosite);
        SolutionUKP *s = ukp_branch_and_bound(p, &stats, cfg.verbosite);
        output_afficher_solution_ukp(p, s, &stats, cfg.verbosite);
        if (cfg.dossier_export[0]) {
            char chemin[2048];
            char fichier[256];
            snprintf(fichier, sizeof(fichier), "%s_bb.csv",
                     p->nom_instance ? p->nom_instance : "ukp");
            if (chemin_concatener(chemin, sizeof(chemin), cfg.dossier_export, fichier)) {
                output_exporter_ukp_csv(chemin, p, s, &stats);
            }
        }
        if (!s || !s->valide) code_retour = EXIT_FAILURE;
        solution_ukp_liberer(s);
        probleme_ukp_liberer(p);
    } else {
        ProblemeTSP *p = parser_tsp_lire(cfg.fichier_entree);
        if (!p) return EXIT_FAILURE;
        output_afficher_probleme_tsp(p, cfg.verbosite);
        SolutionTSP *s = tsp_branch_and_bound(p, &stats, cfg.verbosite, cfg.active_2opt);
        output_afficher_solution_tsp(p, s, &stats, cfg.verbosite);
        if (cfg.dossier_export[0]) {
            char chemin[2048];
            char fichier[256];
            snprintf(fichier, sizeof(fichier), "%s_bb.csv",
                     p->nom_instance ? p->nom_instance : "tsp");
            if (chemin_concatener(chemin, sizeof(chemin), cfg.dossier_export, fichier)) {
                output_exporter_tsp_csv(chemin, p, s, &stats);
            }
        }
        if (!s || !s->valide) code_retour = EXIT_FAILURE;
        solution_tsp_liberer(s);
        probleme_tsp_liberer(p);
    }

    return code_retour;
}
