#!/usr/bin/env python3
"""acts/build_a3_manifest.py — manifest A3 (r03.gate_run_r03 nie emituje manifestu). Buduje ten sam
kształt co A1/A2 (`act_common.build_manifest`) do artefaktów próby; `finalize_manifest` domyka aneks_h.

A3 = GPS-denied (R0.3a NIETKNIĘTY), intruz absent ⇒ brak kanału detekcji celu (detection_channel = n/a).
Uruchom: python3 -m acts.build_a3_manifest <RUNDIR> --world-sdf worlds/world_demo_A3.sdf [--head SHA]
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--world-sdf", required=True); ap.add_argument("--head", default=None)
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    from acts import act_common as AC
    head = args.head or subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                                        capture_output=True, text=True).stdout.strip() or "unknown"
    m = AC.build_manifest("A3", args.world_sdf, head, token_gated=True, contention="none",
                          aneks_h={"note": "S2 GPS-denied (R0.3a NIETKNIĘTY); rtf z kadencji ticków r03"})
    m["detection_channel"] = "n/a"   # A3: intruz absent, decyzja = POS_DEGRADED (nie kanał celu)
    m["note"] = "gate_run_r03 SCEN=S2 (GPS-denied) w world_demo_A3 — ANEKS_D6 §4 próba A3"
    out = os.path.join(args.run_dir, "manifest.json")
    json.dump(m, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"[a3-manifest] → {out} (head={head[:12]} world_hash={str(m.get('world_hash'))[:16]}…)")


if __name__ == "__main__":
    main()
