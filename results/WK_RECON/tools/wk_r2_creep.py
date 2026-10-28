#!/usr/bin/env python3
"""results/WK_RECON/tools/wk_r2_creep.py — R2 PEŁZANIE WYSOKOŚCI (PROMPT_WK_S0 §R2), 0 bootów.

Czyta ISTNIEJĄCE logi lotów (demo.jsonl + manifest.json per boot), nic nie zapisuje poza --out.
Per epizod (scenario_id, attempt), ticki AKTYWNE = cmd_v_ned ≠ 0 (sieć/egzekutor komenderuje;
hold sieci = [0,0,0], net_controller.py:107-111):
  alt = −own_pos_ned[2]; alt0 = alt na 1. ticku aktywnym; alt_max, alt_end (ostatni wiersz epizodu);
  cmd_vz_med = mediana cmd_v_ned[2] po tickach aktywnych (NED: <0 = wznoszenie);
  cmd_vz_med_last30 = mediana po tickach aktywnych z ostatnich 30 s epizodu;
  slope = nachylenie MNK alt(t) po tickach aktywnych [m/s] (>0 = wznosi się).
Klasy (z manifestu, nie z nazwy katalogu): habitat = 'wind' gdy world_hash wskazuje world_wind_*
(model x500_base z enable_wind prependowany przez w_launcher), inaczej 'stock'; ramię = controller
(+ net_arm / liq_arm); feed = 'V2' (kamera det_v2) gdy manifest ma blok feed_v2, inaczej 'emul'.

Użycie: wk_r2_creep.py <out.json> <katalog_boota>...
"""
import glob
import json
import os
import statistics as st
import sys


def classify(man, d):
    wh = man.get("world_hash") or ""
    world = os.path.basename(wh.split()[-1]).replace(".sdf", "") if wh else "?"
    habitat = "wind" if world.startswith("world_wind") else "stock"
    ctrl = man.get("controller") or "?"
    # NET_ARM domyślnie ncp (net_controller.py:52) — dotyczy też opakowań net_akw / net_fantom
    arm = man.get("net_arm") or man.get("liq_arm") or ("ncp" if ctrl.startswith("net") else None)
    # feed kamerowy rozpoznany po artefaktach klienta FEED=V2 w katalogu boota (DEMO-C nie niesie bloku feed_v2)
    feed = "V2" if ("feed_v2" in man or os.path.exists(os.path.join(d, "client_e2e.jsonl"))) else "emul"
    return {"world": world, "habitat": habitat, "controller": ctrl, "arm": arm, "feed": feed,
            "controller_sha16": (man.get("controller_sha") or "")[:16]}


def slope(ts, ys):
    n = len(ts)
    if n < 3:
        return None
    mt, my = sum(ts) / n, sum(ys) / n
    den = sum((t - mt) ** 2 for t in ts)
    return sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / den if den > 0 else None


def episodes(demo):
    eps = {}
    for line in open(demo):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        eps.setdefault((r.get("scenario_id"), r.get("attempt", 0)), []).append(r)
    return eps


def ep_stats(rows):
    act = [r for r in rows if any(abs(c) > 0 for c in r["cmd_v_ned"])]
    if len(act) < 10:
        return None
    t_end = rows[-1]["t_sim"]
    alts = [-r["own_pos_ned"][2] for r in rows]
    a_t = [r["t_sim"] for r in act]
    a_alt = [-r["own_pos_ned"][2] for r in act]
    vz = [r["cmd_v_ned"][2] for r in act]
    vz30 = [r["cmd_v_ned"][2] for r in act if r["t_sim"] >= t_end - 30.0]
    return {"n_rows": len(rows), "n_active": len(act),
            "t_active_s": round(a_t[-1] - a_t[0], 2),
            "alt0": round(a_alt[0], 3), "alt_max": round(max(alts), 3), "alt_end": round(alts[-1], 3),
            "cmd_vz_med": round(st.median(vz), 4),
            "cmd_vz_med_last30": round(st.median(vz30), 4) if vz30 else None,
            "slope_m_s": round(slope(a_t, a_alt), 4) if slope(a_t, a_alt) is not None else None,
            "frac_active_vz_neg": round(sum(1 for v in vz if v < 0) / len(vz), 4)}


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        mp, dp = os.path.join(d, "manifest.json"), os.path.join(d, "demo.jsonl")
        if not (os.path.exists(mp) and os.path.exists(dp)):
            continue
        cls = classify(json.load(open(mp)), d)
        for (sid, att), rows in sorted(episodes(dp).items(), key=lambda kv: kv[1][0]["t_sim"]):
            s = ep_stats(rows)
            if s:
                res.append({"boot": os.path.relpath(d), "sid": sid, "attempt": att, **cls, **s})
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"[zapis] {out}: {len(res)} epizodów z {len(dirs)} katalogów")


if __name__ == "__main__":
    main()
