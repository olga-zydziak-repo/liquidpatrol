"""r02/test_mti.py — testy MTI. B1 (SR-M1: instrument derotacji), B2 (R-M5: wektory FP), B3 (brama ENTRY).

B1 jest BRAMĄ SR-M1: FAIL ⇒ STOP (bez zsynchronizowanej derotacji MTI bezprzedmiotowe). Uruchom w env
z cv2 (`.b0deps`): PYTHONPATH=.b0deps/lib/python3.12/site-packages:. python3 -m pytest r02/test_mti.py -q
(lub `python3 r02/test_mti.py` — samodzielny runner z podsumowaniem PASS/FAIL).
"""
from __future__ import annotations
import math
import numpy as np

from r02.mti import (K, K_INV, C_FRD2OPT, quat_to_R, rel_rotation_opt, homography,
                     motion_components, MTIParams, MTITracker, box_matches_component)


# ---------- pomocnicze: euler(FRD→NED) → R → quat (round-trip waliduje quat_to_R) ----------
def euler_to_R(yaw, pitch, roll):
    """R_ned<-frd = Rz(yaw)·Ry(pitch)·Rx(roll) (aerospace ZYX)."""
    cy, sy = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pitch), math.sin(pitch); cr, sr = math.cos(roll), math.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


def R_to_quat(R):
    """R (3×3) → [w,x,y,z] (Hamilton)."""
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2; w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s; y = (R[0, 2] - R[2, 0]) / s; z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        w = (R[2, 1] - R[1, 2]) / s; x = 0.25 * s; y = (R[0, 1] + R[1, 0]) / s; z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        w = (R[0, 2] - R[2, 0]) / s; x = (R[0, 1] + R[1, 0]) / s; y = 0.25 * s; z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        w = (R[1, 0] - R[0, 1]) / s; x = (R[0, 2] + R[2, 0]) / s; y = (R[1, 2] + R[2, 1]) / s; z = 0.25 * s
    return np.array([w, x, y, z])


def quat_of(yaw_d, pitch_d, roll_d):
    return R_to_quat(euler_to_R(math.radians(yaw_d), math.radians(pitch_d), math.radians(roll_d)))


def project(q, d_ned):
    """Rzut kierunku NED (punkt w ∞) przez kamerę o attitude q → piksel (lub None za kamerą).
    Ścieżka NIEZALEŻNA od homografii: d_frd=R(q)^T d_ned; d_opt=C d_frd; p=K d_opt/z."""
    R = quat_to_R(q)
    d_frd = R.T @ np.asarray(d_ned, float)
    d_opt = C_FRD2OPT @ d_frd
    if d_opt[2] <= 1e-6:
        return None
    p = K @ (d_opt / d_opt[2])
    return np.array([p[0], p[1]])


# ============================ B1 — INSTRUMENT (SR-M1) ============================
def test_quat_to_R_sanity():
    """quat_to_R identyczności = I; round-trip R→quat→R; ortonormalność."""
    assert np.allclose(quat_to_R([1, 0, 0, 0]), np.eye(3), atol=1e-9)
    for e in [(30, 0, 0), (0, 20, 0), (0, 0, 15), (40, -12, 8), (170, 20, -30)]:
        R = euler_to_R(*[math.radians(v) for v in e]); q = R_to_quat(R)
        assert np.allclose(quat_to_R(q), R, atol=1e-6), f"round-trip {e}"
        assert np.allclose(quat_to_R(q) @ quat_to_R(q).T, np.eye(3), atol=1e-6)


def _homography_recovers(q_prev, q_cur, n=200, seed=1):
    """Rzutuj n punktów-w-∞ przez obie pozy (ścieżka niezależna); sprawdź że H=K·R_opt·K⁻¹ mapuje
    p_prev→p_cur sub-pikselowo. Zwraca max błąd [px] (po punktach in-frame w obu klatkach)."""
    rng = np.random.default_rng(seed)
    R_opt = rel_rotation_opt(q_prev, q_cur); H = homography(R_opt)
    errs = []
    # kierunki wokół osi optycznej prev (forward ≈ body+X przy małym attitude) w stożku ±35°
    Rp = quat_to_R(q_prev)
    for _ in range(n):
        az = math.radians(rng.uniform(-35, 35)); el = math.radians(rng.uniform(-30, 30))
        d_opt_prev = np.array([math.tan(az), math.tan(el), 1.0]); d_opt_prev /= np.linalg.norm(d_opt_prev)
        d_frd_prev = C_FRD2OPT.T @ d_opt_prev
        d_ned = Rp @ d_frd_prev                        # kierunek w NED (punkt w ∞)
        p_prev = project(q_prev, d_ned); p_cur = project(q_cur, d_ned)
        if p_prev is None or p_cur is None:
            continue
        if not (0 <= p_prev[0] < 640 and 0 <= p_prev[1] < 480 and 0 <= p_cur[0] < 640 and 0 <= p_cur[1] < 480):
            continue
        ph = H @ np.array([p_prev[0], p_prev[1], 1.0]); ph = ph[:2] / ph[2]
        errs.append(float(np.linalg.norm(ph - p_cur)))
    return max(errs) if errs else 999.0, len(errs)


def test_derotation_geometry_both_axes():
    """SR-M1 rdzeń: homografia derotacji re-aligns rzuty sub-pikselowo, OBA kierunki osi + brzegowe."""
    cases = {
        "yaw+8": (quat_of(0, 0, 0), quat_of(8, 0, 0)),
        "yaw-8": (quat_of(0, 0, 0), quat_of(-8, 0, 0)),
        "pitch+20": (quat_of(0, 0, 0), quat_of(0, 20, 0)),   # brzegowy pitch 20°
        "pitch-20": (quat_of(0, 0, 0), quat_of(0, -20, 0)),
        "roll+15": (quat_of(0, 0, 0), quat_of(0, 0, 15)),
        "fast_yaw_21": (quat_of(10, -5, 3), quat_of(31, -5, 3)),  # szybki yaw Δ=21° z niezerowej bazy
        "mixed": (quat_of(40, 8, -6), quat_of(46, 14, -2)),
    }
    worst = 0.0
    for name, (qp, qc) in cases.items():
        err, npts = _homography_recovers(qp, qc)
        assert npts >= 20, f"{name}: za mało punktów in-frame ({npts})"
        assert err < 0.5, f"{name}: max reproj err {err:.3f}px ≥ 0.5"
        worst = max(worst, err)
    return worst


def _texture(seed=7, w=640, h=480):
    rng = np.random.default_rng(seed)
    base = rng.integers(40, 210, (h // 8, w // 8), dtype=np.uint8)
    import cv2
    return cv2.resize(base, (w, h), interpolation=cv2.INTER_LINEAR)


def test_pipeline_background_null_and_object():
    """Pipeline: znana rotacja → residuum tła ~0 (0 komponentów); wstrzyknięty ruchomy obiekt → wykryty."""
    import cv2
    qp = quat_of(5, 3, -2); qc = quat_of(11, 7, -2)           # znana rotacja (yaw+6, pitch+4)
    I_prev = _texture()
    R_opt = rel_rotation_opt(qp, qc); H = homography(R_opt)
    I_cur = cv2.warpPerspective(I_prev, H, (640, 480))         # scena stała, tylko rotacja kamery
    # (a) samo tło: 0 komponentów po derotacji
    comps, dbg = motion_components(I_prev, qp, I_cur, qc, MTIParams())
    assert len(comps) == 0, f"tło niezerowe: {len(comps)} komp, dbg={dbg}"
    # (b) wstrzyknij ruchomy obiekt do I_cur (nieobjaśniony rotacją)
    obj = I_cur.copy()
    cv2.rectangle(obj, (300, 210), (330, 240), 255, -1)        # jasny blok 30×30 w centrum
    comps2, dbg2 = motion_components(I_prev, qp, obj, qc, MTIParams())
    hit = any(abs(c["cx"] - 315 / 640) < 0.06 and abs(c["cy"] - 225 / 480) < 0.06 for c in comps2)
    assert hit, f"ruchomy obiekt niewykryty: {comps2}"
    return dbg2


def test_pairing_tolerance():
    """Parowanie klatka↔attitude (PRE_MTI R1): XRCE 100 Hz, offset stały przy time-jump=0.
    Test logiki NN + budżet tolerancji (zmierzony live: 5 ms → 0.81 px @6.84 m v=3 m/s)."""
    # attitude @100 Hz (epoch-µs) ; klatka @15 Hz (sim-upłynięty s) ; offset O stały
    O = 1786749095.0                                   # start_epoch (przykład live)
    att = [{"ts_us": int((O + k * 0.01) * 1e6), "q": [1, 0, 0, 0]} for k in range(200)]  # 0..2s @100Hz
    frame_sim_s = 0.837                                # klatka w sim-upłyniętym
    # konwersja XRCE→sim: sim = ts_us/1e6 - O ; NN do frame_sim_s
    best = min(att, key=lambda a: abs((a["ts_us"] / 1e6 - O) - frame_sim_s))
    dt = abs((best["ts_us"] / 1e6 - O) - frame_sim_s)
    assert dt <= 0.005 + 1e-9, f"NN tol {dt*1000:.2f} ms > 5 ms"
    v, rng = 3.0, 6.84
    px_err = math.degrees(math.atan2(v * dt, rng)) / (math.degrees(1.74) / 640)
    assert px_err < 1.0, f"px err {px_err:.2f} ≥ 1"
    return {"nn_dt_ms": round(dt * 1000, 3), "px_err": round(px_err, 3)}


# ============================ B2 — R-M5 WEKTORY FP ============================
# Każdy: NAZWANY FP z inwentarza R2 → znany input → OCZEKIWANE ODRZUCENIE (0 komponentów spójnych).
def _tracker_run(frames_quats, params=None):
    """Przepuść sekwencję (frame,q) przez MTITracker; zwróć maks. liczbę SPÓJNYCH komponentów w oknie."""
    tr = MTITracker(params or MTIParams(), delta=1)
    mx = 0; last = []
    for f, q in frames_quats:
        cons, _ = tr.push(f, q)
        mx = max(mx, len(cons)); last = cons
    return mx, last


def test_fp_ground_parallax_translation():
    """FP: paralaksa tekstury gruntu pod TRANSLACJĄ (rotacja=0). Derotacja rotacyjna NIE kompensuje
    translacji → residuum. OCZEKIWANE: pojedyncza klatka daje komponenty (słabość nazwana), ale
    brama STRUKTURA∧MTI je odrzuca (brak boxa strukturalnego) — tu weryfikujemy że to NIE jest
    trwały pojedynczy zwarty cel: rozproszone/niespójne. Raport: liczba komponentów (do B4)."""
    import cv2
    q = quat_of(0, 0, 0)                                # zero rotacji (czysta translacja)
    tex = _texture(seed=3)
    seq = []
    for k in range(4):
        shifted = np.roll(tex, k * 6, axis=1)          # translacja tła 6 px/klatkę (paralaksa)
        seq.append((shifted, q))
    mx, last = _tracker_run(seq)
    # paralaksa translacyjna: residuum ROZPROSZONE (wiele komponentów / duże) — NIE jeden zwarty cel.
    # Kluczowe dla bramy: brak STRUKTURY (box) → i tak brak ENTRY. Tu asercja: nie udaje pojedynczego celu.
    single_compact = len(last) == 1 and last[0]["area_frac"] < 0.02
    assert not single_compact, "paralaksa udaje pojedynczy zwarty cel — filtr niewystarczający"
    return {"n_components": mx}


def test_fp_own_shadow():
    """FP: cień własnego drona — porusza się z platformą po gruncie. Bez koincydencji ze STRUKTURĄ
    (cień nie jest boxem-dronem w górnej części kadru). Test: komponent cienia NIE matchuje boxa celu."""
    import cv2
    q = quat_of(0, 0, 0)
    tex = _texture(seed=9)
    f0 = tex.copy(); f1 = tex.copy()
    cv2.circle(f1, (200, 400), 22, 30, -1)             # ciemny cień nisko w kadrze (grunt)
    comps, _ = motion_components(f0, q, f1, q, MTIParams())
    # box celu (dron) byłby GÓRA-CENTRUM (cy~0.38); cień jest cy~0.83 → brak koincydencji
    from types import SimpleNamespace
    target_box = SimpleNamespace(cx=0.5, cy=0.376)
    assert not box_matches_component(target_box, comps), "cień własny błędnie matchuje box celu"
    return {"n_shadow_comps": len(comps)}


def test_fp_props_frame_edge():
    """FP: śmigła/artefakty przy KRAWĘDZI kadru. border_erode odcina region krawędzi → odrzucone."""
    import cv2
    q = quat_of(0, 0, 0)
    tex = _texture(seed=11)
    f0 = tex.copy(); f1 = tex.copy()
    cv2.rectangle(f1, (0, 0), (18, 60), 255, -1)        # jasny artefakt przy lewej krawędzi
    cv2.rectangle(f1, (624, 430), (639, 479), 255, -1)  # i prawy-dolny róg
    comps, dbg = motion_components(f0, q, f1, q, MTIParams(border_erode=12))
    # oba artefakty DOTYKAJĄ krawędzi → odrzucone przez filtr border-touch; brama i tak wymaga centralności
    edge = [c for c in comps if c["cx"] < 0.05 or c["cx"] > 0.95 or c["cy"] < 0.05 or c["cy"] > 0.95]
    assert not edge, f"artefakty krawędzi nieodrzucone: {edge}"
    return {"n_after_edge_filter": len(comps)}


def test_fp_derotation_residual_fast_yaw():
    """FP: residuum derotacji przy SZYBKIM yaw (drobne speckle z niedokładności/interpolacji).
    Spójność czasowa: transient speckle NIE persystuje ≥persist_m → odrzucone."""
    import cv2
    tex = _texture(seed=5)
    seq = []
    yaws = [0, 12, 25, 40]                              # szybko rosnący yaw
    prev = tex
    for k, yw in enumerate(yaws):
        q = quat_of(yw, 0, 0)
        if k == 0:
            seq.append((tex, q)); continue
        R_opt = rel_rotation_opt(quat_of(yaws[k-1], 0, 0), q); H = homography(R_opt)
        cur = cv2.warpPerspective(prev, H, (640, 480))
        # dodaj losowy szum (speckle residuum) — NIE spójny między klatkami
        rng = np.random.default_rng(100 + k)
        noise = (rng.random((480, 640)) > 0.995).astype(np.uint8) * 255
        cur = cv2.add(cur, noise)
        seq.append((cur, q)); prev = cur
    mx, last = _tracker_run(seq, MTIParams(persist_m=2, persist_window=3))
    # transient speckle nie persystuje → 0 SPÓJNYCH komponentów (lub bardzo mało, nie-zwartych)
    assert len(last) == 0, f"speckle residuum persystuje jako {len(last)} komp"
    return {"max_consistent": mx}


# ============================ B3 — BRAMA ENTRY: struktura ∧ MTI ============================
def test_entry_gate_four_vectors():
    """Deterministyczny test bramy (4 wektory) na TargetChannel z MTI-gate. conf pasywne (nie bramkuje)."""
    from dataclasses import replace
    from r02.target_channel import TargetChannel, Box, EV_ENTRY
    from r02.config_r02 import ChannelConfig
    cfg = replace(ChannelConfig(), entry_require_mti=True)   # tryb DEMO: struktura∧MTI, conf pasywne

    def run(struct_ok, mti_ok):
        ch = TargetChannel(cfg)
        ev = None
        for t in range(cfg.entry_k):                     # k spójnych klatek
            box = Box(0.5, 0.376, 0.05, 0.06, conf=0.02) if struct_ok else None  # conf NISKIE (pasywne)
            ev = ch.on_frame(box, float(t), mti_ok=mti_ok)
        return ev == EV_ENTRY, ch.locked

    e_both, l_both = run(True, True)
    e_nomti, _ = run(True, False)
    e_nostruct, _ = run(False, True)
    e_none, _ = run(False, False)
    assert e_both and l_both, "struktura∧MTI powinno dać ENTRY"
    assert not e_nomti, "struktura bez MTI NIE powinno dać ENTRY"
    assert not e_nostruct, "MTI bez struktury NIE powinno dać ENTRY"
    assert not e_none, "nic NIE powinno dać ENTRY"
    # conf pasywne: nawet WYSOKIE conf bez MTI nie wpuszcza (conf zdegradowane do telemetrii)
    from r02.target_channel import TargetChannel as TC
    ch = TC(cfg); ev = None
    for t in range(cfg.entry_k):
        ev = ch.on_frame(Box(0.5, 0.376, 0.05, 0.06, conf=0.99), float(t), mti_ok=False)
    assert ev != EV_ENTRY, "conf=0.99 bez MTI wpuściło — conf NIE jest pasywne!"
    return "4-wektory + conf-pasywne PASS"


ALL_TESTS = [
    ("B1.quat_sanity", test_quat_to_R_sanity),
    ("B1.derotation_geometry", test_derotation_geometry_both_axes),
    ("B1.pipeline_null_and_object", test_pipeline_background_null_and_object),
    ("B1.pairing_tolerance", test_pairing_tolerance),
    ("B2.fp_ground_parallax", test_fp_ground_parallax_translation),
    ("B2.fp_own_shadow", test_fp_own_shadow),
    ("B2.fp_props_frame_edge", test_fp_props_frame_edge),
    ("B2.fp_derotation_residual_fast_yaw", test_fp_derotation_residual_fast_yaw),
    ("B3.entry_gate_four_vectors", test_entry_gate_four_vectors),
]

if __name__ == "__main__":
    import traceback
    npass = 0
    for name, fn in ALL_TESTS:
        try:
            r = fn(); npass += 1
            print(f"PASS {name}  {r if r is not None else ''}")
        except Exception as e:
            print(f"FAIL {name}: {e}")
            traceback.print_exc()
    print(f"\n=== {npass}/{len(ALL_TESTS)} PASS ===")
    raise SystemExit(0 if npass == len(ALL_TESTS) else 1)
