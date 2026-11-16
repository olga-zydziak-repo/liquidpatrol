#!/usr/bin/env python3
"""results/TEACH/tools/test_teach_s1.py — testy jednostkowe S1 nogi TEACH (PROMPT_TEACH_S1 §4 T; 0 bootów).

Producent harness/teach_map (kadry: render reconu lotu p07_p2_c10_zew na łacie S — krótki lot, 191 + 44 kadry):
  - żadnej poprawki przed flagą (datagram ok = False, Δ = 0, t_fix = None przez całą fazę mapy);
  - georeferencja rozwiązana dokładnie raz (także gdy flaga wraca do 1 po zamknięciu);
  - żadne wiązanie po fladze: kadr z czasem ≥ chwila flagi nie wchodzi do mapy (bufor jednej klatki), mapa po zamknięciu stała;
  - zamknięcie po kadrach mapy = recon (liczba klatek kluczowych, θ_k do 1e-4°);
  - pokrycie K′ = pokrycie reconu przy równych pół-bokach;
Proces harness/nadir_obs.py w gałęzi TEACH (moduł ładowany jak w teach_w1_obs, atrapa wiadomości gz, gniazdo UDS odbiorcy):
  - tryb cienia niczego nie wysyła (wiersze z fx i rejestrem są), tryb lotu wysyła datagram na każdą klatkę;
  - meta TEACH (litera, tor, cień); detektor znaczników liczy dalej (n w wierszu);
Tabela i osłona: tabela FREEZE wczytywana przez osłonę; mutant τ* ≠ ostatnia krawędź odrzucony kodem 45.
Analizator: zrodlo_teach na syntetycznym nadir_obs.jsonl z producenta (ważność, błąd poprawki, opóźnienie).
Uruchom: python3 -m pytest -q results/TEACH/tools/test_teach_s1.py
"""
import gzip
import json
import os
import socket
import sys
import tempfile
import time
import types

import numpy as np
import pytest

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools")]
from harness import teach_map as TM                                   # noqa: E402

LOT, LATA = "p07_p2_c10_zew", "S"
_C = {}


def kadry():
    if "k" not in _C:
        import cv2
        T, R2 = TM.T, TM.R2
        kam = R2.Kam(R2.kamera())
        teren = cv2.imread(os.path.join(ROOT, "results/TEACH_RECON/dane", f"{LATA}_2024-04-27.png"))
        K = [k for k in json.load(gzip.open(os.path.join(ROOT, "results/TEACH_RECON/r2_klatki.json.gz"), "rt")) if k["lot"] == LOT]
        przed = sorted([k for k in K if k["seria"] == "przed"], key=lambda k: k["sim"])
        po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])
        for k in przed + po:
            C, Rk = kam.poza(np.array(k["gt_p"]), R2.rotm(k["gt_q"]))
            k["_img"] = kam.renderuj(teren, T.PIKSEL_T, C, Rk)[0]
        _C["k"] = (przed, po, po[0]["sim"] - po[0]["od_ciecia"])
    return _C["k"]


@pytest.fixture(scope="module")
def przebieg():
    przed, po, t_cut = kadry()
    P = TM.Producent("K")
    recs_mapa = [P.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], 1) for k in przed]
    n_kadrow_przed_zamknieciem = len(P.kadry) + (1 if P.bufor is not None else 0)
    recs_po = []
    for i, k in enumerate(po):
        g = 1 if i == len(po) // 2 else 0                              # flaga wraca na jedną klatkę po zamknięciu
        recs_po.append(P.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], g, t_flagi=t_cut))
    return P, recs_mapa, recs_po, n_kadrow_przed_zamknieciem, t_cut


def test_brak_poprawki_przed_flaga(przebieg):
    P, rm, _, _, _ = przebieg
    assert rm and all(not r["ok"] and r["d_ne"] == [0.0, 0.0] and r["t_fix"] is None and r["powod"] == "mapa" for r in rm)


def test_georeferencja_raz(przebieg):
    P, _, rp, _, _ = przebieg
    assert P.n_zamkniec == 1 and P.zamknieta
    assert sum(1 for r in rp if r["ok"]) > 0


def test_mapa_bez_kadrow_po_fladze(przebieg):
    P, _, _, n_przed, t_cut = przebieg
    assert len(P.kadry) == n_przed
    assert all(x["sim"] < t_cut for x in P.kadry)
    assert all(k["sim"] < t_cut for k in P.kf)
    assert max(w[0] for w in P.wz) < t_cut


def test_bufor_odrzuca_kadr_po_fladze():
    przed, _, _ = kadry()
    P = TM.Producent("K")
    for k in przed[:40]:
        P.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], 1)
    t_buf = P.bufor["sim"]
    n = len(P.kadry)
    k = przed[40]                                                      # flaga spadła PRZED kadrem w buforze
    P.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], 0, t_flagi=t_buf - 0.01)
    assert len(P.kadry) == n and P.n_zamkniec == 1 and P.rejestr.get("odrzucony_z_bufora") == round(t_buf, 4)


def test_zamkniecie_jak_recon(przebieg):
    P, _, _, _, _ = przebieg
    ref = json.load(gzip.open(os.path.join(ROOT, "results/TEACH_RECON2/czesci", f"{LOT}_{LATA}.json.gz"), "rt"))
    assert len(P.kf) == len(ref["kf"])
    for k, r in zip(P.georef["kf"], ref["kf"]):
        assert abs(k["theta_deg"] - r["geo"]["M4/K1_SIFT"]["theta_deg"]) <= 1e-4
        assert max(abs(a - b) for a, b in zip(k["t"], r["geo"]["M4/K1_SIFT"]["t"])) <= 1e-4


def test_pokrycie_k2_rowne_przy_rownych_bokach():
    rng = np.random.default_rng(1)
    for _ in range(200):
        p, q, a = rng.uniform(-10, 10, 2), rng.uniform(-10, 10, 2), rng.uniform(2, 12)
        assert abs(TM.pokrycie_k2(p, a, q, a) - TM.T.pokrycie(p, q, a)) < 1e-12
    assert TM.pokrycie_k2((0, 0), 5.0, (0, 0), 1.0) == pytest.approx(0.04)


def _obs(env, n_klatek, sock_path=None):
    import importlib.util
    import threading
    przed, po, t_cut = kadry()
    seq = przed[-n_klatek:] + po[:n_klatek]
    out = os.path.join(tempfile.mkdtemp(prefix="teach_test_obs_"), "o.jsonl")
    old_env, old_argv = dict(os.environ), sys.argv
    for k in list(os.environ):
        if k.startswith(("NADIR_", "NAD3_", "TEACH_")):
            os.environ.pop(k)
    os.environ.update(env)
    if sock_path:
        os.environ["NADIR_FIX_SOCKS"] = sock_path
    sys.argv = ["nadir_obs.py", "--world", "w", "--model", "m", "--out", out]
    try:
        spec = importlib.util.spec_from_file_location(f"nobs_test_{time.monotonic_ns()}", os.path.join(ROOT, "harness/nadir_obs.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = old_argv
        os.environ.clear(); os.environ.update(old_env)
    th = threading.Thread(target=mod.worker, daemon=True)
    th.start()
    for k in seq:
        mod._ekf.update({"q": k["ekf_q"], "q_mono": time.monotonic(), "pos": k["ekf_pos"], "hdg": None, "pos_mono": time.monotonic()})
        if not getattr(mod, "TEACH_CIEN", False):
            mod._gnss.update({"cs": k["sim"] < t_cut, "t_flagi": None if k["sim"] < t_cut else t_cut})
        n0 = mod.st["n_proc"]
        rgb = k["_img"][:, :, ::-1].copy()
        msg = types.SimpleNamespace(header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=int(k["sim"]), nsec=int(round((k["sim"] % 1) * 1e9)))),
                                    width=640, height=480, data=rgb.tobytes())
        mod.on_img(msg)
        t0 = time.monotonic()
        while mod.st["n_proc"] == n0 and time.monotonic() - t0 < 20:
            time.sleep(0.002)
    mod._stop[0] = True
    th.join(timeout=2)
    mod.fout.close()
    return mod, [json.loads(l) for l in open(out)], t_cut


def _odbiorca():
    p = os.path.join(tempfile.mkdtemp(prefix="teach_sock_"), "r.sock")
    sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sk.bind(p)
    sk.setblocking(False)
    return sk, p


def _odbierz(sk):
    out = []
    while True:
        try:
            out.append(json.loads(sk.recv(65536).decode()))
        except (BlockingIOError, InterruptedError):
            return out


def test_cien_nic_nie_wysyla():
    przed, po, t_cut = kadry()
    sk, p = _odbiorca()
    mod, rows, _ = _obs({"NADIR_MODE": "1", "TEACH_MODE": "1", "TEACH_CIEN": "1", "TEACH_T_CIEN": str(t_cut)}, 12, p)
    rows = [r for r in rows if r.get("t") == "nf"]
    assert len(rows) == 24 and all("fx" in r and "teach" in r for r in rows)
    assert any(r["fx"]["ok"] for r in rows)                            # wynik w rejestrze
    assert _odbierz(sk) == []                                          # nic nie wysłane


def test_lot_wysyla_i_meta():
    przed, po, t_cut = kadry()
    sk, p = _odbiorca()
    mod, rows, _ = _obs({"NADIR_MODE": "1", "TEACH_MODE": "1"}, 12, p)
    nf = [r for r in rows if r.get("t") == "nf"]
    got = _odbierz(sk)
    assert len(got) == len(nf) == 24 and all(g.get("zrodlo") == "teach" for g in got)
    assert any(g["ok"] for g in got) and all(not g["ok"] for g in got[:12])
    assert all("n" in r and "det" in r for r in nf)                   # detektor znaczników liczy dalej
    assert mod.TEACH_MODE and mod._prod.wariant == json.load(open(os.path.join(ROOT, "results/TEACH/s1/tor.json")))["tor"]["wariant_K"]


def test_tabela_i_mutant():
    from r03 import nadir_shield as NS
    p = os.path.join(ROOT, "results/TEACH/s1/freeze_U_TEACH.json")
    d = json.load(open(p))
    T = NS.nad3_tabela(p, d["sha256_tabeli"], r_e=32.0, dt=0.05)
    assert T["punkt"] == "TEACH" and T["tau_star"] == 2.15 and T["prog_ticki"] == 41 and len(T["kraw"]) == 10
    assert all(v == 0.0 for tr in T["F"].values() for v in tr) and T["E"] == 1.0
    d["tabela"]["tau_star_s"] = 2.10
    d["sha256_tabeli"] = NS.tabela_sha(d["tabela"])
    q = os.path.join(tempfile.mkdtemp(), "m.json")
    json.dump(d, open(q, "w"))
    with pytest.raises(NS.NadirStartError) as e:
        NS.nad3_tabela(q, d["sha256_tabeli"], r_e=32.0, dt=0.05)
    assert e.value.kod == 45


def test_analizator_zrodlo():
    import teach_analyze as A
    przed, po, t_cut = kadry()
    mod, rows, _ = _obs({"NADIR_MODE": "1", "TEACH_MODE": "1"}, 30, None)
    d = tempfile.mkdtemp(prefix="teach_an_")
    with open(os.path.join(d, "nadir_obs.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    gt = {round(k["sim"], 4): k for k in przed + po}

    def GTp(t):
        k = gt[round(t, 4)]
        return np.array([k["gt_p"][1], k["gt_p"][0], -k["gt_p"][2]])

    def pose(t):
        k = min(gt.values(), key=lambda x: abs(x["sim"] - t))
        return k["gt_p"], k["gt_q"]
    o = A.zrodlo_teach(d, GTp, t_cut, po[29]["sim"], pose)
    assert o["wazny"] and o["warunki_waznosci"] == {"zero_detekcji_znacznikow": True, "brak_mapy_po_fladze": True, "georef_raz": True}
    assert o["blad_poprawki"]["n"] > 0 and o["blad_poprawki"]["max"] < 1.0
    assert o["opoznienie_pierwszej_poprawki_s"] is not None and o["georef"]["n_kf"] > 0
