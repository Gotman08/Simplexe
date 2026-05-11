from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

from .parsers import ProblemeTSP, ProblemeUKP

_PALETTE_TOUR = LinearSegmentedColormap.from_list(
    "tour", ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
)
_VERT = "#2ca02c"
_GRIS = "#bdbdbd"
_OR  = "#ff7f0e"
_BLEU = "#1f77b4"

def _preparer_dossier(chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)

def tracer_tour_tsp(
    probleme: ProblemeTSP,
    tour: Sequence[int],
    longueur: int,
    chemin_sortie: str | Path,
    titre: str | None = None,
) -> Path:

    chemin_sortie = Path(chemin_sortie)
    _preparer_dossier(chemin_sortie)

    if not probleme.coords_disponibles or len(tour) == 0:
        return _tracer_tour_sans_coords(probleme, tour, longueur, chemin_sortie, titre)

    n = probleme.n
    coords = np.array(probleme.coords)
    sequence = list(tour) + [tour[0]]
    points = coords[sequence]

    grand = n > 200
    tres_grand = n > 1000

    fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

    segments = np.stack([points[:-1], points[1:]], axis=1)
    couleurs = np.linspace(0, 1, len(segments))
    lc = LineCollection(
        segments,
        cmap=_PALETTE_TOUR,
        array=couleurs,
        linewidth=0.5 if tres_grand else (0.9 if grand else 1.6),
        alpha=0.85,
    )
    ax.add_collection(lc)

    taille_pts = 1 if tres_grand else (6 if grand else 30)
    ax.scatter(coords[:, 0], coords[:, 1], s=taille_pts, c="#222222", zorder=3)

    if n <= 60:
        for i, (x, y) in enumerate(coords):
            ax.annotate(
                str(i + 1),
                (x, y),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
                color="#333333",
            )

    ax.scatter(*coords[tour[0]], s=120, marker="*", color=_OR, zorder=5,
               edgecolors="black", linewidths=0.5, label="Départ")

    nom = titre or probleme.nom
    ax.set_title(f"{nom} — N = {n} — longueur = {longueur}", fontsize=13, weight="bold")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.25, linestyle="--")
    ax.legend(loc="upper right", fontsize=9, frameon=True)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def _tracer_tour_sans_coords(
    probleme: ProblemeTSP,
    tour: Sequence[int],
    longueur: int,
    chemin_sortie: Path,
    titre: str | None,
) -> Path:
    n = probleme.n
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    coords = np.stack([np.cos(angles), np.sin(angles)], axis=1)

    fig, ax = plt.subplots(figsize=(8, 8), dpi=200)
    sequence = list(tour) + [tour[0]] if tour else list(range(n)) + [0]
    points = coords[sequence]

    segments = np.stack([points[:-1], points[1:]], axis=1)
    couleurs = np.linspace(0, 1, len(segments))
    lc = LineCollection(segments, cmap=_PALETTE_TOUR, array=couleurs, linewidth=2.0, alpha=0.9)
    ax.add_collection(lc)
    ax.scatter(coords[:, 0], coords[:, 1], s=140, c="#222222", zorder=3)

    for i, (x, y) in enumerate(coords):
        ax.annotate(str(i), (x * 1.08, y * 1.08), ha="center", va="center", fontsize=10)

    if tour:
        ax.scatter(*coords[tour[0]], s=180, marker="*", color=_OR,
                   zorder=5, edgecolors="black", linewidths=0.5, label="Départ")

    nom = titre or probleme.nom
    ax.set_title(f"{nom} — N = {n} — longueur = {longueur}", fontsize=13, weight="bold")
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    if tour:
        ax.legend(loc="upper right", fontsize=9, frameon=True)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_solution_ukp(
    probleme: ProblemeUKP,
    valeurs: Sequence[int],
    utilite_totale: int,
    volume_total: int,
    chemin_sortie: str | Path,
    titre: str | None = None,
) -> Path:

    chemin_sortie = Path(chemin_sortie)
    _preparer_dossier(chemin_sortie)

    n = probleme.n
    ratios = [
        (probleme.utilites[j] / probleme.volumes[j]) if probleme.volumes[j] > 0 else 0.0
        for j in range(n)
    ]
    indices_tries = sorted(range(n), key=lambda j: -ratios[j])
    affichage_indices = indices_tries[:50] if n > 50 else indices_tries

    fig = plt.figure(figsize=(13, max(6, 0.35 * len(affichage_indices) + 3)), dpi=200)
    gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[5, 1], hspace=0.35, wspace=0.25)

    ax_bar = fig.add_subplot(gs[0, 0])
    ax_jauge = fig.add_subplot(gs[0, 1])
    ax_recap = fig.add_subplot(gs[1, :])

    libelles = [f"x{idx + 1} ({probleme.volumes[idx]}, {probleme.utilites[idx]})" for idx in affichage_indices]
    valeurs_aff = [valeurs[idx] if idx < len(valeurs) else 0 for idx in affichage_indices]
    couleurs = [_VERT if v > 0 else _GRIS for v in valeurs_aff]
    largeurs = [
        (valeurs_aff[k] * probleme.volumes[idx]) if valeurs_aff[k] > 0 else probleme.volumes[idx]
        for k, idx in enumerate(affichage_indices)
    ]
    alpha = [0.95 if v > 0 else 0.45 for v in valeurs_aff]

    bars = ax_bar.barh(libelles, largeurs, color=couleurs, alpha=1.0, edgecolor="#444444", linewidth=0.6)
    for b, a in zip(bars, alpha):
        b.set_alpha(a)

    for k, idx in enumerate(affichage_indices):
        v = valeurs_aff[k]
        if v > 0:
            ax_bar.text(
                largeurs[k] + max(largeurs) * 0.01,
                k,
                f"x{v}",
                va="center",
                fontsize=8,
                color="#0a4f12",
                weight="bold",
            )

    nom = titre or probleme.nom
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Volume occupé (= valeur × volume unitaire)", fontsize=10)
    ax_bar.set_title(
        f"Sac à dos : {nom} — {n} objets — affichage trié par utilité / volume"
        + (f" (top 50 / {n})" if n > 50 else ""),
        fontsize=12,
        weight="bold",
    )
    ax_bar.grid(axis="x", alpha=0.3, linestyle="--")
    ax_bar.tick_params(axis="y", labelsize=8)

    pourcentage = (volume_total / probleme.capacite) if probleme.capacite > 0 else 0.0
    pourcentage = max(0.0, min(1.0, pourcentage))

    ax_jauge.barh([""], [1.0], color="#eeeeee", edgecolor="#999999", height=0.5)
    ax_jauge.barh([""], [pourcentage], color=_VERT, edgecolor=_VERT, height=0.5)
    ax_jauge.set_xlim(0, 1)
    ax_jauge.set_title("Remplissage du sac", fontsize=11, weight="bold")
    ax_jauge.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_jauge.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    ax_jauge.set_yticks([])
    ax_jauge.text(
        pourcentage / 2 if pourcentage > 0.15 else pourcentage + 0.04,
        0,
        f"{pourcentage * 100:.1f}%",
        ha="center" if pourcentage > 0.15 else "left",
        va="center",
        fontsize=11,
        weight="bold",
        color="white" if pourcentage > 0.15 else "#333333",
    )

    icone = patches.FancyBboxPatch(
        (0.02, -0.55),
        0.96,
        0.4,
        boxstyle="round,pad=0.02",
        linewidth=1.5,
        edgecolor="#666",
        facecolor="#fafafa",
    )
    ax_jauge.add_patch(icone)
    ax_jauge.text(
        0.5,
        -0.35,
        f"Objets retenus : {sum(1 for v in valeurs if v > 0)} / {n}",
        ha="center",
        va="center",
        fontsize=9,
        color="#333",
    )

    ax_recap.axis("off")
    nb_objets_pris = sum(v for v in valeurs)
    recap = (
        f"Utilité totale : {utilite_totale}    |    "
        f"Volume utilisé : {volume_total} / {probleme.capacite}    |    "
        f"Objets pris : {nb_objets_pris}    |    "
        f"Espace résiduel : {probleme.capacite - volume_total}"
    )
    ax_recap.text(
        0.5, 0.5, recap, ha="center", va="center", fontsize=12, weight="bold", color="#222"
    )

    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_courbes_benchmark(
    series: dict[str, dict[str, list[float]]],
    titre: str,
    label_x: str,
    label_y: str,
    chemin_sortie: str | Path,
    echelle_log_y: bool = True,
) -> Path:

    chemin_sortie = Path(chemin_sortie)
    _preparer_dossier(chemin_sortie)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
    couleurs = [_BLEU, _OR, "#9467bd", "#8c564b"]
    marqueurs = ["o", "s", "^", "D"]

    for k, (nom, donnees) in enumerate(series.items()):
        ax.plot(
            donnees["x"],
            donnees["y"],
            label=nom,
            color=couleurs[k % len(couleurs)],
            marker=marqueurs[k % len(marqueurs)],
            linewidth=2.0,
            markersize=7,
        )

    ax.set_xlabel(label_x, fontsize=11)
    ax.set_ylabel(label_y, fontsize=11)
    ax.set_title(titre, fontsize=13, weight="bold")
    if echelle_log_y:
        ax.set_yscale("log")
    ax.grid(True, alpha=0.3, linestyle="--", which="both")
    ax.legend(fontsize=10, frameon=True, loc="best")

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_panneau_benchmark(
    chemins_csv: dict[str, Path],
    chemin_sortie: str | Path,
) -> Path:

    import csv as _csv

    chemin_sortie = Path(chemin_sortie)
    _preparer_dossier(chemin_sortie)

    def lire(p: Path) -> dict[str, list[float]] | None:
        if not p or not Path(p).exists():
            return None
        n_vals: list[float] = []
        t_vals: list[float] = []
        no_vals: list[float] = []
        with open(p, "r", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                taille = float(row.get("n", 0) or 0)
                temps = float(row.get("temps_s", 0) or 0)
                noeuds = float(row.get("noeuds_generes", row.get("noeuds", 0)) or 0)
                if taille > 0:
                    n_vals.append(taille)
                    t_vals.append(temps)
                    no_vals.append(noeuds)
        ordre = sorted(range(len(n_vals)), key=lambda k: n_vals[k])
        return {
            "n":      [n_vals[k] for k in ordre],
            "temps":  [t_vals[k] for k in ordre],
            "noeuds": [no_vals[k] for k in ordre],
        }

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=200)
    pairs = [
        ("UKP — temps (s)",      "ukp_bb", "ukp_or", axes[0, 0], "temps"),
        ("TSP — temps (s)",      "tsp_bb", "tsp_or", axes[0, 1], "temps"),
        ("UKP — nœuds générés",  "ukp_bb", "ukp_or", axes[1, 0], "noeuds"),
        ("TSP — nœuds générés",  "tsp_bb", "tsp_or", axes[1, 1], "noeuds"),
    ]

    for titre, k1, k2, ax, mesure in pairs:
        d1 = lire(chemins_csv.get(k1)) if chemins_csv.get(k1) else None
        d2 = lire(chemins_csv.get(k2)) if chemins_csv.get(k2) else None
        valeurs_pos: list[float] = []
        if d1 and d1[mesure]:
            ax.plot(d1["n"], d1[mesure], label="Branch & Bound (C)",
                    color=_BLEU, marker="o", linewidth=2.0)
            valeurs_pos.extend([v for v in d1[mesure] if v > 0])
            valeurs_pos.extend([v for v in d1["n"]    if v > 0])
        if d2 and d2[mesure]:
            ax.plot(d2["n"], d2[mesure], label="OR-Tools (Python)",
                    color=_OR, marker="s", linewidth=2.0)
            valeurs_pos.extend([v for v in d2[mesure] if v > 0])
            valeurs_pos.extend([v for v in d2["n"]    if v > 0])
        ax.set_title(titre, fontsize=12, weight="bold")
        ax.set_xlabel("Taille de l'instance N", fontsize=10)
        ax.set_ylabel("Temps (s)" if mesure == "temps" else "Nœuds", fontsize=10)
        if valeurs_pos:
            try:
                ax.set_yscale("log")
                ax.set_xscale("log")
            except ValueError:
                pass
        ax.grid(True, alpha=0.3, linestyle="--", which="both")
        if d1 or d2:
            ax.legend(fontsize=9)
        else:
            ax.text(0.5, 0.5, "Aucune donnée disponible",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#888888", style="italic")

    fig.suptitle(
        "Comparaison croisée Branch & Bound (C) ↔ OR-Tools (Python)",
        fontsize=14,
        weight="bold",
        y=1.00,
    )
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

__all__ = [
    "tracer_tour_tsp",
    "tracer_solution_ukp",
    "tracer_courbes_benchmark",
    "tracer_panneau_benchmark",
]
