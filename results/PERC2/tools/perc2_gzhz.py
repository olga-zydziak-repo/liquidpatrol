#!/usr/bin/env python3
"""results/PERC2/tools/perc2_gzhz.py — pomiar kadencji na poziomie GZ (render-vs-most,
PRE_PERC2 §2.1 / PROMPT_PERC2_S1 §1.2).

Subskrybuje topic kamery bezpośrednio w gz.transport (PRZED mostem ROS): per klatka
rejestruje stempel sensora (header.stamp, sim) i czas ścienny odbioru. Zestawienie
dt na tym poziomie vs dt w percep_feed rozstrzyga, czy klatki gubi RENDER SENSORA
(dt już tu rzadkie) czy TRANSPORT/MOST (tu gęste, w feedzie rzadkie).
Czysty ops: zero importów z toru percepcji (gz.transport to infrastruktura sim).
"""
import argparse
import json
import time

from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--window", type=float, default=35.0)
    ap.add_argument("--out")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    rows = []

    def cb(msg):
        st = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
        rows.append((time.monotonic(), st))

    n = Node()
    assert n.subscribe(Image, a.topic, cb), f"subskrypcja {a.topic} nieudana"
    time.sleep(a.window)

    sim = [r[1] for r in rows]
    wal = [r[0] for r in rows]
    d_sim = [sim[i] - sim[i - 1] for i in range(1, len(sim)) if 0 < sim[i] - sim[i - 1] <= 2.0]
    d_wal = [wal[i] - wal[i - 1] for i in range(1, len(wal)) if 0 < wal[i] - wal[i - 1] <= 2.0]

    def p(xs, q):
        if not xs:
            return None
        s = sorted(xs)
        return round(s[min(len(s) - 1, int(q * (len(s) - 1)))], 4)

    res = {"label": a.label, "topic": a.topic, "window_s": a.window, "n_frames": len(rows),
           "dt_sim_p50": p(d_sim, 0.5), "dt_sim_p90": p(d_sim, 0.9),
           "frac_sim_gt_0p10": (round(sum(1 for d in d_sim if d > 0.10) / len(d_sim), 4)
                                if d_sim else None),
           "dt_wall_p50": p(d_wal, 0.5),
           "hz_sim_p50": (round(1.0 / p(d_sim, 0.5), 2) if d_sim else None)}
    print(json.dumps(res))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
