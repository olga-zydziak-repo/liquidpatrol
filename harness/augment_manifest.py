#!/usr/bin/env python3
"""harness/augment_manifest.py — wstrzykuje pola wrappera do manifest.json PO finalize
(PROMPT_INFRA3 §B1.1 pkt 5/9/7). NIE dotyka sędziego ani logiki finalize — czysta augmentacja:
  - world_hash / world_hash_kind (z world_hash.txt),
  - ulog_sha / ulog_bytes (sha256 + rozmiar boot.ulg — pointer weryfikowalny),
  - model_in_state (dowód obecności intruza, gdy INTRUDER=1).
Idempotentne, brak pola źródłowego ⇒ pole pomijane. Działa też na stub-manifeście.
"""
import argparse
import hashlib
import json
import os


def sha256_size(path):
    if not path or not os.path.exists(path):
        return None, None
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
            n += len(c)
    return h.hexdigest(), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--world-hash-file", default=None)
    ap.add_argument("--ulog", default=None)
    ap.add_argument("--model-in-state", default=None, help="'1'/'0' lub None (gdy bez intruza)")
    a = ap.parse_args()

    mpath = os.path.join(a.out_dir, "manifest.json")
    if not os.path.exists(mpath):
        print(f"[augment] brak {mpath} — pomijam")
        return
    m = json.load(open(mpath))

    if a.world_hash_file and os.path.exists(a.world_hash_file):
        line = open(a.world_hash_file).read().strip()
        m["world_hash"] = line
        m["world_hash_kind"] = "stock" if line.startswith("stock:") else "repo"

    sha, n = sha256_size(a.ulog)
    if sha is not None:
        m["ulog_sha"] = sha
        m["ulog_bytes"] = n

    if a.model_in_state is not None:
        m["model_in_state"] = (str(a.model_in_state).strip() == "1")

    with open(mpath, "w") as f:
        json.dump(m, f, indent=2, default=str)
    print(f"[augment] world_hash={'world_hash' in m} ulog_sha={'ulog_sha' in m} "
          f"model_in_state={m.get('model_in_state')}")


if __name__ == "__main__":
    main()
