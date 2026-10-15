#!/usr/bin/env python3
"""results/FANTOM/tools/test_pre_fantom.py — testy przedlotowe nogi FANTOM
(PRE_FANTOM §3.1 / PROMPT_FANTOM_S1 §1-§2; FAIL któregokolwiek ⇒ nie latamy).

T1 tożsamość delegacji (nota wykonawcza do PRE §3.1, uzasadnienie w RAPORT_FANTOM_S1):
   delegat niesie sieć REKURENCYJNĄ (ncp), której stan ewoluuje wyłącznie na tickach
   track (net_controller.py:106-111 — invalid fd wraca przed siecią), więc:
   (a) ŚWIADEK-DELEGAT: na KAŻDYM ticku cmd `net_fantom` (modulo klucze q_* w
       kwarantannie) jest BIT-W-BIT równy cmd `net_akw` karmionego strumieniem
       EFEKTYWNYM (blank w kwarantannie, realny fd od ticku wyjścia) — pełna
       tożsamość delegacji, obie gałęzie;
   (b) WPROST-VS-NET_AKW: na epizodach, gdzie fd był invalid przez całą kwarantannę
       (ślepy start — strumień efektywny ≡ realny), cmd `net_fantom` == cmd `net_akw`
       BIT-W-BIT na KAŻDYM ticku (track i hold) — litera PRE w najmocniejszej
       uczciwej formie; na strumieniu rozbieżnym (B, lock od startu) bit-w-bit wobec
       kontrfaktycznego net_akw nie może zajść z definicji kwarantanny (ukryła fd),
       a nie z wady delegacji — pokrywa to (a).
TP predykat K1 (wybrany regułą T2): fantom (valid od startu, statyczny) nie robi
   wyjścia A/B — wychodzi fallbackiem C po T_q=3.0; czysty start wychodzi (A) na
   PIERWSZYM przejściu invalid→valid; przeskok trk_pos > D_JUMP vs migawka z t_ref
   wychodzi (B); ślad valid-statyczny (B-ramię bez skoku) wychodzi C po T_q — koszt
   nazwany; wyjście JEDNORAZOWE per epizod; reset() ponownie uzbraja; zero mutacji fd.
TR rejestr: make_controller("net_fantom") działa, controller_sha=sha(fantom_scan.py);
   regresja "net"/"net_akw" NIEZMIENIONA.
"""
import hashlib
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("NET_ARM", "ncp")
os.environ.pop("FANTOM_QLOG", None)      # testy bez dziennika diagnostycznego

from r03.controllers import make_controller, controller_sha
from r03.controllers.akw_scan import AkwScan
from r03.controllers.fantom_scan import (FantomScan, _blank_fd, FANTOM_EPS_S_FROZEN,
                                         FANTOM_TQ_S_FROZEN, FANTOM_DJUMP_M_FROZEN)

DT = 0.05


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
    return {"trk_pos_ned": r["trk_pos_ned"], "trk_vel_ned": r.get("trk_vel_ned", [0, 0, 0]),
            "track_age_s": r["track_age_s"], "track_valid": r["track_valid"]}


def _strip_q(cmd):
    out = dict(cmd)
    out["extra"] = {k: v for k, v in cmd["extra"].items() if not k.startswith("q_")}
    return out


# ---------- T1: tożsamość poza kwarantanną (sekwencje odtworzeniowe) ----------

def _replay_witness(demo_path):
    """(a) świadek-delegat: fantom == net_akw na strumieniu EFEKTYWNYM, każdy tick."""
    rows = _demo_rows(demo_path)
    assert rows, f"pusty replay {demo_path}"
    fant = FantomScan()
    eff = AkwScan()                       # świadek karmiony strumieniem efektywnym
    last_ep = None
    n_q = n_exits = n_post = 0
    for r in rows:
        if r["episode_id"] != last_ep:
            fant.reset(); eff.reset(); last_ep = r["episode_id"]
        fs = _feed_of(r)
        fant.set_feed(fs)
        q_was = fant.q_active
        c_f = fant.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
        q_now = fant.q_active
        eff.set_feed(_blank_fd(fs) if (q_was and q_now and fs["track_valid"]) else fs)
        c_e = eff.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
        if q_was and q_now:
            assert _strip_q(c_f) == c_e, f"kwarantanna != świadek @tick {r['tick']}"
            n_q += 1
        elif q_was and not q_now:
            assert _strip_q(c_f) == c_e, f"tick wyjścia != świadek @tick {r['tick']}"
            n_exits += 1
        else:
            assert c_f == c_e, f"pass-through != świadek @tick {r['tick']}"
            assert not any(k.startswith("q_") for k in c_f["extra"]), "q_* poza kwarantanną"
            n_post += 1
    return len(rows), n_q, n_exits, n_post


def _replay_direct_blind(demo_path):
    """(b) wprost-vs-net_akw: bit-w-bit na epizodach, gdzie fd invalid przez całą
    kwarantannę (strumień efektywny ≡ realny). Zwraca (n_ep_slepych, n_tickow_cmp)."""
    rows = _demo_rows(demo_path)
    by_ep = {}
    for r in rows:
        by_ep.setdefault(r["episode_id"], []).append(r)
    n_eps = n_cmp = 0
    for ep, ers in by_ep.items():
        fant = FantomScan(); akw = AkwScan()
        fant.reset(); akw.reset()
        blind = True
        for r in ers:
            fs = _feed_of(r)
            if fant.q_active and fs["track_valid"]:
                blind = False             # fd ważny w kwarantannie ⇒ strumienie rozbieżne
                break
            fant.set_feed(fs); akw.set_feed(fs)
            q_was = fant.q_active
            c_f = fant.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
            c_a = akw.step(r["tick"], r["own_pos_ned"], r["own_vel_ned"], r["t_sim"], False)
            assert _strip_q(c_f) == c_a, f"ślepy start: cmd różny @tick {r['tick']} ep {ep}"
            if not q_was:
                assert c_f == c_a         # od ticku PO wyjściu: dosłowny bit-w-bit (zero q_*)
            n_cmp += 1
        if blind:
            n_eps += 1
    return n_eps, n_cmp


def test_T1a_swiadek_ramie_B():
    n, n_q, n_ex, n_post = _replay_witness(os.path.join(ROOT, "results/DET/camp/r1_B/demo.jsonl"))
    assert n > 1000 and n_ex >= 1 and n_post > 1000
    assert n_q < 30 * 4                   # B: wyjście szybkie (A przy pierwszym valid / B-skok)


def test_T1a_swiadek_ramie_V2():
    n, n_q, n_ex, n_post = _replay_witness(os.path.join(ROOT, "results/DET/camp/r1_V2/demo.jsonl"))
    assert n > 1000 and n_ex >= 1 and n_post > 500
    assert n_q > 0


def test_T1b_wprost_slepe_starty_V2():
    n_eps, n_cmp = _replay_direct_blind(os.path.join(ROOT, "results/DET/camp/r1_V2/demo.jsonl"))
    assert n_eps >= 2 and n_cmp > 500     # r1_V2 DET: c01–c03 ślepe całe epizody


# ---------- TP: predykat K1 (syntetyczne sekwencje, pełny tor z wagami ncp) ----------

POS = [0.0, 0.0, -10.0]
VEL = [0.0, 0.0, 0.0]
FD_T = {"trk_pos_ned": [0.0, 10.0, -10.0], "trk_vel_ned": [0, 0, 0],
        "track_age_s": 0.05, "track_valid": True}


def _mk():
    f = FantomScan()
    f.reset()
    return f


def _tick(f, fd, t, i=0):
    f.set_feed(fd)
    return f.step(i, POS, VEL, t, False)


FD_BAD = {"trk_pos_ned": [0, 0, 0], "trk_vel_ned": [0, 0, 0],
          "track_age_s": 1e9, "track_valid": False}


def test_TP_fantom_statyczny_wychodzi_C():
    f = _mk()
    t0 = 100.0
    for i in range(int(3.5 / DT)):
        t = t0 + i * DT
        # fantom: valid od t_ref, pozycja statyczna, stemple sprzed t_ref (age = dt + 0.1)
        fd = dict(FD_T, track_age_s=(t - t0) + 0.1)
        c = _tick(f, fd, t, i)
        if t - t0 < FANTOM_TQ_S_FROZEN:
            assert f.q_exit_reason in (None, "C")
            if f.q_exit_reason is None:
                assert c["extra"]["q_active"] is True
    assert f.q_exit_reason == "C"
    assert abs((f.q_exit_t - t0) - FANTOM_TQ_S_FROZEN) < 2 * DT


def test_TP_czysty_start_wychodzi_A():
    f = _mk()
    t0 = 50.0
    for i in range(40):                           # 2 s bez tracku
        c = _tick(f, FD_BAD, t0 + i * DT, i)
        assert c["extra"]["q_active"] is True
    c = _tick(f, dict(FD_T), t0 + 2.0, 40)        # pierwszy ważny ⇒ (A) natychmiast
    assert f.q_active is False and f.q_exit_reason == "A"
    assert c["extra"]["q_exit_reason"] == "A"
    assert abs(f.q_exit_t - (t0 + 2.0)) < 1e-9


def test_TP_przeskok_wychodzi_B():
    f = _mk()
    t0 = 10.0
    _tick(f, dict(FD_T), t0)                      # migawka z t_ref = (0,10)
    _tick(f, dict(FD_T), t0 + DT)
    fd_jump = dict(FD_T, trk_pos_ned=[0.0, 17.0, -10.0])   # skok 7 m > D_JUMP
    c = _tick(f, fd_jump, t0 + 2 * DT)
    assert f.q_active is False and f.q_exit_reason == "B"
    assert c["extra"]["q_exit_reason"] == "B"


def test_TP_slad_B_statyczny_wychodzi_C_koszt_nazwany():
    f = _mk()
    t0 = 10.0
    i = 0
    while f.q_active and i < int(3.5 / DT):
        _tick(f, dict(FD_T), t0 + i * DT, i)      # valid od startu, bez skoku, bez utraty
        i += 1
    assert f.q_exit_reason == "C"
    assert abs((f.q_exit_t - t0) - FANTOM_TQ_S_FROZEN) < 2 * DT


def test_TP_jednorazowe_i_reset_uzbraja():
    f = _mk()
    t0 = 0.0
    _tick(f, FD_BAD, t0)
    _tick(f, dict(FD_T), t0 + 0.2)                # wyjście (A)
    assert f.q_active is False and f.q_exit_reason == "A"
    # utrata i powrót tracku w TYM epizodzie: kwarantanna NIE wraca (pass-through)
    _tick(f, FD_BAD, t0 + 1.0)
    c = _tick(f, dict(FD_T), t0 + 1.2)
    assert f.q_active is False and not any(k.startswith("q_") for k in c["extra"])
    f.reset()
    assert f.q_active is True and f.q_exit_reason is None


def test_TP_zero_mutacji_fd_i_blank_ksztalt():
    f = _mk()
    fd = dict(FD_T)
    fd_copy = json.loads(json.dumps(fd))
    _tick(f, fd, 0.0)                             # kwarantanna: delegat dostaje blank
    assert fd == fd_copy, "fd zmutowany"
    b = _blank_fd(fd)
    assert b["track_valid"] is False and b["track_age_s"] == 1e9
    assert b["trk_pos_ned"] == [0.0, 0.0, 0.0] and "feed_sha" in b
    assert b is not fd


def test_TP_parametry_frozen():
    f = _mk()
    assert (f.eps_s, f.t_q_s, f.d_jump_m) == (0.5, 3.0, 5.0)
    assert os.environ.get("FANTOM_QLOG") is None


# ---------- TR: rejestr ----------

def test_TR_rejestr_net_fantom():
    ctrl = make_controller("net_fantom")
    assert isinstance(ctrl, FantomScan) and ctrl.name == "net_fantom"
    assert controller_sha(ctrl) == _sha256(os.path.join(ROOT, "r03/controllers/fantom_scan.py"))
    # delegacja: atrybuty delegata AkwScan (profil II FROZEN) i NetController
    assert ctrl.scan_mode == "step_stare" and ctrl.step_deg == 40.0
    assert ctrl.arm == "ncp" and len(ctrl.weights_sha) == 64


def test_TR_regresja_net_i_net_akw():
    assert type(make_controller("net")).__name__ == "NetController"
    a = make_controller("net_akw")
    assert isinstance(a, AkwScan)
    assert controller_sha(a) == _sha256(os.path.join(ROOT, "r03/controllers/akw_scan.py"))
