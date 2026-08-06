"""p2/extract_labels.py — ekstrakcja etykiet IR z paczki Anti-UAV300 + prowieniencja + sprzątanie.

Krok 0 (A2): rozpakuj paczkę, znajdź IR_label.json (modalność IR — A1), zorganizuj do
p2/data/antiuav_B/<split>/<seq>/IR_label.json, policz sha256 (rider prowieniencji),
USUŃ wideo (mp4) po ekstrakcji, zapisz listę usuniętych (nazwa+rozmiar) do recon.
Split: użyj katalogów test/train/val jeśli są; inaczej deterministyczny po sekwencjach (seed 1234).
Elastyczny na strukturę — po inspekcji dopasować gdyby nazwy inne.
"""
from __future__ import annotations
import os, sys, json, shutil, hashlib, glob, random

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "_raw")
DST = os.path.join(ROOT, "data", "antiuav_B")
FROZEN = os.path.join(ROOT, "frozen")
SOURCE_URL = "https://drive.google.com/file/d/1NPYaop35ocVTYWHOYQQHn8YHsM9jmLGr/view"
SPLIT_SEED = 1234
SPLIT_FRAC = {"train": 0.5, "val": 0.21, "test": 0.29}   # ~160/67/91 proporcje; użyte gdy brak predefiniowanego
IR_LABEL_NAMES = ("IR_label.json", "ir_label.json", "infrared.json", "IR.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def find_ir_labels(base):
    hits = []
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if fn in IR_LABEL_NAMES:
                hits.append(os.path.join(dp, fn))
    return sorted(hits)


def split_of(path):
    p = path.lower()
    for s in ("test", "val", "train"):
        if os.sep + s + os.sep in p:
            return s
    return None


def main():
    labels = find_ir_labels(RAW)
    if not labels:
        print(f"[extract] BRAK IR_label.json w {RAW} — sprawdź rozpakowanie/nazwy.")
        print("[extract] znalezione .json (próbka):")
        for f in glob.glob(os.path.join(RAW, "**", "*.json"), recursive=True)[:10]:
            print("   ", os.path.relpath(f, RAW))
        sys.exit(2)
    # przypisanie splitu
    have_pre = all(split_of(p) for p in labels)
    prov = {"source_url": SOURCE_URL, "modality": "IR", "package": "Anti-UAV300 (6.04GB)",
            "split_source": "predefiniowany (katalogi)" if have_pre else f"deterministyczny seed={SPLIT_SEED}",
            "files": []}
    seqs = []
    for p in labels:
        seq = os.path.basename(os.path.dirname(p))
        seqs.append((seq, p))
    if not have_pre:
        rng = random.Random(SPLIT_SEED); order = sorted(s for s, _ in seqs); rng.shuffle(order)
        n = len(order); ntr = int(n * SPLIT_FRAC["train"]); nvl = int(n * SPLIT_FRAC["val"])
        assign = {s: ("train" if i < ntr else "val" if i < ntr + nvl else "test") for i, s in enumerate(order)}
    for seq, p in seqs:
        split = split_of(p) if have_pre else assign[seq]
        outdir = os.path.join(DST, split, seq); os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "IR_label.json"); shutil.copy2(p, out)
        prov["files"].append({"split": split, "seq": seq, "orig_path": os.path.relpath(p, RAW),
                              "orig_name": os.path.basename(p), "sha256": sha256(out)})
    os.makedirs(FROZEN, exist_ok=True)
    json.dump(prov, open(os.path.join(FROZEN, "provenance.json"), "w"), indent=2, ensure_ascii=False)
    counts = {}
    for f in prov["files"]:
        counts[f["split"]] = counts.get(f["split"], 0) + 1
    print(f"[extract] etykiety IR: {len(prov['files'])} sekwencji, split={counts}, "
          f"prowieniencja→frozen/provenance.json")

    # sprzątanie wideo (mp4/avi) — lista usuniętych z rozmiarami
    deleted = []
    for ext in ("*.mp4", "*.avi", "*.MP4"):
        for v in glob.glob(os.path.join(RAW, "**", ext), recursive=True):
            sz = os.path.getsize(v); deleted.append({"file": os.path.relpath(v, RAW), "bytes": sz})
            os.remove(v)
    total = sum(d["bytes"] for d in deleted)
    json.dump({"deleted_videos": deleted, "total_bytes": total, "total_GB": round(total / 1e9, 2)},
              open(os.path.join(FROZEN, "deleted_videos.json"), "w"), indent=2)
    print(f"[extract] usunięto {len(deleted)} plików wideo ({total/1e9:.2f} GB) → frozen/deleted_videos.json")


if __name__ == "__main__":
    main()
