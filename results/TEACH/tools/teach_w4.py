#!/usr/bin/env python3
"""results/TEACH/tools/teach_w4.py — W4 decyzja K / K′ (PROMPT_TEACH_S1 §4 W4, reguła PRE_TEACH §6 S1; 0 bootów).

Wejście: results/TEACH/s1/czesci_K/ i czesci_K2/ (teach_w2.py, ten sam bieg w obu wariantach). Miary jak recon S0B
(results/TEACH_RECON2/tools/teach2_r5.stat, import READ-ONLY): na łatę S, M, J osobno „12 cięć” i „lot długi” — największy błąd
przyjętej poprawki, największa przerwa (z [cięcie, pierwsza] i [ostatnia, koniec misji]), liczba przerw > 1.15 s.
Reguła (zapisana z góry w PRE): K′ przyjęty ⇔ w każdej z 6 grup (3 łaty × {12 cięć, lot długi}) max błąd nie rośnie o więcej niż
0.02 m ∧ max przerwa nie rośnie ∧ liczba przerw > 1.15 s nie rośnie ∧ co najmniej jedna z dwóch ostatnich liczb gdzieś maleje.
Inaczej zostaje K (dobór z reconu). Wynik: results/TEACH/s1/w4_dobor.json i results/TEACH/s1/tor.json
({"tor": {...}, "sha256_toru": sha256 kanonicznego JSON}) — loty czytają wariant z tego pliku (harness/nadir_obs.py).
"""
import glob
import gzip
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH_RECON2/tools")]
import teach2_r5 as R5                                               # noqa: E402
from harness import teach_map as TM                                  # noqa: E402

S1 = os.path.join(ROOT, "results/TEACH/s1")
KLUCZ = "M4/K1_SIFT"
LOT_DL = "L_c10_s01"
TOL_ERR = 0.02


def miary(tag):
    W = [json.load(gzip.open(f, "rt")) for f in sorted(glob.glob(os.path.join(S1, f"czesci_{tag}", "*.json.gz")))]
    out = {}
    for lata in ("S", "M", "J"):
        for g, f in (("12_ciec", lambda w: w["lot"] != LOT_DL), ("lot_dlugi", lambda w: w["lot"] == LOT_DL)):
            ws = [w for w in W if w["lata"] == lata and f(w)]
            s = R5.stat([(w["klatki"][KLUCZ], w["t_ciecia"], w["t_konca"]) for w in ws])
            out[f"{lata}/{g}"] = {"n_lotow": len(ws), "blad_max": s["blad_max"], "blad_p95": s["blad_p95"], "udz_przyj": s["udz_przyj"],
                                  "przerwa_max": s["przerwa_max"], "przerwy_gt_115": s["przerwy_gt_115"],
                                  "przerwy_gt_115_lista": s["przerwy_gt_115_lista"]}
    return out


def main():
    a, b = miary("K"), miary("K2")
    grupy, zgoda, maleje = {}, True, False
    for kk in a:
        x, y = a[kk], b[kk]
        w = {"blad": y["blad_max"] - x["blad_max"] <= TOL_ERR + 1e-12, "przerwa": y["przerwa_max"] <= x["przerwa_max"] + 1e-9,
             "n_przerw": y["przerwy_gt_115"] <= x["przerwy_gt_115"]}
        m = y["przerwa_max"] < x["przerwa_max"] - 1e-9 or y["przerwy_gt_115"] < x["przerwy_gt_115"]
        grupy[kk] = {"K": {k: v for k, v in x.items() if k != "przerwy_gt_115_lista"},
                     "K′": {k: v for k, v in y.items() if k != "przerwy_gt_115_lista"},
                     "warunki": w, "maleje": m, "przerwy_K": x["przerwy_gt_115_lista"], "przerwy_K′": y["przerwy_gt_115_lista"]}
        zgoda = zgoda and all(w.values())
        maleje = maleje or m
    przyjety = zgoda and maleje
    wariant = "K′" if przyjety else "K"
    wyn = {"regula": "PRE_TEACH §6 S1: K′ ⇔ ∀ grupa: Δmax błąd ≤ 0.02 m ∧ max przerwa nie rośnie ∧ #przerw > 1.15 s nie rośnie; "
                     "∧ ∃ grupa: max przerwa albo #przerw > 1.15 s maleje",
           "grupy": grupy, "nic_nie_pogarsza": zgoda, "cos_maleje": maleje, "K2_przyjety": przyjety, "wariant": wariant}
    json.dump(wyn, open(os.path.join(S1, "w4_dobor.json"), "w"), ensure_ascii=False, indent=1)
    tor = {"wariant_K": wariant, "mapa": TM.WARIANT_MAPY, "cechy": TM.RODZAJ, "h_min": TM.H_MIN, "regula_przyjecia": "a12_geo0_g1.5",
           "tor_odniesienia": "results/TEACH_RECON2/tools/teach2.py", "sha256_teach2": TM.SHA_TEACH2,
           "decyzja": "results/TEACH/s1/w4_dobor.json"}
    json.dump({"tor": tor, "sha256_toru": TM.kan_sha(tor)}, open(os.path.join(S1, "tor.json"), "w"), ensure_ascii=False, indent=1)
    for kk, g in grupy.items():
        print(kk, "K", (g["K"]["blad_max"], g["K"]["przerwa_max"], g["K"]["przerwy_gt_115"]),
              "K′", (g["K′"]["blad_max"], g["K′"]["przerwa_max"], g["K′"]["przerwy_gt_115"]), g["warunki"], "maleje" if g["maleje"] else "")
    print("K′ przyjęty:", przyjety, "→ wariant", wariant)


if __name__ == "__main__":
    main()
