#!/usr/bin/env python3
"""results/TRANSIT_RECON/tools/transit_r1.py — R1 PROMPT_TRANSIT_S0: anatomia 6 utrat T6
(cel przechodzi pod ślepym skanem) + kontrole (c08–c11 V2 PASS FANTOM S2).

ZERO bootów/SITL/treningu, zero edycji istniejących plików. Dane: artefakty FANTOM S2
(results/FANTOM/camp), manifest ławki, FROZEN narzędzia importowane READ-ONLY:
  - poscig_recon.Episode/interp (results/POSCIG_RECON/tools) — okna epizodów, GT drona
    (trace, enu2ned), GT intruza z MANIFESTU (analitycznie — wolny od tranzientu
    teleportu; walidacja p50 vs gt_intruder w Episode), t_acq semantyką F1_cel (3 m),
  - det_labels.BootGeo (results/DET_RECON/tools, FROZEN 8f7430cd) — etykieta on-target
    kryterium IDENTYCZNYM z det_replay.py:147-151,
  - yaw z own_q percep_feed (wxyz FRD→NED): psi=atan2(2(wz+xy),1-2(y²+z²)) — konwencja
    akw_rot_strat.py (recon AKW R3).

Per epizod: oś czasu klatek percepcji (yaw fizyczny, azymut GT, stożek ±43.45° =
efektywny stożek ENTRY z edge-margin cx∈[0.10,0.90] — RECON_AKW.md:91), pokrycia FOV
(runy klatek w stożku), w pokryciach: los percepcji (box / on-target / mti_ok / fresh /
ev) i dryf kątowy celu W KADRZE [°/klatkę] (reguła jednostek ANEKS_AKW-1), bliskie
przejście (d_min z GT drona vs manifest; dh/dz/faza), kwarantanna (fantom_qlog),
ŚWIADEK erratum (|ned−cmd|_xy>1 m w surowym gt_intruder — zliczony OBOK).
Klasyfikacja rozłączna (i)/(ii)/(iii) względem bliskiego przejścia.

Wyjście: results/TRANSIT_RECON/r1_anatomia.json + tabela na stdout.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools"),
          os.path.join(ROOT, "results", "DET_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from poscig_recon import Episode, interp, iter_jsonl, _SCEN   # READ-ONLY (metoda POSCIG R1)
from det_labels import BootGeo                                # FROZEN 8f7430cd

OUTD = os.path.join(ROOT, "results", "TRANSIT_RECON")

HALF_CONE = 43.45          # efektywny stożek ENTRY (edge-margin 0.10) — RECON_AKW.md:91
STARE_DPS = 15.0           # |yaw_rate| poniżej = nos w stare (rampa profilu II = 60°/s)
GAP_S = 0.6                # przerwa klatek rwie run pokrycia (>~3× okres 5.1 Hz? nie: 0.6>0.196*3)

T6 = ["c08_s03", "c08_s04", "c10_s02", "c11_s02", "c11_s03", "c11_s04"]
CTRL = ["c08_s01", "c08_s02", "c09_s03", "c09_s04", "c10_s01", "c10_s04"]  # c08–c11 V2 PASS
# (c09_s01 PASS ale valid_final=False — poza n_common, wykluczony jawnie)


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def on_target(row, lab):
    b = row.get("box")
    if not b or lab.get("flag") != "OK":
        return False
    bx, by = b[0] * 640, b[1] * 480      # kadr 640×480 (r02/mti.py:20)
    lb = lab["box"]
    return abs(bx - lb[0]) <= lb[2] / 2 and abs(by - lb[1]) <= lb[3] / 2


def med(xs):
    if not xs:
        return None
    s = sorted(xs)
    return round(s[len(s) // 2], 2)


def analyze(sid, group):
    epi = Episode("FANTOM_S2", "V2", sid)
    d = os.path.join(ROOT, epi.dir)
    t0, tend = epi.t0, epi.t_end_demo
    geo = BootGeo(d, 1.0, 60.0)
    cellb = _SCEN[sid]["cell"]["bearing_deg"]

    # --- bliskie przejście: GT drona (trace) vs manifest intruza, siatka 0.05 s ------
    dmin = (1e9, None)
    t = t0 + 0.2
    while t <= tend:
        dp = interp(epi.drone_gt, t)
        ip = interp(epi.intr, t)
        d3 = math.dist(dp, ip)
        if d3 < dmin[0]:
            dmin = (d3, t)
        t += 0.05
    t_dmin_abs = dmin[1]
    dp = interp(epi.drone_gt, t_dmin_abs)
    ip = interp(epi.intr, t_dmin_abs)
    phase_at = min(epi.demo, key=lambda r: abs(r["t_sim"] - t_dmin_abs))
    dmin_row = {"d3": round(dmin[0], 3), "t_rel": round(t_dmin_abs - t0, 2),
                "dh": round(math.hypot(ip[0] - dp[0], ip[1] - dp[1]), 3),
                "dz": round(abs(ip[2] - dp[2]), 3),
                "phase": phase_at["phase"], "track_valid": phase_at["track_valid"]}

    # --- świadek erratum: surowe gt_intruder w oknie, marker |ned−cmd|_xy>1 m --------
    wit = 0
    wit_rows = 0
    for r in iter_jsonl(os.path.join(d, "gt_intruder.jsonl")):
        if r.get("ned") and r.get("cmd_ned") and t0 <= r["t_sim"] <= tend:
            wit_rows += 1
            if math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0:
                wit += 1

    # --- kwarantanna: q_enter/q_exit w oknie -----------------------------------------
    qev = [r for r in iter_jsonl(os.path.join(d, "fantom_qlog.jsonl"))
           if t0 - 0.5 <= r.get("t", -1) <= tend]

    # --- klatki percepcji w oknie -----------------------------------------------------
    pf = [r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
          if r.get("t_frame") is not None and r.get("own_q") and t0 <= r["t_frame"] <= tend]
    pf.sort(key=lambda r: r["t_frame"])
    dts = [pf[i + 1]["t_frame"] - pf[i]["t_frame"] for i in range(len(pf) - 1)]
    hz = round(1.0 / med(dts), 2) if dts else None

    rows = []
    prev = None
    for r in pf:
        tr = r["t_frame"] - t0
        yw = yaw_of(r["own_q"])
        g = interp(epi.intr, r["t_frame"])
        op = r["own_pos_ned"]
        az = math.degrees(math.atan2(g[1] - op[1], g[0] - op[0]))
        be = wrap(az - yw)
        dh = math.hypot(g[0] - op[0], g[1] - op[1])
        b = r.get("box")
        central = bool(b) and min(b[0], 1.0 - b[0], b[1], 1.0 - b[1]) >= 0.10  # entry_edge_margin (config_r02.py:36)
        row = {"t": tr, "yaw": yw, "az": az, "berr": be, "dh": dh,
               "in_cone": abs(be) <= HALF_CONE,
               "box": b is not None, "central": central, "mti": bool(r.get("mti_ok")),
               "fresh": bool(r.get("fresh")), "gate": r.get("gate"), "ev": r.get("ev"),
               "locked": bool(r.get("locked")),
               "on_tgt": on_target(r, geo.label(r["t_frame"]))}
        if prev is not None and row["t"] - prev["t"] <= GAP_S:
            row["yaw_rate"] = wrap(row["yaw"] - prev["yaw"]) / (row["t"] - prev["t"])
            row["dberr"] = abs(wrap(row["berr"] - prev["berr"]))     # [°/klatkę] dryf w kadrze
            row["daz"] = abs(wrap(row["az"] - prev["az"]))           # [°/klatkę] ruch celu (bez yaw)
        else:
            row["yaw_rate"] = None
            row["dberr"] = None
            row["daz"] = None
        row["stare"] = (row["yaw_rate"] is not None and abs(row["yaw_rate"]) <= STARE_DPS)
        rows.append(row)
        prev = row

    t_acq = epi.t_acq      # semantyka F1_cel (3 m) — poscig_recon
    t_dmin_rel = dmin_row["t_rel"]

    # --- pokrycia: runy klatek in_cone (przerwa > GAP_S rwie) -------------------------
    covs = []
    cur = None
    for row in rows:
        if row["in_cone"]:
            if cur is None or (row["t"] - cur["rows"][-1]["t"]) > GAP_S:
                cur = {"rows": []}
                covs.append(cur)
            cur["rows"].append(row)
        else:
            cur = None
    cov_out = []
    for c in covs:
        rr = c["rows"]
        stare_rr = [x for x in rr if x["stare"]]
        # max run kolejnych klatek z koniunkcją admisji ENTRY (central∧mti; k=3 — config_r02.py:26)
        best = run = 0
        for x in rr:
            run = run + 1 if (x["central"] and x["mti"]) else 0
            best = max(best, run)
        cov_out.append({
            "t_od": round(rr[0]["t"], 2), "t_do": round(rr[-1]["t"], 2),
            "n_kl": len(rr), "n_stare": len(stare_rr),
            "dh_od_do": [round(rr[0]["dh"], 1), round(rr[-1]["dh"], 1)],
            "dberr_stare_med_deg_kl": med([x["dberr"] for x in stare_rr if x["dberr"] is not None]),
            "dberr_stare_max_deg_kl": (round(max(x["dberr"] for x in stare_rr
                                                 if x["dberr"] is not None), 2)
                                       if any(x["dberr"] is not None for x in stare_rr) else None),
            "n_box": sum(1 for x in rr if x["box"]),
            "n_central": sum(1 for x in rr if x["central"]),
            "n_on_tgt": sum(1 for x in rr if x["on_tgt"]),
            "n_mti": sum(1 for x in rr if x["mti"]),
            "n_on_tgt_mti": sum(1 for x in rr if x["on_tgt"] and x["mti"]),
            "max_run_central_mti": best,
            "n_fresh": sum(1 for x in rr if x["fresh"]),
            "ev": sorted({x["ev"] for x in rr if x["ev"]}),
            "przed_dmin": rr[-1]["t"] < t_dmin_rel,
            "przed_acq": (t_acq is None or rr[0]["t"] < t_acq),
        })

    covs_przed_dmin = [c for c in cov_out if c["przed_dmin"]]
    covs_przed_dmin_stare = [c for c in covs_przed_dmin if c["n_stare"] >= 3]
    entry_przed_dmin = any("ENTRY" in c["ev"] for c in covs_przed_dmin)

    # klasa rozłączna (i)/(ii)/(iii) względem bliskiego przejścia
    if not covs_przed_dmin:
        klasa = "i_nigdy_w_FOV"
    elif not entry_przed_dmin:
        klasa = "ii_w_FOV_admisja_pada"
    else:
        klasa = "iii_admisja_za_pozno_inny_powod"

    res = {
        "sid": sid, "group": group, "dir": epi.dir, "bearing_cell_deg": cellb,
        "v_intr": _SCEN[sid]["cell"]["v_intr"], "hz_percep": hz, "n_klatek": len(rows),
        "t0_abs": round(t0, 2), "dur_s": round(tend - t0, 1),
        "real": {"success_D6": epi.rec["success_D6"], "fail_reasons": epi.rec["fail_reasons"],
                 "t_entry_s": epi.rec["t_entry_s"], "d_min_judge": epi.rec["d_min_m"]},
        "t_acq_s": (round(t_acq, 2) if t_acq is not None else None),
        "t_hold0_rel": round(next((r["t_sim"] for r in epi.demo if r["phase"] == "hold"),
                                  epi.demo[0]["t_sim"]) - t0, 2),
        "bliskie_przejscie": dmin_row,
        "swiadek_erratum": {"n_wierszy_gt": wit_rows, "n_artefakt": wit},
        "kwarantanna": qev,
        "gt_manifest_val_p50_m": epi.gt_val_p50,
        "pokrycia_FOV": cov_out,
        "n_pokryc_przed_dmin": len(covs_przed_dmin),
        "n_pokryc_stare3_przed_dmin": len(covs_przed_dmin_stare),
        "ENTRY_przed_dmin": entry_przed_dmin,
        "klasa": klasa,
    }
    return res


def main():
    os.makedirs(OUTD, exist_ok=True)
    out = {"half_cone_deg": HALF_CONE, "stare_thr_dps": STARE_DPS,
           "zrodla": "stożek RECON_AKW.md:91; profil II akw_scan.py:38-42; "
                     "yaw own_q konwencja akw_rot_strat.py; etykieta det_labels 8f7430cd; "
                     "GT intruza = manifest (wolny od tranzientu; ERRATUM_DMIN.md §2)",
           "episodes": []}
    for grp, lst in (("T6", T6), ("CTRL", CTRL)):
        for sid in lst:
            r = analyze(sid, grp)
            out["episodes"].append(r)
            bp = r["bliskie_przejscie"]
            print(f"[R1] {grp} {sid} bear={r['bearing_cell_deg']:3d} hz={r['hz_percep']} "
                  f"t_acq={r['t_acq_s']} dmin={bp['d3']}@{bp['t_rel']}s(dh={bp['dh']},dz={bp['dz']},"
                  f"{bp['phase']},valid={bp['track_valid']}) "
                  f"pokrycia_przed_dmin={r['n_pokryc_przed_dmin']} "
                  f"(stare>=3: {r['n_pokryc_stare3_przed_dmin']}) ENTRY_przed={r['ENTRY_przed_dmin']} "
                  f"klasa={r['klasa']} świadek={r['swiadek_erratum']['n_artefakt']}")
            for c in r["pokrycia_FOV"]:
                if c["przed_acq"]:
                    print(f"      pokrycie {c['t_od']}-{c['t_do']}s n={c['n_kl']} stare={c['n_stare']} "
                          f"dh={c['dh_od_do']} dberr_med/max={c['dberr_stare_med_deg_kl']}/"
                          f"{c['dberr_stare_max_deg_kl']}°/kl box={c['n_box']} centr={c['n_central']} "
                          f"on_tgt={c['n_on_tgt']} mti={c['n_mti']} run(c∧m)={c['max_run_central_mti']} "
                          f"fresh={c['n_fresh']} ev={c['ev']} przed_dmin={c['przed_dmin']}")
    json.dump(out, open(os.path.join(OUTD, "r1_anatomia.json"), "w"), indent=1)
    print("zapisano r1_anatomia.json")


if __name__ == "__main__":
    main()
