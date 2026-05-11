#ifndef SE_TSPLIB_H
#define SE_TSPLIB_H

/**
 * @brief Distance euclidienne 2D entière (norme EUC_2D au sens TSPLIB).
 *
 * @param[in] x1 Abscisse du premier point.
 * @param[in] y1 Ordonnée du premier point.
 * @param[in] x2 Abscisse du second point.
 * @param[in] y2 Ordonnée du second point.
 * @return Distance euclidienne arrondie à l'entier le plus proche.
 */
long tsplib_distance_euc2d(double x1, double y1, double x2, double y2);

/**
 * @brief Remplit la matrice de distances entières d'un nuage de n points.
 *
 * @param[in]  n       Nombre de points.
 * @param[in]  x       Coordonnées x (taille n).
 * @param[in]  y       Coordonnées y (taille n).
 * @param[out] matrice Matrice n×n pré-allouée, remplie sur place.
 */
void tsplib_calculer_matrice(int n, const double *x, const double *y, long **matrice);

#endif
