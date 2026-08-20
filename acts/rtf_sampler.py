#!/usr/bin/env python3
"""acts/rtf_sampler.py — ANEKS_D7 §7b: próbnik sim-time↔wall dla bramki habitatu (H1/H2/H4).

W procesie (gz.transport13), ZERO subprocess w pętli (higiena §6: `gz topic -e` per-próbka churnował
transport → sam psuł RTF). Subskrybuje `/world/<W>/clock` (Clock: sim.sec/nsec — ten sam kanał, którego
używa GzPoseClient). Na każdej próbce liczy chwilowe rtf = Δsim/Δwall między kolejnymi próbkami
(decymacja ~min_dt wall) i dopisuje {"wall": unix, "sim": float_sim, "rtf": float} do pliku.

Wielkość AUTORYTATYWNA H2 (Δsim/Δwall) liczona jest w `habitat_gate.py` regresją liniową sim↔wall po
segmencie — pole `rtf` (chwilowe) służy WYŁĄCZNIE do frac<0.5 i p10. sim logowany jako FLOAT (nie int)
→ bez artefaktu obcięcia z §5c.

Uruchom (w runnerze, w tle, ubijany przy teardown):
  python3 -m acts.rtf_sampler --world world_demo_A1 --out RUNDIR/rtf_stream.jsonl [--min-dt 0.08]
Kończy się na SIGTERM/SIGINT (flush + close).
"""
from __future__ import annotations
import argparse, json, signal, sys, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-dt", type=float, default=0.08)   # decymacja wall [s] → ~12 Hz
    args = ap.parse_args()

    import gz.transport13 as _T
    from gz.msgs10 import clock_pb2

    f = open(args.out, "w", buffering=1)   # line-buffered
    state = {"prev_wall": None, "prev_sim": None, "n": 0}

    def on_clock(msg):
        sim = msg.sim.sec + msg.sim.nsec * 1e-9
        wall = time.time()
        pw, ps = state["prev_wall"], state["prev_sim"]
        if pw is not None:
            dw = wall - pw
            if dw < args.min_dt:
                return                      # decymacja
            rtf = (sim - ps) / dw if dw > 0 else 0.0
            f.write(json.dumps({"wall": round(wall, 3), "sim": round(sim, 4),
                                "rtf": rtf}) + "\n")
            state["n"] += 1
        state["prev_wall"] = wall
        state["prev_sim"] = sim

    node = _T.Node()
    ok = node.subscribe(clock_pb2.Clock, f"/world/{args.world}/clock", on_clock)
    if not ok:
        print(f"[rtf_sampler] subscribe FAIL /world/{args.world}/clock", file=sys.stderr)
        sys.exit(2)

    stop = {"v": False}
    def _sig(*_):
        stop["v"] = True
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)

    print(f"[rtf_sampler] START /world/{args.world}/clock → {args.out}", file=sys.stderr)
    while not stop["v"]:
        time.sleep(0.2)
    f.flush(); f.close()
    print(f"[rtf_sampler] STOP n={state['n']}", file=sys.stderr)


if __name__ == "__main__":
    main()
