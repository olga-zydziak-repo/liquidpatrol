#!/usr/bin/env python3
"""bench/tests_bench_finalize.py — bench_finalize bez SITL: manifest bez null; robust na braku danych.

Nie uruchamia bootu. Używa realnego katalogu re-shakeout b2 (read-only) + syntetycznego pustego katalogu.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.bench_finalize import build_manifest

REQUIRED = ("kind", "flight", "boot", "rc", "sha_harness", "controller", "controller_sha", "feed_sha",
            "executor_params_sha", "ulog_sha", "ulog_bytes", "world_hash", "proc_gate",
            "n_demo_rows", "n_episodes", "n_valid_V2p", "n_success_D6", "episodes")
EP_REQUIRED = ("episode_id", "scenario_id", "attempt", "valid_V2p", "success_D6",
               "n_deep_stall", "longest_stall_s", "dsim_dwall", "d_min_m", "refuse_count", "breach")


def _assert_no_null(m):
    def walk(x, path):
        assert x is not None, f"null pod {path}"
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
    walk(m, "manifest")


def test_manifest_on_reshakeout_b2_no_null():
    od = os.path.join(ROOT, "results/BENCH/reshakeout/boot2")
    if not os.path.exists(os.path.join(od, "trace.jsonl")):
        return                                            # brak danych (środowisko) — pomiń
    m = build_manifest(od, boot=2, rc=0, harness_file=os.path.join(ROOT, "bench/bench_flight.py"),
                       arm="E", point="0.0", kind="bench", ulog=None)
    for k in REQUIRED:
        assert k in m, f"brak pola {k}"
    _assert_no_null(m)
    assert m["controller_sha"] and m["executor_params_sha"] and m["feed_sha"], "shas puste na realnym boocie"
    assert m["ulog_sha"] and m["world_hash"], "ulog/world hash puste na realnym boocie"
    assert m["proc_gate"].startswith("CLEAN"), m["proc_gate"]
    assert m["n_episodes"] == 4 and m["n_demo_rows"] > 0
    assert m["n_valid_V2p"] == 4 and m["n_success_D6"] == 4       # D9=V2′: 4/4 (c00 n_deep=5 przechodzi)
    for e in m["episodes"]:
        for k in EP_REQUIRED:
            assert k in e, f"epizod brak {k}"
        assert isinstance(e["valid_V2p"], bool) and isinstance(e["success_D6"], bool)


def test_manifest_on_empty_dir_no_null_no_crash():
    """Robust: brak trace/demo/ulog → manifest bez null (pola puste ''/[]/0), NIE crash, NIE stub."""
    with tempfile.TemporaryDirectory() as td:
        m = build_manifest(td, boot=1, rc=2, harness_file=os.path.join(ROOT, "bench/bench_flight.py"),
                           arm="E", point="0.0", kind="bench", ulog=None)
        for k in REQUIRED:
            assert k in m, f"brak pola {k}"
        _assert_no_null(m)
        assert m["episodes"] == [] and m["n_episodes"] == 0 and m["n_demo_rows"] == 0
        assert m["controller_sha"] == "" and m["ulog_sha"] == "" and m["world_hash"] == ""
        assert m["feed_sha"], "feed_sha fallback (hash pliku feedu) powinien być niepusty"
        assert m["sha_harness"], "sha_harness pliku bench_flight powinien być niepusty"
        assert m["proc_gate"] == "NIEZNANY"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_bench_finalize: ALL PASS")
