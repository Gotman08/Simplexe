#!/usr/bin/env bash
# Compare le benchmark courant (Resultats/benchmarks_pousses/) avec le precedent
# (Resultats/benchmarks_pousses_avant/) pour mettre en evidence les changements
# de performance dus aux modifications de code (ex : rewrite des boucles).
set -e
cd "$(dirname "$0")/.."
PY="OR-Tools/.venv/bin/python3"

"$PY" - <<'PY'
import csv
import statistics
from pathlib import Path

racine = Path("/mnt/c/Users/nicol/Desktop/Simplexe").resolve()
nouv = racine / "Resultats" / "benchmarks_pousses"
anc  = racine / "Resultats" / "benchmarks_pousses_avant"

def lire_brut(chemin: Path) -> dict[tuple[str, str], list[dict]]:
    bucket: dict[tuple[str, str], list[dict]] = {}
    if not chemin.exists():
        return bucket
    with open(chemin, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["instance"], row["methode"])
            try:
                row["temps_s"] = float(row.get("temps_s", 0) or 0)
                row["valeur"] = int(float(row.get("valeur", 0) or 0))
            except (ValueError, TypeError):
                row["temps_s"] = 0.0
                row["valeur"] = 0
            bucket.setdefault(key, []).append(row)
    return bucket

def median_ok(runs: list[dict]) -> tuple[float, int]:
    """Retourne (mediane temps, valeur) sur les runs OK."""
    ok = [r for r in runs if r.get("statut") in ("OK", "OPTIMAL", "OPTIMAL_OU_FAISABLE")]
    if not ok:
        return (0.0, 0)
    t = statistics.median([r["temps_s"] for r in ok])
    v = max(r["valeur"] for r in ok)
    return (t, v)

print("=" * 110)
print("  COMPARAISON BENCHMARK : avant (←) vs apres modifications (→)")
print("=" * 110)

for type_pb in ("ukp", "tsp"):
    print(f"\n>>> {type_pb.upper()}")
    bucket_anc  = lire_brut(anc / f"{type_pb}_brut.csv")
    bucket_nouv = lire_brut(nouv / f"{type_pb}_brut.csv")

    instances_communes = sorted(set(k[0] for k in bucket_anc) & set(k[0] for k in bucket_nouv))
    print(f"  {'Instance':<22} {'Methode':<12} {'Avant (s)':<12} {'Apres (s)':<12} {'Δ %':<10} {'val avant':<12} {'val apres':<10} {'changement':<12}")
    print("  " + "-" * 108)

    for inst in instances_communes:
        for methode in ("OR-Tools", "B&B (C)"):
            key = (inst, methode)
            t_a, v_a = median_ok(bucket_anc.get(key, []))
            t_n, v_n = median_ok(bucket_nouv.get(key, []))
            if t_a == 0 and t_n == 0:
                continue
            delta = ((t_n - t_a) / t_a * 100.0) if t_a > 0 else float("inf")
            delta_str = f"{delta:+.1f}%" if abs(delta) < 10000 else "—"
            chg = ""
            if v_a != v_n and v_a and v_n:
                chg = f"val ! ({v_a}→{v_n})"
            elif t_a > 0 and t_n > 0:
                if delta > 20:    chg = "+ lent"
                elif delta < -20: chg = "+ rapide"
                else:             chg = "stable"
            else:
                chg = "nouveau" if t_a == 0 else "perdu"
            print(f"  {inst:<22} {methode:<12} {t_a:<12.4f} {t_n:<12.4f} {delta_str:<10} {v_a:<12} {v_n:<10} {chg:<12}")

print("\n" + "=" * 110)
print("  Note : Δ % > 0 ⇒ benchmark plus lent apres modifications.")
print("         Δ % < 0 ⇒ benchmark plus rapide apres modifications.")
print("=" * 110)
PY
