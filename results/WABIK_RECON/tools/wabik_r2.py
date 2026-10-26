#!/usr/bin/env python3
"""results/WABIK_RECON/tools/wabik_r2.py — R2 PROMPT_WABIK_S0: sygnatury ruchu celu
liczone ONLINE ze stanu śledzenia + BASELINE NULL na wszystkich celach 3 kampanii.

Cechy per epizod, liczone WYŁĄCZNIE z tego, co niesie feed (demo.jsonl:
trk_pos_ned per tick, track_valid) — czyli z sygnału, który widziałby przyszły
klasyfikator online (zero GT w cechach; GT tylko do metadanych epizodu):
  • v_rad_p50 [m/s]   — mediana prędkości radialnej DO home (dodatnia = zbliża się);
                        okno różnicowe 1.0 s na trk_pos_ned,
  • course_rate_p95 [°/s] — p95 tempa zmiany KURSU WYGŁADZONEGO (kurs z prędkości
                        okna 1 s; różnica kursów próbkowana co ≥0.5 s) — kurs
                        tick-po-ticku jest zdominowany szumem estymaty tracka
                        (zmierzone: ramię B p50 ~2855 °/s dla celów lecących
                        prosto) i jako cecha online wymaga wygładzenia,
  • frac_closing      — frakcja ticków z v_rad > 0.3 m/s (tempo zbliżania),
  • t_in_band_s [s]   — czas tracka w pasie admisji dh∈[5,18] m,
  • t_in_zone_s [s]   — czas tracka w dh<18 m (czas w strefie),
  • speed_p50 [m/s]   — mediana modułu prędkości tracka,
  • dh_min_track [m]  — minimalne dh tracka w epizodzie (CZY cel schodzi pod 5 m —
                        kandydat na najsilniejszy dyskryminator: wabik-krążownik
                        nigdy nie zejdzie, cel poważny w siatce schodzi).
(reakcja na manewr obrońcy — cecha interakcyjna, NIE liczalna z dzisiejszych
logów; nazwana w raporcie, tu nieobecna.)

BASELINE NULL: każdy dzisiejszy cel jest „poważny" (prosty, radialny w pierwszym
segmencie, v∈{0,0.5,1.0}) ⇒ rozkłady p5/p50/p95 tych cech = przyszły zbiór
negatywny klasyfikatora wabika i darmowy test FP. Ramiona V2 i B raportowane
osobno (track percepcyjny vs emulowany) + pula łączna.

Wyjście: results/WABIK_RECON/r2_null.json + tabele stdout.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

OUTD = os.path.join(ROOT, "results", "WABIK_RECON")
CAMPS = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
         ("FANTOM_S2", "results/FANTOM/camp")]
WIN = 1.0      # [s] okno różnicowe prędkości
V_CLOSE = 0.3  # [m/s] próg „zbliża się"


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))]


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def episode_features(rows):
    """rows: [(t, [N,E])] ticki z WAŻNYM trackiem. Cechy online (okno 1 s wstecz)."""
    if len(rows) < 25:
        return None
    vr, cr, sp = [], [], []
    dh_min = 1e9
    hd_prev = None
    t_hd_prev = None
    t_band = 0.0
    t_zone = 0.0
    import bisect
    ts = [r[0] for r in rows]
    for i in range(1, len(rows)):
        t, p = rows[i]
        dt_tick = t - rows[i - 1][0]
        if 0 < dt_tick <= 0.5:
            dh = math.hypot(p[0], p[1])
            dh_min = min(dh_min, dh)
            if dh < 18.0:
                t_zone += dt_tick
                if dh >= 5.0:
                    t_band += dt_tick
        j = bisect.bisect_left(ts, t - WIN)
        if j >= i or ts[i] - ts[j] < 0.5:
            continue
        q = rows[j][1]
        dt = t - ts[j]
        vN, vE = (p[0] - q[0]) / dt, (p[1] - q[1]) / dt
        dh_now = math.hypot(p[0], p[1])
        dh_then = math.hypot(q[0], q[1])
        vr.append((dh_then - dh_now) / dt)          # + = zbliża się do home
        v = math.hypot(vN, vE)
        sp.append(v)
        if v > 0.15:
            hd = math.degrees(math.atan2(vE, vN))      # kurs z predkosci OKNA 1 s (wygladzony)
            if hd_prev is not None and t - t_hd_prev >= 0.5:
                cr.append(abs(wrap(hd - hd_prev)) / (t - t_hd_prev))
                hd_prev, t_hd_prev = hd, t
            elif hd_prev is None:
                hd_prev, t_hd_prev = hd, t
        else:
            hd_prev = None
            t_hd_prev = None
    if len(vr) < 20:
        return None
    return {"v_rad_p50": round(pct(vr, 0.5), 3),
            "course_rate_p95": round(pct(cr, 0.95), 1) if cr else None,
            "frac_closing": round(sum(1 for x in vr if x > V_CLOSE) / len(vr), 3),
            "t_in_band_s": round(t_band, 1), "t_in_zone_s": round(t_zone, 1),
            "speed_p50": round(pct(sp, 0.5), 3),
            "dh_min_track": round(dh_min, 2) if dh_min < 1e8 else None,
            "n_okno": len(vr)}


def main():
    eps_out = []
    for camp, base in CAMPS:
        for i in range(1, 13):
            for arm in ("V2", "B"):
                d = os.path.join(ROOT, base, f"r{i}_{arm}")
                if not os.path.isdir(d):
                    continue
                demo = list(iter_jsonl(os.path.join(d, "demo.jsonl")))
                by_sid = {}
                for r in demo:
                    if r.get("track_valid") and r.get("trk_pos_ned"):
                        by_sid.setdefault(r["scenario_id"], []).append(
                            (r["t_sim"], r["trk_pos_ned"][:2]))
                for sid, rows in by_sid.items():
                    f = episode_features(sorted(rows))
                    if f:
                        f.update({"camp": camp, "arm": arm, "boot": f"r{i}_{arm}", "sid": sid})
                        eps_out.append(f)
    # agregaty
    def agg(sel, label):
        out = {"label": label, "n_epizodow": len(sel)}
        for k in ("v_rad_p50", "course_rate_p95", "frac_closing",
                  "t_in_band_s", "t_in_zone_s", "speed_p50", "dh_min_track"):
            xs = [e[k] for e in sel if e.get(k) is not None]
            out[k] = {"p5": pct(xs, 0.05), "p50": pct(xs, 0.5), "p95": pct(xs, 0.95),
                      "n": len(xs)}
        return out
    aggs = [agg(eps_out, "POOL (V2+B, 3 kampanie)"),
            agg([e for e in eps_out if e["arm"] == "V2"], "V2 (track percepcyjny)"),
            agg([e for e in eps_out if e["arm"] == "B"], "B (track emulowany)")]
    for camp, _ in CAMPS:
        aggs.append(agg([e for e in eps_out if e["camp"] == camp], camp))
    for a in aggs:
        print(f"== {a['label']} (n={a['n_epizodow']}) ==")
        for k, v in a.items():
            if isinstance(v, dict):
                print(f"  {k:18s} p5={v['p5']}  p50={v['p50']}  p95={v['p95']}  (n={v['n']})")
    json.dump({"okno_s": WIN, "prog_closing_ms": V_CLOSE,
               "zrodla": "demo.jsonl trk_pos_ned/track_valid (sygnal online feedu); "
                         "cechy bez GT; ramiona V2/B osobno",
               "agregaty": aggs, "epizody": eps_out},
              open(os.path.join(OUTD, "r2_null.json"), "w"), indent=1)
    print(f"zapisano r2_null.json ({len(eps_out)} epizodów)")


if __name__ == "__main__":
    main()
