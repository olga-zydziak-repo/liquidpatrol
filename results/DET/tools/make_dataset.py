#!/usr/bin/env python3
"""results/DET/tools/make_dataset.py — T2 PROMPT_DET_S1: YOLO-dataset ze WSZYSTKICH etykiet
wg splitu PRE_DET §3 (FROZEN): TEST {c06,c09} · VAL {c02,c04} · TRAIN reszta; stary korpus
2A (c08,c11) wyłącznie TRAIN z konstrukcji; negatywy (puste etykiety F3) w swoich komórkach.

Wejścia: katalogi etykiet (labels/*.txt + meta.jsonl) z det_labels.py 8f7430cd — stary
korpus results/DET_RECON/labels/<boot> (klatki w results/2A/stageA/<boot>/frames), nowy
results/DET/labels/<boot> (klatki w results/DET/collect/<boot>/frames). Komórka bootu
z manifestu (episodes[0].scenario_id → cXX).

Wyjście (LOKALNE, gitignore): results/DET/dataset/{images,labels}/{train,val,test}/
<boot>__<frame>; images = symlinki (oszczędność dysku), labels = kopie. dataset.yaml
zawiera WYŁĄCZNIE train+val (PRE §4: TEST nieobecny w yaml treningu); split test budowany
na dysku dla S2-TEST-raz, ale poza yaml. COMMITOWANY manifest:
results/DET/dataset_manifest.json (liczności per komórka/boot/split + sha zbioru etykiet).

W S1 WYŁĄCZNIE budowa + manifest — zero treningu.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os

ROOT = "/home/olga/projects/liquidpatrol"
SPLIT = {"c06": "test", "c09": "test", "c02": "val", "c04": "val"}   # reszta → train (PRE_DET §3)
OLD = [("results/DET_RECON/labels", "results/2A/stageA")]
NEW = [("results/DET/labels", "results/DET/collect")]
OUT = os.path.join(ROOT, "results/DET/dataset")


def boot_cell(frames_root, boot):
    m = json.load(open(os.path.join(ROOT, frames_root, boot, "manifest.json")))
    return m["episodes"][0]["scenario_id"].split("_")[0]


def main():
    recs = []        # (boot, cell, split, frame_jpg_abs, label_txt_abs)
    for (lab_root, fr_root) in OLD + NEW:
        for lab_dir in sorted(glob.glob(os.path.join(ROOT, lab_root, "*", "labels"))):
            boot = lab_dir.split("/")[-2]
            cell = boot_cell(fr_root, boot)
            split = SPLIT.get(cell, "train")
            for lt in sorted(glob.glob(os.path.join(lab_dir, "*.txt"))):
                base = os.path.basename(lt)[:-4]
                jpg = os.path.join(ROOT, fr_root, boot, "frames", base + ".jpg")
                if os.path.exists(jpg):
                    recs.append((boot, cell, split, jpg, lt))

    # budowa drzewa
    for sp in ("train", "val", "test"):
        for kind in ("images", "labels"):
            os.makedirs(os.path.join(OUT, kind, sp), exist_ok=True)
    h = hashlib.sha256()
    counts = {}
    for (boot, cell, split, jpg, lt) in recs:
        name = f"{boot}__{os.path.basename(jpg)}"
        dst_img = os.path.join(OUT, "images", split, name)
        dst_lab = os.path.join(OUT, "labels", split, name[:-4] + ".txt")
        if not os.path.lexists(dst_img):
            os.symlink(jpg, dst_img)
        lab = open(lt).read()
        open(dst_lab, "w").write(lab)
        h.update((name + "\n" + lab + "\n").encode())
        pos = bool(lab.strip())
        c = counts.setdefault(cell, {}).setdefault(boot, {"split": split, "pos": 0, "neg": 0})
        c["pos" if pos else "neg"] += 1

    yaml = (f"path: {OUT}\ntrain: images/train\nval: images/val\n"
            f"nc: 1\nnames: [intruder]\n")                 # TEST poza yaml (PRE §4)
    open(os.path.join(OUT, "dataset.yaml"), "w").write(yaml)

    totals = {}
    for cell, boots in counts.items():
        for b, c in boots.items():
            t = totals.setdefault(c["split"], {"pos": 0, "neg": 0, "n_boots": 0})
            t["pos"] += c["pos"]; t["neg"] += c["neg"]; t["n_boots"] += 1
    man = {"split_rule": "PRE_DET par.3 FROZEN: TEST c06+c09, VAL c02+c04, TRAIN reszta",
           "n_records": len(recs), "labels_set_sha256": h.hexdigest(),
           "per_cell": counts, "totals": totals,
           "dataset_yaml": yaml}
    with open(os.path.join(ROOT, "results/DET/dataset_manifest.json"), "w") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print(json.dumps({"n_records": len(recs), "totals": totals,
                      "labels_set_sha8": h.hexdigest()[:8]}, indent=1))


if __name__ == "__main__":
    main()
