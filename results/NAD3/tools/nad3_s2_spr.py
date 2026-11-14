#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s2_spr.py — sprawdziany mechaniczne cięć smoke NAD3 (PROMPT_NAD3_S2 §3: B3 i B4).

(k)  klucze (B3, bez degradacji): wiersze nf nadir_obs.jsonl bez pola „fx_deg”, meta producenta bez „nad3”; zbiór kluczy wiersza nf
     i meta identyczny z lotem NAD2 (wzorzec results/NAD2/s3/c05_s01_r2/nadir_obs.jsonl).
(r)  replay 100%: producent harness/nadir_fix.Rama(litera NAD2) na zapisanych klatkach → harness/nad3_degrad.Degradacja(konfiguracja
     i ziarno z meta producenta; brak ⇒ None, asercja `is`) odtwarza fx (ok, tryb, ids, kosz, t_fix, seq, |Δd_ne|, |Δp_fix| ≤ 5e-5 m)
     i fx_deg (ok, powód, t_fix, nad3.slot, |ΔE|, |Δd_ne|, |Δp_fix| ≤ 5e-5 m); osłona r03/nadir_shield.NadirShield(nad3, tabela i suma
     z meta lotu) przez results/NAD3/tools/nad3_krok.krok na wejściach ticku z zapisu (rama.jsonl, trace tk, demo), stan ramy = klient
     na strumieniu z replayu (datagram zdegradowany, jeśli jest) odtwarza per tick: przedział, τ (1e-4), R_k, fazę, decyzję, regułę,
     d_ne konsumenta, tick zatrzasku.
(s1) decymacja na żywo (B4): w strumieniu dostarczonym (fx_deg ok) numery slotów ściśle rosnące — najwyżej jedna poprawka na slot;
     odstępy t_fix dostarczonych (p50 / min / max) i τ max w misji (rama.jsonl, faza misji, ticki utraty).
(s3) meta (B4): meta producenta „nad3” = {model bias_rad, kierunek = oczekiwany, E_max = E tabeli, f 1, K 0}; tabela z meta lotu
     (trace meta nad3.oslona) = tabela FREEZE punktu (sha z results/NAD3/s1/freeze_U_<P>.json), E i punkt zgodne.
(b1) ticki utraty nieocenione przez B1 analizatora — policzone i nazwane z przyczyną (przedział None / koszyk None / brak próbki EKF
     w oknie [sim − 0.4, sim + 0.1] s).
Wyjście: <boot>/sprawdziany_s2_nad3.json. Użycie: nad3_s2_spr.py <katalog_bootu> <B3|B4> [kierunek]
"""
import bisect
import gzip
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools")]
import nad3_krok
from harness import nad3_degrad as DG
from harness.nadir_fix import Rama
from r03 import nadir_shield as NS
from r03 import config as C

UTRATA = ("KONT", "KONT_REFUSE")
MISJA = ("approach", "hold", "orbit")
WZORZEC_NAD2 = os.path.join(ROOT, "results/NAD2/s3/c05_s01_r2/nadir_obs.jsonl")


def jl(p, typ=None):
    out = []
    if not os.path.exists(p) and os.path.exists(p + ".gz"):
        f = gzip.open(p + ".gz", "rt")
    else:
        f = open(p)
    with f:
        for l in f:
            if typ is not None and f'"{typ}"' not in l:
                continue
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if typ is None or r.get("t") == typ:
                out.append(r)
    return out


def klucze(d):
    meta = jl(os.path.join(d, "nadir_obs.jsonl"), "meta")[0]
    nf = jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    wm = jl(WZORZEC_NAD2, "meta")[0]
    wn = jl(WZORZEC_NAD2, "nf")
    kl = sorted({tuple(sorted(r)) for r in nf})
    kw = sorted({tuple(sorted(r)) for r in wn})
    fx_k = sorted({tuple(sorted(r["fx"])) for r in nf if "fx" in r})
    fx_w = sorted({tuple(sorted(r["fx"])) for r in wn if "fx" in r})
    o = {"wiersze_z_fx_deg": sum("fx_deg" in r for r in nf), "meta_ma_nad3": "nad3" in meta,
         "klucze_meta_eq_NAD2": sorted(meta) == sorted(wm), "klucze_wiersza_eq_NAD2": kl == kw, "klucze_fx_eq_NAD2": fx_k == fx_w,
         "klucze_wiersza": [list(x) for x in kl], "klucze_wiersza_NAD2": [list(x) for x in kw]}
    o["ok"] = o["wiersze_z_fx_deg"] == 0 and not o["meta_ma_nad3"] and o["klucze_meta_eq_NAD2"] and o["klucze_wiersza_eq_NAD2"] \
        and o["klucze_fx_eq_NAD2"]
    return o


def meta_lotu(d):
    m = next((r for r in jl(os.path.join(d, "trace.jsonl"), "meta")), {})
    return ((m.get("nad3") or {}).get("oslona") or {})


def _maxd(a, b):
    if a is None or b is None:
        return 0.0 if a == b else float("inf")
    return max(abs(x - y) for x, y in zip(a, b))


def replay(d):
    meta = jl(os.path.join(d, "nadir_obs.jsonl"), "meta")[0]
    cfg = meta.get("nad3")
    nf = [r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx" in r]
    R = Rama(litera="NAD2")
    dg = DG.Degradacja(cfg)
    n = zle_fx = zle_deg = 0
    dmax = 0.0
    strumien, przyklad = {}, None
    for row in nf:
        fx = R.obserwacja(row["sim"], row["det"], row["ekf_q"], row["ekf_pos"])
        o = dg.przetworz(fx)
        if cfg is None:
            assert o is fx
        z = row["fx"]
        n += 1
        ok1 = all(fx.get(k) == z.get(k) for k in ("ok", "tryb", "ids", "kosz", "t_fix", "seq"))
        d1 = max(_maxd(fx["d_ne"], z["d_ne"]), _maxd(fx.get("p_fix_ne"), z.get("p_fix_ne")))
        zle_fx += int(not ok1 or d1 > 5e-5)
        if cfg is not None:
            zd = row.get("fx_deg")
            ok2 = zd is not None and all(o.get(k) == zd.get(k) for k in ("ok", "powod", "t_fix", "seq"))
            d2 = max(_maxd(o["d_ne"], (zd or {}).get("d_ne")), _maxd(o.get("p_fix_ne"), (zd or {}).get("p_fix_ne")))
            if o.get("nad3") or (zd or {}).get("nad3"):
                ok2 = ok2 and (o.get("nad3") or {}).get("slot") == ((zd or {}).get("nad3") or {}).get("slot")
                d2 = max(d2, _maxd((o.get("nad3") or {}).get("E"), ((zd or {}).get("nad3") or {}).get("E")))
            zle_deg += int(not ok2 or d2 > 5e-5)
            d1 = max(d1, d2 if d2 != float("inf") else 1e9)
        dmax = max(dmax, d1)
        if (zle_fx or zle_deg) and przyklad is None:
            przyklad = {"seq": z["seq"], "zapis": {k: z.get(k) for k in ("ok", "tryb", "kosz", "d_ne")},
                        "zapis_deg": row.get("fx_deg"), "replay": {k: o.get(k) for k in ("ok", "powod", "d_ne", "nad3")}}
        strumien[o["seq"]] = o
    prod = {"n_fx": n, "fx_niezgodne": zle_fx, "fx_deg_niezgodne": zle_deg, "max_abs_d": round(dmax, 7), "przyklad": przyklad,
            "konfiguracja": cfg}
    # osłona
    ml = meta_lotu(d)
    rama = sorted(jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in jl(os.path.join(d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in jl(os.path.join(d, "demo.jsonl"))}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=ml.get("tabela"), tabela_sha=ml.get("sha256_tabeli"))
    sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    class Kl:
        d_ne, t_fix, kosz, tryb = [0.0, 0.0], None, None, None
    kl, seqs, ip = Kl(), sorted(strumien), 0
    w = {"n": 0, "przedzial": 0, "tau": 0, "R_k": 0, "faza": 0, "dec": 0, "rule": 0, "d_ne": 0, "brak_tk": 0}
    lat_z = lat_r = None
    przyk = None
    for r in rama:
        while ip < len(seqs) and seqs[ip] <= r["seq"]:
            m = strumien[seqs[ip]]
            kl.d_ne, kl.t_fix = list(m["d_ne"]), m["t_fix"]
            if m.get("ok"):
                kl.kosz, kl.tryb = m.get("kosz"), m.get("tryb")
            ip += 1
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            w["brak_tk"] += 1
            continue
        pe = r["p_ekf"]
        own = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
        dd, _ = nad3_krok.krok(sh, r["tick"], pe, own, dm["own_vel_ned"], r["sp_ekf"], r["sp_net"], "PATROL", t["pf"], t["cs"], r["sim"],
                               t.get("dr"), kl)
        w["n"] += 1
        n2, nd = dd.get("nad2") or {}, dd.get("nadir") or {}
        lt = (r.get("nadir") or {}).get("tau")
        pom = {"przedzial": n2.get("przedzial") != (r.get("nad2") or {}).get("przedzial"),
               "tau": (lt is None) != (nd.get("tau") is None) or (lt is not None and abs(nd["tau"] - lt) > 1e-4),
               "R_k": dd["kont"].get("R_k") != r.get("R_k"), "faza": sh.kont_phase() != r.get("ph"),
               "dec": dd.get("decision") != r.get("dec"), "rule": dd.get("rule") != r.get("rule"),
               "d_ne": _maxd(kl.d_ne, r["d_ne"]) > 5e-7}
        for k, v in pom.items():
            w[k] += int(v)
        if any(pom.values()) and przyk is None:
            przyk = {"tick": r["tick"], "pola": [k for k, v in pom.items() if v]}
        if lat_z is None and r.get("ph") == "KONT_REFUSE":
            lat_z = r["tick"]
        if lat_r is None and sh.kont_phase() == "KONT_REFUSE":
            lat_r = r["tick"]
    w.update(zatrzask_zapis=lat_z, zatrzask_replay=lat_r, przyklad=przyk)
    ok = (n > 0 and zle_fx == 0 and zle_deg == 0 and w["n"] > 0 and w["brak_tk"] == 0 and lat_z == lat_r
          and all(w[k] == 0 for k in ("przedzial", "tau", "R_k", "faza", "dec", "rule", "d_ne")))
    return {"producent": prod, "oslona": w, "ok": ok}


def decymacja(d):
    nf = [r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx_deg" in r]
    dost = [r["fx_deg"] for r in nf if r["fx_deg"].get("ok")]
    sloty = [x["nad3"]["slot"] for x in dost]
    tf = [x["t_fix"] for x in dost]
    odst = sorted(round(b - a, 4) for a, b in zip(tf, tf[1:]))
    rama = jl(os.path.join(d, "rama.jsonl"))
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    zp = next((e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"), 1e18)
    taus = [(r.get("nadir") or {}).get("tau") for r in rama if r.get("ph") in UTRATA and r.get("phase") in MISJA and not r.get("desc")
            and r["sim"] < zp]
    taus = [x for x in taus if x is not None]
    o = {"dostarczone": len(dost), "sloty_scisle_rosnace": all(b > a for a, b in zip(sloty, sloty[1:])),
         "odstep_t_fix": {"min": odst[0], "p50": odst[len(odst) // 2], "max": odst[-1]} if odst else None,
         "tau_max_misja": round(max(taus), 4) if taus else None}
    o["ok"] = len(dost) > 0 and o["sloty_scisle_rosnace"]
    return o


def meta_spr(d, kierunek):
    meta = jl(os.path.join(d, "nadir_obs.jsonl"), "meta")[0].get("nad3") or {}
    ml = meta_lotu(d)
    o = {"meta_producenta": meta, "tabela_lotu": {k: ml.get(k) for k in ("tabela", "sha256_tabeli", "punkt", "E")}}
    try:
        punkt = ml.get("punkt")
        frz = json.load(open(os.path.join(ROOT, f"results/NAD3/s1/freeze_U_{punkt}.json")))
        o["sha_freeze_zgodna"] = frz["sha256_tabeli"] == ml.get("sha256_tabeli")
        o["E_zgodne"] = abs(float(meta.get("E_max", -1)) - frz["tabela"]["E"]) < 1e-12 and abs(float(ml.get("E", -2)) - frz["tabela"]["E"]) < 1e-12
    except (OSError, ValueError, TypeError):
        o["sha_freeze_zgodna"] = o["E_zgodne"] = False
    o["model_ok"] = meta.get("model") == "bias_rad" and float(meta.get("f") or 0) == 1.0 and int(meta.get("K", -1)) == 0
    o["kierunek_ok"] = meta.get("kierunek") == kierunek
    o["ok"] = o["sha_freeze_zgodna"] and o["E_zgodne"] and o["model_ok"] and o["kierunek_ok"]
    return o


def b1_nieocenione(d):
    """Ticki utraty epizodu cięcia nieocenione przez B1 (logika nad3_analyze: przedział/koszyk None ⇒ pominięty; t_probki None ⇒
    pominięty), z przyczyną."""
    rama = sorted(jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    cut = next((e for e in ev if e.get("ev") == "denial"), None)
    U = {}
    vt = vp = None
    p = os.path.join(d, "ulg.jsonl.gz")
    if os.path.exists(p):
        with gzip.open(p, "rt") as f:
            for l in f:
                r = json.loads(l)
                if r["temat"] == "vehicle_local_position":
                    vt = r["dane"]["timestamp"]; vp = list(zip(r["dane"]["x"], r["dane"]["y"], r["dane"]["z"]))
    przy = {}
    n_ut = 0
    for r in rama:
        if cut is None or r["ep"] != cut.get("episode_id") or r.get("ph") not in UTRATA or r.get("nad2") is None:
            continue
        n_ut += 1
        i, j = r["nad2"].get("przedzial"), (r.get("nadir") or {}).get("j")
        if i is None:
            k = "przedział None (τ + 0.012 poza ostatnią krawędzią — po zatrzasku τ*)" if r.get("ph") == "KONT_REFUSE" else "przedział None"
        elif j is None:
            k = "koszyk None"
        elif vt is not None:
            i0, i1 = bisect.bisect_left(vt, r["sim"] - 0.4), bisect.bisect_right(vt, r["sim"] + 0.1)
            k = None if i1 > i0 else "brak próbki EKF w oknie [sim − 0.4, sim + 0.1] s"
        else:
            k = "brak wyciągu ULG"
        if k:
            e = przy.setdefault(k, {"n": 0, "faza_misji": 0, "pierwszy_tick": r["tick"]})
            e["n"] += 1
            e["faza_misji"] += int(r.get("phase") in MISJA and not r.get("desc"))
    return {"ticki_utraty": n_ut, "nieocenione": sum(v["n"] for v in przy.values()), "przyczyny": przy}


def sprawdz(d, lot, kierunek=None):
    out = {"replay": replay(d), "b1_nieocenione": b1_nieocenione(d)}
    if lot == "B3":
        out["klucze"] = klucze(d)
    else:
        out["s1_decymacja"] = decymacja(d)
        out["s3_meta"] = meta_spr(d, kierunek)
    json.dump(out, open(os.path.join(d, "sprawdziany_s2_nad3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return out


if __name__ == "__main__":
    o = sprawdz(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps({k: v.get("ok") for k, v in o.items() if isinstance(v, dict) and "ok" in v}))
