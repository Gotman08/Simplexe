from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .distances import matrice_distances

@dataclass
class ProblemeUKP:
    nom: str
    n: int
    capacite: int
    volumes: list[int]
    utilites: list[int]

@dataclass
class ProblemeTSP:
    nom: str
    n: int
    coords: list[tuple[float, float]]
    distances: list[list[int]]
    distances_explicites: bool = False
    coords_disponibles: bool = True

_RE_COEF = re.compile(r"([+-])\s*(\d+(?:\.\d+)?)\s*[xX](\d+)")
_RE_BORNE = re.compile(r"<=\s*(-?\d+(?:\.\d+)?)")

def _nom_instance(chemin: Path) -> str:
    return chemin.stem

def _detecter_format_ukp(chemin: Path) -> str:
    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l or l.startswith("#"):
                continue
            if l.startswith("n_variables"):
                return "lp"
            if l.startswith("n:") or l.startswith("n "):
                return "direct"
            return "inconnu"
    return "inconnu"

def _lire_ukp_lp(chemin: Path) -> ProblemeUKP:
    n = 0
    coef_obj: list[int] = []
    coef_contr: list[int] = []
    capacite = 0
    mode = None

    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l:
                if mode == "max":
                    mode = "contrainte"
                continue

            if l.startswith("n_variables"):
                n = int(l.split()[1])
                coef_obj = [0] * n
                coef_contr = [0] * n
            elif l.startswith("n_contraintes"):
                pass
            elif l == "max":
                mode = "max"
            elif l == "min":
                mode = "min"
            elif mode in ("max", "min") and (l[0] in "+-" or l[0].isdigit()):
                for signe, val, idx in _RE_COEF.findall(l):
                    coefficient = float(val) * (1 if signe == "+" else -1)
                    j = int(idx) - 1
                    if 0 <= j < n:
                        coef_obj[j] = int(coefficient)
                mode = "contrainte"
            elif mode == "contrainte" and (l[0] in "+-" or l[0].isdigit()):
                for signe, val, idx in _RE_COEF.findall(l):
                    coefficient = float(val) * (1 if signe == "+" else -1)
                    j = int(idx) - 1
                    if 0 <= j < n:
                        coef_contr[j] = int(coefficient)
                m_borne = _RE_BORNE.search(l)
                if m_borne:
                    capacite = int(float(m_borne.group(1)))

    if n == 0:
        raise ValueError(f"Format UKP LP invalide : {chemin}")

    return ProblemeUKP(
        nom=_nom_instance(chemin),
        n=n,
        capacite=capacite,
        volumes=coef_contr,
        utilites=coef_obj,
    )

def _lire_ukp_direct(chemin: Path) -> ProblemeUKP:
    n: Optional[int] = None
    capacite: Optional[int] = None
    volumes: list[int] = []
    utilites: list[int] = []

    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l:
                continue
            if l.startswith("n:") or l.startswith("n "):
                n = int(l.split()[1] if ":" in l else l.split()[1])
            elif l.startswith("c:") or l.startswith("c "):
                capacite = int(l.split()[1] if ":" in l else l.split()[1])
            else:
                parts = l.split()
                if len(parts) >= 2:
                    volumes.append(int(parts[0]))
                    utilites.append(int(parts[1]))

    if n is None or capacite is None or len(volumes) != n:
        raise ValueError(f"Format UKP direct invalide : {chemin}")

    return ProblemeUKP(
        nom=_nom_instance(chemin),
        n=n,
        capacite=capacite,
        volumes=volumes,
        utilites=utilites,
    )

def lire_ukp(chemin: str | Path) -> ProblemeUKP:
    chemin = Path(chemin)
    fmt = _detecter_format_ukp(chemin)
    if fmt == "lp":
        return _lire_ukp_lp(chemin)
    if fmt == "direct":
        return _lire_ukp_direct(chemin)
    raise ValueError(f"Format UKP non reconnu : {chemin}")

def _detecter_format_tsp(chemin: Path) -> str:
    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l or l.startswith("#"):
                continue
            if l.startswith("n_sommets"):
                return "graphe"
            if l.startswith(("NAME", "TYPE", "DIMENSION", "COMMENT")):
                return "tsplib95"
            return "inconnu"
    return "inconnu"

def _lire_tsp_graphe(chemin: Path) -> ProblemeTSP:
    n = 0
    oriente = False
    distances: list[list[int]] = []
    dans_aretes = False

    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l:
                continue
            if l.startswith("n_sommets"):
                n = int(l.split()[1])
                distances = [[-1] * n for _ in range(n)]
                for i in range(n):
                    distances[i][i] = 0
            elif l.startswith("oriente"):
                oriente = bool(int(l.split()[1]))
            elif l.startswith("value"):
                pass
            elif l.startswith("DEBUT_DEF_ARETES"):
                dans_aretes = True
            elif l.startswith("FIN_DEF_ARETES"):
                dans_aretes = False
            elif dans_aretes:
                parts = l.split()
                if len(parts) >= 2 and n > 0:
                    u, v = int(parts[0]), int(parts[1])
                    w = int(parts[2]) if len(parts) >= 3 else 1
                    distances[u][v] = w
                    if not oriente:
                        distances[v][u] = w

    max_w = max((max(row) for row in distances), default=0)
    inaccessible = (max_w + 1) * n + 1
    for i in range(n):
        for j in range(n):
            if i != j and distances[i][j] < 0:
                distances[i][j] = inaccessible

    return ProblemeTSP(
        nom=_nom_instance(chemin),
        n=n,
        coords=[(float(i), 0.0) for i in range(n)],
        distances=distances,
        distances_explicites=True,
        coords_disponibles=False,
    )

def _lire_tsp_tsplib(chemin: Path) -> ProblemeTSP:
    n = 0
    type_arete = "EUC_2D"
    coords: list[tuple[float, float]] = []
    dans_coords = False

    with chemin.open("r", encoding="utf-8", errors="replace") as f:
        for ligne in f:
            l = ligne.strip()
            if not l:
                continue

            if not dans_coords:
                if l.startswith("DIMENSION"):
                    n = int(re.search(r"(\d+)", l).group(1))
                elif l.startswith("EDGE_WEIGHT_TYPE"):
                    type_arete = l.split(":")[-1].strip()
                elif l.startswith("NODE_COORD_SECTION"):
                    dans_coords = True
                    coords = [(0.0, 0.0)] * n
            else:
                if l.startswith("EOF"):
                    break
                parts = l.split()
                if len(parts) >= 3:
                    idx = int(parts[0]) - 1
                    if 0 <= idx < n:
                        coords[idx] = (float(parts[1]), float(parts[2]))

    if n == 0 or not coords:
        raise ValueError(f"Format TSPLIB95 invalide : {chemin}")

    if type_arete != "EUC_2D":
        raise ValueError(
            f"EDGE_WEIGHT_TYPE = {type_arete} non supporté (seul EUC_2D est strict)."
        )

    return ProblemeTSP(
        nom=_nom_instance(chemin),
        n=n,
        coords=coords,
        distances=matrice_distances(coords),
        distances_explicites=False,
        coords_disponibles=True,
    )

def lire_tsp(chemin: str | Path) -> ProblemeTSP:
    chemin = Path(chemin)
    fmt = _detecter_format_tsp(chemin)
    if fmt == "graphe":
        return _lire_tsp_graphe(chemin)
    if fmt == "tsplib95":
        return _lire_tsp_tsplib(chemin)
    raise ValueError(f"Format TSP non reconnu : {chemin}")
