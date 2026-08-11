#!/usr/bin/env python3
"""grab.py — ENGINE-RECON: przechwyt klatki z sensora kamery gz (gz transport, BEZ ROS-bridge),
pomiar dark_px w regionie projekcji celu (dead-ahead = centrum), enumeracja sceny, metadane as-run.

Guard RAPORTUJE, nie orzeka (wzorzec §8). Wynik per bieg → JSON + .npy + PNG w katalogu biegu.
Uruchom (po starcie gz -s): python3 grab.py <img_topic> <out_dir>
Env do metadanych: HEADLESS, RENDER_BACKEND, GZ_VER, CAM_KIND, CAM_Z, INTR_KIND, INTR_RANGE, DISC, RUN.
"""
import os, sys, json, time, subprocess, re
import numpy as np

DARK_THR = 160          # mesh/box ciemny < 160 na tle nieba 0.7*255≈178 / gruntu 0.8*255≈204
MIN_PX = 8              # próg widoczności (jak scene_sanity_intruder)
BOX_FRAC = 0.12        # okno centralne ~12% ramki (cel dead-ahead → centrum)


def enumerate_models():
    """gz model --list → nazwy modeli w STANIE sceny (model_in_state). Guard raportuje."""
    try:
        out = subprocess.run(["gz", "model", "--list"], capture_output=True, text=True, timeout=8).stdout
        names = re.findall(r"^\s*-\s*(\S+)\s*$", out, re.M) or re.findall(r"\b(\w+)\b", out)
        names = [n for n in names if n not in ("Available", "models", "Requesting", "world", "No")]
        return {"names": names, "intruder_present": "intruder" in names, "raw": out.strip()[:400]}
    except Exception as e:
        return {"names": None, "intruder_present": None, "err": str(e)}


def grab_frame(topic, wait_s=12.0):
    from gz.transport13 import Node
    from gz.msgs10.image_pb2 import Image
    box = {"frame": None, "w": None, "h": None, "fmt": None}

    def cb(msg):
        if box["frame"] is not None:
            return
        w, h = msg.width, msg.height
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = max(1, len(buf) // (w * h)) if w * h else 1
        box["frame"] = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)
        box["w"], box["h"], box["fmt"] = w, h, int(msg.pixel_format_type)

    node = Node()
    if not node.subscribe(Image, topic, cb):
        return None, "subscribe_failed"
    t0 = time.time()
    while box["frame"] is None and time.time() - t0 < wait_s:
        time.sleep(0.1)
    return box, ("ok" if box["frame"] is not None else "no_frame")


def measure_dark(frame):
    """dark_px w oknie centralnym (cel dead-ahead). Zwraca dark_px, region_px, verdict."""
    g = (frame[..., 0] if frame.ndim == 3 else frame).astype(int)
    h, w = g.shape
    cx, cy = w // 2, h // 2
    r = max(6, int(BOX_FRAC * min(h, w) / 2))
    reg = g[cy - r:cy + r, cx - r:cx + r]
    dark = int((reg < DARK_THR).sum()) if reg.size else 0
    return {"dark_px": dark, "min_px": MIN_PX, "region_px": int(reg.size),
            "center_min": int(reg.min()) if reg.size else None,
            "center_mean": round(float(reg.mean()), 1) if reg.size else None,
            "visible": dark >= MIN_PX}


def main():
    topic = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta = {k: os.environ.get(k) for k in
            ("HEADLESS", "RENDER_BACKEND", "GZ_VER", "CAM_KIND", "CAM_Z", "INTR_KIND",
             "INTR_RANGE", "DISC", "RUN", "IMG_TOPIC")}
    meta["img_topic"] = topic
    meta["models"] = enumerate_models()

    box, status = grab_frame(topic)
    meta["capture_status"] = status
    if box is None or box["frame"] is None:
        meta["verdict"] = "NO_FRAME"
        with open(os.path.join(outdir, "result.json"), "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"[grab] NO FRAME z {topic} — {status}")
        print(json.dumps(meta, ensure_ascii=False))
        sys.exit(3)

    frame = box["frame"]
    np.save(os.path.join(outdir, "frame.npy"), frame)
    # PNG 1:1
    try:
        from PIL import Image as PImage
        arr = frame if frame.ndim == 3 else np.stack([frame] * 3, -1)
        PImage.fromarray(arr[..., :3].astype(np.uint8)).save(os.path.join(outdir, "frame.png"))
        meta["png"] = "frame.png"
    except Exception as e:
        meta["png_err"] = str(e)

    m = measure_dark(frame)
    meta.update(m)
    meta["frame_shape"] = list(frame.shape)
    meta["frame_min"] = int(frame.min()); meta["frame_max"] = int(frame.max())
    meta["frame_mean"] = round(float(frame.mean()), 1)
    # RENDER verdict (guard raportuje): PASS = cel widoczny (dark_px≥min); FAIL = w stanie, brak w obrazie
    present = meta["models"].get("intruder_present")
    if m["visible"]:
        meta["verdict"] = "RENDER_PASS_visible"
    elif present:
        meta["verdict"] = "RENDER_FAIL_in_state_not_in_image"
    else:
        meta["verdict"] = "AMBIG_not_in_state"     # D0: model nieobecny → nie bug renderu

    with open(os.path.join(outdir, "result.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"[grab] {meta['verdict']} dark_px={m['dark_px']}/{m['min_px']} "
          f"center(min={m['center_min']},mean={m['center_mean']}) frame(mean={meta['frame_mean']}) "
          f"intruder_in_state={present} shape={frame.shape}")
    print(json.dumps({k: meta[k] for k in ('verdict','dark_px','visible','models','capture_status')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
