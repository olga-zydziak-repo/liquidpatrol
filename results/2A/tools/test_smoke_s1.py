#!/usr/bin/env python3
"""results/2A/tools/test_smoke_s1.py — smoke S1 nogi 2A (PROMPT_2A_S1 §4 a/c; zero SITL).

(a) pinhole: syntetyczny box o znanej geometrii → NED, błąd numeryczny ~0 (projekcja w przód
    liczona NIEZALEŻNYM wzorem w teście, box_to_ned musi ją odwrócić);
(c) feed_vision tor syntetyczny end-to-end: admisja k=3 (struktura∧MTI) → track → kontrakt →
    utrata → age → EXPIRE; negatyw: mti_ok=False nigdy nie admituje; box przy krawędzi nie
    admituje (edge_margin).
Plus: rejestr feedów — nieznana nazwa podnosi ValueError; gałąź "B" konstruuje FeedB 1:1
(parametry identyczne z dzisiejszą konstrukcją bench_flight), gdy gz.transport dostępny.

Uruchomienie: pytest results/2A/tools/test_smoke_s1.py
"""
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest

from harness.feed_vision import (FeedVision, box_to_ned, F_PX, W_REAL_M, CAM_OFF_FRD,
                                 IMG_W, IMG_H)
from r02.mti import CX, CY, quat_to_R
from r02.target_channel import Box


def quat_yaw_pitch(yaw, pitch):
    """Kwaternion [w,x,y,z] FRD→NED dla zadanych yaw/pitch (roll=0), konwencja ZYX."""
    cy_, sy_ = math.cos(yaw / 2), math.sin(yaw / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    return [cy_ * cp, -sy_ * sp, cy_ * sp, sy_ * cp]   # w, x, y, z (roll=0)


def project_forward(target_ned, own_ned, q):
    """NIEZALEŻNA projekcja w przód (wzór pisany od geometrii, nie kopią box_to_ned):
    target NED → wektor FRD → minus offset kamery → ramka optyczna → (cx,cy,w) znorm."""
    import numpy as np
    R = quat_to_R(q)                                    # FRD→NED
    d_ned = np.array(target_ned) - np.array(own_ned)
    d_frd = R.T @ d_ned                                 # NED→FRD
    d_cam = d_frd - np.array(CAM_OFF_FRD)               # środek kamery
    # opt: x=prawo(+Y_frd), y=dół(+Z_frd), z=przód(+X_frd)
    x_opt, y_opt, z_opt = d_cam[1], d_cam[2], d_cam[0]
    assert z_opt > 0, "cel przed kamerą"
    u = CX + F_PX * x_opt / z_opt
    v = CY + F_PX * y_opt / z_opt
    w_px = F_PX * W_REAL_M / z_opt
    return Box(cx=u / IMG_W, cy=v / IMG_H, w=w_px / IMG_W, h=w_px / IMG_H)


# --- (a) pinhole ------------------------------------------------------------

def test_pinhole_roundtrip_identity():
    own = [0.0, 0.0, -10.0]
    q = [1.0, 0.0, 0.0, 0.0]
    target = [8.0, 0.5, -11.5]
    box = project_forward(target, own, q)
    rec = box_to_ned(box, own, q)
    assert max(abs(rec[k] - target[k]) for k in range(3)) < 1e-9


def test_pinhole_roundtrip_yaw_pitch():
    own = [3.0, -2.0, -9.0]
    q = quat_yaw_pitch(math.radians(35.0), math.radians(-7.0))
    target = [10.5, 3.2, -11.0]
    box = project_forward(target, own, q)
    rec = box_to_ned(box, own, q)
    assert max(abs(rec[k] - target[k]) for k in range(3)) < 1e-9


def test_pinhole_degenerate_box_none():
    assert box_to_ned(Box(cx=0.5, cy=0.5, w=0.0005, h=0.0005), [0, 0, -10], [1, 0, 0, 0]) is None


# --- (c) cykl życia tracku (syntetycznie, bez kamery) ------------------------

BOX_C = Box(cx=0.5, cy=0.5, w=0.05, h=0.05)             # centralny, 32 px


def mk_feed():
    fv = FeedVision(detector=None)
    fv.push_own(0.0, [0.0, 0.0, -10.0], [1.0, 0.0, 0.0, 0.0])
    return fv


def test_lifecycle_entry_track_loss_expire():
    fv = mk_feed()
    # przed czymkolwiek: kontrakt zwraca invalid (jak FeedB przed 1. próbką)
    s = fv.sample(0.0)
    assert s["track_valid"] is False and s["feed_sha"] == fv.feed_sha
    # admisja k=3 @10 Hz: klatki 0.0/0.1 nie wystarczają
    assert fv.ingest_box(0.0, BOX_C, mti_ok=True) is None
    assert fv.sample(0.05)["track_valid"] is False
    assert fv.ingest_box(0.1, BOX_C, mti_ok=True) is None
    ev = fv.ingest_box(0.2, BOX_C, mti_ok=True)
    assert ev == "ENTRY" and fv.channel.locked
    s = fv.sample(0.2)
    assert s["track_valid"] is True and s["track_age_s"] == 0.0
    # pozycja = pinhole dla boxa centralnego: cel na osi, Z = f·W/w_px = 270·2.5/32 ≈ 21.09 m
    z_exp = F_PX * W_REAL_M / (BOX_C.w * IMG_W)
    assert abs(s["trk_pos_ned"][0] - (z_exp + CAM_OFF_FRD[0])) < 1e-3
    assert abs(s["trk_pos_ned"][2] - (-10.0 + CAM_OFF_FRD[2])) < 1e-3
    # kolejne świeże klatki: age wraca do 0, licznik fresh rośnie
    fv.ingest_box(0.3, BOX_C, mti_ok=True)
    assert fv.n_fresh == 2 and fv.sample(0.3)["track_age_s"] == 0.0
    # utrata: brak boxów → ZOH, age rośnie, valid jeszcze True (konsument tnie na 1.0 s)
    fv.ingest_box(0.4, None, mti_ok=False)
    s = fv.sample(0.9)
    assert s["track_valid"] is True and abs(s["track_age_s"] - 0.6) < 1e-6
    # EXPIRE po suficie θ_age (3.0 s): kanał odpuszcza lock → valid False
    t, ev = 0.5, None
    while t < 5.0 and ev != "EXPIRE":
        ev = fv.ingest_box(t, None, mti_ok=False)
        t += 0.1
    assert ev == "EXPIRE" and not fv.channel.locked
    assert fv.sample(t)["track_valid"] is False


def test_no_entry_without_mti():
    fv = mk_feed()
    for i in range(6):
        ev = fv.ingest_box(0.1 * i, BOX_C, mti_ok=False)   # struktura jest, MTI nie ma
        assert ev is None
    assert not fv.channel.locked and fv.sample(0.6)["track_valid"] is False
    assert fv.n_fresh == 0


def test_no_entry_at_edge():
    fv = mk_feed()
    edge = Box(cx=0.03, cy=0.5, w=0.05, h=0.05)            # edge_dist < margin 0.10
    for i in range(6):
        assert fv.ingest_box(0.1 * i, edge, mti_ok=True) is None
    assert not fv.channel.locked


def test_trk_vel_regression_moving_target():
    fv = mk_feed()
    # box malejący w szerokości → cel oddala się wzdłuż osi x z ~stałą prędkością
    for i, w in enumerate([0.060, 0.058, 0.056, 0.054, 0.052, 0.050]):
        fv.ingest_box(0.1 * i, Box(cx=0.5, cy=0.5, w=w, h=w), mti_ok=True)
    s = fv.sample(0.5)
    assert s["track_valid"] and s["trk_vel_ned"][0] > 1.0   # oddala się (x rośnie)
    assert abs(s["trk_vel_ned"][1]) < 0.5


# --- rejestr feedów ----------------------------------------------------------

def test_registry_unknown_raises():
    from harness.feed_registry import make_feed
    with pytest.raises(ValueError):
        make_feed("X", seed=1, world="w")


def test_registry_b_is_feedb_1to1():
    gz = pytest.importorskip("gz.transport13")             # host lotny ma bindingi; inaczej skip
    from harness.feed_registry import make_feed
    from harness.track_feed import FeedB, TrackFeedGz
    feed, holder = make_feed("B", seed=123, world="world_demo_A3")
    ref = FeedB(123, f=10.0)
    assert isinstance(feed, FeedB) and isinstance(holder, TrackFeedGz)
    assert feed.params == ref.params and feed.feed_sha == ref.feed_sha
    assert holder.feed is feed
