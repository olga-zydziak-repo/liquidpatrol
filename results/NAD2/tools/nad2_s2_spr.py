#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s2_spr.py — sprawdziany mechaniczne lotu C smoke NAD2 (PROMPT_NAD2_S2 §R (s1)–(s3)).

(s1) wierność na żywo: harness/nadir_fix.Rama(litera="NAD2") na zapisanych klatkach nf (nadir_obs.jsonl, sekwencyjnie) odtwarza
     zapisane fx w 100%: ok, tryb, koszyk, |Δp_fix| ≤ 1e-4 m, d_ne ≤ 1e-4 m; oraz każda przyjęta poprawka w logu producenta niesie
     tryb i literę NAD2.
(s2) tabela w locie: w 100% ticków utraty (rama.jsonl, ph ∈ {KONT, KONT_REFUSE}, przedział zdefiniowany) R_k z logu =
     round(r_nad2(przedział, koszyk, tryb), 3); każda poprawka przyjęta w obs ramy (datagram u konsumenta) niesie tryb i literę.
(s3) rama: r_est osłony (nad2.r_est) = |p_corr| (≤ 1e-3 m) w 100% ticków utraty i = |p_EKF| w 100% ticków NOMINAL; pierwszy tick
     utraty już w ramie poprawionej.
Wyjście: <boot>/sprawdziany_s2.json. Użycie: nad2_s2_spr.py <katalog_bootu>
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from harness import nadir_fix as NF
from r03 import nadir_shield as NS

UTRATA = ("KONT", "KONT_REFUSE")


def jl(p, typ=None):
    out = []
    for l in open(p):
        if typ is not None and f'"{typ}"' not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if typ is None or r.get("t") == typ:
            out.append(r)
    return out


def sprawdz(d):
    nf = [r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx" in r]
    rama = sorted(jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    out = {}
    # (s1)
    rv = NF.Rama(litera="NAD2")
    n = zg = bez_pol = 0
    dmax = 0.0
    zle = []
    for r in nf:
        fx0 = r["fx"]
        fx = rv.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
        n += 1
        ok = fx["ok"] == fx0["ok"] and max(abs(rv.d_ne[k] - fx0["d_ne"][k]) for k in range(2)) <= 1e-4
        if ok and fx["ok"]:
            dd = max(abs(fx["p_fix_ne"][k] - fx0["p_fix_ne"][k]) for k in range(2))
            dmax = max(dmax, dd)
            ok = fx["tryb"] == fx0["tryb"] and fx["kosz"] == fx0["kosz"] and dd <= 1e-4
        if fx0.get("ok") and not (fx0.get("tryb") in NS.TRYBY_NAD2 and fx0.get("litera") == "NAD2"):
            bez_pol += 1
        zg += int(ok)
        if not ok and len(zle) < 5:
            zle.append({"sim": r["sim"], "zapis": {k: fx0.get(k) for k in ("ok", "tryb", "kosz", "p_fix_ne")},
                        "replay": {k: fx.get(k) for k in ("ok", "tryb", "kosz", "p_fix_ne")}})
    out["s1"] = {"klatki": n, "zgodne": zg, "max_dp_fix_m": round(dmax, 7), "poprawki_bez_trybu_lub_litery": bez_pol,
                 "przyklady": zle, "ok": n > 0 and zg == n and bez_pol == 0}
    # (s2)
    nk = rz = 0
    obs_n = obs_bez = 0
    for r in rama:
        for ob in r.get("obs") or []:
            if ob.get("ok"):
                obs_n += 1
                obs_bez += int(not (ob.get("tryb") in NS.TRYBY_NAD2 and ob.get("litera") == "NAD2"))
        n2 = r.get("nad2") or {}
        if r.get("ph") not in UTRATA or n2.get("przedzial") is None:
            continue
        nk += 1
        j = (r.get("nadir") or {}).get("j")
        exp = round(NS.r_nad2(n2["przedzial"], j, n2["tryb"], 32.0), 3)
        rz += int(r.get("R_k") is None or abs(r["R_k"] - exp) > 1e-9)
    out["s2"] = {"ticki_utraty": nk, "R_k_niezgodne": rz, "poprawki_w_obs": obs_n, "poprawki_bez_trybu_lub_litery": obs_bez,
                 "ok": nk > 0 and rz == 0 and obs_n > 0 and obs_bez == 0}
    # (s3)
    nu = nn = zu = zn = 0
    pierwszy = None
    for r in rama:
        n2 = r.get("nad2")
        if n2 is None:
            continue
        pc, pe = r["p_corr"], r["p_ekf"]
        if r.get("ph") in UTRATA:
            nu += 1
            zu += int(abs(n2["r_est"] - math.hypot(pc[0], pc[1])) > 1e-3)
            if pierwszy is None:
                pierwszy = {"tick": r["tick"], "sim": r["sim"], "rama": n2["rama"]}
        else:
            nn += 1
            zn += int(abs(n2["r_est"] - math.hypot(pe[0], pe[1])) > 1e-3)
    out["s3"] = {"ticki_utraty": nu, "zle_utrata": zu, "ticki_nominal": nn, "zle_nominal": zn, "pierwszy_tick_utraty": pierwszy,
                 "ok": nu > 0 and zu == 0 and zn == 0 and pierwszy is not None and pierwszy["rama"] == "corr"}
    json.dump(out, open(os.path.join(d, "sprawdziany_s2.json"), "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(json.dumps({k: v["ok"] for k, v in sprawdz(d).items()}))
