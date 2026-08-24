#!/usr/bin/env python3
"""
tools/infra1_empty_finalize.py — INFRA-1 I3: manifest pustego bootu walidacyjnego.

Buduje manifest.json + habitat.json dla scenariusza pustego (arm→takeoff→hover→land). Kryteria
habitatu IDENTYCZNE jak PRE_K1 §2 (timejump=0 ∧ Δsim/Δwall≥0.95), liczone na oknie 60 s hoveru
[hover_start_sim, hover_end_sim] przez acts.habitat_gate (ten sam kod co K1). NIE dotyka sędziego,
osłony, kryteriów K1 — to narzędzie diagnostyczne w tools/.

Pola manifestu (do bramki 10 bootów I3): arm_ok, took_off, landed, conv_s, loadavg, mem_free_kb,
session_boot_count, env_restart, b4, timejump_pre/post, ekf_health_hits, habitat_verdict, hover_window.
"""
import os, sys, json, argparse, hashlib


def sha256_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for ch in iter(lambda: f.read(65536), b""):
                h.update(ch)
        return h.hexdigest()
    except Exception:
        return None


def _read_int_file(p, default=None):
    try:
        return int(open(p).read().strip())
    except Exception:
        return default


def _proc_meminfo_kb(key):
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith(key + ":"):
                return int(ln.split()[1])
    except Exception:
        pass
    return None


def _loadavg():
    try:
        return [float(x) for x in open("/proc/loadavg").read().split()[:3]]
    except Exception:
        return None


def load_trace(path):
    gt, ekf, events, meta, outcome = [], [], [], None, None
    if not os.path.exists(path):
        return gt, ekf, events, meta, outcome
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        t = r.get("t")
        if t == "gt":
            gt.append(r)
        elif t == "ekf":
            ekf.append(r)
        elif t == "event":
            events.append(r)
        elif t == "meta":
            meta = r
        elif t == "outcome":
            outcome = r
    return gt, ekf, events, meta, outcome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--boot", type=int, required=True)
    ap.add_argument("--rc", type=int, default=None)
    ap.add_argument("--harness-sha-file", dest="harness_file", required=True)
    a = ap.parse_args()
    od = a.out_dir

    gt, ekf, events, meta, outcome = load_trace(os.path.join(od, "trace.jsonl"))
    ev_by = {}
    for e in events:
        ev_by.setdefault(e.get("ev"), e)
    evs = set(ev_by.keys())

    arm_ok = "armed" in evs
    took_off = "takeoff" in evs
    landed = "touchdown" in evs
    hs = ev_by.get("hover_start", {}).get("sim")
    he = ev_by.get("hover_end", {}).get("sim")

    # habitat na oknie hoveru — ten sam kod i próg co K1 (PRE_K1 §2)
    hab_verdict, hab_detail = "INVALID(habitat)", {}
    try:
        from acts import habitat_gate as HG
        samples = HG.load_rtf(od)
        h1 = HG.h1_lockstep(od, samples) if samples else {"pass": None, "timejump_total": None}
        seg_m, dsim_ok = {"n": 0, "dsim_dwall": None}, False
        if samples and hs is not None and he is not None and he > hs:
            seg = [s for s in samples if hs <= s.get("sim", -1) <= he]
            seg_m = HG.seg_metrics(seg)
            dsim_ok = bool(seg_m.get("dsim_dwall", 0.0) is not None and seg_m["dsim_dwall"] >= HG.H2_DSIM_DWALL_MIN)
        hab_verdict = "VALID" if (arm_ok and landed and h1.get("pass") and dsim_ok) else "INVALID(habitat)"
        hab_detail = {"verdict": hab_verdict,
                      "criterion": "PRE_K1 §2 (na oknie hoveru): timejump=0 ∧ Δsim/Δwall≥0.95",
                      "h1": h1, "dsim_dwall_ok": dsim_ok, "hover_seg": seg_m,
                      "hover_window_sim": [hs, he], "arm_ok": arm_ok, "landed": landed}
        with open(os.path.join(od, "habitat.json"), "w") as f:
            json.dump(hab_detail, f, indent=2)
    except Exception as e:
        hab_detail = {"verdict": "INVALID(habitat)", "error": repr(e)}
        with open(os.path.join(od, "habitat.json"), "w") as f:
            json.dump(hab_detail, f, indent=2)

    _sbc = os.environ.get("K1_SESSION_BOOT_COUNT")
    manifest = {
        "arm": "E", "point": 0.0, "boot_n": a.boot, "kind": "empty",
        "rc": a.rc,
        "arm_ok": arm_ok, "took_off": took_off, "landed": landed,
        "conv_s": _read_int_file(os.path.join(od, "convergence_s.txt"), None),
        "session": {
            "mem_free_kb": _proc_meminfo_kb("MemFree"),
            "mem_available_kb": _proc_meminfo_kb("MemAvailable"),
            "loadavg": _loadavg(),
            "session_boot_count": (int(_sbc) if _sbc not in (None, "") else None),
            "env_restart": (os.environ.get("K1_ENV_RESTART") or None),
            "captured_at": "finalize",
        },
        "b4": (json.load(open(os.path.join(od, "b4_state.json")))
               if os.path.exists(os.path.join(od, "b4_state.json")) else None),
        "timejump_pre": _read_int_file(os.path.join(od, "timejump_pre.txt"), None),
        "timejump_post": _read_int_file(os.path.join(od, "timejump_post.txt"), None),
        "ekf_health_hits": _read_int_file(os.path.join(od, "ekf_health_hits.txt"), None),
        "hover_window_sim": [hs, he],
        "n_gt": len(gt), "n_ekf": len(ekf), "events": [e.get("ev") for e in events],
        "habitat_verdict": hab_verdict,
        "sha_harness": sha256_file(a.harness_file), "harness_file": a.harness_file,
    }
    with open(os.path.join(od, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps({"boot": a.boot, "arm_ok": arm_ok, "landed": landed,
                      "habitat": hab_verdict, "conv_s": manifest["conv_s"],
                      "loadavg1": (manifest["session"]["loadavg"] or [None])[0]}))


if __name__ == "__main__":
    main()
