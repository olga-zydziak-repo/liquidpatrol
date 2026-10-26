#!/usr/bin/env python3
"""results/WABIK/tools/wabik_sig.py — klasyfikator progowy sygnatury WABIKA
(PRE_WABIK §1/§2.2; PROMPT_WABIK_S1 §1.4). SIDECAR DIAGNOSTYCZNY — NIE steruje
lotem; w S1/S2 liczony POSTHOC z percep_feed.jsonl (trk_pos_ned per klatka —
strumień 1:1 z live; posthoc werdyktowo równoważny).

CECHY (lista zamknięta FREEZE_WABIK; okno wygładzone 1.0 s; KRZYWIZNA POZA
zestawem — NULL: nie separuje): v_rad [m/s] (prędkość radialna DO home;
dodatnia = zbliża), speed [m/s] (moduł prędkości okna), dh [m] (dystans tracka
od home), dh_min dotychczasowe [m], czas w strefie (dh<18).

REGUŁA DECYZJI (FROZEN; progi z NULL — FREEZE_WABIK, zmiana = ANEKS):
  warunek chwilowy W(t) = [speed > V_MOVE] ∧ [dh < R_ZONE] ∧ [v_rad < V_RAD_MAX]
                          ∧ [dh_min_dotychczas ≥ DH_MIN_FLOOR]
  etykieta „wabik" (AKTYWNA) ⇔ W(t) spełnione CIĄGLE przez ≥ T_FLAG s;
  ODWOŁANIE: złamanie podłogi dh_min < DH_MIN_FLOOR po fladze ⇒ etykieta
  cofnięta (re-klasyfikacja do „poważny" — stan bieżący, nie wyrok; klasyfikator
  online nie zna przyszłości). Raportowane OBIE metryki: kiedykolwiek / końcowa.
Wyjście: wabik_sig.jsonl (cechy per klatka-okno + stan + czas-do-flagi) +
podsumowanie per epizod na stdout.

Tryby:  --feed <percep_feed> --t0 <t0_sim> [--t1 ...]  — jeden epizod;
        --null-scan — kalibracja T_FLAG na NULL (V2 percep_feed 3 kampanii;
        progi cech stałe z kwantyli r2_null): raport FP per T.
"""
import argparse
import bisect
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# --- PROGI FROZEN (FREEZE_WABIK; kalibracja WYŁĄCZNIE na NULL r2_null.json) ---
V_MOVE = 0.30        # [m/s] warunek RUCCHU: speed okna > 0.30 (klasa v=0 NULL: speed_p50 p5=0.068,
                     #  cele ruchome v=0.5/1.0 >> 0.5; 0.30 rozdziela z marginesem z obu stron)
R_ZONE = 18.0        # [m] strefa (dysk ławki; t_in_zone NULL p95=74 s — strefa to kontekst, nie próg)
V_RAD_MAX = 0.30     # [m/s] "nie-zbliża": v_rad < 0.30 = p95 NULL v_rad_p50 (0.289) + margines
DH_MIN_FLOOR = 5.0   # [m] track nigdy <5 m (NULL ruchomi v=1.0 łamią w 88/90; podłoga pasa admisji)
T_FLAG = 12.0        # [s] ciągłego spełniania ⇒ „wabik" (kalibracja NULL-scan: patrz FREEZE)
WIN = 1.0            # [s] okno wygładzenia


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def classify(rows, out_f=None):
    """rows: [(t_sim, [N,E])] klatki z ważnym trk. Zwraca podsumowanie epizodu."""
    ts = [r[0] for r in rows]
    dh_min = 1e9
    streak_t0 = None
    t_flag = None
    t_revoke = None
    n_w = 0
    for i, (t, p) in enumerate(rows):
        dh = math.hypot(p[0], p[1])
        dh_min = min(dh_min, dh)
        j = bisect.bisect_left(ts, t - WIN)
        feat = None
        if j < i and ts[i] - ts[j] >= 0.5:
            q = rows[j][1]
            dt = t - ts[j]
            vN, vE = (p[0] - q[0]) / dt, (p[1] - q[1]) / dt
            speed = math.hypot(vN, vE)
            v_rad = (math.hypot(q[0], q[1]) - dh) / dt
            W = (speed > V_MOVE) and (dh < R_ZONE) and (v_rad < V_RAD_MAX) \
                and (dh_min >= DH_MIN_FLOOR)
            feat = {"t_sim": round(t, 3), "dh": round(dh, 2), "speed": round(speed, 3),
                    "v_rad": round(v_rad, 3), "dh_min": round(dh_min, 2), "W": W}
            if W:
                n_w += 1
                if streak_t0 is None:
                    streak_t0 = t
                if t_flag is None and t - streak_t0 >= T_FLAG:
                    t_flag = t
            else:
                streak_t0 = None
            if t_flag is not None and t_revoke is None and dh_min < DH_MIN_FLOOR:
                t_revoke = t                               # ODWOŁANIE (podłoga złamana)
            if t_flag is not None and t_revoke is None:
                feat["etykieta"] = "wabik"
            if out_f:
                out_f.write(json.dumps(feat) + "\n")
    return {"n_klatek": len(rows), "n_W": n_w, "dh_min": round(dh_min, 2) if rows else None,
            "etykieta": ("wabik" if t_flag is not None else "-"),
            "etykieta_koncowa": ("wabik" if (t_flag is not None and t_revoke is None) else "-"),
            "t_do_flagi_s": (round(t_flag - rows[0][0], 2) if t_flag is not None else None),
            "t_odwolania_s": (round(t_revoke - rows[0][0], 2) if t_revoke is not None else None)}


def feed_rows(path, t0, t1):
    rows = []
    for r in iter_jsonl(path):
        t = r.get("t_frame")
        if t is None or not (t0 <= t <= t1):
            continue
        trk = r.get("trk_pos_ned")
        if trk:
            rows.append((t, trk[:2]))
    rows.sort()
    return rows


def episodes_of(d):
    eps = []
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id"):
            eps.append({"sid": r["scenario_id"], "t0": r["t0_sim"]})
    for i, e in enumerate(eps):
        e["t1"] = eps[i + 1]["t0"] - 1.0 if i + 1 < len(eps) else e["t0"] + 112.0
    return eps


def null_scan():
    camps = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
             ("FANTOM_S2", "results/FANTOM/camp")]
    global T_FLAG
    cases = []
    for camp, base in camps:
        for i in range(1, 13):
            d = os.path.join(ROOT, base, f"r{i}_V2")
            pf = os.path.join(d, "percep_feed.jsonl")
            if not os.path.isdir(d) or not os.path.exists(pf):
                continue
            for e in episodes_of(d):
                rows = feed_rows(pf, e["t0"], e["t1"])
                if len(rows) >= 50:
                    cases.append((camp, f"r{i}_V2", e["sid"], rows))
    print(f"[null-scan] epizodów NULL (V2, trk ważny): {len(cases)}")
    for tf in (4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0):
        T_FLAG = tf
        fp = [(c, b, s) for (c, b, s, rows) in cases if classify(rows)["etykieta"] == "wabik"]
        print(f"  T_FLAG={tf:5.1f} s → FP {len(fp)}/{len(cases)}"
              + (f"  np. {fp[:4]}" if fp else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed")
    ap.add_argument("--t0", type=float)
    ap.add_argument("--t1", type=float)
    ap.add_argument("--out")
    ap.add_argument("--null-scan", action="store_true")
    a = ap.parse_args()
    if a.null_scan:
        null_scan()
        return
    rows = feed_rows(a.feed, a.t0, a.t1 if a.t1 else a.t0 + 112.0)
    of = open(a.out, "a") if a.out else None
    res = classify(rows, of)
    if of:
        of.close()
    print(json.dumps(res))


if __name__ == "__main__":
    main()
