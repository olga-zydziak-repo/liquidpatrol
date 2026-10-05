#!/usr/bin/env python3
"""results/2A/tools/test_aneks1.py — testy napraw ANEKS_2A-1 (N1 granica jednostek yaw,
N2 bramkowanie REFRESH). Uruchamiane pytestem z korzenia repo (wzór test_smoke_s1)."""
import math
import os
import re
import sys

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness.feed_vision import FeedVision, REFRESH_GATE_M, box_to_ned
from r02.target_channel import Box

BOX_C = Box(cx=0.5, cy=0.5, w=0.05, h=0.04, conf=0.3)       # centralny; Z=270·2.5/32≈21.09 m
BOX_EDGE_FAR = Box(cx=0.97, cy=0.5, w=0.30, h=0.20, conf=0.9)  # tło: przy krawędzi, inny zasięg


def _lock(fv, t0=0.0):
    """ENTRY k=3 koniunkcją struktura∧MTI; zwraca czas ostatniej klatki."""
    fv.push_own(t0, [0.0, 0.0, -10.0], [1.0, 0.0, 0.0, 0.0])
    for i in range(3):
        fv.ingest_box(t0 + 0.1 * i, BOX_C, mti_ok=True)
    assert fv.channel.locked and fv.n_fresh == 1
    return t0 + 0.2


# --- N1: granica jednostek yaw na wywołaniu MAVSDK (bench_flight.py) -------------------

def test_n1_yaw_degrees_at_mavsdk_boundary():
    """Jedyne lotne wywołanie VelocityNedYaw z yaw kontrolera przechodzi przez math.degrees;
    wyrażenie WYJĘTE ZE ŹRÓDŁA daje dla cmd yaw=π dokładnie 180.0 (wymóg aneksu §3-N1)."""
    src = open(os.path.join(ROOT, "bench/bench_flight.py")).read()
    m = re.search(r"VelocityNedYaw\(v\[0\], v\[1\], v\[2\],\s*(math\.degrees\(cmd\.get\(\"yaw\", 0\.0\)\))\)", src)
    assert m, "brak math.degrees na granicy MAVSDK (N1)"
    cmd = {"yaw": math.pi}
    assert eval(m.group(1)) == 180.0
    cmd = {"yaw": -math.pi / 2}
    assert eval(m.group(1)) == -90.0
    # dokładnie JEDNO miejsce konwersji (kontrolery dalej emitują radiany)
    assert src.count("math.degrees") == 1


# --- N2: bramkowanie REFRESH ------------------------------------------------------------

def test_n2_background_does_not_drag_track():
    """Scenariusz aneksu: „cel znika, tło strzela" ⇒ track starzeje się i WYGASA,
    zero przeciągnięcia (trk_pos stoi na ostatniej dobrej pozycji aż do EXPIRE)."""
    fv = FeedVision(detector=None)
    t = _lock(fv)
    good = list(fv._last_pos)
    ev_seen = []
    # tło strzela: box przy krawędzi, inny zasięg, bez MTI — przez >θ_age (3.0 s)
    for i in range(1, 40):
        ev = fv.ingest_box(t + 0.1 * i, BOX_EDGE_FAR, mti_ok=False)
        ev_seen.append(ev)
        s = fv.sample(t + 0.1 * i)
        if s["track_valid"]:
            assert s["trk_pos_ned"] == [round(x, 4) for x in good]   # zero przeciągnięcia
    assert fv.n_fresh == 1                                           # ani jednego refreshu tłem
    assert "FEED_EXPIRE" in ev_seen and fv.n_feed_expire == 1        # sufit wieku feedu zadziałał
    assert not fv.channel.locked                                     # reset ⇒ pełna re-admisja
    assert not fv.sample(t + 4.0)["track_valid"]
    # re-admisja wyłącznie pełną bramą ENTRY k=3 struktura∧MTI
    t2 = t + 4.0
    for i in range(3):
        fv.ingest_box(t2 + 0.1 * i, BOX_C, mti_ok=True)
    assert fv.channel.locked and fv.sample(t2 + 0.2)["track_valid"]


def test_n2_refresh_via_admission_conjunction():
    """(a) box centralny ∧ mti_ok odświeża track (gate=mti) — semantyka S1 zachowana."""
    fv = FeedVision(detector=None)
    t = _lock(fv)
    fv.ingest_box(t + 0.1, BOX_C, mti_ok=True)
    assert fv.n_fresh == 2 and fv.sample(t + 0.1)["track_age_s"] == 0.0


def test_n2_refresh_via_prediction_window():
    """(b) box BEZ MTI, ale kandydat NED w oknie REFRESH_GATE_M wokół predykcji ⇒ refresh."""
    fv = FeedVision(detector=None)
    t = _lock(fv)
    near = Box(cx=0.52, cy=0.5, w=0.05, h=0.04)      # Δcx=0.02→~1.0 m lateralnie @21 m
    cand = box_to_ned(near, [0.0, 0.0, -10.0], [1.0, 0.0, 0.0, 0.0])
    assert math.dist(cand, fv._last_pos) <= REFRESH_GATE_M
    fv.ingest_box(t + 0.1, near, mti_ok=False)
    assert fv.n_fresh == 2


def test_n2_central_leg_required_in_admission():
    """Box z MTI ale NIE-centralny (krawędź) nie przechodzi (a); poza oknem ⇒ ZOH."""
    fv = FeedVision(detector=None)
    t = _lock(fv)
    fv.ingest_box(t + 0.1, BOX_EDGE_FAR, mti_ok=True)   # mti jest, central NIE, okno NIE
    assert fv.n_fresh == 1
    assert fv.sample(t + 0.1)["track_age_s"] > 0.0


def test_n2_feed_sha_changed_and_params_echo():
    """Zmiana parametrów (refresh_gate) jest częścią feed_sha (prowieniencja)."""
    fv = FeedVision(detector=None)
    assert fv.params["refresh_gate_m"] == REFRESH_GATE_M == 3.0
    assert fv.feed_sha != "ffccf86b59d5055f2efe50f716a82a1fce777bf87e7010a8a9d14260c964ad7b"
