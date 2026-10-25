#!/usr/bin/env python3
"""results/PERC2/tools/perc2_s2_analyze.py — analiza bootów S2 (ANEKS_PERC2-1 §3.5-3.6).

Per epizod bootu S2:
  • okno radialne/czołowe (przyrząd 1:1 z perc2_r1.anchor_windows / transit_r1:
    stożek ±43.45° wokół yaw z own_q, runy GAP 0.6 s; okno = pokrycie z max klatek
    z boxem przed t_acq+1 s, a dla epizodów bez akwizycji przed bliskim przejściem),
  • p̂ per-klatkowe central∧MTI w oknie, max run, admisja (run≥3 / ENTRY),
    przewidywanie modelu DP P(run≥3|n,p̂) + przewidywanie S0 (okno ~3× dłuższe @k=1),
  • kadencja percep W LOCIE (dt_p50 per epizod — P-P2-5),
  • D6 OPISOWO literą zamrożonego sędziego (bench.bench_judge.judge_episode na GT
    drona z trace + intruzie z MANIFESTU analitycznie) + ŚWIADEK erratum
    |ned−cmd|_xy>1 m zliczony OBOK na surowym gt_intruder,
  • q_events kwarantanny w oknie epizodu, breach/REFUSE z demo/manifestu.
Wyjście: results/PERC2/s2_okna.json + tabela stdout.
Użycie: perc2_s2_analyze.py <bootdir> [<bootdir>...]
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import scenarios as S
from bench.bench_judge import judge_episode          # sędzia FROZEN 8ec0fcfb (litera)
from common.frames import enu2ned

OUTD = os.path.join(ROOT, "results", "PERC2")
HALF_CONE = 43.45
GAP_S = 0.6
DTC = 0.05
SIM_SPAN = 115.0
MANIFEST = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
SCEN = {e["scenario_id"]: e for e in MANIFEST["episodes"]}


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def interp(series, t):
    if t <= series[0][0]:
        return list(series[0][1])
    if t >= series[-1][0]:
        return list(series[-1][1])
    lo, hi = 0, len(series) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if series[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    t0, p0 = series[lo]; t1, p1 = series[hi]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [p0[k] + a * (p1[k] - p0[k]) for k in range(3)]


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


def p_run3(n, p, k=3):
    if n < k or p <= 0:
        return 0.0
    st = [0.0] * k
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


def analyze_boot(d):
    # epizody + GT drona z trace
    eps = []
    drone_gt = []
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        t = r.get("t")
        if t == "event" and r.get("ev") == "episode_start" and r.get("scenario_id"):
            eps.append({"sid": r["scenario_id"], "t0": r["t0_sim"], "eid": r.get("episode_id")})
        elif t == "gt":
            drone_gt.append((r["sim"], enu2ned([r["x"], r["y"], r["z"]])))
    drone_gt.sort()
    demo = list(iter_jsonl(os.path.join(d, "demo.jsonl")))
    pf = [r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
          if r.get("t_frame") is not None and r.get("own_q")]
    pf.sort(key=lambda r: r["t_frame"])
    man = json.load(open(os.path.join(d, "manifest.json")))
    qev = (man.get("fantom") or {}).get("q_events", [])
    out = []
    for i, e in enumerate(eps):
        sid, t0 = e["sid"], e["t0"]
        drows = [r for r in demo if r.get("scenario_id") == sid]
        if not drows:
            continue
        tend = drows[-1]["t_sim"]
        # intruz z manifestu analitycznie (NED)
        intr = []
        t = 0.0
        while t <= SIM_SPAN:
            x, y, z = S.position_at(SCEN[sid], t)
            intr.append((t0 + t, [x, y, -z]))
            t += DTC
        # świadek erratum OBOK (surowy gt_intruder)
        wit = tot = 0
        for r in iter_jsonl(os.path.join(d, "gt_intruder.jsonl")):
            if r.get("ned") and r.get("cmd_ned") and t0 <= r["t_sim"] <= tend:
                tot += 1
                if math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0:
                    wit += 1
        # walidacja GT manifestu vs log (p50)
        gl = [(r["t_sim"], r["ned"]) for r in iter_jsonl(os.path.join(d, "gt_intruder.jsonl"))
              if r.get("ned") and t0 <= r["t_sim"] <= tend]
        dif = sorted(math.dist(interp(intr, tt)[:2], nn[:2]) for tt, nn in gl[::max(1, len(gl) // 200)])
        gt_val_p50 = round(dif[len(dif) // 2], 3) if dif else None
        # t_acq (semantyka F1_cel — poscig_recon): track_valid ∧ |trk−GT|≤3 m
        t_acq = None
        for r in drows:
            if r.get("track_valid") and r.get("trk_pos_ned"):
                g = interp(intr, r["t_sim"])
                if math.hypot(r["trk_pos_ned"][0] - g[0], r["trk_pos_ned"][1] - g[1]) <= 3.0:
                    t_acq = r["t_sim"] - t0
                    break
        # d_min (GT drona vs manifest)
        dmin = (1e9, None)
        tt = t0 + 0.2
        while tt <= tend:
            d3 = math.dist(interp(drone_gt, tt), interp(intr, tt))
            if d3 < dmin[0]:
                dmin = (d3, tt - t0)
            tt += DTC
        # klatki percep epizodu
        rows = []
        for r in pf:
            if not (t0 <= r["t_frame"] <= tend):
                continue
            yw = yaw_of(r["own_q"])
            g = interp(intr, r["t_frame"])
            op = r["own_pos_ned"]
            be = wrap(math.degrees(math.atan2(g[1] - op[1], g[0] - op[0])) - yw)
            b = r.get("box")
            central = bool(b) and min(b[0], 1.0 - b[0], b[1], 1.0 - b[1]) >= 0.10
            rows.append({"t": r["t_frame"] - t0, "in_cone": abs(be) <= HALF_CONE,
                         "box": b is not None, "central": central,
                         "mti": bool(r.get("mti_ok")),
                         "conj": central and bool(r.get("mti_ok")),
                         "ev": r.get("ev"), "fresh": bool(r.get("fresh")),
                         "dh": math.hypot(g[0] - op[0], g[1] - op[1])})
        dts = [rows[j + 1]["t"] - rows[j]["t"] for j in range(len(rows) - 1)
               if 0 < rows[j + 1]["t"] - rows[j]["t"] <= 2.0]
        dt_p50 = round(pct(dts, 0.5), 4) if dts else None
        frac_slow = round(sum(1 for x in dts if x > 0.10) / len(dts), 4) if dts else None
        # pokrycia stożka
        covs, cur = [], None
        for row in rows:
            if row["in_cone"]:
                if cur is None or (row["t"] - cur[-1]["t"]) > GAP_S:
                    cur = []
                    covs.append(cur)
                cur.append(row)
            else:
                cur = None
        tcut = (t_acq + 1.0) if t_acq is not None else (dmin[1] if dmin[1] else 1e9)
        cands = [c for c in covs if c[0]["t"] < tcut and sum(1 for x in c if x["box"]) >= 3]
        win = max(cands, key=lambda c: sum(1 for x in c if x["box"])) if cands else []
        conj = [x["conj"] for x in win]
        best = run = 0
        for c in conj:
            run = run + 1 if c else 0
            best = max(best, run)
        n = len(win)
        p_hat = round(sum(conj) / n, 3) if n else None
        # D6 literą sędziego (seria GT drona; okno sędziego jak poscig: pełna seria epizodu)
        dser = [(t, p) for t, p in drone_gt if t0 - 1.0 <= t <= tend + 1.0]
        v = judge_episode(dser, intr) if dser else {}
        # q_events i REFUSE/breach z demo
        qe = [q for q in qev if t0 - 0.5 <= q.get("t", -1) <= tend]
        refuse = sum(1 for r in drows if r.get("refuse"))
        out.append({
            "sid": sid, "eid": e["eid"], "t0_abs": round(t0, 2),
            "kadencja_lotu": {"dt_p50": dt_p50, "frac_gt_0p10": frac_slow, "n_klatek": len(rows)},
            "t_acq_s": round(t_acq, 2) if t_acq is not None else None,
            "d_min_gt": {"d3": round(dmin[0], 3), "t_rel": round(dmin[1], 2) if dmin[1] else None},
            "okno": ({"t": [round(win[0]["t"], 2), round(win[-1]["t"], 2)],
                      "dh": [round(win[0]["dh"], 1), round(win[-1]["dh"], 1)],
                      "n_klatek": n, "n_box": sum(1 for x in win if x["box"]),
                      "n_central": sum(1 for x in win if x["central"]),
                      "n_mti": sum(1 for x in win if x["mti"]),
                      "n_conj": sum(conj), "p_hat_conj": p_hat,
                      "max_run_conj": best, "admisja_run3": best >= 3,
                      "ENTRY_w_oknie": any(x["ev"] == "ENTRY" for x in win),
                      "P_model_run3": round(p_run3(n, p_hat or 0.0), 3)} if win else None),
            "ENTRY_epizod": any(x["ev"] == "ENTRY" for x in rows),
            "n_fresh_epizod": sum(1 for x in rows if x["fresh"]),
            "sedzia_D6_opisowo": {"success_D6": v.get("success_D6"),
                                  "fail_reasons": v.get("fail_reasons"),
                                  "t_entry_s": v.get("t_entry_s"), "d_min_m": v.get("d_min_m"),
                                  "frac_band": v.get("frac_band_6_10"), "sweep_deg": v.get("sweep_deg")},
            "swiadek_erratum": {"n_artefakt": wit, "n_wierszy": tot},
            "gt_manifest_val_p50_m": gt_val_p50,
            "kwarantanna_q": [{k: q.get(k) for k in ("t", "ev", "why", "exit")} for q in qe],
            "refuse_ticks": refuse,
        })
    return out


def main():
    boots = sys.argv[1:]
    res = {"zrodla": "przyrzad okien 1:1 perc2_r1/transit_r1; sedzia FROZEN bench_judge "
                     "8ec0fcfb importem (litera); GT intruza=manifest (erratum), swiadek OBOK",
           "booty": {}}
    for d in boots:
        rows = analyze_boot(d)
        res["booty"][os.path.basename(d.rstrip("/"))] = rows
        for r in rows:
            o = r["okno"] or {}
            sj = r["sedzia_D6_opisowo"]
            print(f"[{os.path.basename(d.rstrip('/'))} {r['sid']}] "
                  f"dt_lot={r['kadencja_lotu']['dt_p50']}/{r['kadencja_lotu']['frac_gt_0p10']} "
                  f"t_acq={r['t_acq_s']} okno n={o.get('n_klatek')} p̂={o.get('p_hat_conj')} "
                  f"run={o.get('max_run_conj')} admisja={o.get('admisja_run3')} "
                  f"P_model={o.get('P_model_run3')} ENTRY_ep={r['ENTRY_epizod']} "
                  f"D6={sj.get('success_D6')} fail={sj.get('fail_reasons')} dmin_j={sj.get('d_min_m')} "
                  f"świadek={r['swiadek_erratum']['n_artefakt']}/{r['swiadek_erratum']['n_wierszy']} "
                  f"q={len(r['kwarantanna_q'])}")
    json.dump(res, open(os.path.join(OUTD, "s2_okna.json"), "w"), indent=1)
    print("zapisano s2_okna.json")


if __name__ == "__main__":
    main()
