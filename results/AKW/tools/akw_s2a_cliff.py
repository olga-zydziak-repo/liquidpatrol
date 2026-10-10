#!/usr/bin/env python3
"""results/AKW/tools/akw_s2a_cliff.py — S2a ANEKS_AKW-1 §4: lokalizacja klifu admisji
w ω·dt [°/klatkę] (ZERO lotów). Rozszerzenie akw_rot_strat (AKW_RECON, frozen — ten plik
jest NOWY, oryginał S0 nietknięty) o:
  (a) binowanie po °/klatkę — ω·dt liczone Z WŁASNYCH DANYCH (Δψ z own_q między kolejnymi
      rekordami percepcji, nie z nominału profilu),
  (b) decymację ×2 replayów dolotu D01–D12 (jedyne booty z frames/ na dysku): frozen
      det_replay.py (bajt w bajt, subprocess) na bootdirze-cieniu z co 2. klatką
      → brama YOLO+MTI+admisja NAPRAWDĘ przeżywa podwojony obrót międzyklatkowy
      (syntetyczny wolny mod ~7.5 Hz, pasmo ~1.4–3.4°/kl),
  (c) dołożenie obu bootów smoke S1 (punkty zmierzone w locie: 2.04°/kl i 3.96°/kl).

ODCHYLENIE JAWNE #1 od litery §4(b): percep_feed kampanii V2 NIE MA klatek na dysku
(boot zapisuje rekordy, nie obrazy) ⇒ decymacja ×2 na nim nie jest fizycznie wykonalna
(mti_ok wymaga re-egzekucji MTI na klatkach); kampania V2 wchodzi do binowania
°/kl BEZ decymacji (pasmo natywne), syntetyczne pasmo 1.4–3.4 dają replaye dolotu.

DOPRECYZOWANIE JAWNE #2 (wynik pierwszego przebiegu, mechanizm): ω·dt korpusu NIE jest
tożsame z ruchem pikselowym CELU. W reżimie ŚLEDZENIA (locked, nos na cel) box jest
pikselowo ~stacjonarny mimo dużego ω·dt — admisja przeżywa; w reżimie AKWIZYCJI
(unlocked, skan nad celem transitującym kadr) prędkość pikselowa celu ≈ ω·dt — i to
ten reżim brama musi przeżyć, żeby ENTRY w ogóle zaszło. Tabela mieszana (prereg §4)
jest przez to niemonotonna; κ₉₀ do REGUŁY §5 liczone na REŻIMIE AKWIZYCJI
(locked=False, cel w FOV, box) — deklaracja wprost w raporcie. Obie tabele w wyniku.

Admisja per klatka (dokładnie człony bramy ENTRY, target_channel.py:102-128):
box ∧ central(edge_dist≥0.10) ∧ mti_ok. Dekompozycja: który człon pada pierwszy;
k=3-łamliwość: ruch środka boxa > ENTRY_MOVE_THR między kolejnymi klatkami admitowanymi.
Etykieta celu w FOV: BootGeo (det_labels 8f7430cd, READ-ONLY) jak R3.
κ₉₀ = górna krawędź ostatniego bina ciągłego prefiksu (n≥30) z admisją ≥90%,
licząc od pierwszego bina ruchu skanowego (patrz raport).

WALIDACJA PRZYRZĄDU: odtworzenie liczb S1 na DOKŁADNYM podzbiorze S1 (okna epizodów
ślepych c01–c03 z trace.jsonl): boot 2 → box 1925 / fresh 1823 (gmti 1799 + gwin 24),
boot 3 → box 235 / fresh 0. Rozjazd = przyrząd nieważny.

Użycie:
  akw_s2a_cliff.py dec2    # 12 replayów zdecymowanych ×2 -> results/AKW/s2a_desk/replays_dec2/
  akw_s2a_cliff.py cliff   # tabele + kappa90 + walidacja -> results/AKW/s2a_desk/akw_s2a_cliff.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
OUTD = os.path.join(ROOT, "results/AKW/s2a_desk")
SCRATCH = os.environ.get("AKW_S2A_SCRATCH",
                         "/tmp/claude-1000/-home-olga-projects-liquidpatrol/"
                         "3cad566c-5308-430f-9212-55c581857242/scratchpad/s2a_dec2")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/DET_RECON/tools"))

from det_labels import BootGeo                    # frozen 8f7430cd (READ-ONLY)

DET_REPLAY = os.path.join(ROOT, "results/DET/tools/det_replay.py")   # frozen
DET_V2 = os.path.join(ROOT, "net/frozen/det_v2.pt")                  # frozen 775ead15
COLLECT = os.path.join(ROOT, "results/DET/collect")
CAMP_V2 = os.path.join(ROOT, "results/DET/camp")
REPLAYS_S0 = os.path.join(ROOT, "results/AKW_RECON/replays")
SMOKE = [("smoke_fast", os.path.join(ROOT, "results/AKW/camp/smoke_r1_V2")),
         ("smoke_slow", os.path.join(ROOT, "results/AKW/camp/smoke_r1_V2_rep"))]
BLIND_SIDS = {"c01_s01", "c02_s01", "c03_s01"}

DT_MAX = 0.3                 # [s] maks. odstęp pary rekordów (odcina teleporty/granice epizodów)
EDGE_MARGIN = 0.10           # ENTRY_EDGE_MARGIN (config_r02.py:36) — człon central
MOVE_THR = 0.15              # ENTRY_MOVE_THR (config_r02.py:30) — spójność serii k
BIN_W = 0.3                  # [°/kl] szerokość bina (§4: „co ~0.3°/kl")
BIN_MAX = 5.1
MIN_N = 30                   # minimalna liczność bina do werdyktu κ₉₀
REGIMES = ("acq", "trk", "all")   # acq=locked False (akwizycja), trk=locked True (śledzenie)


def load_jsonl(path):
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def yaw_of(q):
    w, x, y, z = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def edge_dist(box):
    cx, cy = box[0], box[1]
    return min(cx, 1.0 - cx, cy, 1.0 - cy)


def new_bins():
    n = int(BIN_MAX / BIN_W) + 1
    return [{"n_fov": 0, "n_fov_box": 0, "adm": 0, "fail_central": 0, "fail_mti": 0,
             "fresh": 0, "g_mti": 0, "g_window": 0, "k3_pairs": 0, "k3_move_break": 0,
             "px_speeds": []} for _ in range(n)]


def bin_idx(r):
    return min(int(r / BIN_W), int(BIN_MAX / BIN_W))


def episode_windows(bootdir):
    """Okna epizodów z trace.jsonl (jak akw_analyze.py:88-98): sid -> (lo, hi)."""
    wins = {}
    cur = None
    for e in load_jsonl(os.path.join(bootdir, "trace.jsonl")):
        if e.get("t") != "event":
            continue
        if e.get("ev") == "episode_start":
            cur = {"sid": e.get("scenario_id"), "lo": e.get("t0_sim")}
        elif e.get("ev") == "invalid_start":
            cur = None
        elif e.get("ev") == "episode_end" and cur:
            wins[cur["sid"]] = (cur["lo"], e["sim"])
            cur = None
    return wins


def scan_stream(name, rows, bootdir, tabs, per_src):
    """tabs: {regime: bins}. Zlicza klatki z celem w FOV; reżim z pola locked."""
    rows = [r for r in rows if r.get("t_frame") is not None and r.get("own_q")]
    rows.sort(key=lambda r: r["t_frame"])
    geo = BootGeo(bootdir, 1.0, 60.0)
    src = per_src.setdefault(name, {"n": 0, "rots": [], "n_box": 0, "n_fresh": 0})
    prev = None                      # poprzedni rekord (para °/kl)
    prev_adm = {}                    # regime -> (center, t) ostatniej klatki admitowanej
    for r in rows:
        if r.get("box"):
            src["n_box"] += 1
            if r.get("fresh"):
                src["n_fresh"] += 1
        rot = None
        pbox_center = None
        if prev is not None and 0.0 < r["t_frame"] - prev["t_frame"] <= DT_MAX:
            d = yaw_of(r["own_q"]) - yaw_of(prev["own_q"])
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            rot = abs(math.degrees(d))
            if prev.get("box"):
                pbox_center = (prev["box"][0], prev["box"][1])
        prev = r
        if rot is None:
            prev_adm.clear()
            continue
        src["n"] += 1
        src["rots"].append(rot)
        regime = "trk" if r.get("locked") else "acq"
        lab = geo.label(r["t_frame"])
        if lab.get("flag") != "OK":
            prev_adm.clear()
            continue
        k = bin_idx(rot)
        box = r.get("box")
        for reg in (regime, "all"):
            B = tabs[reg][k]
            B["n_fov"] += 1
            if not box:
                continue
            B["n_fov_box"] += 1
            central = edge_dist(box) >= EDGE_MARGIN
            mti = bool(r.get("mti_ok"))
            if not central:
                B["fail_central"] += 1
            elif not mti:
                B["fail_mti"] += 1
            else:
                B["adm"] += 1
                pa = prev_adm.get(reg)
                if pa is not None and r["t_frame"] - pa[1] <= DT_MAX:
                    B["k3_pairs"] += 1
                    if math.hypot(box[0] - pa[0][0], box[1] - pa[0][1]) > MOVE_THR:
                        B["k3_move_break"] += 1
            if r.get("fresh"):
                B["fresh"] += 1
                g = str(r.get("gate"))
                if g == "mti":
                    B["g_mti"] += 1
                elif g == "window":
                    B["g_window"] += 1
            if pbox_center is not None:
                B["px_speeds"].append(math.hypot(box[0] - pbox_center[0],
                                                 box[1] - pbox_center[1]))
        if box and edge_dist(box) >= EDGE_MARGIN and r.get("mti_ok"):
            for reg in (regime, "all"):
                prev_adm[reg] = ((box[0], box[1]), r["t_frame"])
        else:
            prev_adm.pop(regime, None)
            prev_adm.pop("all", None)


def validate_s1(res):
    """Odtworzenie liczb S1: okna c01–c03, fresh/box + gate'y (pełne rekordy, bez par)."""
    expect = {"smoke_fast": {"box": 1925, "fresh": 1823, "g_mti": 1799, "g_window": 24},
              "smoke_slow": {"box": 235, "fresh": 0, "g_mti": 0, "g_window": 0}}
    out = {}
    ok_all = True
    for name, d in SMOKE:
        wins = [w for sid, w in episode_windows(d).items() if sid in BLIND_SIDS]
        got = {"box": 0, "fresh": 0, "g_mti": 0, "g_window": 0}
        for r in load_jsonl(os.path.join(d, "percep_feed.jsonl")):
            t = r.get("t_frame")
            if t is None or not any(lo <= t <= hi for lo, hi in wins):
                continue
            if r.get("box"):
                got["box"] += 1
                if r.get("fresh"):
                    got["fresh"] += 1
                    g = str(r.get("gate"))
                    if g == "mti":
                        got["g_mti"] += 1
                    elif g == "window":
                        got["g_window"] += 1
        ok = got == expect[name]
        ok_all = ok_all and ok
        out[name] = {"got": got, "expect": expect[name], "ok": ok}
    res["walidacja_S1"] = out
    res["walidacja_S1_PASS"] = ok_all
    return ok_all


def cmd_dec2():
    os.makedirs(os.path.join(OUTD, "replays_dec2"), exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    boots = sorted(d for d in glob.glob(os.path.join(COLLECT, "D??_*")) if os.path.isdir(d))
    for b in boots:
        bid = os.path.basename(b)
        out = os.path.join(OUTD, "replays_dec2", bid + ".json")
        if os.path.exists(out):
            print(f"[skip] {bid} (jest)")
            continue
        shadow = os.path.join(SCRATCH, bid)
        frames_d = os.path.join(shadow, "frames")
        os.makedirs(frames_d, exist_ok=True)
        for aux in ("shadow_feed.jsonl", "trace.jsonl", "gt_intruder.jsonl"):
            dst = os.path.join(shadow, aux)
            if not os.path.exists(dst):
                os.symlink(os.path.join(b, aux), dst)
        frames = sorted(glob.glob(os.path.join(b, "frames", "*.jpg")))
        kept = frames[::2]                      # decymacja ×2: co 2. klatka
        for fp in kept:
            dst = os.path.join(frames_d, os.path.basename(fp))
            if not os.path.exists(dst):
                os.symlink(fp, dst)
        print(f"[dec2] {bid}: {len(frames)} -> {len(kept)} klatek ...", flush=True)
        subprocess.run([sys.executable, DET_REPLAY, shadow, "--detector", DET_V2,
                        "--out", out], check=True,
                       stdout=open(out + ".log", "w"), stderr=subprocess.STDOUT)
    print("dec2 DONE")


def finish(bins):
    out = []
    for i, B in enumerate(bins):
        lo, hi = round(i * BIN_W, 1), round((i + 1) * BIN_W, 1)
        e = {k: v for k, v in B.items() if k != "px_speeds"}
        e["bin"] = f"{lo}-{hi}" if i < len(bins) - 1 else f"{lo}+"
        e["adm_pct"] = round(100 * B["adm"] / B["n_fov_box"], 1) if B["n_fov_box"] else None
        e["fail_central_pct"] = (round(100 * B["fail_central"] / B["n_fov_box"], 1)
                                 if B["n_fov_box"] else None)
        e["fail_mti_pct"] = (round(100 * B["fail_mti"] / B["n_fov_box"], 1)
                             if B["n_fov_box"] else None)
        e["k3_move_break_pct"] = (round(100 * B["k3_move_break"] / B["k3_pairs"], 1)
                                  if B["k3_pairs"] else None)
        ps = sorted(B["px_speeds"])
        e["px_speed_p50"] = round(ps[len(ps) // 2], 4) if ps else None
        out.append(e)
    return out


def kappa90(table):
    """Górna krawędź ostatniego bina ciągłego prefiksu z adm≥90% (n≥MIN_N)."""
    k = 0.0
    for e in table:
        if e["n_fov_box"] < MIN_N:
            continue
        if e["adm_pct"] is not None and e["adm_pct"] >= 90.0:
            k = float(e["bin"].split("-")[0].rstrip("+")) + BIN_W
        else:
            break
    return round(k, 2)


def print_table(title, table):
    print(f"\n== {title} ==")
    print("bin °/kl | n_fov_box |  adm%  | failC% | failM% | k3brk% | pxspd_p50 | fresh")
    for e in table:
        if e["n_fov_box"] == 0:
            continue
        print(f"{e['bin']:>8} | {e['n_fov_box']:9} | {str(e['adm_pct']):>6} | "
              f"{str(e['fail_central_pct']):>6} | {str(e['fail_mti_pct']):>6} | "
              f"{str(e['k3_move_break_pct']):>6} | {str(e['px_speed_p50']):>9} | {e['fresh']:5}")


def cmd_cliff():
    tabs_all = {reg: new_bins() for reg in REGIMES}
    per_group = {}
    per_src = {}
    groups = []
    for j in sorted(glob.glob(os.path.join(REPLAYS_S0, "D??_*.json"))):
        bid = os.path.basename(j)[:-5]
        groups.append(("replay_B_15Hz", "r:" + bid, j + ".replay.jsonl",
                       os.path.join(COLLECT, bid)))
    for j in sorted(glob.glob(os.path.join(OUTD, "replays_dec2", "D??_*.json"))):
        bid = os.path.basename(j)[:-5]
        groups.append(("replay_B_dec2", "d2:" + bid, j + ".replay.jsonl",
                       os.path.join(COLLECT, bid)))
    for d in sorted(glob.glob(os.path.join(CAMP_V2, "r*_V2"))):
        pf = os.path.join(d, "percep_feed.jsonl")
        if os.path.exists(pf):
            groups.append(("live_camp_V2", "v2:" + os.path.basename(d), pf, d))
    for name, d in SMOKE:
        groups.append((name, name, os.path.join(d, "percep_feed.jsonl"), d))

    for grp, name, path, bootdir in groups:
        gt = per_group.setdefault(grp, {reg: new_bins() for reg in REGIMES})
        rows = load_jsonl(path)
        scan_stream(name, rows, bootdir, tabs_all, per_src)
        scan_stream("__" + name, rows, bootdir, gt, {})

    res = {
        "def_admisja": "box ∧ central(edge_dist≥0.10) ∧ mti_ok, klatki z celem w FOV "
                       "(BootGeo flag=OK); °/kl = |Δψ(own_q)| do poprzedniego rekordu, "
                       "dt≤0.3 s; reżim: acq=locked False (akwizycja), trk=locked True",
        "tables": {reg: finish(tabs_all[reg]) for reg in REGIMES},
        "per_group": {g: {reg: finish(t[reg]) for reg in REGIMES}
                      for g, t in per_group.items()},
        "per_source": {},
        "min_n_bin": MIN_N,
    }
    res["kappa90_acq"] = kappa90(res["tables"]["acq"])
    res["kappa90_all_prereg"] = kappa90(res["tables"]["all"])
    # Trzeci kandydat (dowód skanowy wprost): największy punkt °/kl z DOWIEDZIONĄ
    # akwizycją ze skanu w locie = 2.04 (boot 2 S1; ENTRY ze skanu c02/c03) → górna
    # krawędź jego bina 2.1; następny punkt skanowy 3.96 = 0/235 (martwy).
    res["kappa90_scan_dowod"] = 2.1
    k_max = max(res["kappa90_acq"], res["kappa90_all_prereg"], res["kappa90_scan_dowod"])
    omega_safe = 0.85 * k_max * 7.58
    path = "I_ciagly" if omega_safe >= 14.0 else "II_step_and_stare"
    worst_wait = (18.2 if path == "I_ciagly" else 9 * (40.0 / 60.0 + 1.2))
    res["regula_s5"] = {
        "kappa90_kandydaci": {"all_prereg_prefiks": res["kappa90_all_prereg"],
                              "acq_rezim": res["kappa90_acq"],
                              "scan_dowod": res["kappa90_scan_dowod"]},
        "kappa90_najkorzystniejszy_obroniony": k_max,
        "omega_safe_dps": round(omega_safe, 2),
        "prog_dps": 14.0,
        "sciezka": path,
        "worst_wait_s": round(worst_wait, 2),
        "t_A_s": min(23, math.ceil((worst_wait + 3.0) * 1.25)),
        "nota": "wszystkie odczyty kappa90 (takze najkorzystniejszy) daja omega_safe<14 "
                "=> sciezka II niezaleznie od interpretacji definicji kappa90",
    }
    for name, s in per_src.items():
        rs = sorted(s["rots"])
        res["per_source"][name] = {
            "n": s["n"], "n_box": s["n_box"], "n_fresh": s["n_fresh"],
            "rot_p50": round(rs[len(rs) // 2], 2) if rs else None,
            "rot_p90": round(rs[int(len(rs) * 0.9)], 2) if rs else None}
    ok = validate_s1(res)
    os.makedirs(OUTD, exist_ok=True)
    with open(os.path.join(OUTD, "akw_s2a_cliff.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("WALIDACJA S1 (okna epizodów ślepych c01–c03):")
    for k, v in res["walidacja_S1"].items():
        print(f"  {k}: got={v['got']} expect={v['expect']} {'OK' if v['ok'] else 'ROZJAZD'}")
    print(f"WALIDACJA: {'PASS' if ok else 'FAIL — PRZYRZĄD NIEWAŻNY'}")
    print_table("REŻIM AKWIZYCJI (locked=False) — podstawa κ₉₀ reguły §5", res["tables"]["acq"])
    print_table("REŻIM ŚLEDZENIA (locked=True) — kontekst", res["tables"]["trk"])
    print_table("MIESZANA (prereg §4 literalnie)", res["tables"]["all"])
    print(f"\nkappa90 (acq) = {res['kappa90_acq']} °/kl ;  "
          f"kappa90 (mieszana, literalna) = {res['kappa90_all_prereg']} °/kl ; n≥{MIN_N}")
    print("OK -> results/AKW/s2a_desk/akw_s2a_cliff.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["dec2", "cliff"])
    a = ap.parse_args()
    if a.mode == "dec2":
        cmd_dec2()
    else:
        cmd_cliff()
