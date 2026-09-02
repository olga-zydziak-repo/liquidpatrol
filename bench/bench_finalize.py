#!/usr/bin/env python3
"""bench/bench_finalize.py — manifest pierwszej klasy ławki (ANEKS_BENCH-1a §2 R2).

Wołany z gałęzi `bench)` wrappera zamiast crashującego `k1_finalize` (k1 zakłada certy/piny K1, których
ławka nie ma). Buduje `manifest.json` per boot ławki: lista epizodów (attempt, scenario_id, ważność V2′
= D9 ANEKS-1a §2 R1), controller_sha, feed_sha, executor_params_sha, ulog_sha, world_hash, wynik bramki
procesowej, n wierszy demo. ZERO null (kontrakt jak demo_logger). Sędzia/egzekutor/feed NIETKNIĘTE —
ważność liczona przez `campaign_analyze.judge_boot` (override slotu V2 sędziego frozen 8ec0fcfb).

Nie crashuje na brakujących danych (best-effort, pola puste = "" / [] / 0, NIE null); realny wyjątek →
wrapper łapie (FIN_RC≠0 lub brak manifestu ⇒ stub_manifest, „stub tylko przy crashu").
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def sha256_file(p):
    if not p or not os.path.exists(p):
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_line(path):
    try:
        return open(path).read().strip()
    except Exception:
        return ""


def _meta_from_trace(trace):
    """Pierwszy wiersz t=meta z trace (controller_sha, exec_params_sha, controller)."""
    if not os.path.exists(trace):
        return {}
    with open(trace) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("t") == "meta":
                return r
    return {}


def _demo_summary(demo_path):
    """n wierszy + feed_sha + attempt per epizod (z ep_meta wiersza demo — autorytatywne)."""
    n = 0
    feed_sha = ""
    attempt_by_ep = {}
    if not os.path.exists(demo_path):
        return n, feed_sha, attempt_by_ep
    with open(demo_path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            n += 1
            if not feed_sha and r.get("feed_sha"):
                feed_sha = r["feed_sha"]
            if r.get("episode_id") is not None:
                attempt_by_ep[r["episode_id"]] = r.get("attempt", 0)
    return n, feed_sha, attempt_by_ep


def _episodes_v2p(outdir):
    """Per-epizod ważność V2′ z campaign_analyze.judge_boot (frozen sędzia + override V2). [] gdy brak trace/danych."""
    try:
        from bench.campaign_analyze import judge_boot
        return judge_boot(outdir)
    except Exception:
        return []


def build_manifest(outdir, boot, rc, harness_file, arm, point, kind, ulog):
    trace = os.path.join(outdir, "trace.jsonl")
    meta = _meta_from_trace(trace)
    n_demo, feed_sha_row, attempt_by_ep = _demo_summary(os.path.join(outdir, "demo.jsonl"))
    # feed_sha: preferuj wartość z wiersza demo (co realnie było w locie); fallback = hash pliku feedu
    feed_sha = feed_sha_row or sha256_file(os.path.join(ROOT, "harness/track_feed.py"))

    ulog_sha, ulog_bytes = "", 0
    us = _read_line(os.path.join(outdir, "ulog_sha.txt"))
    if us:
        parts = us.split()
        ulog_sha = parts[0]
        if len(parts) > 1 and parts[1].isdigit():
            ulog_bytes = int(parts[1])
    if not ulog_sha and ulog and os.path.exists(ulog):
        ulog_sha = sha256_file(ulog); ulog_bytes = os.path.getsize(ulog)

    wh_line = _read_line(os.path.join(outdir, "world_hash.txt"))
    world_hash = wh_line.split()[0] if wh_line else ""
    world_ref = wh_line.split()[1] if len(wh_line.split()) > 1 else ""

    proc_gate = _read_line(os.path.join(outdir, "proc_gate.log")) or "NIEZNANY"

    verdicts = _episodes_v2p(outdir)
    episodes = []
    for v in verdicts:
        eid = v.get("episode_id")
        episodes.append({
            "episode_id": eid if eid is not None else -1,
            "scenario_id": v.get("scenario_id", ""),
            "attempt": attempt_by_ep.get(eid, 0),
            "valid_V2p": bool(v.get("valid_campaign_V2p", False)),
            "success_D6": bool(v.get("success_D6", False)),
            "n_deep_stall": int(v.get("stalls", {}).get("n_deep", 0)),
            "longest_stall_s": float(v.get("stalls", {}).get("longest_s", 0.0)),
            "dsim_dwall": float(v.get("stalls", {}).get("dsim_dwall", 1.0)),
            "d_min_m": v.get("d_min_m") if v.get("d_min_m") is not None else -1.0,
            "refuse_count": int(v.get("refuse_count", 0)),
            "breach": bool(v.get("breach", False)),
        })

    manifest = {
        "kind": kind, "flight": "bench", "boot": int(boot), "rc": int(rc),
        "arm": arm, "point": point,
        "harness_file": harness_file or "", "sha_harness": sha256_file(harness_file),
        "controller": meta.get("controller", ""),
        "controller_sha": meta.get("controller_sha", ""),
        "feed_sha": feed_sha,
        "executor_params_sha": meta.get("exec_params_sha", ""),
        "ulog_sha": ulog_sha, "ulog_bytes": ulog_bytes,
        "world_hash": world_hash, "world_ref": world_ref,
        "proc_gate": proc_gate,
        "n_demo_rows": int(n_demo),
        "n_episodes": len(episodes),
        "n_valid_V2p": sum(1 for e in episodes if e["valid_V2p"]),
        "n_success_D6": sum(1 for e in episodes if e["success_D6"]),
        "episodes": episodes,
    }
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--boot", type=int, default=1)
    ap.add_argument("--rc", type=int, default=0)
    ap.add_argument("--harness-sha-file", dest="harness_file", default="")
    ap.add_argument("--arm", default="E")
    ap.add_argument("--point", default="0.0")
    ap.add_argument("--kind", default="bench")
    ap.add_argument("--ulog", default=None)
    a = ap.parse_args()
    m = build_manifest(a.out_dir, a.boot, a.rc, a.harness_file, a.arm, a.point, a.kind, a.ulog)
    with open(os.path.join(a.out_dir, "manifest.json"), "w") as f:
        json.dump(m, f, indent=2)
    print(f"[bench_finalize] manifest.json boot={a.boot} n_episodes={m['n_episodes']} "
          f"valid_V2p={m['n_valid_V2p']} success_D6={m['n_success_D6']} n_demo={m['n_demo_rows']}")


if __name__ == "__main__":
    main()
