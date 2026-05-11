#ifndef SE_TIMER_H
#define SE_TIMER_H

/**
 * @brief Chronomètre monotone basé sur CLOCK_MONOTONIC.
 */
typedef struct {
    double debut; /**< Instant de départ en secondes. */
} Chronometre;

/**
 * @brief Démarre le chronomètre (initialise l'instant de départ).
 *
 * @param[out] c Chronomètre à initialiser.
 */
void   timer_demarrer(Chronometre *c);

/**
 * @brief Renvoie le temps écoulé depuis le dernier timer_demarrer().
 *
 * @param[in] c Chronomètre déjà démarré.
 * @return Durée écoulée en secondes.
 */
double timer_temps_ecoule(const Chronometre *c);

#endif
