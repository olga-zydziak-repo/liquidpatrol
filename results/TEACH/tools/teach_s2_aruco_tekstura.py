#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_aruco_tekstura.py — znalezisko próby na sucho S2 (0 bootów): detektor znaczników bootu (harness/nadir_obs.py:
cv2.aruco DICT_4X4_50, parametry domyślne, bez lustra — NADIR_FLIP=0 jak w teach_boot.sh) na kadrach reconu TEACH (render terenu łat S, M, J
przy pozie GT, results/TEACH_RECON/r2_klatki.json.gz — serie przed i po, 13 lotów). Liczy detekcje na samym terenie (świat bez znaczników):
liczba, kadry, ID, bok [px]. Wyjście: results/TEACH/s2/dryrun/aruco_tekstura.json.
ANEKS_TEACH-2 §4.3 (TEACH-2A): każda detekcja niesie uv; po skanie zgodność z manifestem (teach_analyze.zgodnosc_detekcji: ID z manifestu
v2, punkt gruntu środka z pozy GT kadru ≤ 1.0 m od pozycji ID) — oczekiwane 0 zgodnych."""
from multiprocessing import Pool
import numpy as np
import gzip, json, os, sys
ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/ORTO_RECON/tools")]
import cv2, orto_r2 as R2
D, P = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters_create()
K = json.load(gzip.open(os.path.join(ROOT, "results/TEACH_RECON/r2_klatki.json.gz"), "rt"))

def zad(arg):
    lata, i0, i1 = arg
    cv2.setNumThreads(1)
    kam = R2.Kam(R2.kamera()); teren = cv2.imread(os.path.join(ROOT, f"results/TEACH_RECON/dane/{lata}_2024-04-27.png"))
    out = []
    for k in K[i0:i1]:
        C, Rk = kam.poza(np.array(k["gt_p"]), R2.rotm(k["gt_q"]))
        g = cv2.cvtColor(kam.renderuj(teren, 0.05, C, Rk)[0], cv2.COLOR_BGR2GRAY)
        c, ids, _ = cv2.aruco.detectMarkers(g, D, parameters=P)
        if ids is not None:
            for cc, i in zip(c, ids.ravel()):
                cc = cc.reshape(4, 2)
                out.append({"lot": k["lot"], "seria": k["seria"], "sim": k["sim"], "id": int(i),
                            "uv": [round(float(x), 2) for x in cc.mean(0)], "gt_p": k["gt_p"], "gt_q": k["gt_q"],
                            "bok": round(min(float(np.linalg.norm(cc[j] - cc[(j + 1) % 4])) for j in range(4)), 2)})
    return lata, i1 - i0, out

if __name__ == "__main__":
    n = len(K); ch = [(l, a, min(a + 500, n)) for l in "SMJ" for a in range(0, n, 500)]
    res = {l: {"klatki": 0, "det": []} for l in "SMJ"}
    with Pool(8) as p:
        for l, m, o in p.imap_unordered(zad, ch):
            res[l]["klatki"] += m; res[l]["det"] += o
    for l, v in res.items():
        b = [d["bok"] for d in v["det"]]
        print(l, "klatki", v["klatki"], "detekcji", len(b), "klatek z detekcją", len({(d["lot"], d["sim"]) for d in v["det"]}),
              "bok max", max(b) if b else None, "bok>=16:", sum(x >= 16 for x in b), "id", sorted({d["id"] for d in v["det"]}))
        per = {}
        for d in v["det"]:
            per[d["lot"]] = per.get(d["lot"], 0) + 1
        print("  per lot", per)
    sys.path.insert(0, os.path.join(ROOT, "results/TEACH/tools"))
    import teach_analyze as A
    for l, v in res.items():
        poz = {(d["lot"], d["sim"]): (d["gt_p"], d["gt_q"]) for d in v["det"]}
        wp = {}
        for d in v["det"]:
            wp.setdefault((d["lot"], d["sim"]), []).append({"id": d["id"], "uv": d["uv"], "bok": d["bok"]})
        zg = {"surowe": {"n": 0}, "zgodne": {"n": 0, "lista": []}}
        for (lot, sim), det in wp.items():
            z = A.zgodnosc_detekcji([(sim, det)], lambda t, _k=(lot, sim): poz[_k])
            zg["surowe"]["n"] += z["surowe"]["n"]; zg["zgodne"]["n"] += z["zgodne"]["n"]
            zg["zgodne"]["lista"] += [{"lot": lot, **x} for x in z["zgodne"]["lista"]]
        v["zgodnosc_z_manifestem"] = zg
        print(l, "surowe", zg["surowe"]["n"], "ZGODNE Z MANIFESTEM", zg["zgodne"]["n"], zg["zgodne"]["lista"][:5])
    print("RAZEM kadry", sum(v["klatki"] for v in res.values()), "surowe", sum(len(v["det"]) for v in res.values()),
          "zgodne", sum(v["zgodnosc_z_manifestem"]["zgodne"]["n"] for v in res.values()))
    json.dump(res, open(os.path.join(ROOT, "results/TEACH/s2/dryrun/aruco_tekstura.json"), "w"))
