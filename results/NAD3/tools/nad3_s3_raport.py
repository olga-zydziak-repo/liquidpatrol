#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s3_raport.py — zestawienie bramki S3 NADIR-III (PROMPT_NAD3_S3 §5; 0 bootów).

Dla każdego lotu ważnego z księgi kolejki (results/NAD3/s3/kampania_ksiega.jsonl) sędzia nad3_s3_lot liczony PONOWNIE (wersja z poprawką
wykrywania odmowy w misji — tick zatrzasku z desc = True), potem: tabela 14 pozycji (ważność, B1–B5, D1, odmowy w misji i w zejściu
z przyczyną), P1 wobec progu, P2/P3 opisowo, obserwable, 6 par, liczby do rozliczenia P-NAD3-2 … P-NAD3-7 (bez rozliczenia), werdykt
literą PRE §6 (V-A: zero naruszeń B1–B5 ∧ P1 ≥ 3/4; V-B: zero naruszeń, P1 < 3/4; V-C: naruszenie).
Odmowy w zejściu: pierwszy tick KONT_REFUSE po komendzie zejścia planowego (przyczyna z trace tk).
Wyjście: results/NAD3/s3/wyniki_s3.json.
"""
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools")]
import nad3_s3_lot as LOT
import nad3_s2_spr as SPR

S3 = os.path.join(ROOT, "results/NAD3/s3")


def odmowa_w_zejsciu(d):
    rama = sorted(SPR.jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in SPR.jl(os.path.join(d, "trace.jsonl"), "tk")}
    ev = SPR.jl(os.path.join(d, "trace.jsonl"), "event")
    zp = next((e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"), None)
    if zp is None:
        return None
    r = next((r for r in rama if r.get("ph") == "KONT_REFUSE" and r["sim"] >= zp), None)
    if r is None:
        return None
    return {"tick": r["tick"], "po_zejsciu_s": round(r["sim"] - zp, 2), "przyczyna": (tk.get(r["tick"]) or {}).get("cause"),
            "tau": (r.get("nadir") or {}).get("tau"), "r_est": round(r["nad2"]["r_est"], 3), "bariera_R_k": r.get("R_k")}


def main():
    ks = [json.loads(l) for l in open(os.path.join(S3, "kampania_ksiega.jsonl")) if l.strip()]
    wazne = {w["pozycja"]: w for w in ks if w.get("status") == "wazny"}
    wyn, tab = {}, []
    for poz in sorted(LOT.POZ):
        w = wazne.get(poz)
        if w is None:
            tab.append({"pozycja": poz, "lot": None})
            continue
        d = os.path.join(S3, w["nazwa"])
        s = LOT.sedzia(d, poz)
        wyn[poz] = s
        P = LOT.POZ[poz]
        row = {"pozycja": poz, "rodzaj": P["rodzaj"], "punkt": P["punkt"], "kierunek": P["kierunek"], "lot": w["nazwa"], "boot_nogi": w["boot_s3"],
               "tempo": s["tempo"], "wazny": s["wazny"], "litera_ok": s["litera_ok"], "b1_nieocenione": s["b1_nieocenione"]}
        if P["rodzaj"] == "ciecie":
            e = next(x for x in s["epizody"] if x["ciecie"])
            row.update(scenario=e["scenario_id"], B=e["B"], D1=e["D1"], D1_dostepne=s["D1_dostepne"], t_entry=e["t_entry"],
                       odmowa_w_misji=e.get("odmowa_w_misji"), odmowa_w_zejsciu=odmowa_w_zejsciu(d), max_r_est_misja=e.get("max_r_est_misja"),
                       min_zapas_bariery_misja=e.get("min_zapas_bariery_misja"), r_max_gt_misja=e["r_max_gt_misja"], r_sr_gt_misja=e["r_sr_gt_misja"],
                       max_e_do_U=e["max_e_do_U"], e_corr=e["e_corr"], obserwable=e["obserwable"], track=e.get("track"), pasmo=e.get("pasmo"),
                       decymacja=s["decymacja"])
        else:
            row.update(epizody=[{k: x.get(k) for k in ("scenario_id", "B", "akwizycja", "B5_pusty", "t_entry", "r_max_gt_misja", "r_sr_gt_misja",
                                                       "okno_misji_s")} for x in s["epizody"]])
        tab.append(row)
    ciecia = [r for r in tab if r.get("rodzaj") == "ciecie" and r.get("lot")]
    p1 = [r for r in ciecia if r["punkt"] == "P1"]
    narusz = [r["pozycja"] for r in tab if r.get("lot") and not r["litera_ok"]]
    p1_dost = sum(bool(r["D1_dostepne"]) for r in p1)
    werdykt = "V-C" if narusz else ("V-A" if p1_dost >= 3 else "V-B")
    eU = [r["max_e_do_U"] for r in ciecia]
    pr = {
        "P-NAD3-2_P1_ciecia_bez_REFUSE_w_misji": f"{sum(r['odmowa_w_misji'] is None for r in p1)}/{len(p1)}",
        "P-NAD3-3_przekroczenia_przeslanki_12_ciec": sum(r["B"]["B1"] is False for r in ciecia),
        "P-NAD3-3_max_e_do_U_12_ciec": max(eU) if eU else None,
        "P-NAD3-5_P3_na_zewnatrz_REFUSE_bariera": {r["scenario"]: (r["odmowa_w_misji"] or {}).get("przyczyna") for r in ciecia
                                                    if r["punkt"] == "P3" and r["kierunek"] == "na_zewnatrz"},
        "P-NAD3-5_P3_na_zewnatrz_B4": {r["scenario"]: r["B"]["B4"] for r in ciecia if r["punkt"] == "P3" and r["kierunek"] == "na_zewnatrz"},
        "P-NAD3-6_P2_REFUSE_w_misji": f"{sum(r['odmowa_w_misji'] is not None for r in ciecia if r['punkt'] == 'P2')}/4",
        "P-NAD3-7_REFUSE_tau_w_misji_12_ciec": sum((r["odmowa_w_misji"] or {}).get("przyczyna") == "τ*" for r in ciecia),
        "P-NAD3-7_REFUSE_tau_w_zejsciu_12_ciec": sum((r["odmowa_w_zejsciu"] or {}).get("przyczyna") == "τ*" for r in ciecia),
    }
    par = LOT.pary(wyn)
    pr["P-NAD3-4_pary_roznica_r_max_lt_1m"] = f"{sum(abs(v['roznica_r_max']) < 1.0 for v in par.values() if v)}/{sum(1 for v in par.values() if v)}"
    out = {"werdykt": werdykt, "naruszenia_pozycje": narusz, "P1_dostepne": f"{p1_dost}/4", "tabela": tab, "pary": par, "predykcje_liczby": pr,
           "booty": {"S3": len(ks), "wazne": len(wazne), "rezerwa": sum(1 for w in ks if w.get("status") in ("bez_wejscia", "niewazny_stanowisko"))}}
    json.dump(out, open(os.path.join(S3, "wyniki_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("werdykt", "naruszenia_pozycje", "P1_dostepne", "booty", "predykcje_liczby", "pary")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
