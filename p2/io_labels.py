"""p2/io_labels.py — loader etykiet Anti-UAV IR (wariant B) + prowieniencja (A1/A2).

Parsuje IR_label.json (pole `exist` + `gt_rect`/`get_rect`), zwraca per-sekwencja trajektorie
boxów znormalizowane do rozdzielczości IR (A1). Rider prowieniencji: sha256 każdego pliku.

Format Anti-UAV (kanoniczny): {"exist":[0/1,...], "gt_rect":[[x,y,w,h] | [], ...]} (x,y=lewy-górny).
Loader jest defensywny: obsługuje klucze gt_rect/get_rect/res i format xywh/xyxy (param).
Rozdzielczość IR domyślnie 640x512 (Anti-UAV thermal) — POTWIERDZIĆ przy inspekcji danych.
"""
from __future__ import annotations
import json, os, hashlib, glob
import numpy as np

IR_W, IR_H = 640, 512          # A1: normalizacja do rozdzielczości IR (weryfikować z danymi)
DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "antiuav_B")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _boxes_to_norm(rects, exist, box_format="xywh", W=IR_W, H=IR_H):
    """Zwraca [T,4] (cx,cy,w,h) znormalizowane do [0,1]; NaN gdy brak/exist=0."""
    T = len(exist)
    out = np.full((T, 4), np.nan, dtype=np.float64)
    for t in range(T):
        if not exist[t]:
            continue
        r = rects[t] if t < len(rects) else None
        if not r or len(r) < 4 or all(v == 0 for v in r[:4]):
            continue
        x, a, b, c = float(r[0]), float(r[1]), float(r[2]), float(r[3])
        if box_format == "xyxy":       # [x1,y1,x2,y2]
            w, h = b - x, c - a
            cx, cy = x + w / 2.0, a + h / 2.0
        else:                          # [x,y,w,h] (lewy-górny + wh)
            w, h = b, c
            cx, cy = x + w / 2.0, a + h / 2.0
        out[t] = [cx / W, cy / H, w / W, h / H]
    return out


def load_sequence(json_path, box_format="xywh", W=IR_W, H=IR_H):
    """Zwraca dict: name, boxes[T,4] (znorm., NaN gdy absent), exist[T] bool, sha256."""
    d = json.load(open(json_path))
    exist = [int(e) for e in d.get("exist", [])]
    rects = d.get("gt_rect") or d.get("get_rect") or d.get("res") or []
    boxes = _boxes_to_norm(rects, exist, box_format, W, H)
    name = os.path.splitext(os.path.basename(json_path))[0]
    if name.lower() in ("ir_label",):     # układ per-sekwencja: nazwa z katalogu
        name = os.path.basename(os.path.dirname(json_path))
    return {"name": name, "boxes": boxes, "exist": np.array([bool(e) for e in exist]),
            "n_frames": len(exist), "sha256": sha256(json_path), "path": json_path}


def discover(split, root=DATA_ROOT):
    """Znajduje pliki etykiet dla splitu (oba układy: per-katalog i spłaszczony)."""
    base = os.path.join(root, split)
    files = sorted(glob.glob(os.path.join(base, "*", "IR_label.json")))     # per-sekwencja
    if not files:
        files = sorted(glob.glob(os.path.join(base, "*.json")))              # spłaszczony
    return files


def load_split(split, box_format="xywh", root=DATA_ROOT):
    return [load_sequence(f, box_format, root=root) if False else load_sequence(f, box_format)
            for f in discover(split, root)]


if __name__ == "__main__":
    for split in ("train", "val", "test"):
        fs = discover(split)
        print(f"[io] split={split}: {len(fs)} plikow etykiet")
        if fs:
            s = load_sequence(fs[0])
            print(f"      przyklad {s['name']}: {s['n_frames']} kl, exist_frac="
                  f"{s['exist'].mean():.3f}, sha256={s['sha256'][:12]}")
