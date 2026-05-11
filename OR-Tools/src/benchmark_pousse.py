from __future__ import annotations

import csv
import os
import platform
import resource
import shlex
import statistics
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .parsers import lire_tsp, lire_ukp
from .timer import Chronometre
from .tsp_solver import resoudre_tsp
from .ukp_solver import resoudre_ukp
from .visualization_pousse import (
    tracer_boxplot_temps,
    tracer_panneau_principal,
    tracer_performance_profile,
    tracer_qualite_relative,
    tracer_scaling_avec_erreurs,
)

@dataclass
class CategorieInstance:
    nom: str
    fichiers: list[str]
    timeout_s: float
    reps: int

@dataclass
class ConfigBenchmarkPousse:
    racine: Path
    binaire_c: Path
    dossier_tests_ukp: Path
    dossier_tests_tsp: Path
    dossier_resultats: Path
    inclure_grands: bool = True
    reps_petits: int = 5
    reps_moyens: int = 3
    reps_grands: int = 2
    visualiser: bool = True
    phases: tuple[str, ...] = ("ukp_petits", "ukp_moyens", "ukp_grands",
                                "tsp_petits", "tsp_moyens", "tsp_grands")
    timeout_bb_grands: float = 30.0
    timeout_or_grands: float = 90.0
    accumuler: bool = False

def _categorie_ukp(cfg: ConfigBenchmarkPousse) -> list[CategorieInstance]:
    cats = [
        CategorieInstance(
            nom="ukp_petits",
            fichiers=["prob_sac_1.txt", "prob_sac_2.txt", "prob_sac_3.txt",
                      "prob_sac_4.txt", "prob_sac_5.txt", "prob_sac_10.txt"],
            timeout_s=30.0,
            reps=cfg.reps_petits,
        ),
        CategorieInstance(
            nom="ukp_moyens",
            fichiers=["prob_sac_20.txt", "prob_sac_25.txt", "prob_sac_30.txt"],
            timeout_s=60.0,
            reps=cfg.reps_moyens,
        ),
    ]
    if cfg.inclure_grands:
        cats.append(CategorieInstance(
            nom="ukp_grands",
            fichiers=["prob_sac_2000.txt", "prob_sac_20000.txt"],
            timeout_s=cfg.timeout_or_grands,
            reps=cfg.reps_grands,
        ))
    return cats

def _categorie_tsp(cfg: ConfigBenchmarkPousse) -> list[CategorieInstance]:
    cats = [
        CategorieInstance(
            nom="tsp_petits",
            fichiers=["graphe_12.txt", "graphe_13.txt", "graphe_14.txt", "graphe_15.txt",
                      "pd_5.tsp", "pd_11.tsp", "pd_15.tsp"],
            timeout_s=5.0,
            reps=cfg.reps_petits,
        ),
        CategorieInstance(
            nom="tsp_moyens",
            fichiers=["pd_18.tsp", "pd_20.tsp", "pd_22.tsp"],
            timeout_s=15.0,
            reps=cfg.reps_moyens,
        ),
    ]
    if cfg.inclure_grands:
        cats.append(CategorieInstance(
            nom="tsp_grands",
            fichiers=["pd_59.tsp", "canada_4663.tsp", "usa_13509.tsp"],
            timeout_s=cfg.timeout_or_grands,
            reps=cfg.reps_grands,
        ))
    return cats

def _est_grande_categorie(nom: str) -> bool:
    return nom.endswith("_grands")

def _peak_rss_kb() -> int:

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":
        return rss // 1024
    return rss

def _peak_rss_kb_subprocess(child_rusage: Optional[resource.struct_rusage]) -> int:
    if child_rusage is None:
        return 0
    rss = child_rusage.ru_maxrss
    if platform.system() == "Darwin":
        return rss // 1024
    return rss

def _executer_c(binaire: Path, probleme: str, fichier: Path,
                timeout_s: float) -> Optional[dict]:

    if not binaire.exists():
        return None
    cmd = [str(binaire), "--probleme", probleme, "--fichier", str(fichier), "--silent"]
    try:

        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"timeout": True}
    if proc.returncode != 0:
        return {"erreur": True, "stderr": (proc.stderr or "")[:200]}
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
            "lp_racine": float(champs[5]) if len(champs) > 5 else 0.0,
        }
    if probleme == "tsp" and len(champs) >= 4:
        return {
            "instance": champs[0],
            "valeur": int(champs[1]),
            "temps_s": float(champs[2]),
            "noeuds_generes": int(champs[3]),
        }
    return None

def _resoudre_ukp_avec_memoire(probleme, timeout_s: float) -> dict:
    rss_avant = _peak_rss_kb()
    sol = resoudre_ukp(probleme, timeout_s=timeout_s)
    rss_apres = _peak_rss_kb()
    return {
        "instance": probleme.nom,
        "n": probleme.n,
        "valeur": sol.utilite_totale,
        "volume": sol.volume_total,
        "temps_s": sol.temps_secondes,
        "noeuds_generes": max(sol.n_noeuds, 0),
        "memoire_kb": max(rss_apres - rss_avant, 0),
        "statut": sol.statut,
    }

def _resoudre_tsp_avec_memoire(probleme, timeout_s: float) -> dict:
    rss_avant = _peak_rss_kb()
    sol = resoudre_tsp(probleme, timeout_s=timeout_s)
    rss_apres = _peak_rss_kb()
    return {
        "instance": probleme.nom,
        "n": probleme.n,
        "valeur": sol.longueur,
        "temps_s": sol.temps_secondes,
        "noeuds_generes": -1,
        "memoire_kb": max(rss_apres - rss_avant, 0),
        "statut": sol.statut,
    }

def _executer_runs(
    cfg: ConfigBenchmarkPousse,
    type_probleme: str,
    fichier: Path,
    timeout_s: float,
    reps: int,
    timeout_bb: Optional[float] = None,
) -> list[dict]:
    if timeout_bb is None:
        timeout_bb = timeout_s + 5

    lignes: list[dict] = []
    if type_probleme == "ukp":
        probleme = lire_ukp(fichier)
    else:
        probleme = lire_tsp(fichier)

    for r in range(1, reps + 1):
        ligne_or = (_resoudre_ukp_avec_memoire(probleme, timeout_s)
                    if type_probleme == "ukp"
                    else _resoudre_tsp_avec_memoire(probleme, timeout_s))
        ligne_or["methode"]  = "OR-Tools"
        ligne_or["rep"]      = r
        ligne_or["timeout_s"] = timeout_s
        lignes.append(ligne_or)

        result_c = _executer_c(cfg.binaire_c, type_probleme, fichier, timeout_bb)
        ligne_bb: dict
        if result_c is None:
            ligne_bb = {
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": 0,
                "temps_s": 0.0,
                "noeuds_generes": 0,
                "memoire_kb": 0,
                "statut": "BINAIRE_C_INTROUVABLE",
            }
        elif result_c.get("timeout"):
            ligne_bb = {
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": 0,
                "temps_s": timeout_bb,
                "noeuds_generes": 0,
                "memoire_kb": 0,
                "statut": "TIMEOUT",
            }
        elif result_c.get("erreur"):
            ligne_bb = {
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": 0,
                "temps_s": 0.0,
                "noeuds_generes": 0,
                "memoire_kb": 0,
                "statut": f"ERREUR ({result_c.get('stderr', '')[:50]})",
            }
        else:
            ligne_bb = {
                "instance": probleme.nom,
                "n": probleme.n,
                "valeur": result_c["valeur"],
                "temps_s": result_c["temps_s"],
                "noeuds_generes": result_c["noeuds_generes"],
                "memoire_kb": 0,
                "statut": "OK",
                "lp_racine": result_c.get("lp_racine", 0.0),
            }
        ligne_bb["methode"]   = "B&B (C)"
        ligne_bb["rep"]       = r
        ligne_bb["timeout_s"] = timeout_s
        lignes.append(ligne_bb)

        nom_cas = probleme.nom
        v_or, v_bb = ligne_or["valeur"], ligne_bb["valeur"]
        t_or, t_bb = ligne_or["temps_s"], ligne_bb["temps_s"]
        st_bb = ligne_bb["statut"]
        print(f"  [{r}/{reps}] {nom_cas:<22} | OR={v_or:<10} ({t_or:6.3f}s) "
              f"| BB={v_bb:<10} ({t_bb:6.3f}s, {st_bb})", flush=True)

    return lignes

def _agreger(lignes: list[dict], cle: str) -> list[dict]:
    bucket: dict[tuple[str, str], list[dict]] = {}
    for ligne in lignes:
        key = (ligne["instance"], ligne["methode"])
        bucket.setdefault(key, []).append(ligne)

    agregats: list[dict] = []
    for (instance, methode), runs in bucket.items():
        valeurs = [r[cle] for r in runs if isinstance(r.get(cle), (int, float))]
        if not valeurs:
            continue
        n_ok = sum(1 for r in runs if r.get("statut") in ("OK", "OPTIMAL", "OPTIMAL_OU_FAISABLE"))
        agregats.append({
            "instance": instance,
            "methode":  methode,
            "n":        runs[0]["n"],
            "reps":     len(runs),
            "n_ok":     n_ok,
            "median":   statistics.median(valeurs),
            "min":      min(valeurs),
            "max":      max(valeurs),
            "stddev":   statistics.pstdev(valeurs) if len(valeurs) > 1 else 0.0,
            "valeur_obj_median": statistics.median([r["valeur"] for r in runs]) if runs else 0,
        })
    return agregats

def _ecrire_csv(chemin: Path, lignes: Iterable[dict], champs: list[str]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=champs)
        writer.writeheader()
        for ligne in lignes:
            writer.writerow({k: ligne.get(k, "") for k in champs})

def _charger_csv(chemin: Path) -> list[dict]:
    if not chemin.exists():
        return []
    out: list[dict] = []
    with open(chemin, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for k in ("n", "rep", "valeur", "noeuds_generes", "memoire_kb"):
                if k in row and row[k] != "":
                    try:
                        row[k] = int(float(row[k]))
                    except (ValueError, TypeError):
                        pass
            for k in ("temps_s", "timeout_s"):
                if k in row and row[k] != "":
                    try:
                        row[k] = float(row[k])
                    except (ValueError, TypeError):
                        pass
            out.append(row)
    return out

def _instances_dejà(lignes: list[dict]) -> set[tuple[str, str]]:
    return {(l["instance"], l["methode"]) for l in lignes
            if l.get("instance") and l.get("methode")}

def _dp_ukp_optimal(p) -> int:

    W = p.capacite
    f = [0] * (W + 1)
    for w in range(1, W + 1):
        best = f[w - 1]
        for j in range(p.n):
            v = p.volumes[j]
            if v <= w and f[w - v] + p.utilites[j] > best:
                best = f[w - v] + p.utilites[j]
        f[w] = best
    return f[W]

def auditer_qualite(lignes_ukp: list[dict], lignes_tsp: list[dict],
                    dossier_tests_ukp: Path) -> list[str]:

    from .parsers import lire_ukp

    messages: list[str] = []
    print("\n=== AUDIT QUALITE ===")

    bucket_ukp: dict[str, dict[str, list[int]]] = {}
    for l in lignes_ukp:
        d = bucket_ukp.setdefault(l["instance"], {"B&B (C)": [], "OR-Tools": []})
        if l.get("statut") in ("OK", "OPTIMAL", "OPTIMAL_OU_FAISABLE"):
            d.setdefault(l["methode"], []).append(l["valeur"])

    for inst, methodes in sorted(bucket_ukp.items()):
        v_bb = max(methodes.get("B&B (C)", []) or [0])
        v_or = max(methodes.get("OR-Tools", []) or [0])
        if v_bb == 0 and v_or == 0:
            continue
        if v_bb == 0:
            print(f"  [INFO] {inst}: BB n'a pas resolu (verifier le timeout).")
            continue
        if v_or == 0:
            print(f"  [INFO] {inst}: OR-Tools n'a pas resolu.")
            continue
        if v_bb == v_or:
            messages.append(f"OK    | {inst}: BB={v_bb} == OR={v_or}")
        elif v_bb > v_or:
            msg = f"⚠ WARN | {inst}: BB={v_bb} > OR={v_or} (CBC sous-optimal)"
            messages.append(msg)
            print(f"  {msg}")
        else:
            msg = f"❌ ERR  | {inst}: BB={v_bb} < OR={v_or} (BB BUGGY?)"
            messages.append(msg)
            print(f"  {msg}")

    print("\n  Verification DP exhaustive (petites UKP) :")
    for inst, methodes in sorted(bucket_ukp.items()):
        chemin = dossier_tests_ukp / f"{inst}.txt"
        if not chemin.exists():
            continue
        try:
            p = lire_ukp(chemin)
        except Exception:
            continue

        if p.n * p.capacite > 10_000_000:
            continue
        opt_dp = _dp_ukp_optimal(p)
        v_bb = max(methodes.get("B&B (C)", []) or [0])
        v_or = max(methodes.get("OR-Tools", []) or [0])
        if v_bb and v_bb != opt_dp:
            msg = f"❌ ERR  | {inst}: BB={v_bb} != DP={opt_dp} (BB devrait etre exact !)"
            messages.append(msg)
            print(f"    {msg}")
        if v_or and v_or != opt_dp:
            msg = f"⚠ WARN | {inst}: OR-Tools={v_or} != DP={opt_dp} (statut=OPTIMAL ⇒ bug solveur)"
            messages.append(msg)
            print(f"    {msg}")
        if v_bb == opt_dp and v_or == opt_dp:
            print(f"    OK   | {inst}: BB={v_bb} == OR={v_or} == DP={opt_dp}")

    bucket_tsp: dict[str, dict[str, list[int]]] = {}
    for l in lignes_tsp:
        d = bucket_tsp.setdefault(l["instance"], {"B&B (C)": [], "OR-Tools": []})
        if l.get("statut") in ("OK", "OPTIMAL", "OPTIMAL_OU_FAISABLE"):
            d.setdefault(l["methode"], []).append(l["valeur"])

    print("\n  Verification TSP cross-methode :")
    for inst, methodes in sorted(bucket_tsp.items()):
        v_bb = min(methodes.get("B&B (C)", []) or [10**12])
        v_or = min(methodes.get("OR-Tools", []) or [10**12])
        if v_bb >= 10**12 or v_or >= 10**12:
            continue
        if v_bb == v_or:
            print(f"    OK   | {inst}: longueur = {v_bb}")
        else:
            msg = f"⚠ WARN | {inst}: BB={v_bb} ≠ OR={v_or}"
            messages.append(msg)
            print(f"    {msg}")

    n_warn = sum(1 for m in messages if m.startswith("⚠"))
    n_err = sum(1 for m in messages if m.startswith("❌"))
    n_ok = sum(1 for m in messages if m.startswith("OK"))
    print(f"\n  Recap : {n_ok} OK, {n_warn} WARNING, {n_err} ERROR")
    return messages

def lancer_benchmark_pousse(cfg: ConfigBenchmarkPousse) -> dict[str, Path]:
    cfg.dossier_resultats.mkdir(parents=True, exist_ok=True)

    print("============================================================")
    print(f"  BENCHMARK EXHAUSTIF — {platform.node()} ({platform.system()})")
    print(f"  Inclure grands : {cfg.inclure_grands}")
    print(f"  Repetitions    : petits={cfg.reps_petits}, moyens={cfg.reps_moyens}, "
          f"grands={cfg.reps_grands}")
    print(f"  Binaire C      : {cfg.binaire_c} (existe={cfg.binaire_c.exists()})")
    print("============================================================")
    print()

    lignes_ukp: list[dict] = []
    lignes_tsp: list[dict] = []

    if cfg.accumuler:
        lignes_ukp.extend(_charger_csv(cfg.dossier_resultats / "ukp_brut.csv"))
        lignes_tsp.extend(_charger_csv(cfg.dossier_resultats / "tsp_brut.csv"))
        deja = _instances_dejà(lignes_ukp + lignes_tsp)
        print(f"  Mode accumulation : {len(deja)} (instance, methode) deja presents.")
    else:
        deja = set()

    print(">>> UKP")
    for cat in _categorie_ukp(cfg):
        if cat.nom not in cfg.phases:
            continue
        timeout_bb = cfg.timeout_bb_grands if _est_grande_categorie(cat.nom) else cat.timeout_s + 5
        print(f"\n--- Categorie {cat.nom} (OR={cat.timeout_s}s, BB={timeout_bb}s, reps={cat.reps}) ---")
        for nom in cat.fichiers:
            chemin = cfg.dossier_tests_ukp / nom
            if not chemin.exists():
                print(f"  [skip] {nom} introuvable")
                continue
            inst_nom = chemin.stem
            if (inst_nom, "OR-Tools") in deja and (inst_nom, "B&B (C)") in deja:
                print(f"  [deja fait] {nom}")
                continue
            print(f" instance {nom} :")
            try:
                lignes_ukp.extend(_executer_runs(cfg, "ukp", chemin,
                                                  cat.timeout_s, cat.reps, timeout_bb))
            except Exception as exc:
                print(f"  [erreur] {nom}: {exc}")

    print("\n>>> TSP")
    for cat in _categorie_tsp(cfg):
        if cat.nom not in cfg.phases:
            continue
        timeout_bb = cfg.timeout_bb_grands if _est_grande_categorie(cat.nom) else cat.timeout_s + 5
        print(f"\n--- Categorie {cat.nom} (OR={cat.timeout_s}s, BB={timeout_bb}s, reps={cat.reps}) ---")
        for nom in cat.fichiers:
            chemin = cfg.dossier_tests_tsp / nom
            if not chemin.exists():
                print(f"  [skip] {nom} introuvable")
                continue
            inst_nom = chemin.stem
            if (inst_nom, "OR-Tools") in deja and (inst_nom, "B&B (C)") in deja:
                print(f"  [deja fait] {nom}")
                continue
            print(f" instance {nom} :")
            try:
                lignes_tsp.extend(_executer_runs(cfg, "tsp", chemin,
                                                  cat.timeout_s, cat.reps, timeout_bb))
            except Exception as exc:
                print(f"  [erreur] {nom}: {exc}")

    champs_brut = ["instance", "n", "methode", "rep", "valeur", "temps_s",
                   "noeuds_generes", "memoire_kb", "statut", "timeout_s", "lp_racine"]
    csv_ukp_brut = cfg.dossier_resultats / "ukp_brut.csv"
    csv_tsp_brut = cfg.dossier_resultats / "tsp_brut.csv"
    _ecrire_csv(csv_ukp_brut, lignes_ukp, champs_brut)
    _ecrire_csv(csv_tsp_brut, lignes_tsp, champs_brut)

    champs_agrege = ["instance", "methode", "n", "reps", "n_ok",
                     "median", "min", "max", "stddev", "valeur_obj_median"]
    csv_ukp_agg = cfg.dossier_resultats / "ukp_agrege_temps.csv"
    csv_tsp_agg = cfg.dossier_resultats / "tsp_agrege_temps.csv"
    _ecrire_csv(csv_ukp_agg, _agreger(lignes_ukp, "temps_s"), champs_agrege)
    _ecrire_csv(csv_tsp_agg, _agreger(lignes_tsp, "temps_s"), champs_agrege)

    print("\n=== Ecriture des CSV terminee ===")
    print(f"  Brut UKP   : {csv_ukp_brut}")
    print(f"  Brut TSP   : {csv_tsp_brut}")
    print(f"  Agrege UKP : {csv_ukp_agg}")
    print(f"  Agrege TSP : {csv_tsp_agg}")

    figures: dict[str, Path] = {}
    if cfg.visualiser:
        print("\n=== Generation des figures ===")
        figures["panneau"] = tracer_panneau_principal(
            lignes_ukp, lignes_tsp,
            cfg.dossier_resultats / "panneau_principal.png",
        )
        figures["boxplot_ukp"] = tracer_boxplot_temps(
            lignes_ukp, "UKP",
            cfg.dossier_resultats / "boxplot_temps_ukp.png",
        )
        figures["boxplot_tsp"] = tracer_boxplot_temps(
            lignes_tsp, "TSP",
            cfg.dossier_resultats / "boxplot_temps_tsp.png",
        )
        figures["scaling_ukp"] = tracer_scaling_avec_erreurs(
            lignes_ukp, "UKP",
            cfg.dossier_resultats / "scaling_ukp.png",
        )
        figures["scaling_tsp"] = tracer_scaling_avec_erreurs(
            lignes_tsp, "TSP",
            cfg.dossier_resultats / "scaling_tsp.png",
        )
        figures["qualite"] = tracer_qualite_relative(
            lignes_ukp, lignes_tsp,
            cfg.dossier_resultats / "qualite_relative.png",
        )
        figures["perf_profile"] = tracer_performance_profile(
            lignes_ukp, lignes_tsp,
            cfg.dossier_resultats / "performance_profile.png",
        )
        for nom, chemin in figures.items():
            print(f"  {nom:<14} : {chemin}")

    auditer_qualite(lignes_ukp, lignes_tsp, cfg.dossier_tests_ukp)

    return {
        "ukp_brut": csv_ukp_brut,
        "tsp_brut": csv_tsp_brut,
        "ukp_agrege": csv_ukp_agg,
        "tsp_agrege": csv_tsp_agg,
        **figures,
    }
