from __future__ import annotations

import statistics
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

_BLEU = "#1f77b4"
_OR  = "#ff7f0e"
_GRIS = "#888888"
_VERT = "#2ca02c"
_ROUGE = "#d62728"

def _grouper_par_methode(lignes: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for l in lignes:
        out.setdefault(l["methode"], []).append(l)
    return out

def _serie_par_instance(lignes: list[dict], cle: str) -> list[tuple[str, int, list[float]]]:

    bucket: dict[str, list[dict]] = {}
    for l in lignes:
        bucket.setdefault(l["instance"], []).append(l)
    series = []
    for inst, runs in bucket.items():
        valeurs = [r[cle] for r in runs if isinstance(r.get(cle), (int, float))]
        if valeurs:
            series.append((inst, runs[0]["n"], valeurs))
    series.sort(key=lambda x: x[1])
    return series

def _preparer_dossier(chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)

def tracer_panneau_principal(
    lignes_ukp: list[dict],
    lignes_tsp: list[dict],
    chemin_sortie: Path,
) -> Path:

    _preparer_dossier(chemin_sortie)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=200)

    pairs = [
        ("UKP : temps médian (s)",       lignes_ukp, "temps_s",       axes[0, 0], "ukp"),
        ("TSP : temps médian (s)",       lignes_tsp, "temps_s",       axes[0, 1], "tsp"),
        ("UKP : nœuds générés (médiane)", lignes_ukp, "noeuds_generes", axes[1, 0], "ukp"),
        ("TSP : nœuds générés (médiane)", lignes_tsp, "noeuds_generes", axes[1, 1], "tsp"),
    ]

    for titre, lignes, mesure, ax, probleme in pairs:
        groupes = _grouper_par_methode(lignes)
        couleur = {"B&B (C)": _BLEU, "OR-Tools": _OR}
        marqueur = {"B&B (C)": "o", "OR-Tools": "s"}
        a_des_donnees = False

        for methode, runs in groupes.items():
            series = _serie_par_instance(runs, mesure)
            xs = [n for _, n, _ in series]
            ys = [statistics.median(v) for _, _, v in series]
            xs_pos = [x for x, y in zip(xs, ys) if x > 0 and y > 0]
            ys_pos = [y for x, y in zip(xs, ys) if x > 0 and y > 0]
            if xs_pos:
                ax.scatter(xs_pos, ys_pos, label=methode,
                           color=couleur.get(methode, _GRIS),
                           marker=marqueur.get(methode, "o"),
                           s=70, alpha=0.85,
                           edgecolors="#222", linewidths=0.7, zorder=3)
                a_des_donnees = True

        ax.set_title(titre, fontsize=12, weight="bold")
        ax.set_xlabel("Taille N de l'instance", fontsize=10)
        ax.set_ylabel("Temps (s)" if mesure == "temps_s" else "Nœuds", fontsize=10)
        if a_des_donnees:
            try:
                ax.set_xscale("log")
                ax.set_yscale("log")
            except ValueError:
                pass
            ax.legend(fontsize=10, frameon=True, loc="upper left")
        else:
            ax.text(0.5, 0.5, "Aucune donnée",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#888", style="italic")
        ax.grid(True, alpha=0.3, linestyle="--", which="both")

        if probleme == "tsp" and mesure == "temps_s" and a_des_donnees:
            ax.text(0.99, 0.04,
                    "OR-Tools (GUIDED_LOCAL_SEARCH) consomme l'intégralité\n"
                    "du timeout : le « temps » mesuré ici sature au budget,\n"
                    "il ne reflète pas le « time to best ».",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5,
                    style="italic", color="#444",
                    bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff8e1",
                              edgecolor="#bbb", linewidth=0.7))

    fig.suptitle("Comparaison croisée Branch & Bound (C) ↔ OR-Tools (Python) "
                 ": nuages de points (une instance = un point)",
                 fontsize=13.5, weight="bold", y=1.00)
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_boxplot_temps(
    lignes: list[dict],
    titre_probleme: str,
    chemin_sortie: Path,
) -> Path:

    _preparer_dossier(chemin_sortie)

    instances = []
    seen = set()
    for l in lignes:
        if l["instance"] not in seen:
            instances.append((l["instance"], l["n"]))
            seen.add(l["instance"])
    instances.sort(key=lambda x: x[1])

    if not instances:
        fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
        ax.text(0.5, 0.5, "Aucune donnée à tracer", ha="center", va="center",
                fontsize=12, color="#888", style="italic", transform=ax.transAxes)
        ax.set_axis_off()
        plt.savefig(chemin_sortie, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return chemin_sortie

    EPS = 1e-5
    fig, ax = plt.subplots(figsize=(max(10, 0.6 * len(instances) + 4), 7), dpi=200)

    pos_or, data_or = [], []
    pos_bb, data_bb = [], []
    libelles = []

    for k, (inst, _) in enumerate(instances):
        valeurs_or = []
        valeurs_bb = []
        for l in lignes:
            if l["instance"] != inst:
                continue
            t = l.get("temps_s", 0)
            if not isinstance(t, (int, float)):
                continue
            t = max(float(t), EPS)
            statut = l.get("statut", "")
            if l["methode"] == "OR-Tools" and statut not in ("BINAIRE_C_INTROUVABLE",):
                valeurs_or.append(t)
            elif l["methode"] == "B&B (C)" and statut == "OK":
                valeurs_bb.append(t)
        if valeurs_or:
            pos_or.append(k * 3.0)
            data_or.append(valeurs_or)
        if valeurs_bb:
            pos_bb.append(k * 3.0 + 1.0)
            data_bb.append(valeurs_bb)
        libelles.append(inst)

    if data_or:
        bp = ax.boxplot(data_or, positions=pos_or, widths=0.8,
                        patch_artist=True, showfliers=False,
                        medianprops={"color": "white", "linewidth": 2})
        for patch in bp["boxes"]:
            patch.set_facecolor(_OR)
            patch.set_alpha(0.85)
            patch.set_edgecolor("#333")

    if data_bb:
        bp = ax.boxplot(data_bb, positions=pos_bb, widths=0.8,
                        patch_artist=True, showfliers=False,
                        medianprops={"color": "white", "linewidth": 2})
        for patch in bp["boxes"]:
            patch.set_facecolor(_BLEU)
            patch.set_alpha(0.85)
            patch.set_edgecolor("#333")

    ax.set_xticks([k * 3.0 + 0.5 for k in range(len(instances))])
    ax.set_xticklabels(libelles, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Temps (s)", fontsize=11)
    ax.set_title(f"{titre_probleme} : Variabilite du temps par instance "
                 f"(voir legende pour les couleurs des methodes)",
                 fontsize=12, weight="bold")
    if data_or or data_bb:
        ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3, linestyle="--", which="both")

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=_OR,  alpha=0.85, label="OR-Tools (Python)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=_BLEU, alpha=0.85, label="B&B (C) - solutions OK"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=10, frameon=True)

    if titre_probleme.upper() == "TSP":
        ax.text(0.99, 0.02,
                "Note : OR-Tools (GUIDED_LOCAL_SEARCH) utilise systematiquement\n"
                "tout le timeout :les boites OR sont degenerees par construction.",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
                style="italic", color="#444",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff8e1",
                          edgecolor="#aaaaaa", linewidth=0.7))

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_scaling_avec_erreurs(
    lignes: list[dict],
    titre_probleme: str,
    chemin_sortie: Path,
) -> Path:

    _preparer_dossier(chemin_sortie)
    fig, ax = plt.subplots(figsize=(11, 7), dpi=200)

    couleur = {"B&B (C)": _BLEU, "OR-Tools": _OR}
    marqueur = {"B&B (C)": "o", "OR-Tools": "s"}

    for methode, runs in _grouper_par_methode(lignes).items():
        series = _serie_par_instance(runs, "temps_s")
        xs, medians, lows, highs = [], [], [], []
        for _, n, valeurs in series:
            if n <= 0 or not valeurs:
                continue
            med = statistics.median(valeurs)
            if med <= 0:
                continue
            xs.append(n)
            medians.append(med)
            lows.append(med - min(valeurs))
            highs.append(max(valeurs) - med)

        if xs:
            ax.errorbar(
                xs, medians,
                yerr=[lows, highs],
                fmt=marqueur.get(methode, "o") + "-",
                color=couleur.get(methode, _GRIS),
                ecolor=couleur.get(methode, _GRIS),
                elinewidth=1.2,
                capsize=4,
                linewidth=2.0,
                markersize=8,
                label=f"{methode} (médiane + min/max)",
            )

    instances_par_n: dict[int, list[str]] = {}
    for methode, runs in _grouper_par_methode(lignes).items():
        for inst, n, valeurs in _serie_par_instance(runs, "temps_s"):
            if statistics.median(valeurs) > 0 and n > 0:
                instances_par_n.setdefault(n, []).append(inst)

    deja_annote = set()
    for methode, runs in _grouper_par_methode(lignes).items():
        for inst, n, valeurs in _serie_par_instance(runs, "temps_s"):
            if (inst, methode) in deja_annote or not valeurs:
                continue
            med = statistics.median(valeurs)
            if med <= 0 or n <= 0:
                continue
            multi = len(instances_par_n.get(n, [])) > 1
            if multi or n in (10, 15) or any(c.isdigit() for c in inst):
                ax.annotate(inst, (n, med), xytext=(4, 6), textcoords="offset points",
                            fontsize=7, color="#444444", alpha=0.85)
                deja_annote.add((inst, methode))

    ax.set_xlabel("Taille N de l'instance", fontsize=11)
    ax.set_ylabel("Temps (s)", fontsize=11)
    ax.set_title(f"{titre_probleme} : scaling avec barres d'erreur min/max",
                 fontsize=13, weight="bold")
    try:
        ax.set_xscale("log")
        ax.set_yscale("log")
    except ValueError:
        pass
    ax.grid(True, alpha=0.3, linestyle="--", which="both")
    ax.legend(fontsize=10, frameon=True)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_qualite_relative(
    lignes_ukp: list[dict],
    lignes_tsp: list[dict],
    chemin_sortie: Path,
) -> Path:

    _preparer_dossier(chemin_sortie)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=200)

    def construire(lignes: list[dict]) -> tuple[list[str], list[float]]:
        bucket: dict[str, dict[str, list[int]]] = {}
        for l in lignes:
            d = bucket.setdefault(l["instance"], {"B&B (C)": [], "OR-Tools": []})
            if isinstance(l.get("valeur"), int):
                d[l["methode"]].append(l["valeur"])
        instances, ratios = [], []
        for inst, methods in bucket.items():
            v_bb = max(methods["B&B (C)"]) if methods["B&B (C)"] else 0
            v_or = max(methods["OR-Tools"]) if methods["OR-Tools"] else 0
            if v_or > 0 and v_bb > 0:
                instances.append(inst)
                ratios.append(v_bb / v_or)
        return instances, ratios

    for ax, (titre, lignes, type_pb) in zip(
        axes,
        [("UKP (max)", lignes_ukp, "max"), ("TSP (min)", lignes_tsp, "min")],
    ):
        instances, ratios = construire(lignes)
        if not instances:
            ax.text(0.5, 0.5, "Aucune comparaison disponible",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#888", style="italic")
            ax.set_title(titre, fontsize=13, weight="bold")
            continue

        couleurs = [_VERT if (type_pb == "max" and r > 1) or (type_pb == "min" and r < 1)
                    else (_ROUGE if (type_pb == "max" and r < 1) or (type_pb == "min" and r > 1)
                          else _GRIS)
                    for r in ratios]
        ax.bar(range(len(instances)), ratios, color=couleurs, edgecolor="#333", linewidth=0.6)
        ax.axhline(1.0, color="black", linewidth=1.0, linestyle="--")
        ax.set_xticks(range(len(instances)))
        ax.set_xticklabels(instances, rotation=45, ha="right", fontsize=9)
        ax.set_ylabel("valeur(BB) / valeur(OR-Tools)", fontsize=11)
        ax.set_title(f"{titre} : ratio des solutions trouvées", fontsize=13, weight="bold")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        marges = max(0.1, max((abs(r - 1) for r in ratios), default=0.1) * 1.2)
        ax.set_ylim(1 - marges, 1 + marges)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

def tracer_performance_profile(
    lignes_ukp: list[dict],
    lignes_tsp: list[dict],
    chemin_sortie: Path,
) -> Path:

    _preparer_dossier(chemin_sortie)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=200)

    def construire(lignes: list[dict]) -> tuple[dict[str, list[float]], int]:

        bucket: dict[str, dict[str, float]] = {}
        for l in lignes:
            instance = l["instance"]
            methode = l["methode"]
            t = l.get("temps_s", 0)
            if l.get("statut") not in ("OK", "OPTIMAL", "OPTIMAL_OU_FAISABLE"):
                t = float("inf")
            if not isinstance(t, (int, float)) or t <= 0:
                t = float("inf")
            d = bucket.setdefault(instance, {})
            actuel = d.get(methode, float("inf"))
            d[methode] = min(actuel, float(t))

        ratios: dict[str, list[float]] = {}
        n_instances = len(bucket)
        for instance, methodes in bucket.items():
            t_min = min(methodes.values()) if methodes else float("inf")
            if t_min == float("inf") or t_min <= 0:
                continue
            for m, t in methodes.items():
                ratio = t / t_min if t < float("inf") else float("inf")
                ratios.setdefault(m, []).append(ratio)
        return ratios, n_instances

    couleur = {"B&B (C)": _BLEU, "OR-Tools": _OR}
    marqueur = {"B&B (C)": "o", "OR-Tools": "s"}

    for ax, (titre, lignes) in zip(axes, [("UKP", lignes_ukp), ("TSP", lignes_tsp)]):
        ratios, n = construire(lignes)
        if not ratios or n == 0:
            ax.text(0.5, 0.5, "Aucune donnée",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#888", style="italic")
            ax.set_title(f"{titre} : Performance profile", fontsize=12, weight="bold")
            continue

        import numpy as _np
        taus = _np.logspace(0, 4, 200)
        for methode, ratios_m in ratios.items():
            arr = _np.array(ratios_m, dtype=float)
            fraction = _np.array([
                _np.mean(arr <= t) if len(arr) else 0.0 for t in taus
            ])
            ax.plot(taus, fraction, color=couleur.get(methode, _GRIS),
                    marker=marqueur.get(methode, "o"), markevery=20,
                    linewidth=2.0, markersize=6, label=methode)

        ax.set_xscale("log")
        ax.set_xlim(1, 1e4)
        ax.set_ylim(-0.02, 1.05)
        ax.set_xlabel("Facteur τ (par rapport au meilleur temps)", fontsize=10)
        ax.set_ylabel("Fraction d'instances résolues", fontsize=10)
        ax.set_title(f"{titre} : Performance profile (Dolan-Moré, n = {n} instances)",
                     fontsize=12, weight="bold")
        ax.grid(True, alpha=0.3, linestyle="--", which="both")
        ax.legend(fontsize=10, loc="lower right")
        ax.axhline(1.0, color="#888", linewidth=0.5, linestyle=":")

    fig.suptitle("Profils de performance : combien d'instances chaque méthode résout dans un facteur τ du meilleur",
                 fontsize=12, weight="bold", y=1.00)
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin_sortie

__all__ = [
    "tracer_panneau_principal",
    "tracer_boxplot_temps",
    "tracer_scaling_avec_erreurs",
    "tracer_qualite_relative",
    "tracer_performance_profile",
]
