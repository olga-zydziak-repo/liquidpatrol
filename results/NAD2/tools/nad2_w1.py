#!/usr/bin/env python3
"""results/NAD2/tools/nad2_w1.py — PROMPT_NAD2_S1 §R W1: wierność (0 bootów).

(1) NOWY harness/nadir_fix.Rama z literą „NADIR1” (przełącznik jawny) odtwarza zapisane fx 16 bootów S4 w 100% klatek:
    ok, tryb, kosz, ids, d_ne, |Δp_fix| ≤ 1e-4 m.
(2) Kontrola krzyżowa: Rama z literą „NAD2” ≡ replay reconu NAD2 (results/NAD2_RECON/tools/nad2_r3.RamaV, wariant T1Z2C0)
    na tych samych klatkach (ok, tryb, kosz, Δ wewnętrzne ≤ 1e-9 m, zapis p_fix 4 cyfry ≤ 5e-5 m) — produkcja nowej litery = litera, na której policzono FREEZE.
(3) P5_nadir na starej fiksturze S2 (r01.proofs.p9_nadir_verify.prove_p5, bez zapisu certu) PASS bez zmian.
Wyjście: results/NAD2/s1/w1_wiernosc.json.
"""
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools")]
import nad2_dane as D
import nad2_r3 as R3
from harness import nadir_fix as NF

OUT = os.path.join(ROOT, "results/NAD2/s1")


def main():
    os.makedirs(OUT, exist_ok=True)
    wyn = {"stara_litera": {}, "nad2_vs_recon": {}}
    for n in D.CIECIA_S4 + D.NOM_S4:
        b = D.Boot(n)
        r_old, r_new, r_rec = NF.Rama(litera="NADIR1"), NF.Rama(litera="NAD2"), R3.RamaV("T1", "Z2", "C0")
        nk = zg = 0
        dmax = 0.0
        nk2 = zg2 = 0
        d2max = 0.0
        for r in b.nf:
            fx0 = r["fx"]
            fx = r_old.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            nk += 1
            ok = fx["ok"] == fx0["ok"] and abs(r_old.d_ne[0] - fx0["d_ne"][0]) <= 1e-4 and abs(r_old.d_ne[1] - fx0["d_ne"][1]) <= 1e-4
            if ok and fx["ok"]:
                dd = max(abs(fx["p_fix_ne"][k] - fx0["p_fix_ne"][k]) for k in range(2))
                dmax = max(dmax, dd)
                ok = fx["tryb"] == fx0["tryb"] and fx["kosz"] == fx0["kosz"] and sorted(fx["ids"]) == sorted(fx0["ids"]) and dd <= 1e-4
            ok = ok and "litera" not in fx
            zg += int(ok)
            a = r_new.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            c = r_rec.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            nk2 += 1
            ok2 = a["ok"] == c["ok"]
            if ok2 and a["ok"]:
                dd = max(abs(r_new.d_ne[k] - r_rec.d_ne[k]) for k in range(2))             # stan wewnętrzny (bez zaokrąglenia)
                d2max = max(d2max, dd)
                ok2 = (a["tryb"] == c["tryb"] and a["kosz"] == c["kosz"] and dd <= 1e-9
                       and max(abs(a["p_fix_ne"][k] - c["p_fix_ne"][k]) for k in range(2)) <= 5e-5)   # zapis: 4 cyfry
            zg2 += int(ok2)
        wyn["stara_litera"][n] = {"klatki": nk, "zgodne": zg, "max_dp_fix_m": round(dmax, 7)}
        wyn["nad2_vs_recon"][n] = {"klatki": nk2, "zgodne": zg2, "max_dp_fix_m": d2max}
        print(n, nk, zg, round(dmax, 7), "| NAD2≡recon", zg2, "/", nk2, flush=True)
    wyn["W1_stara_litera_100proc"] = all(v["klatki"] == v["zgodne"] for v in wyn["stara_litera"].values())
    wyn["NAD2_rowna_recon_100proc"] = all(v["klatki"] == v["zgodne"] for v in wyn["nad2_vs_recon"].values())
    from r01.proofs import p9_nadir_verify as P
    ok, mism, pt, cov, missing, n, fx = P.prove_p5()
    wyn["P5_nadir_stara_fikstura"] = {"PASS": bool(ok), "rozbieznosci": len(mism), "passthrough": len(pt), "brak_pokrycia": missing,
                                      "ticki": n}
    print("P5_nadir:", wyn["P5_nadir_stara_fikstura"])
    json.dump(wyn, open(os.path.join(OUT, "w1_wiernosc.json"), "w"), ensure_ascii=False, indent=1)
    print("W1:", wyn["W1_stara_litera_100proc"], "NAD2≡recon:", wyn["NAD2_rowna_recon_100proc"])


if __name__ == "__main__":
    main()
