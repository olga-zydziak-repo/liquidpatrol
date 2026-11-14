#!/usr/bin/env python3
"""results/NAD3/tools/nad3_w1.py — W1 wierność NADIR-III (PROMPT_NAD3_S1 §4 W1, PRE_NAD3 §6 S1; 0 bootów).

Nowy kod w reżimie „nad3” z tabelą o parametrach NAD2 (krawędzie 0.25…1.05 i G z results/NAD2/s1/freeze_U.json, F bez zmian,
E = 0, τ* = 1.05, próg 19 ticków, dodatek 0.012 s; plik results/NAD3/s1/tabela_W1_nad2.json — tabela testowa, nie FREEZE)
i degradacją wyłączoną odtwarza zapis 13 lotów NAD2 (12 cięć bramki S3 + lot długi):
  (P) producent: harness/nadir_fix.Rama(litera NAD2) na wierszach nf nadir_obs.jsonl → harness/nad3_degrad.Degradacja(None)
      (asercja: ten sam obiekt) — zgodność z zapisanym fx: ok, tryb, ids, kosz, t_fix, seq, |Δd_ne| i |Δp_fix| ≤ 5e-5 m;
      kontrolnie także Degradacja({model: zero}) (ścieżka kopii, E = 0, pełna częstość, K = 0);
  (O) osłona: r03/nadir_shield.NadirShield(nadir_mode=1, nad3, tabela W1) wołana przez results/NAD3/tools/nad3_krok.krok
      (ścieżka drivera) na wejściach ticku z zapisu (rama.jsonl: p_EKF, sp_EKF, sp_net, seq; trace tk: cs, pf; demo: prędkość
      własna), stan ramy = klient (d_ne, t_fix z datagramu ticku, koszyk/tryb z ostatniej poprawki ok) na strumieniu z (P);
      porównanie per tick z zapisem: przedział, τ (4 cyfry), R_k (3 cyfry), faza, tick zatrzasku REFUSE, decyzja i reguła.
Wyjście: results/NAD3/s1/w1_wiernosc.json; kod 1 przy braku 100%.
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
import nad3_dane as N                                                # loader reconu (13 lotów, .gz)
import nad3_krok
from harness import nad3_degrad as DG
from harness.nadir_fix import Rama
from r03 import nadir_shield as NS
from r03 import config as C                                        # stałe pętli drivera (r03/config.py)

OUT = os.path.join(ROOT, "results/NAD3/s1")
TAB = os.path.join(OUT, "tabela_W1_nad2.json")


def tabela_w1():
    FU = json.load(open(os.path.join(ROOT, "results/NAD2/s1/freeze_U.json")))["tabela"]
    t = {"punkt": "W1_nad2", "E": 0.0, "krawedzie_tau_s": FU["krawedzie_tau_s"], "G": FU["G"], "F": FU["F"], "zapas": FU["zapas"],
         "delta_D5": FU["delta_D5"], "R_E": FU["R_E"], "d_stop": FU["d_stop"], "tau_star_s": FU["tau_star_s"], "tau_eps_s": NS.TAU_EPS_NAD2,
         "prog_zatrzasku_ticki": 19, "dt_s": 0.05, "pole_brak": list(NS.POLE_BRAK_NAD2),
         "regula": "U′ = 1.5·(F_zn + E + G); u′ = U′ + Δ_D5; R = R_E − d_stop − u′ (W1: parametry NAD2, E = 0)"}
    doc = {"tabela": t, "sha256_tabeli": NS.tabela_sha(t), "uwaga": "tabela testowa W1 (PROMPT_NAD3_S1 §4), nie FREEZE",
           "zrodlo": "results/NAD2/s1/freeze_U.json (sha256_tabeli " + json.load(open(os.path.join(ROOT, "results/NAD2/s1/freeze_U.json")))["sha256_tabeli"][:16] + "…)"}
    json.dump(doc, open(TAB, "w"), ensure_ascii=False, indent=1)
    return doc["sha256_tabeli"]


def producent(L, cfg):
    R = Rama(litera="NAD2")
    dg = DG.Degradacja(cfg)
    n = zle = 0
    max_d, strumien, przyklad = 0.0, {}, None
    for row in L.nf:
        fx = R.obserwacja(row["sim"], row["det"], row["ekf_q"], row["ekf_pos"])
        o = dg.przetworz(fx)
        if cfg is None:
            assert o is fx
        z = row["fx"]
        n += 1
        ok = all(o.get(k) == z.get(k) for k in ("ok", "tryb", "ids", "kosz", "t_fix", "seq"))
        d = max(abs(a - b) for a, b in zip(o["d_ne"], z["d_ne"]))
        if o.get("p_fix_ne") is not None and z.get("p_fix_ne") is not None:
            d = max(d, max(abs(a - b) for a, b in zip(o["p_fix_ne"], z["p_fix_ne"])))
        max_d = max(max_d, d)
        if not ok or d > 5e-5:
            zle += 1
            przyklad = przyklad or {"seq": z["seq"], "zapis": {k: z.get(k) for k in ("ok", "tryb", "kosz", "d_ne")},
                                    "replay": {k: o.get(k) for k in ("ok", "tryb", "kosz", "d_ne")}}
        strumien[o["seq"]] = o
    return strumien, {"n_fx": n, "niezgodne": zle, "max_abs_d": round(max_d, 7), "przyklad": przyklad}


class Klient:
    def __init__(self):
        self.d_ne, self.t_fix, self.kosz, self.tryb = [0.0, 0.0], None, None, None


def oslona(L, strumien, sha):
    tk = {r["tick"]: r for r in N.jl(L.d, "trace.jsonl", "tk")}
    demo = {r["tick"]: r for r in N.jl(L.d, "demo.jsonl")}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=TAB, tabela_sha=sha)
    sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS                           # jak driver (nad3_flight.py)
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
    seqs = sorted(strumien)
    kl = Klient()
    ip = 0
    wyn = {"n": 0, "przedzial": 0, "tau": 0, "R_k": 0, "faza": 0, "dec": 0, "rule": 0, "d_ne": 0, "brak_tk": 0}
    latch_log = latch_rep = None
    przyklad = None
    for r in L.rama:
        while ip < len(seqs) and seqs[ip] <= r["seq"]:
            m = strumien[seqs[ip]]
            kl.d_ne, kl.t_fix = list(m["d_ne"]), m["t_fix"]
            if m.get("ok"):
                kl.kosz, kl.tryb = m.get("kosz"), m.get("tryb")
            ip += 1
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            wyn["brak_tk"] += 1
            continue
        pe = r["p_ekf"]
        own_net = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
        d, _ = nad3_krok.krok(sh, r["tick"], pe, own_net, dm["own_vel_ned"], r["sp_ekf"], r["sp_net"], "PATROL", t["pf"], t["cs"],
                              r["sim"], t.get("dr"), kl)
        wyn["n"] += 1
        n2, nd = d.get("nad2") or {}, d.get("nadir") or {}
        lt = (r.get("nadir") or {}).get("tau")
        pom = {"przedzial": n2.get("przedzial") != (r.get("nad2") or {}).get("przedzial"),
               "tau": (lt is None) != (nd.get("tau") is None) or (lt is not None and abs(nd["tau"] - lt) > 1e-4),
               "R_k": d["kont"].get("R_k") != r.get("R_k"), "faza": sh.kont_phase() != r.get("ph"),
               "dec": d.get("decision") != r.get("dec"), "rule": d.get("rule") != r.get("rule"),
               "d_ne": max(abs(kl.d_ne[0] - r["d_ne"][0]), abs(kl.d_ne[1] - r["d_ne"][1])) > 5e-7}
        for k, v in pom.items():
            wyn[k] += int(v)
        if any(pom.values()) and przyklad is None:
            przyklad = {"tick": r["tick"], "pola": [k for k, v in pom.items() if v],
                        "zapis": {"przedzial": (r.get("nad2") or {}).get("przedzial"), "tau": lt, "R_k": r.get("R_k"), "ph": r.get("ph"),
                                  "dec": r.get("dec"), "rule": r.get("rule")},
                        "replay": {"przedzial": n2.get("przedzial"), "tau": nd.get("tau"), "R_k": d["kont"].get("R_k"),
                                   "ph": sh.kont_phase(), "dec": d.get("decision"), "rule": d.get("rule")}}
        if latch_log is None and r.get("ph") == "KONT_REFUSE":
            latch_log = r["tick"]
        if latch_rep is None and sh.kont_phase() == "KONT_REFUSE":
            latch_rep = r["tick"]
    wyn.update(zatrzask_zapis=latch_log, zatrzask_replay=latch_rep, zatrzask_zgodny=latch_log == latch_rep, przyklad=przyklad)
    return wyn


def main():
    sha = tabela_w1()
    out = {"tabela": os.path.relpath(TAB, ROOT), "sha256_tabeli": sha, "loty": {}}
    ok = True
    for n, d, k in N.loty():
        L = N.wczytaj(n, d, k)
        s_pt, p_pt = producent(L, None)
        _, p_z = producent(L, {"model": "zero"})
        o = oslona(L, s_pt, sha)
        lot_ok = (p_pt["niezgodne"] == 0 and p_z["niezgodne"] == 0 and o["brak_tk"] == 0 and o["zatrzask_zgodny"]
                  and all(o[x] == 0 for x in ("przedzial", "tau", "R_k", "faza", "d_ne")))
        out["loty"][n] = {"producent_passthrough": p_pt, "producent_zero": p_z, "oslona": o, "ok": lot_ok}
        ok = ok and lot_ok
        print(n, "fx", p_pt["n_fx"], p_pt["niezgodne"], p_z["niezgodne"], "ticki", o["n"], {x: o[x] for x in ("przedzial", "tau", "R_k", "faza", "dec", "rule", "d_ne")},
              "zatrzask", o["zatrzask_zapis"], o["zatrzask_replay"], "OK" if lot_ok else "FAIL", flush=True)
    out["W1_PASS"] = ok
    out["suma"] = {"fx": sum(v["producent_passthrough"]["n_fx"] for v in out["loty"].values()),
                   "ticki": sum(v["oslona"]["n"] for v in out["loty"].values()),
                   "dec_niezgodne": sum(v["oslona"]["dec"] for v in out["loty"].values()),
                   "rule_niezgodne": sum(v["oslona"]["rule"] for v in out["loty"].values())}
    json.dump(out, open(os.path.join(OUT, "w1_wiernosc.json"), "w"), ensure_ascii=False, indent=1)
    print("W1", "PASS" if ok else "FAIL", out["suma"])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
