#!/usr/bin/env python3
"""harness/stub_manifest.py — awaryjny manifest gdy finalize padł (PROMPT_INFRA3 §B1.1 pkt 10).

Lekcja R5: brak manifestu ≠ brak bootu. Gdy finalize rc≠0 LUB brak manifest.json po finalize, wrapper
woła ten skrypt → manifest.json {run_id, arm, point, boot_n, kind:"stub", rc, finalize_rc,
crash_reason (ostatnie 30 linii finalize.log), ts}, run_valid: null. Boot LICZY się jako komplet
artefaktów (osobny wiersz w raporcie z przyczyną).

Nie nadpisuje istniejącego NIE-stub manifestu (idempotencja: jeśli manifest.json już jest i nie jest
kind:stub, kończy bez zmian).
"""
import argparse
import json
import os
import time


def tail_lines(path, n=30):
    if not os.path.exists(path):
        return None
    try:
        with open(path, errors="replace") as f:
            return "".join(f.readlines()[-n:]).strip()
    except Exception as e:
        return f"<nie można odczytać {path}: {e}>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--arm", default=None)
    ap.add_argument("--point", type=float, default=None)
    ap.add_argument("--boot", type=int, required=True)
    ap.add_argument("--rc", type=int, default=None, help="rc modułu lotu")
    ap.add_argument("--finalize-rc", type=int, default=None)
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()

    mpath = os.path.join(args.out_dir, "manifest.json")
    if os.path.exists(mpath):
        try:
            existing = json.load(open(mpath))
            if existing.get("kind") != "stub":
                print(f"[stub] manifest.json istnieje (kind={existing.get('kind')!r}) — nie nadpisuję")
                return
        except Exception:
            pass  # uszkodzony → nadpisz stubem

    run_id = args.run_id or f"{args.arm}-p{args.point}-b{args.boot}"
    manifest = {
        "run_id": run_id,
        "arm": args.arm,
        "point": args.point,
        "boot_n": args.boot,
        "kind": "stub",
        "rc": args.rc,
        "finalize_rc": args.finalize_rc,
        "crash_reason": tail_lines(os.path.join(args.out_dir, "finalize.log"), 30),
        "ts": time.time(),
        "run_valid": None,
    }
    os.makedirs(args.out_dir, exist_ok=True)
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[stub] zapisano stub manifest → {mpath} (finalize_rc={args.finalize_rc})")


if __name__ == "__main__":
    main()
