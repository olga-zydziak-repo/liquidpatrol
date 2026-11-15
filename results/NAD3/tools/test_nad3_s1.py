#!/usr/bin/env python3
"""results/NAD3/tools/test_nad3_s1.py — testy jednostkowe NAD3 S1 (PROMPT_NAD3_S1 §4 T): decymator (dokładnie jedna poprawka
na slot, żadnej między slotami), passthrough (`przetworz(fx) is fx`), bias radialny, stan dostarczony w datagramach
nieprzyjętych, generator scenariuszy z wartościami domyślnymi bit w bit, odmowa startu osłony z kodem, reżim nad2 bez zmian,
u_nad3 z tabelą W1 ≡ u_nad2 bitowo, manifest NAD3 ↔ suma w nad3_boot.sh."""
import copy
import json
import math
import os
import sys

import pytest

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from harness import nad3_degrad as DG
from r03 import nadir_shield as NS


def strumien(n=60, t0=100.0, brak=()):
    out = []
    for k in range(n):
        t = round(t0 + 0.2 * k, 4)
        ok = k not in brak
        out.append({"t": "fx", "seq": k + 1, "t_frame": t, "ok": ok, "tryb": "para" if ok else None, "kosz": 1 if ok else None,
                    "d_ne": [0.01 * k, -0.02 * k], "t_fix": t if ok else None, "p_fix_ne": [12.0 + 0.1 * k, 5.0] if ok else None})
    return out


def test_passthrough_ten_sam_obiekt(monkeypatch):
    monkeypatch.delenv(DG.ENV, raising=False)
    d = DG.z_env()
    for fx in strumien(10):
        b = json.dumps(fx)
        assert d.przetworz(fx) is fx
        assert json.dumps(fx) == b
    monkeypatch.setenv(DG.ENV, "  ")
    assert DG.z_env().przetworz(strumien(1)[0]) is not None and DG.z_env().cfg is None


@pytest.mark.parametrize("brak", [(), (5, 10, 11, 12, 13, 14, 15, 33)])
def test_decymator_jedna_na_slot(brak):
    s = strumien(60, brak=brak)
    d = DG.Degradacja({"model": "zero", "f": 1, "K": 0})
    dost = [d.przetworz(fx) for fx in s]
    t0 = s[0]["t_frame"]
    sloty = {}
    for o, fx in zip(dost, s):
        if o.get("ok"):
            n = int(math.floor((fx["t_frame"] - t0 + DG.TOL_SLOT) * 1.0))
            assert o["nad3"]["slot"] == n
            sloty.setdefault(n, []).append(fx["t_frame"])
    oczek = {int(math.floor(fx["t_frame"] - t0 + DG.TOL_SLOT)) for fx in s if fx["ok"]}
    assert set(sloty) == oczek                                       # każdy slot z poprawką ok ma dostawę
    assert all(len(v) == 1 for v in sloty.values())                  # dokładnie jedna na slot
    for n, (t,) in sloty.items():                                     # pierwsza poprawka ok w slocie, nic między slotami
        pierwsza = min(fx["t_frame"] for fx in s if fx["ok"] and int(math.floor(fx["t_frame"] - t0 + DG.TOL_SLOT)) == n)
        assert t == pierwsza
    if not brak:
        assert all(abs(v[0] - (t0 + n)) < 1e-9 for n, v in sloty.items())


def test_bias_radialny_i_stan_dostarczony():
    s = strumien(12)
    for kier, znak in (("na_zewnatrz", 1), ("do_srodka", -1)):
        d = DG.Degradacja({"model": "bias_rad", "kierunek": kier, "E_max": 1.75, "f": 1, "K": 0, "ziarno": 3})
        ost = None
        for fx in s:
            o = d.przetworz(fx)
            if o.get("ok"):
                E = o["nad3"]["E"]
                p = fx["p_fix_ne"]
                n = math.hypot(*p)
                assert abs(math.hypot(*E) - 1.75) < 1e-6
                assert abs(E[0] - znak * 1.75 * p[0] / n) < 1e-6 and abs(E[1] - znak * 1.75 * p[1] / n) < 1e-6
                assert abs(o["d_ne"][0] - (fx["d_ne"][0] + E[0])) < 1e-6
                ost = (o["d_ne"], fx["t_fix"])
            else:
                assert o["powod"] == "nad3_decymacja" and (o["d_ne"], o["t_fix"]) == ost
        assert d.echo()["kierunek"] == kier


def test_generator_domyslne_bit_w_bit():
    from bench import scenarios as S
    b = json.dumps(S.gen_manifest(), indent=1)
    assert b == open(os.path.join(ROOT, "results/BENCH/scenario_manifest.json")).read()
    c = S.CELLS[9]
    assert S.gen_episode(c, 3) == S.gen_episode(c, 3, range0=15.0, disk_r=18.0, prog_zawracania=14.0)


def test_manifest_nad3_suma_w_boot():
    m = json.load(open(os.path.join(ROOT, "results/NAD3/s1/nad3_manifest_v2.json")))   # ANEKS_NAD3-1 §3.3: v2
    import hashlib
    assert hashlib.sha256(open(os.path.join(ROOT, m["manifest"]), "rb").read()).hexdigest() == m["sha256"]
    assert m["sha256"] in open(os.path.join(ROOT, "results/NAD3/tools/nad3_boot.sh")).read()
    assert all(t["r_ok"] and t["ciaglosc_ok"] and t["czas_ok"] for t in m["testy"].values())
    man = json.load(open(os.path.join(ROOT, m["manifest"])))["episodes"]
    assert len(man) == 120 and all(i == e["episode_id"] for i, e in enumerate(man))     # pozycja = numer epizodu


def _tab(p):
    path = os.path.join(ROOT, f"results/NAD3/s1/freeze_U_{p}.json")
    return path, json.load(open(path))["sha256_tabeli"]


def test_odmowa_startu_kody(monkeypatch, tmp_path):
    monkeypatch.delenv(NS.OSLONA_ENV, raising=False)
    path, sha = _tab("P1")
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, tabela=str(tmp_path / "brak.json"), tabela_sha=sha)
    assert e.value.kod == 41
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, tabela=path, tabela_sha=None)
    assert e.value.kod == 41
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, tabela=path, tabela_sha="0" * 64)
    assert e.value.kod == 42
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, nad2=True, tabela=path, tabela_sha=sha)
    assert e.value.kod == 43
    monkeypatch.setenv(NS.OSLONA_ENV, "nad4")
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True)
    assert e.value.kod == 44
    monkeypatch.setenv(NS.OSLONA_ENV, "nad2")
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, tabela=path, tabela_sha=sha)
    assert e.value.kod == 43
    doc = json.load(open(path))
    doc["tabela"]["tau_star_s"] = 1.10
    doc["sha256_tabeli"] = NS.tabela_sha(doc["tabela"])
    p2 = tmp_path / "zla.json"
    json.dump(doc, open(p2, "w"))
    monkeypatch.delenv(NS.OSLONA_ENV)
    with pytest.raises(NS.NadirStartError) as e:
        NS.NadirShield(nadir_mode=True, nad3=True, tabela=str(p2), tabela_sha=doc["sha256_tabeli"])
    assert e.value.kod == 45


def test_rezim_nad2_bez_zmian(monkeypatch):
    monkeypatch.delenv(NS.OSLONA_ENV, raising=False)
    monkeypatch.setenv(NS.LITERA_ENV, "NAD2")
    sh = NS.NadirShield(nadir_mode=True)
    assert sh.nad2 and not sh.nad3 and sh.nad3_T is None
    monkeypatch.setenv(NS.LITERA_ENV, "NADIR1")
    sh = NS.NadirShield(nadir_mode=True)
    assert not sh.nad2 and not sh.nad3


def test_u_nad3_w1_eq_u_nad2():
    path = os.path.join(ROOT, "results/NAD3/s1/tabela_W1_nad2.json")
    T = NS.nad3_tabela(path, json.load(open(path))["sha256_tabeli"])
    for tr in NS.TRYBY_NAD2:
        for i in range(5):
            for k in range(5):
                assert NS.u_nad3(T, i, k, tr) == NS.u_nad2(i, k, tr)
                assert NS.r_nad3(T, i, k, tr, 32.0) == NS.r_nad2(i, k, tr, 32.0)
    for tau in (0.0, 0.237, 0.238, 0.4, 1.037, 1.038, 1.2):
        assert NS.przedzial_nad3(T, tau) == NS.przedzial_nad2(tau)


def test_tabele_freeze_progi():
    for p, E in (("P1", 1.0), ("P2", 1.75), ("P3", 2.75)):
        path, sha = _tab(p)
        T = NS.nad3_tabela(path, sha)
        assert T["E"] == E and T["tau_star"] == 1.15 and T["prog_ticki"] == 21 and T["kraw"] == (0.35, 0.55, 0.75, 0.95, 1.15)
