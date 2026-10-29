#!/usr/bin/env python3
"""results/WK/tools/wk_judge.py — sędziowanie nogi WIATR-KAMERA (PRE_WK §2/§3, PROMPT_WK_S1 §1.4).

Importy READ-ONLY (zero edycji): sędzia bazowy `bench.bench_judge.judge_episode` (8ec0fcfb),
helpery w_judge (e68040ae: `median_err_before_trip`, `EPS_FALSE`=2.0, `_load`), wczytanie bootu
i marker-świadek ERRATUM-DMIN z `results/POSCIG_RECON/tools/erratum_sweep.py` (`load_boot`,
`DEV_GATE`=1.0 m: wiersz gt_intruder z |ned − cmd_ned|_xy > 1 m odrzucony = poza sprzed teleportu).

Per epizod (granice z trace: episode_start.t0_sim … episode_end.sim):
  D6 PEŁNY  = judge_episode(GT drona, gt_intruder wszystkie wiersze, refuse_count, breach)
  D6 ŚWIADEK = to samo na gt_intruder po filtrze-świadku (bramka liczona na ŚWIADKU, PROMPT §2.3)
  refuse_count/breach z eventu episode_end (bench_flight.py:418) — sędzia bazowy liczy je w kryterium e.
  Ważność V2′ = pole valid_V2p epizodu w manifeście (bench_finalize, D9).

REFUSE(GEOFENCE) — klasyfikacja PRE_WK §3 („prawdziwy = estymator zdrowy według w_judge, ε_false 2.0 m"):
  median_err_before_trip (w_judge, poziomy |EKF−GT|, ≤20 ticków w 1 s przed tripem) ORAZ ta sama
  mediana dla osi pionowej (geofence ma gałąź pionową — precedens ANEKS_W-2 §2: pion 0.024 m).
  PRAWDZIWY ⇔ obie mediany < 2.0 m (estymator zdrowy ⇒ odmowa oparta na prawdziwej pozycji);
  FAŁSZYWY ⇔ którakolwiek ≥ 2.0 m; brak ticków ⇒ NIEROZSTRZYGNIĘTE.
  UWAGA kierunku: w_judge.classify() ocenia REFUSE(POS) — tam błąd ≥ ε uzasadnia odmowę; dla
  GEOFENCE ta sama liczba czyta się odwrotnie, dlatego klasy liczone są tu jawnie, nie przez classify().
Inne REFUSE (POS_DEGRADED) i breach raportowane do STOP (PRE §3), nie klasyfikowane.

Użycie: wk_judge.py <out.json> <katalog_boota>...
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bench.bench_judge import judge_episode  # noqa: E402
from bench.w_judge import EPS_FALSE, _load as w_load, _median, _nearest, _enu2ned, median_err_before_trip  # noqa: E402
from erratum_sweep import DEV_GATE, load_boot  # noqa: E402

KEYS = ("success_D6", "fail_reasons", "d_min_m", "t_entry_s", "frac_band_6_10", "sweep_deg")


def vert_err_before_trip(ekf, gt, trip_mono, window_s=1.0, n_max=20):
    """Pionowy odpowiednik w_judge.median_err_before_trip (to samo okno i dobór ticków)."""
    win = sorted([r for r in ekf if trip_mono - window_s <= r["mono"] <= trip_mono], key=lambda r: r["mono"])[-n_max:]
    errs = []
    for e in win:
        g = _nearest(gt, e["mono"])
        if g is None or "z" not in e:
            continue
        errs.append(abs(e["z"] - _enu2ned(g["x"], g["y"], g["z"])[2]))
    return _median(errs), len(errs)


def episode_events(trace):
    ends, refuses, breaches = {}, [], []
    _, _, ev = w_load(trace)
    for e in ev:
        if e.get("ev") == "episode_end":
            ends.setdefault(e.get("episode_id"), e)
        elif e.get("ev") == "refuse":
            refuses.append(e)
        elif e.get("ev") == "breach":
            breaches.append(e)
    return ends, refuses, breaches


def judge_boot(d):
    rel = os.path.relpath(d, ROOT)
    man = json.load(open(os.path.join(d, "manifest.json")))
    man_eps = {e["scenario_id"]: e for e in man.get("episodes", [])}
    eps, drone, intr = load_boot(rel)
    trace = os.path.join(d, "trace.jsonl")
    ends, refuses, breaches = episode_events(trace)
    ekf, gt, _ = w_load(trace)
    out = []
    for eid in sorted(eps):
        e = eps[eid]
        if e["t1"] is None:
            continue
        end = ends.get(eid, {})
        rc, br = int(end.get("refuse", 0) or 0), bool(end.get("breach", False))
        rows = [r for r in intr if r.get("scenario_id") == e["sid"] and e["t0"] <= r["t_sim"] <= e["t1"]]
        dr = [(s, n) for s, n in drone if e["t0"] <= s <= e["t1"]]
        if not rows or not dr:
            continue
        full = [(r["t_sim"], r["ned"]) for r in rows]
        filt = [(r["t_sim"], r["ned"]) for r in rows
                if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) <= DEV_GATE]
        vf = judge_episode(dr, full, refuse_count=rc, breach=br)
        vw = judge_episode(dr, filt, refuse_count=rc, breach=br) if filt else vf
        geo = []
        for r in refuses:
            if r.get("episode_id") != eid:
                continue
            item = {"reason": r.get("reason"), "sim": r.get("sim"), "r_est": r.get("r_est")}
            if str(r.get("reason")).upper() == "GEOFENCE":
                mh, nh = median_err_before_trip(ekf, gt, r["mono"])
                mv, nv = vert_err_before_trip(ekf, gt, r["mono"])
                if mh is None or mv is None:
                    cls = "NIEROZSTRZYGNIETE"
                else:
                    cls = "PRAWDZIWY" if (mh < EPS_FALSE and mv < EPS_FALSE) else "FALSZYWY"
                item.update({"med_err_h_m": None if mh is None else round(mh, 4), "n_h": nh,
                             "med_err_v_m": None if mv is None else round(mv, 4), "n_v": nv,
                             "klasa": cls})
            geo.append(item)
        me = man_eps.get(e["sid"], {})
        alt = [-n[2] for _, n in dr]
        out.append({
            "boot": rel, "episode_id": eid, "scenario_id": e["sid"],
            "valid_V2p": me.get("valid_V2p"), "refuse_count": rc, "breach": br,
            "judge_full": {k: vf[k] for k in KEYS}, "judge_swiadek": {k: vw[k] for k in KEYS},
            "swiadek_n_odrzuconych": len(rows) - len(filt),
            "rozjazd_pelny_swiadek": vf["success_D6"] != vw["success_D6"],
            "refuses": geo,
            "manifest_success_D6": me.get("success_D6"), "manifest_d_min_m": me.get("d_min_m"),
            "repro_manifest": (me.get("success_D6") == vf["success_D6"]
                               and (me.get("d_min_m") is None or vf["d_min_m"] is None
                                    or abs(me["d_min_m"] - vf["d_min_m"]) <= 0.01)) if me else None,
            "gt_alt_max_m": round(max(alt), 3),
        })
    return out, {"boot": rel, "n_breach_events": len(breaches),
                 "refuse_reasons": sorted({str(r.get("reason")) for r in refuses})}


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    eps, boots = [], []
    for d in dirs:
        e, b = judge_boot(os.path.abspath(d))
        eps.extend(e); boots.append(b)
        for x in e:
            print(f"{x['boot']} {x['scenario_id']} V2p={x['valid_V2p']} "
                  f"D6 pełny={x['judge_full']['success_D6']} {x['judge_full']['fail_reasons']} | "
                  f"świadek={x['judge_swiadek']['success_D6']} {x['judge_swiadek']['fail_reasons']} "
                  f"d_min={x['judge_full']['d_min_m']}/{x['judge_swiadek']['d_min_m']} "
                  f"refuse={x['refuses']} repro={x['repro_manifest']} alt_max={x['gt_alt_max_m']}")
    json.dump({"epizody": eps, "booty": boots, "dev_gate_m": DEV_GATE, "eps_false_m": EPS_FALSE},
              open(out, "w"), indent=1, ensure_ascii=False)
    print("[zapis]", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
