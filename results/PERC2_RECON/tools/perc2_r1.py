#!/usr/bin/env python3
"""results/PERC2_RECON/tools/perc2_r1.py — R1 PROMPT_PERC2_S0: anatomia kadencji percepcji
+ model łańcucha admisji (sanity prereg: loteria 4/7 @≤5.1 Hz, pewnik @14.3 Hz).

ZERO bootów/SITL/treningu, zero edycji istniejących plików. Dane: percep_feed.jsonl
(t_frame=stempel sensora w sim, wall=monotonic rdzenia feed_vision), summary.json
(push_frame_wall_ms = inferencja+MTI+sample w on_img — percep_proc.py:133-135),
client_e2e.jsonl (e2e_s = sim_now_klienta − t_frame), proc_inventory.txt.

Sensor percepcji: PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf:50-64
(640×480, hfov 1.74, update_rate 15) ⇒ siatka ticków 1/15 s. Hipoteza modów:
mod k = klatka dostarczona co k-ty tick (14.71≈15/1, 7.58≈15/2, 5.10≈15/3).

Model admisji: łańcuch ENTRY wymaga k=3 KOLEJNYCH klatek central∧MTI
(r02/config_r02.py:26, target_channel.py:124-127). Model: klatki w oknie radialnym
niezależne z per-klatkowym p̂ (zmierzonym w TYM oknie) → P(∃ run≥3 w n klatkach) DP.
Okna-kotwice z TRANSIT §R3 (7 radialnych ≤5.1 Hz: PASS c08_s02,c09_s03,c09_s04,
c10_s04 / FAIL c08_s03,c08_s04,c10_s02) + c08_s01 (mod SZYBKI).
Przyrząd okien = kopia metody transit_r1 (stożek ±43.45°, GAP 0.6 s, yaw z own_q).
Wyjście: results/PERC2_RECON/r1_kadencja.json + tabele stdout.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from poscig_recon import Episode, interp, iter_jsonl  # READ-ONLY (wzór transit_r1)

OUTD = os.path.join(ROOT, "results", "PERC2_RECON")
TICK = 1.0 / 15.0          # mono_cam/model.sdf:64 update_rate 15
HALF_CONE = 43.45          # jak transit_r1 (RECON_AKW.md:91)
GAP_S = 0.6

CAMPS = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
         ("FANTOM_S2", "results/FANTOM/camp")]

# okna-kotwice modelu admisji (TRANSIT §R3): 7 radialnych ≤5.1 Hz + c08_s01 SZYBKI
ANCHORS = [("c08_s01", "SZYBKI_kotwica"), ("c08_s02", "PASS"), ("c09_s03", "PASS"),
           ("c09_s04", "PASS"), ("c10_s04", "PASS"), ("c08_s03", "FAIL"),
           ("c08_s04", "FAIL"), ("c10_s02", "FAIL")]
# kotwice FAIL = T6: okno MUSI kończyć się przed bliskim przejściem (t_rel d_min
# z FROZEN wyniku TRANSIT r1_anatomia.json — ta sama litera co ANEKS_TRANSIT-1)
_TR1 = json.load(open(os.path.join(ROOT, "results", "TRANSIT_RECON", "r1_anatomia.json")))
T_DMIN = {e["sid"]: e["bliskie_przejscie"]["t_rel"] for e in _TR1["episodes"]}


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))]


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


# ---------------------------------- A. KADENCJA -----------------------------------
def boot_cadence(camp, d):
    pf = os.path.join(d, "percep_feed.jsonl")
    if not os.path.exists(pf):
        return None
    ts, ws = [], []
    for r in iter_jsonl(pf):
        if r.get("t_frame") is not None and r.get("wall") is not None:
            ts.append(r["t_frame"]); ws.append(r["wall"])
    if len(ts) < 50:
        return None
    # deltas (sim i wall); odrzuć nie-rosnące i >2 s (pauzy/degradacje poza modą)
    dts, dws, ks, resid = [], [], [], []
    for i in range(1, len(ts)):
        dt = ts[i] - ts[i - 1]; dw = ws[i] - ws[i - 1]
        if dt <= 0 or dt > 2.0 or dw <= 0:
            continue
        dts.append(dt); dws.append(dw)
        k = max(1, round(dt / TICK))
        ks.append(k)
        resid.append(abs(dt - k * TICK))
    n = len(dts)
    dt_p50 = pct(dts, 0.5)
    hz = round(1.0 / dt_p50, 2)
    k_mode = max(1, round(dt_p50 / TICK))
    mode = {1: "SZYBKI", 2: "SREDNI", 3: "WOLNY"}.get(k_mode, f"k{k_mode}")
    khist = {}
    for k in ks:
        kk = str(k) if k <= 5 else ">5"
        khist[kk] = khist.get(kk, 0) + 1
    khist = {k: round(v / n, 4) for k, v in sorted(khist.items())}
    # RTF w oknie feedu: suma sim / suma wall (odporna na pojedyncze przerwy)
    rtf = round(sum(dts) / sum(dws), 3)
    # frakcja deltas na siatce ticków (|resid| ≤ 8 ms — pół okresu fizyki 4 ms ×2)
    on_grid = round(sum(1 for r in resid if r <= 0.008) / n, 4)
    out = {"camp": camp, "dir": os.path.relpath(d, ROOT), "n_dt": n,
           "hz_p50": hz, "dt_p50_s": round(dt_p50, 4), "k_mod": k_mode, "mode": mode,
           "k_hist_frac": khist, "frac_on_grid_8ms": on_grid,
           "rtf_feed": rtf,
           "dt_wall_p50_ms": round(pct(dws, 0.5) * 1000, 1),
           "dt_sim_p90_s": round(pct(dts, 0.9), 4)}
    # inferencja (summary percep_proc)
    sp = pf + ".summary.json"
    if os.path.exists(sp):
        s = json.load(open(sp))
        pw = s.get("push_frame_wall_ms") or {}
        out["push_wall_ms_p50"] = pw.get("p50")
        out["push_wall_ms_p95"] = pw.get("p95")
        out["n_frames_sum"] = s.get("n_frames")
    # E2E (client)
    ce = os.path.join(d, "client_e2e.jsonl")
    if os.path.exists(ce):
        es = [r["e2e_s"] for r in iter_jsonl(ce) if r.get("e2e_s") is not None]
        if es:
            out["e2e_p50_s"] = round(pct(es, 0.5), 3)
            out["e2e_p95_s"] = round(pct(es, 0.95), 3)
    # obciążenie hosta: liczba procesów w inwentarzu bootu
    pi = os.path.join(d, "proc_inventory.txt")
    if os.path.exists(pi):
        out["n_proc_inventory"] = sum(1 for _ in open(pi))
    return out


def cadence_all():
    rows = []
    for camp, base in CAMPS:
        for i in range(1, 13):
            d = os.path.join(ROOT, base, f"r{i}_V2")
            if not os.path.isdir(d):
                continue
            r = boot_cadence(camp, d)
            if r:
                r["round"] = i
                rows.append(r)
    return rows


# ------------------------------ B. MODEL ADMISJI ----------------------------------
def p_run3(n, p, k=3):
    """P(∃ run ≥ k sukcesów w n próbach Bernoulliego p) — DP po długości bieżącego runu."""
    if n < k:
        return 0.0
    st = [0.0] * k   # st[j] = P(bieżący run == j, nie było jeszcze runu k)
    st[0] = 1.0
    hit = 0.0
    for _ in range(n):
        ns = [0.0] * k
        for j, pr in enumerate(st):
            if pr == 0.0:
                continue
            ns[0] += pr * (1 - p)
            if j + 1 >= k:
                hit += pr * p
            else:
                ns[j + 1] += pr * p
        st = ns
    return hit


def anchor_windows():
    """Okna radialne kotwic: klatki percep_feed w stożku ±43.45° (runy, GAP 0.6 s),
    wybór okna = pokrycie z max liczbą klatek z boxem PRZED t_acq+1 s (dla FAIL:
    przed bliskim przejściem); per-klatka: central∧mti."""
    res = []
    for sid, grp in ANCHORS:
        epi = Episode("FANTOM_S2", "V2", sid)
        d = os.path.join(ROOT, epi.dir)
        t0, tend = epi.t0, epi.t_end_demo
        pf = [r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
              if r.get("t_frame") is not None and r.get("own_q")
              and t0 <= r["t_frame"] <= tend]
        pf.sort(key=lambda r: r["t_frame"])
        dts = [pf[i + 1]["t_frame"] - pf[i]["t_frame"] for i in range(len(pf) - 1)]
        hz = round(1.0 / pct(dts, 0.5), 2) if dts else None
        rows = []
        for r in pf:
            yw = yaw_of(r["own_q"])
            g = interp(epi.intr, r["t_frame"])
            op = r["own_pos_ned"]
            az = math.degrees(math.atan2(g[1] - op[1], g[0] - op[0]))
            be = wrap(az - yw)
            b = r.get("box")
            central = bool(b) and min(b[0], 1.0 - b[0], b[1], 1.0 - b[1]) >= 0.10
            rows.append({"t": r["t_frame"] - t0, "in_cone": abs(be) <= HALF_CONE,
                         "box": b is not None, "central": central,
                         "mti": bool(r.get("mti_ok")),
                         "conj": central and bool(r.get("mti_ok")),
                         "dh": math.hypot(g[0] - op[0], g[1] - op[1]),
                         "ev": r.get("ev")})
        covs, cur = [], None
        for row in rows:
            if row["in_cone"]:
                if cur is None or (row["t"] - cur[-1]["t"]) > GAP_S:
                    cur = []
                    covs.append(cur)
                cur.append(row)
            else:
                cur = None
        tcut = (epi.t_acq + 1.0) if epi.t_acq is not None else 1e9
        tdmin = T_DMIN.get(sid)
        if grp == "FAIL" and tdmin is not None:
            tcut = min(tcut, tdmin)          # okno radialne PRZED bliskim przejściem
        cands = [c for c in covs if c[0]["t"] < tcut
                 and (grp != "FAIL" or tdmin is None or c[-1]["t"] < tdmin)
                 and sum(1 for x in c if x["box"]) >= 3]
        if not cands:
            continue
        win = max(cands, key=lambda c: sum(1 for x in c if x["box"]))
        n = len(win)
        conj = [x["conj"] for x in win]
        nb = sum(1 for x in win if x["box"])
        p_hat = sum(conj) / n
        best = run = 0
        for c in conj:
            run = run + 1 if c else 0
            best = max(best, run)
        res.append({"sid": sid, "grupa": grp, "hz_boot": hz, "dir": epi.dir,
                    "okno_t": [round(win[0]["t"], 2), round(win[-1]["t"], 2)],
                    "okno_dh": [round(win[0]["dh"], 1), round(win[-1]["dh"], 1)],
                    "n_klatek": n, "n_box": nb,
                    "n_central": sum(1 for x in win if x["central"]),
                    "n_mti": sum(1 for x in win if x["mti"]),
                    "n_conj": sum(conj), "p_hat_conj": round(p_hat, 3),
                    "max_run_conj": best,
                    "ENTRY": any(x["ev"] == "ENTRY" for x in win),
                    "P_model_run3": round(p_run3(n, p_hat), 3)})
    return res


def main():
    os.makedirs(OUTD, exist_ok=True)
    cad = cadence_all()
    print("=== A. KADENCJA per boot V2 (36) ===")
    for r in cad:
        print(f"[{r['camp']:9s} r{r['round']:>2}] hz={r['hz_p50']:6.2f} mod={r['mode']:6s} "
              f"k_hist={r['k_hist_frac']} grid={r['frac_on_grid_8ms']:.2f} "
              f"rtf={r['rtf_feed']:.3f} push={r.get('push_wall_ms_p50')}ms "
              f"e2e_p50={r.get('e2e_p50_s')}s nproc={r.get('n_proc_inventory')}")
    # agregaty per mod
    agg = {}
    for r in cad:
        a = agg.setdefault(r["mode"], {"n": 0, "rtf": [], "push": [], "camps": {}})
        a["n"] += 1
        a["rtf"].append(r["rtf_feed"])
        if r.get("push_wall_ms_p50") is not None:
            a["push"].append(r["push_wall_ms_p50"])
        a["camps"][r["camp"]] = a["camps"].get(r["camp"], 0) + 1
    agg_out = {m: {"n": a["n"], "rtf_p50": pct(a["rtf"], 0.5),
                   "push_p50_ms": pct(a["push"], 0.5), "per_camp": a["camps"]}
               for m, a in agg.items()}
    print("agregaty per mod:", json.dumps(agg_out))

    anch = anchor_windows()
    print("=== B. MODEL ADMISJI (okna-kotwice) ===")
    for a in anch:
        print(f"[{a['grupa']:14s} {a['sid']}] hz={a['hz_boot']} okno {a['okno_t']} "
              f"dh {a['okno_dh']} n={a['n_klatek']} box={a['n_box']} conj={a['n_conj']} "
              f"p̂={a['p_hat_conj']} max_run={a['max_run_conj']} ENTRY={a['ENTRY']} "
              f"P_model(run≥3)={a['P_model_run3']}")
    # sanity prereg: suma przewidywań na 7 oknach wolnych vs obserwowane 4; kotwica szybka ~1
    slow = [a for a in anch if a["grupa"] in ("PASS", "FAIL")]
    exp_slow = sum(a["P_model_run3"] for a in slow)
    obs_slow = sum(1 for a in slow if a["ENTRY"] or a["max_run_conj"] >= 3)
    fast = [a for a in anch if a["grupa"] == "SZYBKI_kotwica"]
    # rozkład Poissona-dwumianowy liczby admisji na oknach wolnych (DP)
    dist = [1.0]
    for a in slow:
        p = a["P_model_run3"]
        nd = [0.0] * (len(dist) + 1)
        for i, pr in enumerate(dist):
            nd[i] += pr * (1 - p)
            nd[i + 1] += pr * p
        dist = nd
    sanity = {"okna_wolne_n": len(slow), "obserwowane_admisje": obs_slow,
              "model_E_admisji": round(exp_slow, 2),
              "model_P(obs)": round(dist[obs_slow], 3) if obs_slow < len(dist) else None,
              "model_rozklad": [round(x, 3) for x in dist],
              "kotwica_szybka": [{"sid": a["sid"], "P_model": a["P_model_run3"],
                                  "max_run": a["max_run_conj"]} for a in fast]}
    print("sanity:", json.dumps(sanity))

    json.dump({"tick_s": round(TICK, 5),
               "zrodla": "sensor mono_cam/model.sdf:50-64 (640x480, hfov 1.74, rate 15); "
                         "push_frame percep_proc.py:133-135; łańcuch admisji k=3 "
                         "config_r02.py:26 + target_channel.py:124-127; okna wzór transit_r1",
               "kadencja": cad, "agregaty_mod": agg_out,
               "model_admisji": {"okna": anch, "sanity": sanity}},
              open(os.path.join(OUTD, "r1_kadencja.json"), "w"), indent=1)
    print("zapisano r1_kadencja.json")


if __name__ == "__main__":
    main()
