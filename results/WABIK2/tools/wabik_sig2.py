#!/usr/bin/env python3
"""results/WABIK2/tools/wabik_sig2.py — selekcja reguły agregacji czasowej
(PRE_WABIK2 §1-§2; PROMPT_WABIK2_S1 §1). NOWY plik; wabik_sig.py v1 NIETYKALNY.

PREDYKAT KLATKOWY W(t) — LITERĄ FREEZE_WABIK (progi NIETYKALNE, cytat):
  V_MOVE = 0.30 m/s · V_RAD_MAX = 0.30 m/s · DH_MIN_FLOOR = 5.0 m ·
  R_ZONE = 18.0 m · WIN = 1.0 s;
  W(t) = [speed>V_MOVE] ∧ [dh<R_ZONE] ∧ [v_rad<V_RAD_MAX] ∧ [dh_min_dot≥5].
Semantyka odwołania bez zmian: po fladze złamanie podłogi dh_min<5 ⇒ cofnięta.

RODZINY REGUŁ (lista zamknięta PRE §1; T_FLAG=12 s bazowe):
  baza  — reguła (i): streak ciągły ≥12 s (zero tolerancji) — KOTWICA
          IMPLEMENTACYJNA: musi odtworzyć wyniki wabik_sig v1 co do liczb;
  A(K)  — streak przeżywa ≤K KOLEJNYCH klatek ¬W (K∈{2,3,5}); flaga gdy
          t − streak_start ≥ 12 s;
  B(θ,T_dec) — flaga gdy frac(W) ≥ θ w PEŁNYM oknie przesuwnym T_dec s
          (θ∈{0.80,0.85,0.90} × T_dec∈{8,10,12});
  C     — zegar i stan od początku CIĄGŁEGO segmentu śledzenia (przerwa
          klatek trk >1.0 s resetuje stan reguły i zegar) — solo = baza+C;
  A×C, B×C — kombinacje.
PODWÓJNY ZEGAR: czas-do-flagi raportowany od pierwszej klatki epizodu ORAZ
od startu ciągłego segmentu zawierającego flagę; kryterium selekcji używa
zegara zgodnego z definicją wariantu (C → segmentowy; nie-C → od pierwszej
klatki, segmentowy obok informacyjnie).

Tryby: --anchor (kotwica vs v1 na feedach S2) · --table (pełna tabela
wariant×epizod + NULL) → results/WABIK2/s1_tabela.json.
"""
import bisect
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# --- progi klatkowe: LITERA FREEZE_WABIK (NIETYKALNE) ---
V_MOVE = 0.30
V_RAD_MAX = 0.30
DH_MIN_FLOOR = 5.0
R_ZONE = 18.0
WIN = 1.0
T_FLAG = 12.0
GAP_SEG = 1.0        # [s] przerwa klatek trk rwie ciągły segment śledzenia (C)


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


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


def frame_stream(rows):
    """Strumień (t, W, dh_min_dot, seg_start) — W(t) literą FREEZE_WABIK (jak v1:
    klatki bez policzalnego okna NIE wchodzą do agregacji)."""
    ts = [r[0] for r in rows]
    dh_min = 1e9
    seg_start = None
    prev_t = None
    out = []
    for i, (t, p) in enumerate(rows):
        if prev_t is None or t - prev_t > GAP_SEG:
            seg_start = t
        prev_t = t
        dh = math.hypot(p[0], p[1])
        dh_min = min(dh_min, dh)
        j = bisect.bisect_left(ts, t - WIN)
        if j >= i or ts[i] - ts[j] < 0.5:
            continue
        q = rows[j][1]
        dt = t - ts[j]
        vN, vE = (p[0] - q[0]) / dt, (p[1] - q[1]) / dt
        speed = math.hypot(vN, vE)
        v_rad = (math.hypot(q[0], q[1]) - dh) / dt
        W = (speed > V_MOVE) and (dh < R_ZONE) and (v_rad < V_RAD_MAX) \
            and (dh_min >= DH_MIN_FLOOR)
        out.append((t, W, dh_min, seg_start))
    return out


def evaluate(rows, K=0, theta=None, T_dec=None, C=False):
    """Zwraca wynik epizodu dla wariantu. K=0 ∧ theta=None ∧ C=False == baza (i)."""
    st = frame_stream(rows)
    t_flag = None
    t_revoke = None
    flag_seg_start = None
    streak_t0 = None
    bad_run = 0
    winbuf = []                      # (t, W) do rodziny B
    cur_seg = None
    for (t, W, dh_min, seg_start) in st:
        if C and cur_seg is not None and seg_start != cur_seg:
            streak_t0 = None
            bad_run = 0
            winbuf = []
        cur_seg = seg_start
        if t_flag is None:
            if theta is None:
                if W:
                    bad_run = 0
                    if streak_t0 is None:
                        streak_t0 = t
                    if t - streak_t0 >= T_FLAG:
                        t_flag = t
                        flag_seg_start = seg_start
                else:
                    bad_run += 1
                    if bad_run > K:
                        streak_t0 = None
                        bad_run = 0
            else:
                winbuf.append((t, W))
                while winbuf and t - winbuf[0][0] > T_dec:
                    winbuf.pop(0)
                if winbuf and t - winbuf[0][0] >= T_dec - 0.15 and len(winbuf) >= 10:
                    frac = sum(1 for (_, w) in winbuf if w) / len(winbuf)
                    if frac >= theta:
                        t_flag = t
                        flag_seg_start = seg_start
        if t_flag is not None and t_revoke is None and dh_min < DH_MIN_FLOOR:
            t_revoke = t
    t0_first = rows[0][0] if rows else None
    return {"ever": t_flag is not None,
            "final": t_flag is not None and t_revoke is None,
            "t_flag_od_pierwszej": (round(t_flag - t0_first, 2) if t_flag is not None else None),
            "t_flag_od_segmentu": (round(t_flag - flag_seg_start, 2) if t_flag is not None else None),
            "t_revoke": (round(t_revoke - t0_first, 2) if t_revoke is not None else None)}


def variants():
    out = [("baza(i)", dict(K=0, theta=None, T_dec=None, C=False), 0)]
    for K in (2, 3, 5):
        out.append((f"A(K={K})", dict(K=K, theta=None, T_dec=None, C=False), 1))
    for th in (0.80, 0.85, 0.90):
        for td in (8, 10, 12):
            out.append((f"B(θ={th},T={td}s)", dict(K=0, theta=th, T_dec=float(td), C=False), 1))
    out.append(("C", dict(K=0, theta=None, T_dec=None, C=True), 1))
    for K in (2, 3, 5):
        out.append((f"A(K={K})×C", dict(K=K, theta=None, T_dec=None, C=True), 2))
    for th in (0.80, 0.85, 0.90):
        for td in (8, 10, 12):
            out.append((f"B(θ={th},T={td}s)×C", dict(K=0, theta=th, T_dec=float(td), C=True), 2))
    return out


S2_EPS = [("bA_tp1", "w00a_s01", "TP"), ("bA_tp1", "w00b_s01", "TP"),
          ("bA_tp1", "w01a_s01", "TP"), ("bA_tp1", "w01b_s01", "TP"),
          ("bB_tp2fp", "w02a_s01", "TP"), ("bB_tp2fp", "w02b_s01", "TP"),
          ("bB_tp2fp", "c08_s03", "FP"), ("bB_tp2fp", "c10_s02", "FP"),
          ("bC_fporb", "m00_s01", "FP"),
          ("bC_fporb", "m01_s01", "ORB"), ("bC_fporb", "m01_s02", "ORB")]


def load_s2():
    out = []
    for boot, sid, rodz in S2_EPS:
        d = os.path.join(ROOT, "results", "WABIK", "s2", boot)
        e = next(x for x in episodes_of(d) if x["sid"] == sid)
        rows = feed_rows(os.path.join(d, "percep_feed.jsonl"), e["t0"], e["t1"])
        out.append((sid, rodz, rows))
    return out


def load_null():
    camps = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
             ("FANTOM_S2", "results/FANTOM/camp")]
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
                    cases.append((f"{camp}:r{i}:{e['sid']}", rows))
    return cases


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--table"
    s2 = load_s2()
    if mode == "--anchor":
        print("== KOTWICA: baza(i) vs wabik_sig v1 (wyniki z s2_wyniki.json) ==")
        ref = json.load(open(os.path.join(ROOT, "results", "WABIK", "s2_wyniki.json")))
        refmap = {e["sid"]: e["klasyfikator"] for e in ref["epizody"]}
        ok = True
        for sid, rodz, rows in s2:
            r = evaluate(rows)
            v1 = refmap[sid]
            same = (r["ever"] == (v1["etykieta"] == "wabik")
                    and r["final"] == (v1["etykieta_koncowa"] == "wabik")
                    and (r["t_flag_od_pierwszej"] == v1["t_do_flagi_s"]
                         or (r["t_flag_od_pierwszej"] is None and v1["t_do_flagi_s"] is None)))
            ok &= same
            print(f"  {sid:10s} v2: ever={r['ever']} final={r['final']} "
                  f"t={r['t_flag_od_pierwszej']} | v1: {v1['etykieta']}/{v1['etykieta_koncowa']} "
                  f"t={v1['t_do_flagi_s']} → {'ZGODNE' if same else 'ROZJAZD'}")
        print("KOTWICA:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    null = load_null()
    print(f"[table] S2: {len(s2)} epizodów; NULL: {len(null)} epizodów")
    table = []
    for (name, cfg, n_mech) in variants():
        row = {"wariant": name, "n_mechanizmow": n_mech, "cfg": cfg, "epizody": {}}
        zegar = "t_flag_od_segmentu" if cfg["C"] else "t_flag_od_pierwszej"
        tp_ok = 0
        fp_flags = 0
        orb_final = 0
        zbliz_ok = 0
        for sid, rodz, rows in s2:
            r = evaluate(rows, **cfg)
            row["epizody"][sid] = r
            if rodz == "TP":
                tz = r[zegar]
                if r["ever"] and tz is not None and tz <= 15.0:
                    tp_ok += 1
                    if sid.startswith("w02"):
                        zbliz_ok += 1
            elif rodz == "FP":
                fp_flags += int(r["ever"])
            elif rodz == "ORB":
                orb_final += int(not r["final"])
        nf = ne = 0
        for _, rows in null:
            r = evaluate(rows, **cfg)
            ne += int(r["ever"])
            nf += int(r["final"])
        row.update({"TP_le15": tp_ok, "ZBLIZ_le15": zbliz_ok, "FP_flags": fp_flags,
                    "ORB_final_niew": orb_final, "NULL_ever": ne, "NULL_final": nf,
                    "zegar_kryterium": zegar})
        row["dopuszczony"] = (tp_ok >= 5 and fp_flags == 0 and orb_final == 2 and nf <= 13)
        table.append(row)
        print(f"  {name:16s} mech={n_mech} TP≤15={tp_ok}/6 (ZBLIŻ {zbliz_ok}/2) "
              f"FP={fp_flags}/3 ORB_ok={orb_final}/2 NULL ever/final={ne}/{nf} "
              f"{'DOPUSZCZONY' if row['dopuszczony'] else '-'}")
    # selekcja literą PRE §2.2
    adm = [r for r in table if r["dopuszczony"]]
    winner = None
    if adm:
        adm.sort(key=lambda r: (r["n_mechanizmow"], r["NULL_final"]))
        winner = adm[0]
        print(f"ZWYCIĘZCA: {winner['wariant']} (mech={winner['n_mechanizmow']}, "
              f"NULL_final={winner['NULL_final']})")
    else:
        print("BRAK DOPUSZCZONYCH — ścieżka śmierci S1 (PRE §2.4)")
    json.dump({"progi_klatkowe_FREEZE_WABIK": {"V_MOVE": V_MOVE, "V_RAD_MAX": V_RAD_MAX,
                                               "DH_MIN_FLOOR": DH_MIN_FLOOR, "R_ZONE": R_ZONE,
                                               "WIN": WIN, "T_FLAG": T_FLAG},
               "tabela": table,
               "zwyciezca": (winner["wariant"] if winner else None)},
              open(os.path.join(ROOT, "results", "WABIK2", "s1_tabela.json"), "w"), indent=1)
    print("zapisano s1_tabela.json")


if __name__ == "__main__":
    main()
