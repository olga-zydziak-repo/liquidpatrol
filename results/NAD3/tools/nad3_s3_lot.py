#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s3_lot.py — sędzia pojedynczego lotu bramki S3 NADIR-III (PROMPT_NAD3_S3 §3; PRE_NAD3 §6) i pary (§3 „Pary”).

Wejście: katalog bootu po locie (po wyciągu ULG i nad3_analyze). Narzędzia READ-ONLY: nad3_analyze (B1–B5, D1, obserwable PRE §6),
nad3_s2_spr (replay producenta fx/fx_deg i osłony przez nad3_krok, decymacja, meta, ticki B1 nieocenione z przyczyną).
  ważność = replay 100% ∧ meta zgodna z pozycją planu (punkt, sha FREEZE, E, kierunek, model, f 1, K 0) ∧ najwyżej jedna poprawka na slot;
  litera = B1–B4 (cięcie) / B1–B5 (nominał) z analizatora ∧ ticki B1 nieocenione w fazie misji = 0;
  wejście (cięcie) = zdarzenie „denial”; D1 z analizatora;
  odmowy w misji (cięcie): pierwszy tick KONT_REFUSE w fazie misji (approach/hold/orbit, przed zejściem planowym) — tick, czas od
    t_inj_sim, przyczyna (τ* / bariera, z trace tk), r_est, bariera R_k, r_GT; bez odmowy: max r_est i min zapas bariery (R_k − r_est)
    w tickach utraty misji;
  obserwable: max e′/U′, e′ p50 / p95 / max, τ w misji, skok Δ′, odrzucenia bramki predykcji, r_max GT i średni promień GT w misji,
    track, pasmo, t_entry; nominały per epizod (B5, akwizycja: t_entry None ⇒ „pusty dla B5”, ANEKS_NAD3-2 §3.6).
Pary: dla (punkt, komórka) różnica r_max GT i średniego promienia w misji: „do środka” − „na zewnątrz”.
Wyjście: <boot>/sedzia_s3.json. Użycie: nad3_s3_lot.py <katalog_bootu> <pozycja 1–14>
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools")]
import nad3_s2_spr as SPR

MISJA = ("approach", "hold", "orbit")
UTRATA = ("KONT", "KONT_REFUSE")
C05, C10 = 5, 10
PLAN = [  # (pozycja, rodzaj, punkt, kierunek, epizody)
    (1, "ciecie", "P1", "na_zewnatrz", [C05]), (2, "ciecie", "P1", "na_zewnatrz", [C10]),
    (3, "ciecie", "P1", "do_srodka", [C05]), (4, "ciecie", "P1", "do_srodka", [C10]),
    (5, "nominal", "P1", "na_zewnatrz", [0, 1, 5, 10]),
    (6, "ciecie", "P2", "na_zewnatrz", [C05]), (7, "ciecie", "P2", "na_zewnatrz", [C10]),
    (8, "ciecie", "P2", "do_srodka", [C05]), (9, "ciecie", "P2", "do_srodka", [C10]),
    (10, "nominal", "P1", "do_srodka", [1, 2, 5, 10]),
    (11, "ciecie", "P3", "na_zewnatrz", [C05]), (12, "ciecie", "P3", "na_zewnatrz", [C10]),
    (13, "ciecie", "P3", "do_srodka", [C05]), (14, "ciecie", "P3", "do_srodka", [C10]),
]
POZ = {p[0]: {"rodzaj": p[1], "punkt": p[2], "kierunek": p[3], "epizody": p[4]} for p in PLAN}


def _gt(d):
    tr = os.path.join(d, "trace.jsonl")
    gt = sorted(SPR.jl(tr, "gt"), key=lambda r: r["sim"])
    ev = SPR.jl(tr, "event")
    armed = next((e for e in ev if e.get("ev") == "armed"), None)
    gx0, gy0 = armed["gt_home"] if armed else (0.0, 0.0)
    return gt, ev, gx0, gy0


def promien(gt, gx0, gy0, t0, t1):
    rg = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if t0 <= g["sim"] <= t1]
    return (round(max(rg), 3), round(sum(rg) / len(rg), 3)) if rg else (None, None)


def sedzia(d, poz):
    P = POZ[poz]
    a = json.load(open(os.path.join(d, "wyniki_nad3.json")))
    s = SPR.sprawdz(d, "B4", P["kierunek"])                  # (r), (s1), (s3), b1 — tryb „z degradacją” dla każdej pozycji S3
    gt, ev, gx0, gy0 = _gt(d)
    rama = sorted(SPR.jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in SPR.jl(os.path.join(d, "trace.jsonl"), "tk")}
    meta = s["s3_meta"]
    meta_ok = meta["ok"] and (meta["tabela_lotu"] or {}).get("punkt") == P["punkt"]
    out = {"pozycja": poz, **P, "boot": os.path.basename(d.rstrip("/")), "wazny_analizator": a.get("wazny"),
           "replay_ok": s["replay"]["ok"], "meta_ok": meta_ok, "decymacja_ok": s["s1_decymacja"]["ok"],
           "decymacja": s["s1_decymacja"], "tempo": (a.get("tempo") or {}).get("dsim_dwall_settle"), "epizody": []}
    out["wazny"] = bool(out["replay_ok"] and meta_ok and out["decymacja_ok"] and a.get("wazny"))
    b1n = s["b1_nieocenione"]
    out["b1_nieocenione"] = b1n
    out["b1_nieocenione_w_misji"] = sum(v["faza_misji"] for v in b1n["przyczyny"].values())
    ends = {e["episode_id"]: e for e in ev if e.get("ev") == "episode_end"}
    starts = {e["episode_id"]: e for e in ev if e.get("ev") == "episode_start"}
    zp = {e["episode_id"]: e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"}
    cut = next((e for e in ev if e.get("ev") == "denial"), None)
    out["wejscie"] = cut is not None if P["rodzaj"] == "ciecie" else None
    lit = True
    for o in a.get("epizody", []):
        ep = o["episode_id"]
        ms = [r for r in rama if r["ep"] == ep and r.get("phase") in MISJA and not r.get("desc") and r["sim"] < zp.get(ep, 1e18)]
        t0 = ms[0]["sim"] if ms else None
        t1 = ms[-1]["sim"] if ms else None
        rmax, rsr = promien(gt, gx0, gy0, t0, t1) if ms else (None, None)
        e = {"episode_id": ep, "scenario_id": o["scenario_id"], "ciecie": o["ciecie"],
             "B": {k: (o.get(k) or {}).get("ok") for k in ("B1", "B2", "B3", "B4", "B5") if k in o},
             "D1": o.get("D1"), "max_e_do_U": o["B1"]["max_e_do_U"], "e_corr": o.get("e_corr"),
             "obserwable": o.get("nad3_obserwable"), "r_max_gt_misja": rmax, "r_sr_gt_misja": rsr,
             "t_entry": (ends.get(ep) or {}).get("t_entry"), "okno_misji_s": round(t1 - t0, 2) if ms else None}
        lit = lit and o.get("bezpieczenstwo_ok", False)
        if o["ciecie"]:
            ut = [r for r in ms if r.get("ph") in UTRATA and (r.get("nad2") or {}).get("przedzial") is not None]
            # odmowa w misji: pierwszy zatrzask przed zejściem planowym — tick zatrzasku ma już desc = True (D5 startuje w tym ticku),
            # więc szukany wśród wszystkich ticków epizodu przed zejściem planowym, nie tylko w ms (poprawka po poz. 7 S3)
            ref = next((r for r in rama if r["ep"] == ep and r.get("ph") == "KONT_REFUSE" and r["sim"] < zp.get(ep, 1e18)), None)
            if ref is not None:
                g = min(gt, key=lambda x: abs(x["sim"] - ref["sim"]))
                e["odmowa_w_misji"] = {"tick": ref["tick"], "od_ciecia_s": round(ref["sim"] - cut["t_inj_sim"], 2) if cut else None,
                                       "przyczyna": (tk.get(ref["tick"]) or {}).get("cause"), "r_est": round(ref["nad2"]["r_est"], 3),
                                       "bariera_R_k": ref.get("R_k"), "r_gt": round(math.hypot(g["x"] - gx0, g["y"] - gy0), 3),
                                       "tau": (ref.get("nadir") or {}).get("tau")}
            else:
                e["odmowa_w_misji"] = None
            if ut:
                e["max_r_est_misja"] = round(max(r["nad2"]["r_est"] for r in ut), 3)
                e["min_zapas_bariery_misja"] = round(min(r["R_k"] - r["nad2"]["r_est"] for r in ut if r.get("R_k") is not None), 3)
            e["track"] = (o.get("D1") or {}).get("frac_track")
            e["pasmo"] = (o.get("D1") or {}).get("frac_pasmo")
        else:
            e["akwizycja"] = e["t_entry"] is not None
            e["B5_pusty"] = not e["akwizycja"]
        out["epizody"].append(e)
    out["litera_ok"] = bool(lit and a.get("bezpieczenstwo_ok") and out["b1_nieocenione_w_misji"] == 0)
    if P["rodzaj"] == "ciecie":
        ec = next((e for e in out["epizody"] if e["ciecie"]), None)
        out["D1_dostepne"] = bool(ec and (ec.get("D1") or {}).get("dostepne"))
    json.dump(out, open(os.path.join(d, "sedzia_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return out


def pary(wyniki):
    """wyniki: {pozycja: sedzia}. Zwraca 6 par (punkt, komórka): do_srodka − na_zewnatrz (r_max GT, średni promień w misji)."""
    out = {}
    for pkt in ("P1", "P2", "P3"):
        for ep, kom in ((C05, "c05"), (C10, "c10")):
            w = {}
            for poz, P in POZ.items():
                if P["rodzaj"] == "ciecie" and P["punkt"] == pkt and P["epizody"] == [ep] and poz in wyniki:
                    e = next((x for x in wyniki[poz]["epizody"] if x["ciecie"]), None)
                    w[P["kierunek"]] = e
            if "do_srodka" in w and "na_zewnatrz" in w and w["do_srodka"] and w["na_zewnatrz"]:
                a, b = w["do_srodka"], w["na_zewnatrz"]
                out[f"{pkt}/{kom}"] = {"r_max_do_srodka": a["r_max_gt_misja"], "r_max_na_zewnatrz": b["r_max_gt_misja"],
                                       "roznica_r_max": round(a["r_max_gt_misja"] - b["r_max_gt_misja"], 3),
                                       "r_sr_do_srodka": a["r_sr_gt_misja"], "r_sr_na_zewnatrz": b["r_sr_gt_misja"],
                                       "roznica_r_sr": round(a["r_sr_gt_misja"] - b["r_sr_gt_misja"], 3)}
            else:
                out[f"{pkt}/{kom}"] = None
    return out


if __name__ == "__main__":
    o = sedzia(sys.argv[1], int(sys.argv[2]))
    print(json.dumps({k: o[k] for k in ("pozycja", "wazny", "litera_ok", "wejscie", "D1_dostepne") if k in o}, ensure_ascii=False))
