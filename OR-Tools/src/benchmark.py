from __future__ import annotations

import csv
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .parsers import lire_tsp, lire_ukp
from .timer import Chronometre
from .tsp_solver import resoudre_tsp
from .ukp_solver import resoudre_ukp
from .visualization import tracer_panneau_benchmark

@dataclass
class ConfigBenchmark:
    racine: Path
    binaire_c: Path
    dossier_tests_ukp: Path
    dossier_tests_tsp: Path
    dossier_resultats: Path
    timeout_s: float = 60.0
    inclure_grands: bool = False
    visualiser: bool = True

_INSTANCES_UKP_PETITES = [
    "prob_sac_1.txt",
    "prob_sac_2.txt",
    "prob_sac_3.txt",
    "prob_sac_4.txt",
    "prob_sac_5.txt",
    "prob_sac_10.txt",
    "prob_sac_20.txt",
    "prob_sac_25.txt",
    "prob_sac_30.txt",
]
_INSTANCES_UKP_GRANDES = ["prob_sac_2000.txt", "prob_sac_20000.txt"]

_INSTANCES_TSP_PETITES = [
    "graphe_12.txt", "graphe_13.txt", "graphe_14.txt", "graphe_15.txt",
    "pd_5.tsp", "pd_11.tsp", "pd_15.tsp", "pd_18.tsp", "pd_20.tsp", "pd_22.tsp",
]
_INSTANCES_TSP_GRANDES = ["pd_59.tsp", "canada_4663.tsp", "usa_13509.tsp"]

def _executer_c(binaire: Path, probleme: str, fichier: Path, timeout_s: float) -> Optional[dict]:
    if not binaire.exists():
        return None
    cmd = [str(binaire), "--probleme", probleme, "--fichier", str(fichier), "--silent"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"timeout": True, "instance": fichier.stem}
    sortie = (proc.stdout or "").strip().splitlines()
    if not sortie:
        return None
    derniere = sortie[-1]
    champs = derniere.split(",")
    if probleme == "ukp" and len(champs) >= 5:
        return {
            "instance": champs[0],
            "valeur": int(champs[1]),
            "volume": int(champs[2]),
            "temps_s": float(champs[3]),
            "noeuds_generes": int(champs[4]),
        }
    if probleme == "tsp" and len(champs) >= 4:
        return {
            "instance": champs[0],
            "valeur": int(champs[1]),
            "temps_s": float(champs[2]),
            "noeuds_generes": int(champs[3]),
        }
    return None

def _ecrire_csv(chemin: Path, lignes: Iterable[dict], champs: list[str]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=champs)
        writer.writeheader()
        for ligne in lignes:
            writer.writerow({k: ligne.get(k, "") for k in champs})

def lancer_benchmark(cfg: ConfigBenchmark) -> dict[str, Path]:
    cfg.dossier_resultats.mkdir(parents=True, exist_ok=True)

    instances_ukp = list(_INSTANCES_UKP_PETITES)
    instances_tsp = list(_INSTANCES_TSP_PETITES)
    if cfg.inclure_grands:
        instances_ukp.extend(_INSTANCES_UKP_GRANDES)
        instances_tsp.extend(_INSTANCES_TSP_GRANDES)

    lignes_ukp_bb: list[dict] = []
    lignes_ukp_or: list[dict] = []
    lignes_tsp_bb: list[dict] = []
    lignes_tsp_or: list[dict] = []

    print("=== Benchmark UKP ===")
    for nom in instances_ukp:
        chemin = cfg.dossier_tests_ukp / nom
        if not chemin.exists():
            print(f"  [skip] {nom} (introuvable)")
            continue
        try:
            probleme = lire_ukp(chemin)
        except Exception as exc:
            print(f"  [erreur lecture] {nom}: {exc}")
            continue

        chrono = Chronometre()
        try:
            sol = resoudre_ukp(probleme, timeout_s=cfg.timeout_s)
            lignes_ukp_or.append({
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": sol.utilite_totale,
                "temps_s": sol.temps_secondes,
                "noeuds_generes": max(sol.n_noeuds, 0),
                "statut": sol.statut,
            })
            print(f"  [OR  ] {nom:<25} val={sol.utilite_totale:<10} t={sol.temps_secondes:.4f}s  ({sol.statut})")
        except Exception as exc:
            print(f"  [erreur OR-Tools] {nom}: {exc}")

        result_c = _executer_c(cfg.binaire_c, "ukp", chemin, cfg.timeout_s + 5)
        if result_c and "timeout" not in result_c:
            lignes_ukp_bb.append({
                "instance": result_c["instance"],
                "n": probleme.n,
                "valeur": result_c["valeur"],
                "temps_s": result_c["temps_s"],
                "noeuds_generes": result_c["noeuds_generes"],
            })
            print(f"  [BB  ] {nom:<25} val={result_c['valeur']:<10} t={result_c['temps_s']:.4f}s")
        else:
            print(f"  [BB  ] {nom:<25} (binaire C indisponible ou timeout)")

    print("\n=== Benchmark TSP ===")
    for nom in instances_tsp:
        chemin = cfg.dossier_tests_tsp / nom
        if not chemin.exists():
            print(f"  [skip] {nom} (introuvable)")
            continue
        try:
            probleme = lire_tsp(chemin)
        except Exception as exc:
            print(f"  [erreur lecture] {nom}: {exc}")
            continue

        timeout_or = cfg.timeout_s if probleme.n <= 1000 else max(60.0, cfg.timeout_s)
        try:
            sol = resoudre_tsp(probleme, timeout_s=timeout_or)
            lignes_tsp_or.append({
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": sol.longueur,
                "temps_s": sol.temps_secondes,
                "noeuds_generes": -1,
                "statut": sol.statut,
            })
            print(f"  [OR  ] {nom:<25} long={sol.longueur:<10} t={sol.temps_secondes:.4f}s  ({sol.statut})")
        except Exception as exc:
            print(f"  [erreur OR-Tools] {nom}: {exc}")

        result_c = _executer_c(cfg.binaire_c, "tsp", chemin, cfg.timeout_s + 5)
        if result_c and "timeout" not in result_c:
            lignes_tsp_bb.append({
                "instance": result_c["instance"],
                "n": probleme.n,
                "valeur": result_c["valeur"],
                "temps_s": result_c["temps_s"],
                "noeuds_generes": result_c["noeuds_generes"],
            })
            print(f"  [BB  ] {nom:<25} long={result_c['valeur']:<10} t={result_c['temps_s']:.4f}s")
        else:
            print(f"  [BB  ] {nom:<25} (binaire C indisponible ou timeout)")

    csv_ukp_bb = cfg.dossier_resultats / "ukp_branch_and_bound.csv"
    csv_ukp_or = cfg.dossier_resultats / "ukp_or_tools.csv"
    csv_tsp_bb = cfg.dossier_resultats / "tsp_branch_and_bound.csv"
    csv_tsp_or = cfg.dossier_resultats / "tsp_or_tools.csv"

    _ecrire_csv(csv_ukp_bb, lignes_ukp_bb,
                ["instance", "n", "valeur", "temps_s", "noeuds_generes"])
    _ecrire_csv(csv_ukp_or, lignes_ukp_or,
                ["instance", "n", "valeur", "temps_s", "noeuds_generes", "statut"])
    _ecrire_csv(csv_tsp_bb, lignes_tsp_bb,
                ["instance", "n", "valeur", "temps_s", "noeuds_generes"])
    _ecrire_csv(csv_tsp_or, lignes_tsp_or,
                ["instance", "n", "valeur", "temps_s", "noeuds_generes", "statut"])

    chemins_csv = {
        "ukp_bb": csv_ukp_bb,
        "ukp_or": csv_ukp_or,
        "tsp_bb": csv_tsp_bb,
        "tsp_or": csv_tsp_or,
    }

    if cfg.visualiser:
        chemin_panneau = cfg.dossier_resultats / "panneau_benchmark.png"
        tracer_panneau_benchmark(chemins_csv, chemin_panneau)
        print(f"\n-> Panneau de benchmark : {chemin_panneau}")

    print(f"\n-> CSV : {cfg.dossier_resultats}")
    return chemins_csv
