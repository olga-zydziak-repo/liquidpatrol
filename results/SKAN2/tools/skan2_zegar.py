#!/usr/bin/env python3
"""results/SKAN2/tools/skan2_zegar.py — próbnik dwuzegarowy (PROMPT_SKAN2_S1 §0.4, §2.3).

Co 0.25 s dopisuje {"real": CLOCK_REALTIME, "mono": CLOCK_MONOTONIC} do pliku jsonl.
Skok = |Δreal − Δmono| > 0.05 s między kolejnymi próbkami (lekcja dryfu zegara WSL).
Tryby:
  skan2_zegar.py <out.jsonl> [--seconds N]   — próbkuje (N s albo do SIGTERM)
  skan2_zegar.py --check <out.jsonl>         — wypis: próbki, skoki, dryf real−mono; rc 0 ⇔ 0 skoków
"""
import json
import signal
import sys
import time

PERIOD = 0.25
JUMP_S = 0.05


def check(path):
    rows = []
    for ln in open(path):
        try:
            rows.append(json.loads(ln))
        except ValueError:
            continue
    jumps = []
    for a, b in zip(rows, rows[1:]):
        d = (b["real"] - a["real"]) - (b["mono"] - a["mono"])
        if abs(d) > JUMP_S:
            jumps.append({"real": round(b["real"], 3), "skok_s": round(d, 3)})
    span_m = rows[-1]["mono"] - rows[0]["mono"] if len(rows) > 1 else 0.0
    span_r = rows[-1]["real"] - rows[0]["real"] if len(rows) > 1 else 0.0
    res = {"plik": path, "probki": len(rows), "okno_mono_s": round(span_m, 2),
           "dryf_real_minus_mono_s": round(span_r - span_m, 3), "skoki": len(jumps), "lista": jumps}
    print(json.dumps(res))
    return 0 if not jumps else 1


def sample(path, seconds):
    stop = {"v": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("v", True))
    t_end = time.monotonic() + seconds if seconds else None
    with open(path, "a") as f:
        while not stop["v"] and (t_end is None or time.monotonic() < t_end):
            f.write(json.dumps({"real": time.clock_gettime(time.CLOCK_REALTIME),
                                "mono": time.clock_gettime(time.CLOCK_MONOTONIC)}) + "\n")
            f.flush()
            time.sleep(PERIOD)


def main():
    a = sys.argv[1:]
    if a and a[0] == "--check":
        sys.exit(check(a[1]))
    sec = float(a[a.index("--seconds") + 1]) if "--seconds" in a else None
    sample(a[0], sec)


if __name__ == "__main__":
    main()
