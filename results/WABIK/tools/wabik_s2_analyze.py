#!/usr/bin/env python3
"""results/WABIK/tools/wabik_s2_analyze.py — analiza bootów S2 (ANEKS_WABIK-1 §4.4-4.6).

Per epizod bootu:
  • KLASYFIKATOR (import wabik_sig — progi FROZEN z FREEZE_WABIK w kodzie 1:1):
    posthoc z percep_feed (okno epizodu z trace), cechy/etykieta(kiedykolwiek
    i końcowa)/czas-do-flagi OD STARTU ŚLEDZENIA (pierwsza klatka z trk) +
    zapis strumienia cech do wabik_sig_<sid>.jsonl,
  • SĘDZIA/GT (import analyze_boot z perc2_s2_analyze; SCEN uzupełniony wpisami
    manifestu S2): t_acq, d_min (GT manifest), D6 opisowo, świadek OBOK,
    kadencja lotu,
  • ORB (m01_*): utrzymanie tracka po zmianie kursu (t_rel>9 s): frakcja ticków
    demo z track_valid ∧ |trk−GT|≤3 m w oknie [9,43] s; separacja d_min.
Wyjście: results/WABIK/s2_wyniki.json + tabela stdout.
Użycie: wabik_s2_analyze.py <bootdir> [<bootdir>...]
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "PERC2", "tools"),
          os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import perc2_s2_analyze as PA
import wabik_sig as WS

S2MAN = json.load(open(os.path.join(ROOT, "results", "WABIK", "wabik_manifest_s2.json")))
PA.SCEN.update({e["scenario_id"]: e for e in S2MAN["episodes"]})
OUTD = os.path.join(ROOT, "results", "WABIK")
RODZAJ = {"w00a_s01": "TP", "w00b_s01": "TP", "w01a_s01": "TP", "w01b_s01": "TP",
          "w02a_s01": "TP", "w02b_s01": "TP", "c08_s03": "FP", "c10_s02": "FP",
          "m00_s01": "FP", "m01_s01": "ORB", "m01_s02": "ORB"}


def main():
    res = []
    for d in sys.argv[1:]:
        ja = PA.analyze_boot(d)
        pf = os.path.join(d, "percep_feed.jsonl")
        for r in ja:
            sid = r["sid"]
            rows = WS.feed_rows(pf, r["t0_abs"] if "t0_abs" in r else 0, 0)
            # okno epizodu: z trace (analyze_boot nie zwraca t0 wprost — weź z trace)
        # okna z trace:
        eps = WS.episodes_of(d)
        for e in eps:
            sid = e["sid"]
            jr = next((x for x in ja if x["sid"] == sid), None)
            rows = WS.feed_rows(pf, e["t0"], e["t1"])
            sig_path = os.path.join(d, f"wabik_sig_{sid}.jsonl")
            of = open(sig_path, "w")
            cls = WS.classify(rows, of)
            of.close()
            row = {"boot": os.path.basename(d.rstrip("/")), "sid": sid,
                   "rodzaj": RODZAJ.get(sid, "?"), "klasyfikator": cls}
            if jr:
                row["t_acq_s"] = jr["t_acq_s"]
                row["d_min_gt"] = jr["d_min_gt"]
                row["sedzia_D6_opisowo"] = jr["sedzia_D6_opisowo"]
                row["swiadek"] = jr["swiadek_erratum"]
                row["kadencja_lotu"] = jr["kadencja_lotu"]
            if RODZAJ.get(sid) == "ORB" and jr:
                # utrzymanie tracka po zmianie kursu (t_rel > 9 s)
                ep = PA.SCEN[sid]
                intr = []
                t = 0.0
                while t <= 112:
                    x, y, z = __import__("bench.scenarios", fromlist=["S"]).position_at(ep, t)
                    intr.append((e["t0"] + t, [x, y, -z]))
                    t += 0.05
                n_ok = n_all = 0
                for dr in WS.iter_jsonl(os.path.join(d, "demo.jsonl")):
                    if dr.get("scenario_id") != sid:
                        continue
                    trel = dr["t_sim"] - e["t0"]
                    if not (9.0 <= trel <= 43.0):
                        continue
                    n_all += 1
                    if dr.get("track_valid") and dr.get("trk_pos_ned"):
                        g = PA.interp(intr, dr["t_sim"])
                        if math.hypot(dr["trk_pos_ned"][0] - g[0],
                                      dr["trk_pos_ned"][1] - g[1]) <= 3.0:
                            n_ok += 1
                row["orb_track_po_manewrze"] = {"n_tickow_9_43s": n_all,
                                                "frac_track_na_celu": round(n_ok / n_all, 3)
                                                if n_all else None}
            res.append(row)
            c = row["klasyfikator"]
            print(f"[{row['boot']} {sid} {row['rodzaj']}] etykieta={c['etykieta']}/{c['etykieta_koncowa']} "
                  f"t_flag={c['t_do_flagi_s']} t_odw={c['t_odwolania_s']} dh_min_trk={c['dh_min']} "
                  f"t_acq={row.get('t_acq_s')} d_min_gt={row.get('d_min_gt', {}).get('d3') if row.get('d_min_gt') else None} "
                  f"D6={row.get('sedzia_D6_opisowo', {}).get('success_D6')} "
                  f"świadek={row.get('swiadek', {}).get('n_artefakt')} "
                  + (f"orb={row.get('orb_track_po_manewrze')}" if 'orb_track_po_manewrze' in row else ""))
    json.dump({"progi": {"V_MOVE": WS.V_MOVE, "V_RAD_MAX": WS.V_RAD_MAX,
                         "DH_MIN_FLOOR": WS.DH_MIN_FLOOR, "T_FLAG": WS.T_FLAG},
               "epizody": res},
              open(os.path.join(OUTD, "s2_wyniki.json"), "w"), indent=1)
    print("zapisano s2_wyniki.json")


if __name__ == "__main__":
    main()
