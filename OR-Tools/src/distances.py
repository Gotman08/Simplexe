from __future__ import annotations

from math import sqrt
from typing import Sequence

def distance_euc2d(x1: float, y1: float, x2: float, y2: float) -> int:

    dx, dy = x1 - x2, y1 - y2
    return int(sqrt(dx * dx + dy * dy) + 0.5)

def matrice_distances(coords: Sequence[tuple[float, float]]) -> list[list[int]]:

    n = len(coords)
    if n > 4000:
        return []

    if n > 200:
        try:
            import numpy as _np
            xs = _np.fromiter((c[0] for c in coords), dtype=_np.float64, count=n)
            ys = _np.fromiter((c[1] for c in coords), dtype=_np.float64, count=n)
            dx = xs[:, None] - xs[None, :]
            dy = ys[:, None] - ys[None, :]
            d = _np.sqrt(dx * dx + dy * dy)
            d = (d + 0.5).astype(_np.int32)
            return d.tolist()
        except ImportError:
            pass

    matrice = [[0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = coords[i]
        for j in range(i + 1, n):
            xj, yj = coords[j]
            d = distance_euc2d(xi, yi, xj, yj)
            matrice[i][j] = d
            matrice[j][i] = d
    return matrice
