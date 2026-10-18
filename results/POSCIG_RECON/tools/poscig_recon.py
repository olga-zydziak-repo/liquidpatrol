#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/poscig_recon.py — recon pozycji POŚCIG-V1 (PROMPT_POSCIG_S0 R1/R2).

R1: rachunek wykonalności — IDEALNY pościgowiec (punkt materialny, |v_cmd| ≤ V_MAX=3.0
z r01/config.py:24; ta sama saturacja co clip_v kontrolerów) symulowany na REALNEJ
trajektorii GT intruza (manifest `results/BENCH/scenario_manifest.json`, walidowany
vs gt_intruder.jsonl per epizod); werdykt D6 LITERĄ zamrożonego sędziego
(bench.bench_judge.judge_episode, sha 8ec0fcfb). Warianty: start od chwili REALNEJ
akwizycji (pierwszy tick track_valid w demo.jsonl; prefix = realne GT drona) i od t0;
prowadzenie: OGON (na bieżącą pozycję) vs INTERCEPT (punkt wyprzedzenia z pełną
informacją o prędkości celu).

NIE modelowane (jawnie): dynamika wewnętrzna PX4 (przyspieszenia, lag śledzenia
setpointu — GT potrafi chwilowo przekroczyć setpoint, ERRATUM_VMAX.md), szum estymacji
pozycji własnej/celu (R5), wiatr (ławka bez wiatru), ograniczenia yaw. Punkt materialny
integruje komendę idealnie @20 Hz — rachunek jest GÓRNĄ granicą zdolności.

R2: diagnoza zachowania sieci w porażkach z telemetrii (demo.jsonl + GT): d(t), profil
prędkości komend (%V_MAX), kierunek komendy vs LOS/intercept, miejsce upadku D6, mody.

Zero bootów, zero edycji istniejących plików. Wyniki: r1_feasibility.json, r2_behavior.json.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench import scenarios as S                 # position_at (frame: x=N, y=E, z=alt)
from bench.bench_judge import judge_episode      # zamrożony sędzia (litera D6)
from common.frames import enu2ned

OUTDIR = os.path.join(ROOT, "results", "POSCIG_RECON")

# --- Koperta drona (plik:linia w nagłówku raportu) ---------------------------
V_CMD = 3.0          # r01/config.py:24 (V_MAX — clamp normy komendy; net: clip_v net_controller.py:97)
DT = 0.05            # 20 Hz (r01/config.py TICK_HZ=20)
R_ORB = 8.0          # bench/executor_params.json r_orb_m
ENTER_HI = 10.0      # próg approach→orbit (net_controller.py:36)
Z_NED = -12.0        # z_orb_alt_m=12 (executor_params) — separacja pionowa 2 m od intruza (z=10)
K_R = 0.8            # korekcja radialna jak egzekutor (orbit_executor.py:99)
RCLIP = 1.5          # radial_clip_ms
K_Z = 0.6
OMEGA = math.radians(10.5)   # zadane omiatanie 10.5°/s > wymagane 630°/70 s = 9°/s
T_ORB = 70.0
ENTRY_MAX = 25.0
SIM_SPAN = 115.0     # horyzont symulacji od t0 (trajektoria manifestu zdefiniowana do 110 s, potem hold)

# --- Zbiór odniesienia (§Z promptu) ------------------------------------------
V2_11 = ([("FANTOM_S2", "V2", s) for s in
          ["c05_s02", "c08_s03", "c08_s04", "c09_s02", "c10_s02", "c10_s03",
           "c11_s02", "c11_s03", "c11_s04"]] +
         [("AKW_S3", "V2", s) for s in ["c09_s03", "c10_s01"]])
B_2 = [("FANTOM_S2", "B", s) for s in ["c09_s03", "c11_s02"]]
CTRL_5 = [("FANTOM_S2", "V2", s) for s in ["c08_s02", "c09_s03", "c09_s04", "c10_s01", "c10_s04"]]


def jload(p):
    return json.load(open(p))


def iter_jsonl(p):
    with open(p) as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                continue


_MANIFEST = jload(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json"))
_SCEN = {e["scenario_id"]: e for e in _MANIFEST["episodes"]}
_INDEX = jload(os.path.join(OUTDIR, "index_episodes.json"))


class Episode:
    """Ładuje artefakty jednego epizodu: demo rows, t0 (event episode_start), GT drona (trace),
    GT intruza (manifest analitycznie, walidowany vs gt_intruder.jsonl)."""

    def __init__(self, camp, arm, sid):
        rec = _INDEX[f"{camp}:{arm}:{sid}"]
        self.rec = rec
        self.sid = sid
        self.camp = camp
        self.arm = arm
        d = os.path.join(ROOT, rec["dir"])
        self.dir = rec["dir"]
        self.demo = [r for r in iter_jsonl(os.path.join(d, "demo.jsonl")) if r["scenario_id"] == sid]
        assert self.demo, f"brak wierszy demo {sid} w {d}"
        # t0 z eventu episode_start (trace), GT drona z t:gt (gz-ENU→NED jak sędzia)
        self.t0 = None
        self.drone_gt = []
        eid = rec["episode_id"]
        for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
            t = r.get("t")
            if t == "event" and r.get("ev") == "episode_start" and r.get("episode_id") == eid:
                self.t0 = r["t0_sim"]
            elif t == "gt":
                self.drone_gt.append((r["sim"], enu2ned([r["x"], r["y"], r["z"]])))
        assert self.t0 is not None, f"brak episode_start {sid}"
        self.drone_gt.sort()
        self.t_end_demo = self.demo[-1]["t_sim"]
        self.drone_gt = [(t, p) for t, p in self.drone_gt if self.t0 - 1.0 <= t <= self.t_end_demo + 1.0]
        # GT intruza: manifest analitycznie (NED: x=N, y=E, z=-alt), walidacja vs gt_intruder.jsonl
        ep = _SCEN[sid]
        self.intr = []
        t = 0.0
        while t <= SIM_SPAN:
            x, y, z = S.position_at(ep, t)
            self.intr.append((self.t0 + t, [x, y, -z]))
            t += DT
        gtlog = [(r["t_sim"], r["ned"]) for r in iter_jsonl(os.path.join(d, "gt_intruder.jsonl"))
                 if r.get("ned") and self.t0 <= r["t_sim"] <= self.t_end_demo]
        diffs = []
        for tt, ned in gtlog[:: max(1, len(gtlog) // 400)]:
            m = interp(self.intr, tt)
            diffs.append(math.dist(m[:2], ned[:2]))
        diffs.sort()
        self.gt_val_p50 = round(diffs[len(diffs) // 2], 3) if diffs else None
        self.gt_val_max = round(diffs[-1], 3) if diffs else None
        # akwizycja PRAWDZIWEGO celu: pierwszy tick demo z track_valid ∧ |trk − GT_intr| ≤ 3 m
        # (demo loguje SUROWY feed — w ramieniu fantom lock fantomowy jest widoczny w telemetrii
        # mimo kwarantanny delegata; brama 3 m = semantyka klasy F1_cel z akw_analyze)
        self.t_acq = None
        for r in self.demo:
            if r["track_valid"]:
                gt = interp(self.intr, r["t_sim"])
                trk = r["trk_pos_ned"]
                if math.hypot(trk[0] - gt[0], trk[1] - gt[1]) <= 3.0:
                    self.t_acq = r["t_sim"] - self.t0
                    break


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


def vel_of(series, t, h=0.25):
    p0 = interp(series, t - h); p1 = interp(series, t + h)
    return [(p1[k] - p0[k]) / (2 * h) for k in range(3)]


def intercept_dir(own, tgt, tv, vmax):
    """Punkt wyprzedzenia: |tgt + tv·τ − own| = vmax·τ (poziomo). Zwraca wersor poziomy do punktu."""
    rx, ry = tgt[0] - own[0], tgt[1] - own[1]
    a = tv[0] ** 2 + tv[1] ** 2 - vmax ** 2
    b = 2 * (rx * tv[0] + ry * tv[1])
    c = rx ** 2 + ry ** 2
    tau = None
    if abs(a) > 1e-9:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r1 = (-b + math.sqrt(disc)) / (2 * a); r2 = (-b - math.sqrt(disc)) / (2 * a)
            cands = [r for r in (r1, r2) if r > 0]
            tau = min(cands) if cands else None
    elif abs(b) > 1e-9:
        r1 = -c / b
        tau = r1 if r1 > 0 else None
    if tau is None:
        tau = math.hypot(rx, ry) / vmax
    ax, ay = rx + tv[0] * tau, ry + tv[1] * tau
    n = math.hypot(ax, ay)
    return (ax / n, ay / n) if n > 1e-9 else (0.0, 0.0)


def simulate(epi, t_start, guidance):
    """Idealny pościgowiec od t_start (abs sim). Prefix = realne GT drona [t0, t_start].
    Zwraca serię drone_ned do sędziego + t pierwszego wejścia w pasmo przez SYMULANTA."""
    t0 = epi.t0
    series = [(t, p) for t, p in epi.drone_gt if t <= t_start]
    own = interp(epi.drone_gt, t_start) if epi.drone_gt else [0.0, 0.0, -10.0]
    t = t_start
    t_end = t0 + SIM_SPAN
    entry_sim = None
    while t < t_end:
        tgt = interp(epi.intr, t)
        tv = vel_of(epi.intr, t)
        rx, ry = tgt[0] - own[0], tgt[1] - own[1]
        d = math.hypot(rx, ry)
        if entry_sim is None and 6.0 <= d <= 10.0:
            entry_sim = t - t0
        vz = max(-1.0, min(1.0, K_Z * (Z_NED - own[2])))
        vmax_h = math.sqrt(max(V_CMD ** 2 - vz ** 2, 0.0))
        if d > ENTER_HI:                                   # APPROACH
            if guidance == "intercept":
                ux, uy = intercept_dir(own, tgt, tv, vmax_h)
            else:                                          # ogon: na bieżącą pozycję
                ux, uy = rx / d, ry / d
            spd = min(vmax_h, max(0.0, 1.0 * (d - R_ORB)))
            vx, vy = spd * ux, spd * uy
        else:                                              # ORBIT: pełny ff + radial P + styczna
            inx, iny = (rx / d, ry / d) if d > 1e-6 else (0.0, 0.0)
            outx, outy = -inx, -iny
            v_rad = max(-RCLIP, min(RCLIP, K_R * (d - R_ORB)))
            ux_, uy_ = tv[0] + v_rad * inx, tv[1] + v_rad * iny      # u = ff + radial
            if d < 5.0:                                    # ewazja: cel wszedł pod orbitę
                ux_, uy_ = tv[0] + vmax_h * outx * 0.8, tv[1] + vmax_h * outy * 0.8
            tx, ty = -outy, outx                           # styczna CCW (sędzia liczy |Δbearing|)
            vt = OMEGA * max(d, 6.0)
            vx, vy = ux_ + vt * tx, uy_ + vt * ty
            n = math.hypot(vx, vy)
            if n > vmax_h:                                 # priorytet: pasmo przed omiataniem
                un = math.hypot(ux_, uy_)
                if un >= vmax_h:
                    s = vmax_h / un
                    vx, vy = ux_ * s, uy_ * s
                else:                                      # skaluj styczną: |u + s·vt·t̂| = vmax_h
                    bq = 2 * (ux_ * tx + uy_ * ty) * vt
                    aq = vt * vt
                    cq = un * un - vmax_h * vmax_h
                    disc = bq * bq - 4 * aq * cq
                    s = (-bq + math.sqrt(max(disc, 0.0))) / (2 * aq) if aq > 1e-9 else 0.0
                    s = max(0.0, min(1.0, s))
                    vx, vy = ux_ + s * vt * tx, uy_ + s * vt * ty
        own = [own[0] + vx * DT, own[1] + vy * DT, own[2] + vz * DT]
        t += DT
        series.append((t, list(own)))
    return series, entry_sim


def feas_one(epi, t_start_rel, guidance):
    t_start = epi.t0 + max(0.0, t_start_rel)
    series, entry_sim = simulate(epi, t_start, guidance)
    v = judge_episode(series, epi.intr)
    te = v["t_entry_s"]
    return {
        "guidance": guidance, "start_rel_s": round(max(0.0, t_start_rel), 3),
        "success_D6": v["success_D6"], "fail_reasons": v["fail_reasons"],
        "t_entry_s": te, "margin_entry_s": (round(ENTRY_MAX - te, 2) if te is not None else None),
        "frac_band": v["frac_band_6_10"], "sweep_deg": v["sweep_deg"], "d_min_m": v["d_min_m"],
    }


def r1():
    out = {"params": {"V_CMD": V_CMD, "DT": DT, "R_ORB": R_ORB, "Z_NED": Z_NED, "OMEGA_deg_s": 10.5,
                      "zrodla": "V_MAX r01/config.py:24; clip_v r03/controllers/common.py; "
                                "sedzia bench/bench_judge.py:121-127 (DEFAULTS :21-23)",
           "nie_modelowane": "dynamika PX4 (accel/lag; ERRATUM_VMAX), szum estymacji, wiatr, yaw"},
           "episodes": []}
    for grp, lst in (("V2_11", V2_11), ("B_2", B_2), ("CTRL_5", CTRL_5)):
        for camp, arm, sid in lst:
            epi = Episode(camp, arm, sid)
            row = {"group": grp, "camp": camp, "arm": arm, "scenario_id": sid, "dir": epi.dir,
                   "v_intr": _SCEN[sid]["cell"]["v_intr"],
                   "t_acq_s": (round(epi.t_acq, 3) if epi.t_acq is not None else None),
                   "real": {"success_D6": epi.rec["success_D6"], "fail_reasons": epi.rec["fail_reasons"],
                            "t_entry_s": epi.rec["t_entry_s"], "d_min_m": epi.rec["d_min_m"]},
                   "gt_manifest_val_p50_m": epi.gt_val_p50, "gt_manifest_val_max_m": epi.gt_val_max,
                   "from_acq": {}, "from_t0": {}}
            tacq = epi.t_acq if epi.t_acq is not None else 0.0
            for g in ("ogon", "intercept"):
                row["from_acq"][g] = feas_one(epi, tacq, g)
                row["from_t0"][g] = feas_one(epi, 0.0, g)
            out["episodes"].append(row)
            fa = row["from_acq"]; f0 = row["from_t0"]
            print(f"[R1] {grp} {camp}:{arm}:{sid} v={row['v_intr']} t_acq={row['t_acq_s']} "
                  f"real={'PASS' if row['real']['success_D6'] else 'FAIL ' + str(row['real']['fail_reasons'])} | "
                  f"od_akw: ogon={'OK' if fa['ogon']['success_D6'] else fa['ogon']['fail_reasons']} "
                  f"int={'OK' if fa['intercept']['success_D6'] else fa['intercept']['fail_reasons']} "
                  f"(margines wejścia {fa['intercept']['margin_entry_s']}) | "
                  f"od_t0: ogon={'OK' if f0['ogon']['success_D6'] else f0['ogon']['fail_reasons']} "
                  f"int={'OK' if f0['intercept']['success_D6'] else f0['intercept']['fail_reasons']}")
    json.dump(out, open(os.path.join(OUTDIR, "r1_feasibility.json"), "w"), indent=1)
    print("zapisano r1_feasibility.json")


# ----------------------------------- R2 --------------------------------------
def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]


def ang(a, b):
    """kąt [deg] między wektorami 2D."""
    na, nb = math.hypot(*a), math.hypot(*b)
    if na < 1e-9 or nb < 1e-9:
        return None
    c = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (na * nb)))
    return math.degrees(math.acos(c))


def r2():
    out = {"episodes": []}
    for camp, arm, sid in V2_11 + B_2 + CTRL_5:
        grp = "V2_11" if (camp, arm, sid) in V2_11 else ("B_2" if (camp, arm, sid) in B_2 else "CTRL_5")
        epi = Episode(camp, arm, sid)
        t0 = epi.t0
        # d_gt(t) na tickach demo + statystyki komend
        chase_spd, band_rows, chase_rows = [], [], []
        ang_los, ang_int = [], []
        hold_after_acq = 0
        n_valid = 0
        dmin = (1e9, None)       # (d3, t_rel)
        rows = []
        for r in epi.demo:
            t = r["t_sim"]
            dp = interp(epi.drone_gt, t)
            ip = interp(epi.intr, t)
            dh = math.hypot(ip[0] - dp[0], ip[1] - dp[1])
            d3 = math.dist(dp, ip)
            if d3 < dmin[0]:
                dmin = (d3, t - t0)
            cmd = r["cmd_v_ned"]
            ch = (cmd[0], cmd[1])
            spd = math.hypot(*ch)
            valid = r["track_valid"]
            if epi.t_acq is not None and t - t0 > epi.t_acq:
                if r["phase"] == "hold":
                    hold_after_acq += 1
            if valid:
                n_valid += 1
            rows.append((t - t0, dh, spd, valid, r["phase"]))
            if valid and dh > 10.0:
                chase_rows.append((t - t0, dh))
                chase_spd.append(spd)
                if spd > 0.3:
                    tv = vel_of(epi.intr, t)
                    los = (ip[0] - dp[0], ip[1] - dp[1])
                    a1 = ang(ch, los)
                    idir = intercept_dir(dp, ip, tv, V_CMD)
                    a2 = ang(ch, idir)
                    if a1 is not None:
                        ang_los.append(a1)
                    if a2 is not None:
                        ang_int.append(a2)
            if valid and 6.0 <= dh <= 10.0:
                band_rows.append((t - t0, dh, spd))
        # zbieżność d(t) w oknie pościgu (regresja liniowa)
        slope = None
        if len(chase_rows) >= 20:
            n = len(chase_rows)
            mt = sum(x[0] for x in chase_rows) / n
            md = sum(x[1] for x in chase_rows) / n
            num = sum((x[0] - mt) * (x[1] - md) for x in chase_rows)
            den = sum((x[0] - mt) ** 2 for x in chase_rows)
            slope = num / den if den > 1e-9 else None
        # stan w chwili d_min
        at_dmin = min(rows, key=lambda x: abs(x[0] - dmin[1])) if rows else None
        # po wejściu: ucieczka z pasma? (ticki d>10 po pierwszym wejściu w pasmo z trackiem)
        t_in = next((x[0] for x in rows if 6.0 <= x[1] <= 10.0), None)
        out_after_entry = sum(1 for x in rows if t_in is not None and x[0] > t_in and x[1] > 10.0)
        res = {
            "group": grp, "camp": camp, "arm": arm, "scenario_id": sid,
            "v_intr": _SCEN[sid]["cell"]["v_intr"],
            "fail_reasons": epi.rec["fail_reasons"], "success_D6": epi.rec["success_D6"],
            "t_acq_s": (round(epi.t_acq, 3) if epi.t_acq is not None else None),
            "frac_hold_po_akwizycji": round(hold_after_acq / max(1, len(rows)), 4),
            "poscig": {
                "n_tickow": len(chase_rows),
                "spd_p50": round(pct(chase_spd, 0.5), 3) if chase_spd else None,
                "spd_p90": round(pct(chase_spd, 0.9), 3) if chase_spd else None,
                "pct_VMAX_p50": round(100 * pct(chase_spd, 0.5) / V_CMD, 1) if chase_spd else None,
                "pct_VMAX_p90": round(100 * pct(chase_spd, 0.9) / V_CMD, 1) if chase_spd else None,
                "frac_sat_90": (round(sum(1 for s in chase_spd if s >= 0.9 * V_CMD) / len(chase_spd), 3)
                                if chase_spd else None),
                "slope_d_m_s": (round(slope, 3) if slope is not None else None),
                "ang_cmd_LOS_p50": round(pct(ang_los, 0.5), 1) if ang_los else None,
                "ang_cmd_INT_p50": round(pct(ang_int, 0.5), 1) if ang_int else None,
            },
            "pasmo": {"n_tickow": len(band_rows),
                      "spd_p50": round(pct([x[2] for x in band_rows], 0.5), 3) if band_rows else None,
                      "ticki_poza_po_wejsciu": out_after_entry},
            "d_min": {"d3": round(dmin[0], 3), "t_rel": round(dmin[1], 2),
                      "track_valid": bool(at_dmin[3]) if at_dmin else None,
                      "phase": at_dmin[4] if at_dmin else None},
        }
        out["episodes"].append(res)
        p = res["poscig"]
        print(f"[R2] {grp} {camp}:{arm}:{sid} fail={res['fail_reasons']} t_acq={res['t_acq_s']} "
              f"chase n={p['n_tickow']} spd p50/p90={p['spd_p50']}/{p['spd_p90']} "
              f"({p['pct_VMAX_p50']}/{p['pct_VMAX_p90']}% VMAX) slope={p['slope_d_m_s']} "
              f"angLOS={p['ang_cmd_LOS_p50']} angINT={p['ang_cmd_INT_p50']} "
              f"dmin={res['d_min']['d3']}@{res['d_min']['t_rel']}s({res['d_min']['phase']},"
              f"valid={res['d_min']['track_valid']}) out_po_wejsciu={res['pasmo']['ticki_poza_po_wejsciu']}")
    json.dump(out, open(os.path.join(OUTDIR, "r2_behavior.json"), "w"), indent=1)
    print("zapisano r2_behavior.json")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("r1", "all"):
        r1()
    if what in ("r2", "all"):
        r2()
