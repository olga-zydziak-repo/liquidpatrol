#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r1.py — R1 PROMPT_SKAN2_S0: latencja admisji po wejściu celu
w stożek centralny przy nosie nieruchomym (stare), populacje (a) PERC2 S2 @14.7 Hz, (c) FANTOM S2 V2 @5 Hz.

Przyrząd (wszystko z istniejących logów, importy READ-ONLY):
  • epizody i GT drona: trace.jsonl (episode_start, t:"gt"); okno epizodu do ostatniego wiersza demo;
  • GT intruza: MANIFEST analitycznie (bench.scenarios.position_at — reguła erratum), wstawiony do
    det_labels.BootGeo 8f7430cd (its/ips podmienione na serię z manifestu; projekcja FROZEN 1:1);
  • klatki: percep_feed.jsonl (box znorm., mti_ok, fresh, trk_pos_ned, own_q, ev);
  • STOŻEK CENTRALNY = środek rzutu celu (label uvZ) z edge_dist ≥ 0.10 (r02/config_r02.py:36,
    r02/target_channel.py:47-49,124) — ta sama geometria, którą widzi brama ENTRY;
  • STARE = |yaw_rate| < 15°/s między kolejnymi klatkami (yaw z own_q; transit_r1:42);
  • box NA CELU = środek top-1 w boxie etykiety (det_replay.py:149-152);
  • koincydencja = box na celu ∧ box centralny (edge_dist ≥ 0.10) ∧ mti_ok (target_channel.py:124-128);
  • run ≥ 3 = trzecia kolejna klatka koincydencji (ENTRY k=3, config_r02.py:27);
  • fresh NA CELU = fresh ∧ |trk_pos_ned − GT|_xy ≤ 3.0 m (= REFRESH_GATE_M; odsiewa fantomy/locki
    sprzed startu — kwarantanna FANTOM).
ZDARZENIE (tryb MODE, env SKAN2_MODE): "stare" (litera promptu) = odcinek (cel w stożku ∧ stare);
"any" (odchylenie nazwane: admisja w rampie istnieje przy 14.7 Hz — c10_s02 ENTRY przy 60–75°/s) =
odcinek (cel w stożku) przy dowolnym yaw_rate, z frakcją klatek stare w oknie latencji;
pierwsza klatka ciągłego odcinka, przerwa ≤ GAP 0.6 s scala
(perc2_s2_analyze GAP_S), liczone TYLKO przed pierwszą fresh na celu w epizodzie. Wynik per
zdarzenie: czasy do kamieni milowych od startu zdarzenia; okno (długość odcinka); UCIĘTE = fresh
na celu nie zaszła przed końcem odcinka (+ GAP). Ucięte NIE są pomijane.
Wyjście: JSON {warstwa: {bootdir: [epizody]}} (argv[1]) + wydruk.
Użycie: SKAN2_MODE=stare|any skan2_r1.py <out.json> <bootdir>,<warstwa> ...
Warstwy reconu: a = results/PERC2/s2/{bA_c08,bB_c1011}; a2 = results/WK/booty/wk0_b{1,2},
results/WK2/booty/{g0,g15,g3}_b{1,2}, results/WK3/booty/p{1,2}_b{1,2}; c = results/FANTOM/camp/r*_V2.
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/DET_RECON/tools"))
from bench import scenarios as S                          # noqa: E402
from common.frames import enu2ned                        # noqa: E402
from det_labels import BootGeo                           # noqa: E402  READ-ONLY 8f7430cd

MAN = {e["scenario_id"]: e for e in json.load(open(os.path.join(ROOT, "results/BENCH/scenario_manifest.json")))["episodes"]}
EDGE = 0.10
STARE_DPS = 15.0
GAP_S = 0.6
FRESH_GATE_M = 3.0
MODE = os.environ.get("SKAN2_MODE", "stare")


def iter_jsonl(p):
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def edge_dist(cx, cy):
    return min(cx, 1 - cx, cy, 1 - cy)


def analyze(d):
    eps = []
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id"):
            eps.append((r["scenario_id"], r["t0_sim"]))
    demo = list(iter_jsonl(os.path.join(d, "demo.jsonl")))
    pf = sorted((r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
                 if r.get("t_frame") is not None and r.get("own_q")), key=lambda r: r["t_frame"])
    geo = BootGeo(d, 1.0, 60.0)
    out = []
    for sid, t0 in eps:
        drows = [r for r in demo if r.get("scenario_id") == sid]
        if not drows:
            continue
        tend = drows[-1]["t_sim"]
        its, ips = [], []
        t = 0.0
        while t <= tend - t0 + 1.0:
            x, y, z = S.position_at(MAN[sid], t)
            its.append(t0 + t); ips.append([x, y, -z])
            t += 0.05
        geo.its, geo.ips = its, ips                          # GT z manifestu (erratum)
        fr = [r for r in pf if t0 <= r["t_frame"] <= tend]
        rows = []
        prev = None
        for r in fr:
            lab = geo.label(r["t_frame"])
            rate = None
            if prev is not None and r["t_frame"] > prev["t_frame"]:
                rate = abs(wrap(yaw_of(r["own_q"]) - yaw_of(prev["own_q"]))) / (r["t_frame"] - prev["t_frame"])
            prev = r
            inc = False
            on = cen_box = False
            if lab.get("flag") == "OK":
                u, v, Z = lab["uvZ"]
                inc = edge_dist(u / 640, v / 480) >= EDGE
                b = r.get("box")
                if b:
                    on = abs(b[0] * 640 - lab["box"][0]) <= lab["box"][2] / 2 and abs(b[1] * 480 - lab["box"][1]) <= lab["box"][3] / 2
                    cen_box = edge_dist(b[0], b[1]) >= EDGE
            fresh_on = False
            if r.get("fresh") and r.get("trk_pos_ned"):
                i = int(round((r["t_frame"] - t0) / 0.05))
                i = max(0, min(len(ips) - 1, i))
                g = ips[i]
                fresh_on = math.hypot(r["trk_pos_ned"][0] - g[0], r["trk_pos_ned"][1] - g[1]) <= FRESH_GATE_M
            rows.append({"t": r["t_frame"], "inc": inc, "stare": rate is not None and rate < STARE_DPS,
                         "rate": rate, "on": on, "mti": bool(r.get("mti_ok")),
                         "conj": on and cen_box and bool(r.get("mti_ok")), "fresh_on": fresh_on,
                         "Z": lab.get("uvZ", [None, None, None])[2] if lab.get("flag") == "OK" else None})
        t_fresh = next((x["t"] for x in rows if x["fresh_on"]), None)
        dts = [rows[i + 1]["t"] - rows[i]["t"] for i in range(len(rows) - 1)]
        hz = round(1 / sorted(dts)[len(dts) // 2], 2) if dts else None
        # odcinki (inc ∧ stare) przed t_fresh
        segs, cur = [], None
        for x in rows:
            if t_fresh is not None and x["t"] >= t_fresh:
                break
            if x["inc"] and (x["stare"] or MODE == "any"):
                if cur and x["t"] - cur[1] <= GAP_S:
                    cur[1] = x["t"]
                else:
                    if cur:
                        segs.append(cur)
                    cur = [x["t"], x["t"]]
        if cur:
            segs.append(cur)
        evs = []
        for s0, s1 in segs:
            post = [x for x in rows if x["t"] >= s0]
            def first(pred):
                for x in post:
                    if pred(x):
                        return round(x["t"] - s0, 3)
                return None
            run, t_run = 0, None
            for x in post:
                run = run + 1 if x["conj"] else 0
                if run >= 3:
                    t_run = round(x["t"] - s0, 3); break
            lat = {"box_on": first(lambda x: x["on"]), "mti": first(lambda x: x["on"] and x["mti"]),
                   "conj": first(lambda x: x["conj"]), "run3": t_run,
                   "fresh_on": (round(t_fresh - s0, 3) if t_fresh is not None else None)}
            win = round(s1 - s0, 3)
            cens = lat["fresh_on"] is None or lat["fresh_on"] > win + GAP_S
            z0 = next((x["Z"] for x in post if x["Z"] is not None), None)
            t_end = s0 + (lat["fresh_on"] if lat["fresh_on"] is not None else win)
            inw = [x for x in post if x["t"] <= t_end and x["rate"] is not None]
            fr_st = round(sum(1 for x in inw if x["stare"]) / len(inw), 2) if inw else None
            r0 = post[0]["rate"]
            evs.append({"t_rel": round(s0 - t0, 3), "okno_s": win, "uciete": cens, "Z0": z0 and round(z0, 2),
                        "rate0_dps": r0 and round(r0, 1), "frac_stare_do_fresh": fr_st, **lat})
        out.append({"sid": sid, "hz": hz, "t_fresh_on_rel": t_fresh and round(t_fresh - t0, 3), "zdarzenia": evs})
    return out


def main():
    res = {}
    for a in sys.argv[2:]:
        d, lab = a.split(",")
        res.setdefault(lab, {})[d] = analyze(os.path.join(ROOT, d))
    json.dump(res, open(sys.argv[1], "w"), indent=1)
    for lab, boots in res.items():
        for b, eps in boots.items():
            for e in eps:
                print(lab, os.path.basename(b), e["sid"], e["hz"], "fresh_on", e["t_fresh_on_rel"], "zdarzen", len(e["zdarzenia"]))


if __name__ == "__main__":
    main()
