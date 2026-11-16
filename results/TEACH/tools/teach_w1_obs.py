#!/usr/bin/env python3
"""results/TEACH/tools/teach_w1_obs.py — W1 (część „proces producenta”): harness/nadir_obs.py bez TEACH_MODE bajtowo jak przed zmianą
(PROMPT_TEACH_S1 §4 W1; 0 bootów).

Dwie wersje modułu: bieżąca (plik roboczy) i odniesienia (`git show ad1e71fd:harness/nadir_obs.py`, zapisana do katalogu
tymczasowego). Każda ładowana osobno (importlib, argv --world/--model/--out), z tym samym env, i karmiona tymi samymi klatkami
przez własne `on_img` (atrapa wiadomości gz: header.stamp, width, height, data RGB) z migawką EKF wstawioną do `_ekf` przed
klatką; wątek roboczy modułu przetwarza każdą klatkę (czekanie na n_proc — bez pominięć). Klatki: wiersze nf lotu NAD3 S3
p01_p1_c05_zew (pierwsze N z detekcją i bez): obraz 640 × 480 szary 128 ze znacznikami DICT_4X4_50 narysowanymi w zapisanych
narożnikach (warpPerspective wzorca cv2.aruco), EKF z wiersza. Porównanie wierszy JSONL po usunięciu pól zegarowych (mono, ms,
ekf_q_age, ekf_pos_age) i meta po usunięciu mono: wymagana równość. Tryby: NADIR_MODE=0; NADIR_MODE=1 z NADIR_LITERA=NAD2;
NADIR_MODE=1 z NAD3_DEGRAD (bias_rad, E 1.0, f 1, K 0). W każdym trybie także TEACH_MODE=1 bez NADIR_MODE (gałąź nieaktywna).
Dodatkowo kody odmowy gałęzi TEACH: 47 (TEACH_MODE + NAD3_DEGRAD), 48 (TEACH_CIEN bez TEACH_T_CIEN).
Wyjście: results/TEACH/s1/w1_obs.json; kod 1 przy niezgodności.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import types

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3_RECON/tools")]
import cv2                                                      # noqa: E402
import nad3_dane as N                                            # noqa: E402

LOT = os.path.join(ROOT, "results/NAD3/s3/p01_p1_c05_zew")
REF_COMMIT = "ad1e71fd"
N_KLATEK = 240
ZEGAR = ("mono", "ms", "ekf_q_age", "ekf_pos_age")
DEGRAD = json.dumps({"model": "bias_rad", "kierunek": "na_zewnatrz", "E_max": 1.0, "f": 1, "K": 0, "ziarno": 1})


def klatki():
    rows = [r for r in N.jl(LOT, "nadir_obs.jsonl", "nf") if r.get("ekf_pos") and r.get("ekf_q")]
    z = [r for r in rows if r.get("det")][: N_KLATEK * 3 // 4]
    bez = [r for r in rows if not r.get("det")][: N_KLATEK - len(z)]
    out = sorted(z + bez, key=lambda r: r["sim"])
    slow = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    for r in out:
        img = np.full((480, 640), 128, np.uint8)
        for m in r.get("det") or []:
            wz = cv2.aruco.drawMarker(slow, m["id"], 120)
            wz = cv2.copyMakeBorder(wz, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
            src = np.float32([[20, 20], [139, 20], [139, 139], [20, 139]])
            H = cv2.getPerspectiveTransform(src, np.float32(m["c"]))
            war = cv2.warpPerspective(wz, H, (640, 480), flags=cv2.INTER_LINEAR, borderValue=0)
            msk = cv2.warpPerspective(np.full_like(wz, 255), H, (640, 480), flags=cv2.INTER_NEAREST, borderValue=0)
            img[msk > 0] = war[msk > 0]
        r["_img"] = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return out


def zaladuj(sciezka, out, env):
    old_env = dict(os.environ)
    for k in ("NADIR_MODE", "NADIR_LITERA", "NAD3_DEGRAD", "TEACH_MODE", "TEACH_CIEN", "TEACH_T_CIEN", "TEACH_MASKA", "NADIR_FIX_SOCKS"):
        os.environ.pop(k, None)
    os.environ.update(env)
    old_argv = sys.argv
    sys.argv = [sciezka, "--world", "w", "--model", "m", "--out", out]
    try:
        spec = importlib.util.spec_from_file_location(f"nobs_{abs(hash((sciezka, out)))}", sciezka)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = old_argv
        os.environ.clear(); os.environ.update(old_env)
    return mod


def przebieg(sciezka, env, kl, tmp, tag):
    out = os.path.join(tmp, f"{tag}.jsonl")
    mod = zaladuj(sciezka, out, env)
    meta = {"t": "meta", "topic": mod.TOPIC, "opencv": cv2.__version__, "slownik": "DICT_4X4_50", "flip": mod.FLIP}
    if getattr(mod, "NADIR_MODE", False):                       # meta jak w main() modułu (bez ROS)
        meta["litera"] = mod._rama.litera
        if mod._deg.echo() is not None:
            meta["nad3"] = mod._deg.echo()
    import threading
    th = threading.Thread(target=mod.worker, daemon=True)
    th.start()
    for r in kl:
        mod._ekf.update({"q": r["ekf_q"], "q_mono": time.monotonic(), "pos": r["ekf_pos"], "hdg": r.get("ekf_hdg"),
                         "pos_mono": time.monotonic()})
        n0 = mod.st["n_proc"]
        sec, nsec = int(r["sim"]), int(round((r["sim"] - int(r["sim"])) * 1e9))
        msg = types.SimpleNamespace(header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=sec, nsec=nsec)), width=640, height=480,
                                    data=r["_img"].tobytes())
        mod.on_img(msg)
        t0 = time.monotonic()
        while mod.st["n_proc"] == n0 and time.monotonic() - t0 < 10:
            time.sleep(0.002)
    mod._stop[0] = True
    th.join(timeout=2)
    mod.fout.close()
    rows = []
    for l in open(out):
        x = json.loads(l)
        for k in ZEGAR:
            x.pop(k, None)
        rows.append(json.dumps(x, sort_keys=True))
    return meta, rows, {k: v for k, v in mod.st.items() if k != "det_ms"}


def kod(env):
    e = {**{k: v for k, v in os.environ.items() if not k.startswith(("NADIR_", "NAD3_", "TEACH_"))}, **env}
    p = subprocess.run([sys.executable, os.path.join(ROOT, "harness/nadir_obs.py"), "--world", "w", "--model", "m", "--out",
                        os.path.join(tempfile.gettempdir(), "teach_w1_kod.jsonl")], env=e, capture_output=True, text=True, timeout=120,
                       cwd=ROOT)
    return p.returncode


def main():
    tmp = tempfile.mkdtemp(prefix="teach_w1_obs_")
    ref = os.path.join(tmp, "nadir_obs_ref.py")
    open(ref, "wb").write(subprocess.run(["git", "show", f"{REF_COMMIT}:harness/nadir_obs.py"], cwd=ROOT, capture_output=True,
                                         check=True).stdout)
    cur = os.path.join(ROOT, "harness/nadir_obs.py")
    kl = klatki()
    tryby = {"NADIR_MODE=0": {}, "NADIR_MODE=1/NAD2": {"NADIR_MODE": "1", "NADIR_LITERA": "NAD2"},
             "NADIR_MODE=1/NAD2/NAD3_DEGRAD": {"NADIR_MODE": "1", "NADIR_LITERA": "NAD2", "NAD3_DEGRAD": DEGRAD}}
    wyn = {"lot": os.path.relpath(LOT, ROOT), "n_klatek": len(kl), "n_z_detekcja": sum(1 for r in kl if r.get("det")),
           "odniesienie": f"{REF_COMMIT}:harness/nadir_obs.py", "tryby": {}}
    ok = True
    for nazwa, env in tryby.items():
        for teach in (False, True):
            e = dict(env)
            if teach:
                e["TEACH_MODE"] = "1"
            tag = nazwa.replace("/", "_").replace("=", "") + ("_TEACHbezNADIR" if teach else "")
            if teach and env.get("NADIR_MODE") == "1":
                continue                                        # TEACH_MODE z NADIR_MODE to gałąź TEACH — nie regresja
            m0, r0, s0 = przebieg(ref, env, kl, tmp, tag + "_ref")
            m1, r1, s1 = przebieg(cur, e, kl, tmp, tag + "_cur")
            rozn = sum(1 for a, b in zip(r0, r1) if a != b) + abs(len(r0) - len(r1))
            zg = rozn == 0 and m0 == m1 and s0 == s1 and len(r0) == len(kl)
            ok = ok and zg
            nfx = sum(1 for l in r1 if '"fx"' in l and '"ok": true' in l)
            wyn["tryby"][nazwa + (" + TEACH_MODE=1" if teach else "")] = {"wiersze": len(r0), "rozne": rozn, "meta_rowne": m0 == m1,
                                                                           "summary_rowne": s0 == s1, "n_det_klatki": s1.get("n_det_klatki"),
                                                                           "n_fx_ok": nfx, "zgodne": zg}
            print(nazwa, "teach" if teach else "", wyn["tryby"][nazwa + (" + TEACH_MODE=1" if teach else "")], flush=True)
    kody = {"TEACH+NAD3_DEGRAD": kod({"NADIR_MODE": "1", "TEACH_MODE": "1", "NAD3_DEGRAD": DEGRAD}),
            "TEACH_CIEN bez TEACH_T_CIEN": kod({"NADIR_MODE": "1", "TEACH_MODE": "1", "TEACH_CIEN": "1"})}
    wyn["kody_odmowy"] = kody
    wyn["kody_ok"] = kody == {"TEACH+NAD3_DEGRAD": 47, "TEACH_CIEN bez TEACH_T_CIEN": 48}
    ok = ok and wyn["kody_ok"]
    wyn["zgodne_wszystkie"] = ok
    print("kody", kody, "W1-obs", ok)
    json.dump(wyn, open(os.path.join(ROOT, "results/TEACH/s1/w1_obs.json"), "w"), ensure_ascii=False, indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
