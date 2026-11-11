"""results/NAD2/tools/test_nad2_s1.py — testy S1 NADIR-II (PROMPT_NAD2_S1 §R T): przełączniki jawne, domyślnie stare zachowanie,
stałe tabeli ≡ freeze_U.json, wybór ramy w osłonie, przedział z τ + 0.012 s, próg REFUSE(τ*) 0.95 s, passthrough NADIR_MODE=0."""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/NAD2/tools"))

from harness import nadir_fix as NF
from r03 import nadir_shield as NS


def _sh(**kw):
    s = NS.NadirShield(**kw); s.reset(); return s


def test_domyslnie_stara_litera_i_stary_rezim(monkeypatch):
    monkeypatch.delenv("NADIR_LITERA", raising=False)
    assert NF.Rama().litera == "NADIR1"
    assert _sh(kont_mode=True, nadir_mode=True).nad2 is False


def test_env_wlacza_nad2_tylko_w_nadir(monkeypatch):
    monkeypatch.setenv("NADIR_LITERA", "NAD2")
    assert NF.Rama().litera == "NAD2"
    assert _sh(kont_mode=True, nadir_mode=True).nad2 is True
    assert _sh(kont_mode=True, nadir_mode=False).nad2 is False


def test_tabela_zgodna_z_freeze():
    assert all(NS.nad2_tabela_check(ROOT).values())


def test_przedzial_z_marginesem():
    assert NS.przedzial_nad2(0.232) == 0
    assert NS.przedzial_nad2(0.2381) == 1
    assert NS.przedzial_nad2(1.038) == 4
    assert NS.przedzial_nad2(1.0381) is None


def _krok(sh, k, pe, pc, cs, now, t_fix=0.0, kosz=1, tryb="para"):
    return sh.step(k, pe, [0, 0, 0], pe, cs_gnss_pos=cs, now=now, t_fix=t_fix, kosz_j=kosz, tryb=tryb, pos_corr=pc, target_corr=pc)


def test_wybor_ramy_i_r_est():
    sh = _sh(kont_mode=True, nadir_mode=True, nad2=True)
    pe, pc = [2.0, 1.0, -10.0], [6.0, 4.0, -10.0]
    d = _krok(sh, 0, pe, pc, True, 0.0)
    assert d["nad2"]["rama"] == "ekf" and abs(sh._r_est - math.hypot(2, 1)) < 1e-12
    for k in range(1, 4):
        d = _krok(sh, k, pe, pc, False, k * 0.05, t_fix=k * 0.05)
    assert sh.kont_phase() == "KONT" and d["nad2"]["rama"] == "corr" and abs(sh._r_est - math.hypot(6, 4)) < 1e-12
    assert d["applied"][:2] == [pc[0] - 4.0, pc[1] - 3.0]


def test_refuse_tau_star_przy_095():
    sh = _sh(kont_mode=True, nadir_mode=True, nad2=True)
    p = [5.0, 0.0, -10.0]
    for k, now in enumerate((0.0, 0.05, 0.94)):
        _krok(sh, k, p, p, False, now, t_fix=0.0)
    assert sh.kont_phase() == "KONT"
    thr = NS.TAU_STAR_NAD2 - 2 * sh.cfg.dt                  # 0.95 (float 0.9500000000000001 — ta sama formuła co NADIR-I i lustro)
    _krok(sh, 3, p, p, False, thr - 1e-9, t_fix=0.0)
    assert sh.kont_phase() == "KONT"
    _krok(sh, 4, p, p, False, thr, t_fix=0.0)
    assert sh.kont_phase() == "KONT_REFUSE" and sh.kont_cause == NS.CAUSE_TAUSTAR


def test_brak_poprawki_pole_najgorsze():
    sh = _sh(kont_mode=True, nadir_mode=True, nad2=True)
    p = [5.0, 0.0, -10.0]
    for k, now in enumerate((0.0, 0.05, 0.1)):
        sh.step(k, p, [0, 0, 0], p, cs_gnss_pos=False, now=now, pos_corr=p, target_corr=p)
    assert (sh._tryb_eff, sh._j_eff) == NS.POLE_BRAK_NAD2


def test_krok_drivera_r_est_z_ramy():
    import nad2_krok

    class R:
        t_fix, kosz, tryb = 0.0, 2, "jeden"
    sh = _sh(kont_mode=True, nadir_mode=True, nad2=True)
    pe, pc = [1.0, 1.0, -10.0], [9.0, -3.0, -10.0]
    for k in range(4):
        d, pb = nad2_krok.krok(sh, k, pe, pc, [0, 0, 0], pe, pc, "PATROL", None, False, k * 0.05, None, R)
    assert pb == pc and abs(sh._r_est - math.hypot(9, -3)) < 1e-12
