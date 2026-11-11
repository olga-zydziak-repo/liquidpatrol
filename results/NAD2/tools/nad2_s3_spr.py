#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s3_spr.py — sprawdziany przyrządu per boot S3 NADIR-II (PROMPT_NAD2_S3 §R: „(s1) wierność na żywo 100%,
(s2) tabela w locie 100%; poniżej 100% ⇒ STOP”). Liczy results/NAD2/tools/nad2_s2_spr.sprawdz (READ-ONLY, ten sam kod co smoke)
i sądzi per rodzaj bootu:
  cięcie  — (s1), (s2), (s3) dokładnie jak w smoke (ticki utraty > 0);
  nominał — (s1) jak w smoke; (s2) zero niezgodnych R_k i 100% poprawek w datagramach z trybem i literą NAD2 (ticki utraty
            w nominale są sprawą (B5), nie przyrządu); (s3) r_est = |p_EKF| w 100% ticków NOMINAL.
Wyjście: <boot>/sprawdziany_s3.json (obok sprawdziany_s2.json z modułu smoke). Użycie: nad2_s3_spr.py <katalog_bootu> [nominal]
"""
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/NAD2/tools"), ROOT]
import nad2_s2_spr as SPR                          # READ-ONLY


def sprawdz(d, nominal):
    s = SPR.sprawdz(d)
    if nominal:
        s1, s2, s3 = s["s1"], s["s2"], s["s3"]
        ok = {"s1": s1["ok"],
              "s2": s2["R_k_niezgodne"] == 0 and s2["poprawki_w_obs"] > 0 and s2["poprawki_bez_trybu_lub_litery"] == 0,
              "s3": s3["ticki_nominal"] > 0 and s3["zle_nominal"] == 0 and s3["zle_utrata"] == 0}
    else:
        ok = {k: s[k]["ok"] for k in ("s1", "s2", "s3")}
    out = {"rodzaj": "nominal" if nominal else "ciecie", "ok": ok, "szczegoly": s,
           "przyrzad_ok": ok["s1"] and ok["s2"]}      # STOP-owe wg §R: (s1), (s2)
    json.dump(out, open(os.path.join(d, "sprawdziany_s3.json"), "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    r = sprawdz(sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "nominal")
    print(json.dumps({"rodzaj": r["rodzaj"], "ok": r["ok"], "przyrzad_ok": r["przyrzad_ok"]}))
