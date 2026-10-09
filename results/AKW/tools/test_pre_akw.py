#!/usr/bin/env python3
"""results/AKW/tools/test_pre_akw.py — testy przedlotowe PRE_AKW §3 / PROMPT_AKW_S1 §2
(FAIL któregokolwiek ⇒ nie latamy).

§3.1 pass-through bajtowy: na sekwencjach feedów ODTWORZONYCH z logów DET (demo.jsonl
     ramienia B i V2 — pola own_pos/vel, trk_pos_ned, track_age_s, track_valid, t_sim
     niosą komplet wejść kontraktu step) AkwScan zwraca cmd IDENTYCZNY polami
     z NetController dla phase≠hold; na tickach hold różni się WYŁĄCZNIE polem yaw.
§3.2 profil: rampa ψ(t) 30°/s CCW (yaw atan2 rosnący), wrap do (-π,π], dwell 2.0 s,
     wznowienie od bieżącego yaw (nigdy powrót do 0), reset() czyści stan;
     pierwsze hold bez historii tracku: baza = yaw delegata 0.0 (nota wiążąca).
§3.3 rejestr: make_controller("net_akw") działa, controller_sha = sha(akw_scan.py);
     make_controller("net") NIEZMIENIONE (regresja).
"""
import hashlib
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("NET_ARM", "ncp")

from r03.controllers import make_controller, controller_sha
from r03.controllers.net_controller import NetController
from r03.controllers.akw_scan import AkwScan, AKW_SCAN_DPS_FROZEN, AKW_DWELL_S_FROZEN

DT = 0.05  # pętla 20 Hz


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def _demo_rows(path):
    rows = []
    with open(path) as f:
        for ln in f:
            r = json.loads(ln)
            if "tick" in r and "own_pos_ned" in r:
                rows.append(r)
    return rows


def _feed_of(r):
    return {"trk_pos_ned": r["trk_pos_ned"], "track_age_s": r["track_age_s"],
            "track_valid": r["track_valid"]}


def _replay_compare(demo_path):
    """Przegania identyczną sekwencję feed/own przez NetController i AkwScan.
    Zwraca (n_ticks, n_hold, n_hold_yaw_zmieniony)."""
    rows = _demo_rows(demo_path)
    assert rows, f"pusty replay {demo_path}"
    net = NetController()
    akw = AkwScan()
    n_hold = 0
    n_hold_yaw_diff = 0
    last_ep = None
    for r in rows:
        if r["episode_id"] != last_ep:          # jak bench: kontroler per epizod → reset
            net.reset(); akw.reset(); last_ep = r["episode_id"]
        fs = _feed_of(r)
        net.set_feed(fs); akw.set_feed(fs)
        c_net = net.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
        c_akw = akw.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
        if c_net["extra"]["phase"] == "hold":
            n_hold += 1
            for k in c_net:
                if k == "yaw":
                    continue
                assert c_akw[k] == c_net[k], \
                    f"hold tick {r['tick']} ep {r['episode_id']}: pole {k} różne"
            if c_akw["yaw"] != c_net["yaw"]:
                n_hold_yaw_diff += 1
        else:
            assert c_akw == c_net, \
                f"tick {r['tick']} ep {r['episode_id']} phase={c_net['extra']['phase']}: cmd różny"
    return len(rows), n_hold, n_hold_yaw_diff


# ---------- §3.1 pass-through bajtowy ----------

def test_passthrough_ramie_B():
    n, n_hold, _ = _replay_compare(os.path.join(ROOT, "results/DET/camp/r1_B/demo.jsonl"))
    assert n > 1000
    assert n_hold >= 1          # B ma ticki hold tylko na rozbiegu epizodu (age=1e9)


def test_passthrough_ramie_V2():
    n, n_hold, n_diff = _replay_compare(os.path.join(ROOT, "results/DET/camp/r1_V2/demo.jsonl"))
    assert n > 1000
    assert n_hold > 100         # V2 r1 ma długie odcinki ślepe (c01-c03)
    assert n_diff > 0           # skan faktycznie zmienia yaw po dwell


def test_passthrough_hold_yaw_rozny_po_dwell():
    """Na ramieniu V2: w obrębie jednego ciągłego odcinka hold yaw delegata (0.0)
    i yaw skanu rozjeżdżają się najpóźniej po dwell+1 tick."""
    rows = _demo_rows(os.path.join(ROOT, "results/DET/camp/r1_V2/demo.jsonl"))
    akw = AkwScan()
    hold_run_t0 = None
    seen_diff_in_long_hold = False
    last_ep = None
    for r in rows:
        if r["episode_id"] != last_ep:
            akw.reset(); hold_run_t0 = None; last_ep = r["episode_id"]
        akw.set_feed(_feed_of(r))
        c = akw.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
        if c["extra"]["phase"] == "hold":
            if hold_run_t0 is None:
                hold_run_t0 = r["t_sim"]
            if r["t_sim"] - hold_run_t0 > AKW_DWELL_S_FROZEN + 2 * DT and c["yaw"] != 0.0:
                seen_diff_in_long_hold = True
        else:
            hold_run_t0 = None
    assert seen_diff_in_long_hold


def test_passthrough_wazne_tracki_V2_z_percep_feed():
    """PROMPT_AKW_S1 §2.1: ważne (fresh) tracki V2 wprost z percep_feed.jsonl —
    na tickach track (phase≠hold) cmd AkwScan IDENTYCZNY polami z NetController."""
    fresh = []
    with open(os.path.join(ROOT, "results/DET/camp/r1_V2/percep_feed.jsonl")) as f:
        for ln in f:
            r = json.loads(ln)
            if r.get("fresh") and r.get("trk_pos_ned") and "t_frame" in r:
                fresh.append(r)
    assert len(fresh) > 300
    demo = _demo_rows(os.path.join(ROOT, "results/DET/camp/r1_V2/demo.jsonl"))
    owns = sorted((d["t_sim"], d["own_pos_ned"], d["own_vel_ned"]) for d in demo)
    own_t = [o[0] for o in owns]
    import bisect
    net = NetController(); akw = AkwScan()
    n_cmp = 0
    for k, r in enumerate(sorted(fresh, key=lambda x: x["t_frame"])):
        t = r["t_frame"]
        i = bisect.bisect_left(own_t, t)
        if i >= len(owns):
            break
        _, own, vel = owns[i]
        fs = {"trk_pos_ned": r["trk_pos_ned"], "track_age_s": 0.05, "track_valid": True}
        net.set_feed(fs); akw.set_feed(fs)
        c_net = net.step(k, own, vel, t, False)
        c_akw = akw.step(k, own, vel, t, False)
        assert c_net["extra"]["phase"] != "hold"
        assert c_akw == c_net, f"t_frame {t}: cmd różny na ważnym tracku V2"
        n_cmp += 1
    assert n_cmp > 300


# ---------- §3.2 profil ----------

class _StubNet:
    """Delegat-zaślepka: hold gdy feed nieważny, inaczej track z yaw=atan2."""
    def __init__(self):
        self._feed = None
    def reset(self):
        self._feed = None
    def set_feed(self, fs):
        self._feed = fs
    def step(self, tick, pos, vel, now_s, descending):
        fd = self._feed
        if fd is None or not fd.get("track_valid") or fd.get("track_age_s", 1e9) > 1.0:
            return {"tgt_ned": tuple(pos), "v_ned": (0.0, 0.0, 0.0), "yaw": 0.0,
                    "seg_i": 0, "dist": None, "wps": None, "extra": {"phase": "hold"}}
        trk = fd["trk_pos_ned"]
        yaw = math.atan2(trk[1] - pos[1], trk[0] - pos[0])
        return {"tgt_ned": tuple(trk), "v_ned": (1.0, 0.0, 0.0), "yaw": yaw,
                "seg_i": 0, "dist": 5.0, "wps": None, "extra": {"phase": "approach"}}


def _akw_ze_stubem():
    akw = AkwScan.__new__(AkwScan)        # bez __init__ delegata (wagi niepotrzebne w teście profilu)
    akw._net = _StubNet()
    akw.scan_dps = AKW_SCAN_DPS_FROZEN
    akw.dwell_s = AKW_DWELL_S_FROZEN
    akw.scan_frozen = True
    akw._omega = math.radians(AKW_SCAN_DPS_FROZEN)
    akw.reset()
    return akw


FEED_BRAK = None
FEED_OK_E = {"trk_pos_ned": [0.0, 10.0, -10.0], "track_age_s": 0.1, "track_valid": True}

POS = [0.0, 0.0, -10.0]
VEL = [0.0, 0.0, 0.0]


def _tick(akw, fs, now_s, tick=0):
    akw.set_feed(fs)
    return akw.step(tick, POS, VEL, now_s, False)


def test_profil_dwell_i_rampa_30dps():
    akw = _akw_ze_stubem()
    t = 100.0
    yaws = []
    for i in range(int(8.0 / DT)):          # 8 s hold od zimnego startu
        c = _tick(akw, FEED_BRAK, t + i * DT, i)
        assert c["extra"]["phase"] == "hold"
        yaws.append((i * DT, c["yaw"]))
    for dt_rel, y in yaws:
        if dt_rel <= AKW_DWELL_S_FROZEN:
            assert y == 0.0, f"dwell naruszony @ {dt_rel}: {y}"
        else:
            expected = math.radians(AKW_SCAN_DPS_FROZEN) * (dt_rel - AKW_DWELL_S_FROZEN)
            expected = math.atan2(math.sin(expected), math.cos(expected))
            assert abs(y - expected) < 1e-9, f"rampa @ {dt_rel}: {y} vs {expected}"
    # CCW = yaw ROSNĄCY zaraz po dwell
    po_dwell = [y for dt_rel, y in yaws if AKW_DWELL_S_FROZEN < dt_rel < AKW_DWELL_S_FROZEN + 1.0]
    assert all(b > a for a, b in zip(po_dwell, po_dwell[1:]))


def test_profil_wrap_pelny_obrot():
    akw = _akw_ze_stubem()
    t = 0.0
    n = int((AKW_DWELL_S_FROZEN + 360.0 / AKW_SCAN_DPS_FROZEN + 1.0) / DT)  # dwell + 12 s + 1 s
    last = None
    for i in range(n):
        c = _tick(akw, FEED_BRAK, t + i * DT, i)
        y = c["yaw"]
        assert -math.pi < y <= math.pi + 1e-12, f"poza wrap: {y}"
        last = (i * DT, y)
    # po pełnym obrocie (dwell+12 s) ψ wraca w okolice bazy (0): |ψ| = ω·resztka
    dt_rel, y = last
    expected = math.radians(AKW_SCAN_DPS_FROZEN) * (dt_rel - AKW_DWELL_S_FROZEN) % (2 * math.pi)
    expected = math.atan2(math.sin(expected), math.cos(expected))
    assert abs(y - expected) < 1e-9


def test_profil_wznowienie_od_biezacego_yaw_nigdy_do_zera():
    akw = _akw_ze_stubem()
    t = 50.0
    # track → yaw=atan2(10,0)=π/2 (intruz na wschodzie)
    c = _tick(akw, FEED_OK_E, t)
    assert c["extra"]["phase"] == "approach" and abs(c["yaw"] - math.pi / 2) < 1e-12
    # utrata → hold: dwell trzyma π/2 (ostatni yaw), nie 0
    for i in range(1, int(AKW_DWELL_S_FROZEN / DT)):
        c = _tick(akw, FEED_BRAK, t + i * DT)
        assert c["yaw"] == math.pi / 2, f"dwell nie trzyma ostatniego yaw: {c['yaw']}"
    # po dwell rampa OD π/2 w górę (CCW), bez skoku do 0
    # (hold zaczął się w t+DT, więc w t+DWELL+10·DT rampa biegnie 9·DT)
    c = _tick(akw, FEED_BRAK, t + AKW_DWELL_S_FROZEN + 10 * DT)
    expected = math.pi / 2 + math.radians(AKW_SCAN_DPS_FROZEN) * (9 * DT)
    assert abs(c["yaw"] - expected) < 1e-9


def test_profil_reakwizycja_i_ponowna_utrata():
    akw = _akw_ze_stubem()
    t = 0.0
    for i in range(100):                     # 5 s hold (skan już kręci)
        c = _tick(akw, FEED_BRAK, t + i * DT)
    y_skan = c["yaw"]
    assert y_skan != 0.0
    # reakwizycja: yaw wraca do atan2 delegata (pass-through)
    c = _tick(akw, FEED_OK_E, t + 5.0)
    assert abs(c["yaw"] - math.pi / 2) < 1e-12
    # ponowna utrata: NOWY dwell 2.0 s od π/2, potem rampa od π/2
    c = _tick(akw, FEED_BRAK, t + 5.0 + DT)
    assert c["yaw"] == math.pi / 2
    c = _tick(akw, FEED_BRAK, t + 5.0 + DT + AKW_DWELL_S_FROZEN - DT)
    assert c["yaw"] == math.pi / 2, "nowy dwell po reakwizycji nierespektowany"


def test_profil_reset_czysci_stan():
    akw = _akw_ze_stubem()
    for i in range(200):
        akw.set_feed(FEED_BRAK)
        akw.step(i, POS, VEL, 10.0 + i * DT, False)
    akw.reset()
    assert akw._hold_t0 is None and akw._base_yaw is None and akw._last_yaw == 0.0
    # po resecie: zimny start → baza ψ_last=0.0 (PROMPT_AKW_S1 §1), dwell od nowego now_s
    c = _tick(akw, FEED_BRAK, 777.0)
    assert c["yaw"] == 0.0


# ---------- §3.3 rejestr ----------

def test_rejestr_net_akw():
    ctrl = make_controller("net_akw")
    assert isinstance(ctrl, AkwScan) and ctrl.name == "net_akw"
    assert controller_sha(ctrl) == _sha256(os.path.join(ROOT, "r03/controllers/akw_scan.py"))
    assert ctrl.scan_frozen and ctrl.scan_dps == 30.0 and ctrl.dwell_s == 2.0
    # delegacja atrybutów delegata (SR-2 guard już przeszedł w konstruktorze)
    assert ctrl.arm == "ncp" and len(ctrl.weights_sha) == 64


def test_rejestr_net_regresja():
    ctrl = make_controller("net")
    assert type(ctrl) is NetController and ctrl.name == "net"
    assert controller_sha(ctrl) == _sha256(os.path.join(ROOT, "r03/controllers/net_controller.py"))


def test_rejestr_nieznany_nadal_blad():
    try:
        make_controller("nie_ma_takiego")
        assert False
    except ValueError:
        pass
