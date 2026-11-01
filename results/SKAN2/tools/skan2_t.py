#!/usr/bin/env python3
"""results/SKAN2/tools/skan2_t.py — testy na sucho wrappera net_skan2 (PROMPT_SKAN2_S1 §1;
FAIL któregokolwiek ⇒ nie startuje). Bez SITL; pełny tor z wagami ncp (guard SR-2).

T1 pass-through: replay demo.jsonl PERC2 S2 (oba booty, 8 epizodów, strumień fd z logu):
   poza hold `out is cmd_delegata` (tożsamość obiektu zwróconego przez FantomScan);
   równolegle samodzielny FantomScan na tym samym strumieniu — na KAŻDYM ticku cmd
   identyczny poza `yaw` i kluczami s2_* (hold); na tickach kwarantanny klucze q_* identyczne.
T2 profil: ticki 0.05 s, sam hold od resetu: ψ stałe przez 1.0 s, rampa 60°/s ± 0.5 %,
   krok 68.3° ± 0.05°, stare 0.4 s ± 1 tick; azymut +273.1° w t = 1.0 + 4·1.5383 − 0.4 −
   (4·68.3 − 273.1)/60 ± 1 tick; wyjście z hold i powrót ⇒ dwell 2.0 s od bieżącego ψ_last.
T3 reset: po reset() znowu dwell 1.0 s i ψ_last = 0.
T4 rejestr: make_controller("net_skan2", kw jak bench_flight) buduje się; weights_sha i
   guard identyczne z net_fantom; pozostałe wpisy bez zmian (diff rejestru = 2 linie +).
Użycie: python3 results/SKAN2/tools/skan2_t.py  (wypis PASS/FAIL per test, rc≠0 przy FAIL)
"""
import hashlib
import json
import math
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
os.environ.setdefault("NET_ARM", "ncp")
os.environ.pop("FANTOM_QLOG", None)

from r01.config import V_MAX                                       # noqa: E402
from r03.controllers import make_controller, controller_sha, _REGISTRY   # noqa: E402
from r03.controllers.fantom_scan import FantomScan                 # noqa: E402
from r03.controllers.skan2_scan import (SkanScan, SKAN2_STEP_DEG, SKAN2_SLEW_DPS,  # noqa: E402
                                        SKAN2_STARE_S)

DT = 0.05
POS = [0.0, 0.0, -10.0]
VEL = [0.0, 0.0, 0.0]
FD_BAD = {"trk_pos_ned": [0, 0, 0], "trk_vel_ned": [0, 0, 0], "track_age_s": 1e9, "track_valid": False}
FD_T = {"trk_pos_ned": [0.0, 10.0, -10.0], "trk_vel_ned": [0, 0, 0], "track_age_s": 0.05, "track_valid": True}
DEMOS = ["results/PERC2/s2/bB_c1011/demo.jsonl", "results/PERC2/s2/bA_c08/demo.jsonl"]
EXEC_PARAMS = json.load(open(os.path.join(ROOT, "bench/executor_params.json")))


def _sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def _rows(p):
    out = []
    for ln in open(os.path.join(ROOT, p)):
        r = json.loads(ln)
        if "tick" in r and "own_pos_ned" in r:
            out.append(r)
    return out


def _feed(r):
    return {"trk_pos_ned": r["trk_pos_ned"], "trk_vel_ned": r.get("trk_vel_ned", [0, 0, 0]),
            "track_age_s": r["track_age_s"], "track_valid": r["track_valid"]}


def _wo(cmd):
    o = dict(cmd)
    o.pop("yaw")
    o["extra"] = {k: v for k, v in cmd["extra"].items() if not k.startswith("s2_")}
    return o


def t1():
    n = n_pass = n_hold = n_q = 0
    for p in DEMOS:
        s = SkanScan(); ref = FantomScan()
        got = {}
        orig = s._fan.step
        def spy(*a, **k):                     # przechwyt obiektu zwracanego przez delegata
            got["c"] = orig(*a, **k)
            return got["c"]
        s._fan.step = spy
        last = None
        for r in _rows(p):
            if r["episode_id"] != last:
                s.reset(); ref.reset(); last = r["episode_id"]
            fd = _feed(r)
            s.set_feed(fd); ref.set_feed(fd)
            c_s = s.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
            c_r = ref.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
            n += 1
            if c_r["extra"].get("phase") != "hold":
                assert c_s is got["c"], f"poza hold out is not cmd_delegata @{p} tick {r['tick']}"
                assert c_s == c_r, f"poza hold cmd != FantomScan @{p} tick {r['tick']}"
                n_pass += 1
            else:
                assert _wo(c_s) == _wo(c_r), f"hold: cmd poza yaw/s2_* != FantomScan @{p} tick {r['tick']}"
                assert set(c_s["extra"]) - set(c_r["extra"]) == {"s2_dwell_s", "s2_t_scan"}
                n_hold += 1
            qs = {k: v for k, v in c_s["extra"].items() if k.startswith("q_")}
            qr = {k: v for k, v in c_r["extra"].items() if k.startswith("q_")}
            assert qs == qr, f"q_* rozjazd @{p} tick {r['tick']}"
            n_q += bool(qr)
    return f"ticki {n}: pass-through {n_pass} (tożsamość obiektu), hold {n_hold}, z q_* {n_q}"


def _hold_run(s, t0, T, i0=0):
    ys = []
    for i in range(int(round(T / DT)) + 1):
        t = t0 + i * DT
        s.set_feed(FD_BAD)
        c = s.step(i0 + i, POS, VEL, t, False)
        assert c["extra"]["phase"] == "hold"
        ys.append((round(t - t0, 6), c["yaw"], c["extra"]["s2_dwell_s"]))
    return ys


def _unwrap(ys):
    out = [ys[0][1]]
    for (_, a, _), (_, b, _) in zip(ys, ys[1:]):
        out.append(out[-1] + math.atan2(math.sin(b - a), math.cos(b - a)))
    return out


def t2():
    s = SkanScan(); s.reset()
    ys = _hold_run(s, 100.0, 12.0)
    tt = [y[0] for y in ys]; u = [math.degrees(x) for x in _unwrap(ys)]
    assert all(y[2] == 1.0 for y in ys), "dwell startowy != 1.0"
    assert all(abs(u[i]) < 1e-9 for i in range(len(tt)) if tt[i] <= 1.0 + 1e-9), "ψ nie stałe w dwell"
    rates = [(u[i] - u[i - 1]) / DT for i in range(1, len(u))]
    ramp = [r for r in rates if r > 1.0]
    full = [r for i, r in enumerate(rates, 1) if r > 1.0 and rates[i - 2] > 1.0 and i < len(rates) and rates[i] > 1.0]
    assert full and all(abs(r - SKAN2_SLEW_DPS) <= 0.005 * SKAN2_SLEW_DPS for r in full), f"rampa {min(full)}..{max(full)}"
    # plateau (stare): kolejne odcinki stałego ψ po dwell
    plat, cur = [], None
    for i in range(1, len(u)):
        if tt[i] <= 1.0:
            continue
        if abs(u[i] - u[i - 1]) < 1e-9:
            cur = [tt[i - 1], tt[i], u[i]] if cur is None else [cur[0], tt[i], u[i]]
        elif cur is not None:
            plat.append(cur); cur = None
    steps = [plat[0][2]] + [b[2] - a[2] for a, b in zip(plat, plat[1:])]
    stares = [p[1] - p[0] for p in plat]
    assert all(abs(x - SKAN2_STEP_DEG) <= 0.05 for x in steps), f"kroki {steps}"
    assert all(abs(x - SKAN2_STARE_S) <= DT + 1e-9 for x in stares), f"stare {stares}"
    t_pred = 1.0 + 4 * 1.5383 - 0.4 - (4 * 68.3 - 273.1) / 60
    t_hit = next(tt[i] for i in range(len(tt)) if u[i] >= 273.1 - 1e-9)
    assert abs(t_hit - t_pred) <= DT + 1e-9, f"273.1° o {t_hit} vs {t_pred}"
    # wyjście z hold (track) i powrót ⇒ dwell 2.0 od bieżącego ψ_last
    t1_ = 100.0 + 12.0 + DT
    s.set_feed(dict(FD_T)); c = s.step(999, POS, VEL, t1_, False)
    assert c["extra"]["phase"] != "hold"
    psi_trk = c["yaw"]
    ys2 = _hold_run(s, t1_ + DT, 4.0, 1000)
    assert all(y[2] == 2.0 for y in ys2), "dwell po utracie != 2.0"
    assert all(y[1] == psi_trk for y in ys2 if y[0] <= 2.0 + 1e-9), "dwell 2.0 nie od ψ_last"
    assert any(y[1] != psi_trk for y in ys2 if y[0] > 2.0 + DT), "brak skanu po dwell 2.0"
    return (f"dwell 1.0 OK; rampa {min(full):.3f}–{max(full):.3f}°/s; kroki {min(steps):.4f}–{max(steps):.4f}°; "
            f"stare {min(stares):.3f}–{max(stares):.3f} s (n={len(stares)}); 273.1° o t={t_hit:.2f} s "
            f"(wzór {t_pred:.4f}); powrót: dwell 2.0 od ψ_last={math.degrees(psi_trk):.2f}°")


def t3():
    s = SkanScan(); s.reset()
    _hold_run(s, 0.0, 5.0)
    s.set_feed(dict(FD_T)); s.step(0, POS, VEL, 5.1, False)
    s.reset()
    assert s._last_yaw == 0.0 and s._first_hold is True
    ys = _hold_run(s, 50.0, 2.0)
    assert all(y[2] == 1.0 for y in ys)
    assert all(y[1] == 0.0 for y in ys if y[0] <= 1.0 + 1e-9)
    assert any(y[1] != 0.0 for y in ys if y[0] > 1.0 + DT)
    return "po reset(): dwell 1.0 s, ψ_last = 0.0, skan rusza po 1.0 s"


def t4():
    kw = dict(params=EXEC_PARAMS, orbit_dir="CCW", vmax=V_MAX, home_ned=(0.0, 0.0, -10.0))
    a = make_controller("net_skan2", **kw)
    b = make_controller("net_fantom", **kw)
    assert isinstance(a, SkanScan) and a.name == "net_skan2"
    assert controller_sha(a) == _sha("r03/controllers/skan2_scan.py")
    assert a.weights_sha == b.weights_sha and a.arm == b.arm == "ncp"
    assert controller_sha(b) == _sha("r03/controllers/fantom_scan.py")
    assert sorted(_REGISTRY) == sorted(["route", "orbit", "net", "gru", "mlp20", "net_akw", "net_fantom", "net_skan2"])
    d = subprocess.run(["git", "diff", "--numstat", "585f4d14", "--", "r03/controllers/__init__.py"],
                       cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert d[:2] == ["2", "0"], f"diff rejestru {d}"
    return f"net_skan2 OK; weights_sha {a.weights_sha[:16]} == net_fantom; rejestr 8 wpisów; diff rejestru +2/−0"


def main():
    rc = 0
    for nm, fn in (("T1", t1), ("T2", t2), ("T3", t3), ("T4", t4)):
        try:
            print(f"{nm} PASS — {fn()}")
        except AssertionError as e:
            rc = 1; print(f"{nm} FAIL — {e}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
