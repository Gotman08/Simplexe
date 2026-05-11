#define _POSIX_C_SOURCE 200809L
#include "timer.h"

#include <time.h>

/**
 * @brief Lit l'horloge monotone et renvoie un nombre de secondes en virgule flottante.
 *
 * @return Horodatage monotone (résolution nanoseconde).
 */
static double secondes_actuelles(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

void timer_demarrer(Chronometre *c) {
    c->debut = secondes_actuelles();
}

double timer_temps_ecoule(const Chronometre *c) {
    return secondes_actuelles() - c->debut;
}
