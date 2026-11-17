#!/usr/bin/env python3
"""results/TEACH/tools/test_teach_s2.py — testy poprawek F1–F3 (PROMPT_TEACH_S2 §1; 0 bootów).

Proces harness/nadir_obs.py w gałęzi TEACH (moduł ładowany jak w test_teach_s1._obs), flaga podawana przez teach_flaga(cs, t) —
tę samą funkcję woła subskrypcja /fmu/out/estimator_status_flags. Kadry: render reconu p07_p2_c10_zew, łata S (test_teach_s1.kadry).
Faza „na ziemi” = te same kadry z wysokością EKF 1 m (pod H_MIN — nie wchodzą do mapy), faza „mapa” = kadry z wysokością lotu.
  - flaga 0 od początku (pierwsza wiadomość 0), potem 1, mapa, spadek ⇒ jedno zamknięcie przy spadku (chwila = czas spadku), mapa
    niepusta, wiersze sprzed mapy w fazie „przed_mapa” albo „mapa”;
  - flaga 0 przez cały czas (także z kadrami z wysokości lotu) ⇒ żadnego zamknięcia, wszystkie wiersze „przed_mapa”, zero poprawek;
  - restart EKF: 0 → 1 → 0 → 1 → mapa → 0 ⇒ zatrzask skasowany powrotem do 1, zamknięcie przy ostatnim spadku;
  - pusta mapa z kadrem w buforze sprzed flagi ⇒ zamknięcie z jednym kadrem (F2: bufor niepusty);
  - F3: zamknięcie niesie pełną listę wiązań, zgodną z wiązaniami producenta;
  - tryb cienia: wiersz niesie flagę rzeczywistą i zatrzask (gnss_rz, t_flagi_rz).
ANEKS_TEACH-3 §4.4: sekwencje przepisane na flagę jako stan (producent bez chwili flagi; stempel w wierszu „ts_flagi”): jedno
zamknięcie, mapa niepusta, kadr z bufora odrzucony, τ = 0 przy pierwszej klatce po zamknięciu; ścieżka z podaną chwilą bez zmian.
Uruchom: python3 -m pytest -q results/TEACH/tools/test_teach_s2.py
"""
import copy
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import types

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools")]
import test_teach_s1 as S1                                            # noqa: E402
from harness import teach_map as TM                                   # noqa: E402


def zaladuj(env):
    out = os.path.join(tempfile.mkdtemp(prefix="teach_s2_obs_"), "o.jsonl")
    old_env, old_argv = dict(os.environ), sys.argv
    for k in list(os.environ):
        if k.startswith(("NADIR_", "NAD3_", "TEACH_")):
            os.environ.pop(k)
    os.environ.update(env)
    sys.argv = ["nadir_obs.py", "--world", "w", "--model", "m", "--out", out]
    try:
        spec = importlib.util.spec_from_file_location(f"nobs_s2_{time.monotonic_ns()}", os.path.join(ROOT, "harness/nadir_obs.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = old_argv
        os.environ.clear(); os.environ.update(old_env)
    th = threading.Thread(target=mod.worker, daemon=True)
    th.start()
    return mod, th, out


def klatka(mod, k, ziemia=False):
    pos = list(k["ekf_pos"])
    if ziemia:
        pos[2] = -1.0
    mod._ekf.update({"q": k["ekf_q"], "q_mono": time.monotonic(), "pos": pos, "hdg": None, "pos_mono": time.monotonic()})
    n0 = mod.st["n_proc"]
    rgb = k["_img"][:, :, ::-1].copy()
    msg = types.SimpleNamespace(header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=int(k["sim"]), nsec=int(round((k["sim"] % 1) * 1e9)))),
                                width=640, height=480, data=rgb.tobytes())
    mod.on_img(msg)
    t0 = time.monotonic()
    while mod.st["n_proc"] == n0 and time.monotonic() - t0 < 20:
        time.sleep(0.002)


def zakoncz(mod, th, out):
    mod._stop[0] = True
    th.join(timeout=2)
    mod.fout.close()
    return [r for r in map(json.loads, open(out)) if r.get("t") == "nf"]


def sekwencja(plan, env=None):
    """plan: lista (kadr, ziemia, flaga|None — wiadomość flagi przed kadrem z czasem kadru − 0.05 s)."""
    mod, th, out = zaladuj(env or {"NADIR_MODE": "1", "TEACH_MODE": "1"})
    for k, ziemia, fl in plan:
        if fl is not None:
            mod.teach_flaga(fl, k["sim"] - 0.05)
        klatka(mod, k, ziemia)
    return mod, zakoncz(mod, th, out)


def kadry():
    przed, po, _ = S1.kadry()
    return przed, po


def zamkniecie(rows):
    geo = [r for r in rows if r["teach"].get("georef")]
    assert len(geo) == 1
    return geo[0]


def test_zero_od_poczatku_potem_mapa_i_spadek():
    """TEACH-3: flaga jako stan — zamknięcie przy pierwszej klatce z flagą 0, chwila = czas tej klatki, kadr z bufora odrzucony, τ = 0."""
    przed, po = kadry()
    plan = [(k, True, False) for k in przed[:15]] + [(przed[15], True, True)] + [(k, True, None) for k in przed[16:25]]
    plan += [(k, False, None) for k in przed[25:120]]
    plan += [(po[0], False, False)] + [(k, False, None) for k in po[1:20]]
    mod, rows = sekwencja(plan)
    fazy = [r["teach"]["faza"] for r in rows]
    assert all(f in ("przed_mapa", "mapa") for f in fazy[:120])
    assert fazy[:15] == ["przed_mapa"] * 15
    assert mod._prod.n_zamkniec == 1 and len(mod._prod.kadry) > 0
    g = zamkniecie(rows)
    assert g["sim"] == round(po[0]["sim"], 4) and mod._prod.t_flagi == float(round(po[0]["sim"], 4))
    assert g["teach"]["odrzucony_z_bufora"] == round(przed[119]["sim"], 4)                # kadr z bufora odrzucony
    assert max(x["sim"] for x in mod._prod.kadry) == przed[118]["sim"]
    assert g["teach"]["tau"] == 0.0                                                      # τ od klatki zamknięcia
    assert all(r["t_flagi"] is None for r in rows)                                       # producent nie dostaje chwili flagi
    assert rows[-1]["ts_flagi"] == round(po[0]["sim"] - 0.05, 6)                          # stempel tylko w rejestrze
    assert any(r["fx"]["ok"] for r in rows[120:])
    assert not any(r["fx"]["ok"] for r in rows[:120])


def test_zero_caly_czas():
    przed, po = kadry()
    plan = [(przed[0], True, False)] + [(k, False, None) for k in przed[1:60]]
    mod, rows = sekwencja(plan)
    assert mod._prod.n_zamkniec == 0 and not mod._prod.zamknieta
    assert all(r["teach"]["faza"] == "przed_mapa" for r in rows) and not any(r["fx"]["ok"] for r in rows)
    assert mod._gnss["t_flagi"] is None                                  # pierwsze 0 bez wcześniejszej 1 nie jest spadkiem


def test_restart_ekf():
    """0 → 1 → 0 → 1 → mapa → 0: jedno zamknięcie, przy pierwszej klatce ostatniego zera; mapa niepusta."""
    przed, po = kadry()
    plan = [(przed[0], True, False)] + [(k, True, None) for k in przed[1:5]]
    plan += [(przed[5], True, True)] + [(k, True, None) for k in przed[6:10]]
    plan += [(przed[10], True, False)] + [(k, True, None) for k in przed[11:15]]       # spadek na ziemi (restart EKF)
    plan += [(przed[15], True, True)] + [(k, True, None) for k in przed[16:20]]       # powrót do 1
    plan += [(k, False, None) for k in przed[20:110]]
    plan += [(po[0], False, False)] + [(k, False, None) for k in po[1:10]]
    mod, rows = sekwencja(plan)
    assert [r["teach"]["faza"] for r in rows[10:15]] == ["przed_mapa"] * 5                # zero na ziemi przy pustej mapie
    assert all(r["ts_flagi"] == round(przed[10]["sim"] - 0.05, 6) for r in rows[10:15])  # zatrzask stempla (rejestr)
    assert all(r["ts_flagi"] is None for r in rows[15:110])
    assert mod._prod.n_zamkniec == 1 and len(mod._prod.kadry) > 0
    g = zamkniecie(rows)
    assert g["sim"] == round(po[0]["sim"], 4) and g["teach"]["tau"] == 0.0
    assert "odrzucony_z_bufora" in g["teach"] and "wlaczony" not in g["teach"]


def test_bufor_przy_flagi_jako_stanie():
    przed, _ = kadry()
    k0, k1, k2 = przed[30], przed[31], przed[32]
    P = TM.Producent("K")                                                # lot: kadr z bufora odrzucony, pusta mapa się nie zamyka
    P.obserwacja(k0["sim"], k0["_img"], k0["ekf_q"], k0["ekf_pos"], 1)
    P.obserwacja(k1["sim"], k1["_img"], k1["ekf_q"], k1["ekf_pos"], 0)
    assert P.n_zamkniec == 0 and P.rejestr["faza"] == "przed_mapa" and P.rejestr["odrzucony_z_bufora"] == round(k0["sim"], 4)
    assert P.bufor is None and not P.kadry
    P1 = TM.Producent("K")                                               # lot: kadr wchodzi, gdy po nim przyszła klatka z flagą 1
    for k in (k0, k1):
        P1.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], 1)
    P1.obserwacja(k2["sim"], k2["_img"], k2["ekf_q"], k2["ekf_pos"], 0)
    assert P1.n_zamkniec == 1 and [x["sim"] for x in P1.kadry] == [k0["sim"]] and P1.t_flagi == k2["sim"]
    assert P1.rejestr["odrzucony_z_bufora"] == round(k1["sim"], 4) and P1.rejestr["tau"] == 0.0


def test_bufor_z_podana_chwila():
    """Tryb cienia / replay z podaną chwilą bez zmian (TEACH-S2 F2)."""
    przed, _ = kadry()
    P = TM.Producent("K")
    k0, k1 = przed[30], przed[31]
    P.obserwacja(k0["sim"], k0["_img"], k0["ekf_q"], k0["ekf_pos"], 1)
    P.obserwacja(k1["sim"], k1["_img"], k1["ekf_q"], k1["ekf_pos"], 0, t_flagi=k1["sim"])
    assert P.n_zamkniec == 1 and len(P.kadry) == 1 and len(P.kf) == 1
    P2 = TM.Producent("K")
    P2.obserwacja(k0["sim"], k0["_img"], k0["ekf_q"], k0["ekf_pos"], 1)
    P2.obserwacja(k1["sim"], k1["_img"], k1["ekf_q"], k1["ekf_pos"], 0, t_flagi=k0["sim"] - 0.01)   # bufor po fladze
    assert P2.n_zamkniec == 0 and P2.rejestr["faza"] == "przed_mapa" and P2.bufor is None


def test_f3_wiazania():
    przed, po = kadry()
    P = TM.Producent("K")
    for k in przed:
        P.obserwacja(k["sim"], k["_img"], k["ekf_q"], k["ekf_pos"], 1)
    P.obserwacja(po[0]["sim"], po[0]["_img"], po[0]["ekf_q"], po[0]["ekf_pos"], 0, t_flagi=po[0]["sim"])
    w = P.rejestr["georef"]["wiazania"]
    assert len(w) == P.georef["n_wiazan"] == len(P.wz) and w == [x[:6] for x in P.wz]
    assert sum(x[5] for x in w) == P.georef["n_wiazan_przyjetych"]
    json.dumps(P.rejestr)                                                            # wiersz serializowalny


def test_cien_flaga_rzeczywista():
    przed, po = kadry()
    t_c = po[0]["sim"]
    plan = [(przed[0], True, False)] + [(przed[1], True, True)] + [(k, False, None) for k in przed[2:40]]
    plan += [(po[0], False, False)] + [(k, False, None) for k in po[1:5]]
    mod, rows = sekwencja(plan, {"NADIR_MODE": "1", "TEACH_MODE": "1", "TEACH_CIEN": "1", "TEACH_T_CIEN": str(t_c)})
    assert all("gnss_rz" in r and "t_flagi_rz" in r for r in rows)
    assert rows[0]["gnss_rz"] is False and rows[1]["gnss_rz"] is True and rows[0]["t_flagi_rz"] is None
    assert rows[-1]["gnss_rz"] is False and rows[-1]["t_flagi_rz"] == round(t_c - 0.05, 6)
    assert mod._prod.n_zamkniec == 1 and mod._prod.t_flagi == t_c
