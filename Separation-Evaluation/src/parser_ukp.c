#include "parser_ukp.h"
#include "common.h"

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

FormatUKP parser_ukp_detecter_format(const char *chemin) {
    FILE *f = fopen(chemin, "r");
    if (!f) return UKP_FORMAT_INCONNU;

    char ligne[LIGNE_MAX];
    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0' || *l == '#') continue;
        fclose(f);
        if (strncmp(l, "n_variables", 11) == 0) return UKP_FORMAT_LP;
        if (strncmp(l, "n:", 2) == 0)            return UKP_FORMAT_DIRECT;
        if (strncmp(l, "n ",  2) == 0)           return UKP_FORMAT_DIRECT;
        return UKP_FORMAT_INCONNU;
    }
    fclose(f);
    return UKP_FORMAT_INCONNU;
}

static int parse_coefficient(const char *ligne, int *coef, int *indice_var) {
    int signe = +1;
    const char *p = ligne;

    while (*p && isspace((unsigned char)*p)) ++p;
    if (*p == '+') { signe = +1; ++p; }
    else if (*p == '-') { signe = -1; ++p; }
    while (*p && isspace((unsigned char)*p)) ++p;

    char *fin = NULL;
    long val = strtol(p, &fin, 10);
    if (fin == p) return 0;
    *coef = signe * (int)val;

    p = fin;
    while (*p && isspace((unsigned char)*p)) ++p;
    if (*p != 'x' && *p != 'X') return 0;
    ++p;
    val = strtol(p, &fin, 10);
    if (fin == p) return 0;
    *indice_var = (int)val;
    return (int)(fin - ligne);
}

static ProblemeUKP *parser_ukp_lire_lp(FILE *f, const char *chemin) {
    char ligne[LIGNE_MAX];
    int  n = -1;
    int  n_contraintes = -1;
    int  mode_max = -1;
    int *coef_obj = NULL;
    int *coef_contr = NULL;
    int  capacite = 0;

    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0') continue;

        if (strncmp(l, "n_variables", 11) == 0) {
            sscanf(l, "n_variables %d", &n);
            coef_obj   = se_xcalloc((size_t)n, sizeof(int));
            coef_contr = se_xcalloc((size_t)n, sizeof(int));
        } else if (strncmp(l, "n_contraintes", 13) == 0) {
            sscanf(l, "n_contraintes %d", &n_contraintes);
        } else if (strcmp(l, "max") == 0) {
            mode_max = 1;
        } else if (strcmp(l, "min") == 0) {
            mode_max = 0;
        } else if (mode_max == 1 && coef_obj && (l[0] == '+' || l[0] == '-' || isdigit((unsigned char)l[0]))) {
            const char *p = l;
            int coef, indice;
            int avancement;
            while ((avancement = parse_coefficient(p, &coef, &indice)) > 0) {
                if (indice >= 1 && indice <= n) coef_obj[indice - 1] = coef;
                p += avancement;
                while (*p && isspace((unsigned char)*p)) ++p;
                if (*p == '\0') break;
            }
            mode_max = 2;
        } else if (mode_max == 2 && (l[0] == '+' || l[0] == '-' || isdigit((unsigned char)l[0]))) {
            const char *p = l;
            int coef, indice;
            int avancement;
            while ((avancement = parse_coefficient(p, &coef, &indice)) > 0) {
                if (indice >= 1 && indice <= n) coef_contr[indice - 1] = coef;
                p += avancement;
                while (*p && isspace((unsigned char)*p)) ++p;
                if (*p == '<' || *p == '=') break;
            }
            const char *eq = strstr(l, "<=");
            if (!eq) eq = strstr(l, "=");
            if (eq) {
                eq += (eq[0] == '<' && eq[1] == '=') ? 2 : 1;
                capacite = (int)strtol(eq, NULL, 10);
            }
        }
    }

    (void)n_contraintes;
    if (n <= 0 || !coef_obj || !coef_contr) {
        free(coef_obj);
        free(coef_contr);
        fprintf(stderr, "Format LP invalide : %s\n", chemin);
        return NULL;
    }

    ProblemeUKP *p = probleme_ukp_creer(n, capacite);
    for (int i = 0; i < n; ++i) {
        p->volumes[i]  = coef_contr[i];
        p->utilites[i] = coef_obj[i];
    }
    p->nom_instance = extraire_nom(chemin);
    free(coef_obj);
    free(coef_contr);
    return p;
}

static ProblemeUKP *parser_ukp_lire_direct(FILE *f, const char *chemin) {
    char ligne[LIGNE_MAX];
    int  n = -1;
    int  c = -1;

    while (fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0') continue;
        if (sscanf(l, "n: %d", &n) == 1) continue;
        if (sscanf(l, "n %d",  &n) == 1) continue;
        if (sscanf(l, "c: %d", &c) == 1) break;
        if (sscanf(l, "c %d",  &c) == 1) break;
    }

    if (n <= 0 || c <= 0) {
        fprintf(stderr, "Format direct invalide : %s\n", chemin);
        return NULL;
    }

    ProblemeUKP *p = probleme_ukp_creer(n, c);
    int lus = 0;
    while (lus < n && fgets(ligne, sizeof(ligne), f)) {
        char *l = trim(ligne);
        if (*l == '\0') continue;
        int volume, utilite;
        if (sscanf(l, "%d %d", &volume, &utilite) == 2) {
            p->volumes[lus]  = volume;
            p->utilites[lus] = utilite;
            ++lus;
        }
    }

    if (lus != n) {
        fprintf(stderr, "Lecture incomplete (%d / %d objets) : %s\n", lus, n, chemin);
        probleme_ukp_liberer(p);
        return NULL;
    }

    p->nom_instance = extraire_nom(chemin);
    return p;
}

ProblemeUKP *parser_ukp_lire(const char *chemin) {
    FormatUKP fmt = parser_ukp_detecter_format(chemin);
    if (fmt == UKP_FORMAT_INCONNU) {
        fprintf(stderr, "Format UKP non reconnu : %s\n", chemin);
        return NULL;
    }
    FILE *f = fopen(chemin, "r");
    if (!f) {
        fprintf(stderr, "Impossible d'ouvrir : %s\n", chemin);
        return NULL;
    }
    ProblemeUKP *p = (fmt == UKP_FORMAT_LP)
                   ? parser_ukp_lire_lp(f, chemin)
                   : parser_ukp_lire_direct(f, chemin);
    fclose(f);
    return p;
}
