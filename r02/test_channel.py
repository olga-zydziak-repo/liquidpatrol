"""r02/test_channel.py — testy DETERMINISTYCZNE kanału ZOH-age (R3).

Pokrycie zamrożonej semantyki (PRE_R02 §2.3 + 0ter/A1): ENTRY k=3 strukturalny (NIE conf),
próg ruchu, zerwanie serii, ZOH + starzenie age, sufit θ_age → EXPIRE, ε_FP, 5-dim BEZ conf.
Uruchom: python3 -m r02.test_channel   (exit 0 = PASS, 1 = FAIL)
"""
from __future__ import annotations
import sys

from r02.config_r02 import ChannelConfig
from r02.target_channel import TargetChannel, Box, EV_ENTRY, EV_EXPIRE, EV_REFRESH

CFG = ChannelConfig(entry_k=3, entry_move_thr=0.15, l_deliver_s=0.10, theta_age_s=3.0, det_dt=1.0)
FAILS = []


def check(name, cond):
    print(f"  {'✓' if cond else '✗ FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


def fresh():
    ch = TargetChannel(CFG); return ch


def test_entry_k3_exact():
    """ENTRY dokładnie na 3. spójnej klatce; nie wcześniej."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    e1 = ch.on_frame(b, 0.0); e2 = ch.on_frame(b, 1.0); e3 = ch.on_frame(b, 2.0)
    check("k=1,2 bez ENTRY", e1 is None and e2 is None)
    check("k=3 → ENTRY", e3 == EV_ENTRY and ch.locked)
    check("n_entry=1", ch.n_entry == 1)


def test_entry_move_break():
    """Skok środka > move_thr zeruje serię (re-anchor), ENTRY się opóźnia."""
    ch = fresh()
    ch.on_frame(Box(0.5, 0.5, 0.1, 0.1), 0.0)   # streak 1
    ch.on_frame(Box(0.5, 0.5, 0.1, 0.1), 1.0)   # streak 2
    ch.on_frame(Box(0.9, 0.9, 0.1, 0.1), 2.0)   # skok > 0.15 → streak reset do 1
    check("po skoku brak locka", not ch.locked and ch.streak == 1)
    ch.on_frame(Box(0.9, 0.9, 0.1, 0.1), 3.0)   # streak 2
    e = ch.on_frame(Box(0.9, 0.9, 0.1, 0.1), 4.0)   # streak 3 → ENTRY
    check("ENTRY po odbudowie serii w nowej lokalizacji", e == EV_ENTRY)


def test_gap_breaks_streak():
    """Klatka bez boxa (None) przed lockiem zrywa serię."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    ch.on_frame(b, 0.0); ch.on_frame(b, 1.0)
    ch.on_frame(None, 2.0)                       # zerwanie
    check("streak wyzerowany po None", ch.streak == 0 and not ch.locked)
    ch.on_frame(b, 3.0); ch.on_frame(b, 4.0)
    e = ch.on_frame(b, 5.0)
    check("ENTRY dopiero po nowych 3", e == EV_ENTRY)


def test_channel_5dim_no_conf():
    """Wartość kanału = dokładnie 5-dim (cx,cy,w,h,age); conf detektora NIE przenika."""
    ch = fresh(); b = Box(0.3, 0.4, 0.2, 0.25, conf=0.9)
    for t in (0.0, 1.0, 2.0):
        ch.on_frame(b, t)
    v = ch.sample(2.0)
    check("sample 5-dim", v is not None and len(v.as_tuple()) == 5)
    check("age=L_deliver świeżo po detekcji", abs(v.age_s - 0.10) < 1e-6)
    check("kanał = (cx,cy,w,h) boxa", (v.cx, v.cy, v.w, v.h) == (0.3, 0.4, 0.2, 0.25))
    check("brak pola conf w ChannelValue", not hasattr(v, "conf"))


def test_zoh_age_grows_and_refresh():
    """ZOH: bez boxa age rośnie; box odświeża age:=L_deliver."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    for t in (0.0, 1.0, 2.0):
        ch.on_frame(b, t)                        # lock @ t=2, t_last_det=2
    # bez nowej klatki — sample w t=2.5 (ZOH): age = 0.5 + L_deliver
    v = ch.sample(2.5)
    check("age rośnie w ZOH (0.5+0.1)", abs(v.age_s - 0.60) < 1e-6)
    # klatka bez boxa @3.0 (age=1.0+0.1=1.1 < θ=3) → ZOH, brak EXPIRE
    e = ch.on_frame(None, 3.0)
    check("None w wieku → brak EXPIRE, wciąż lock", e is None and ch.locked)
    # świeży box @3.5 → REFRESH, age spada
    e = ch.on_frame(b, 3.5)
    check("box → REFRESH", e == EV_REFRESH)
    check("age zresetowany po REFRESH", abs(ch.sample(3.5).age_s - 0.10) < 1e-6)


def test_theta_age_expire_on_frame():
    """Sufit θ_age: gdy luka > θ_age, klatka bez boxa → EXPIRE, wyjście z locka."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    for t in (0.0, 1.0, 2.0):
        ch.on_frame(b, t)                        # lock @2
    # klatka bez boxa @ 5.2: age = 3.2+0.1 = 3.3 > θ=3.0 → EXPIRE
    e = ch.on_frame(None, 5.2)
    check("EXPIRE po przekroczeniu sufitu", e == EV_EXPIRE and not ch.locked)
    check("sample=None po EXPIRE", ch.sample(5.3) is None)
    check("n_expire=1", ch.n_expire == 1)


def test_theta_age_expire_between_frames():
    """tick_time (kadencja osłony 20 Hz) egzekwuje sufit MIĘDZY klatkami detektora."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    for t in (0.0, 1.0, 2.0):
        ch.on_frame(b, t)                        # lock @2, t_last_det=2
    check("nie wygasł w wieku", ch.tick_time(4.0) is None and ch.locked)  # age=2.1<3
    e = ch.tick_time(5.5)                        # age=3.6>3 → EXPIRE bez czekania na klatkę
    check("tick_time EXPIRE między klatkami", e == EV_EXPIRE and not ch.locked)


def test_reentry_needs_fresh_streak():
    """Po EXPIRE ponowny lock wymaga NOWEJ serii k (nie „doszywa" starej)."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    for t in (0.0, 1.0, 2.0):
        ch.on_frame(b, t)
    ch.on_frame(None, 6.0)                        # EXPIRE (age 4.1>3)
    check("wygasł", not ch.locked)
    e1 = ch.on_frame(b, 7.0); e2 = ch.on_frame(b, 8.0)
    check("1 klatka po EXPIRE nie lockuje", not ch.locked)
    e3 = ch.on_frame(b, 9.0)
    check("ponowny ENTRY po nowych 3", e3 == EV_ENTRY and ch.n_entry == 2)


def test_eps_fp_counting():
    """ε_FP: ENTRY przy gt_present=False liczony jako fałszywy lock (bramka G1)."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    ch.on_frame(b, 0.0, gt_present=False)
    ch.on_frame(b, 1.0, gt_present=False)
    ch.on_frame(b, 2.0, gt_present=False)
    check("fałszywy ENTRY policzony", ch.n_false_entry == 1)


def test_sample_none_before_lock():
    """sample() = None dopóki brak ENTRY (SEARCHING/CANDIDATE)."""
    ch = fresh(); b = Box(0.5, 0.5, 0.1, 0.1)
    check("None w SEARCHING", ch.sample(0.0) is None)
    ch.on_frame(b, 0.0); ch.on_frame(b, 1.0)
    check("None w CANDIDATE (streak<k)", ch.sample(1.0) is None)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    print(f"=== R3 testy kanału ZOH-age ({len(tests)} grup) ===")
    for t in tests:
        print(f"[{t.__name__}]")
        t()
    ok = not FAILS
    print(f"\nWERDYKT test_channel: {'PASS' if ok else 'FAIL — ' + ', '.join(FAILS)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
