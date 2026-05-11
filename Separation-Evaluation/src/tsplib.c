#include "tsplib.h"

#include <math.h>

long tsplib_distance_euc2d(double x1, double y1, double x2, double y2) {
    double dx = x1 - x2;
    double dy = y1 - y2;
    double d  = sqrt(dx * dx + dy * dy);
    return (long)(d + 0.5);
}

void tsplib_calculer_matrice(int n, const double *x, const double *y, long **matrice) {
    for (int i = 0; i < n; ++i) {
        matrice[i][i] = 0;
        for (int j = i + 1; j < n; ++j) {
            long d = tsplib_distance_euc2d(x[i], y[i], x[j], y[j]);
            matrice[i][j] = d;
            matrice[j][i] = d;
        }
    }
}
