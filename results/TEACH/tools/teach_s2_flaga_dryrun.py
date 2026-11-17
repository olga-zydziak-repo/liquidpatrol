#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_flaga_dryrun.py — ANEKS_TEACH-3 §4.4: próba na sucho ze stemplem epoki i jej ostrość (0 bootów).

Epizod syntetyczny „lot” z teach_s2_dryrun (p01_p1_c05_zew, cięcie 173.696; render łaty S przy pozie GT, migawki EKF z wierszy nf,
rama.jsonl odtworzona ścieżką drivera z osłoną nad3 i tabelą TEACH, teach_analyze: B1–B4, ważność), z jedną zmianą wejścia:
wiadomości flagi idą ścieżką on_flags procesu nadir_obs — funkcja wycięta DOSŁOWNYM tekstem z pliku nadir_obs.py (zagnieżdżona
w main()) i wykonana w przestrzeni modułu — ze stemplem jak w boocie: m.timestamp = (sim + 1.79·10⁹ + 0.045·sim) · 10⁶ µs
(przesunięcie rosnące 1.8 s na 40 s sim, jak zatrzask w wierszach cienia C1). Zdarzenia flagi: sekwencja bootu + zmiany
cs_gnss_pos z ULG (teach_s2_dryrun.zdarzenia_flagi).
  --kod ROOT_KODU  katalog, z którego ładowany jest harness/nadir_obs.py i harness/teach_map.py (domyślnie repo; ostrość: worktree
                   34fd058b). Dane lotu, tor i tabela zawsze z repo.
PASS (kod bieżący): jedno zamknięcie, mapa niepusta, przyjętych ≥ 90 % kadrów okna (od spadku ULG do końca misji epizodu, bez
zejścia — okno bramki obrazu teach_s2_cien), B1–B4, lot ważny; ostatni kadr
mapy przed spadkiem ULG. Ostrość (kod 34fd058b): zero przyjętych poprawek.
Wyjście: --wyj plik JSON.
"""
import argparse
import importlib.util
import json
import os
import sys
import textwrap
import time
import types

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools")]
OFF0, OFF_V = 1.79e9, 0.045


def on_flags_tekst(plik):
    src = open(plik, encoding="utf-8").read().splitlines()
    i = next(n for n, l in enumerate(src) if l.strip().startswith("def on_flags(m):"))
    blok = [src[i]]
    for l in src[i + 1:]:
        if not l.strip():
            break
        blok.append(l)
    return textwrap.dedent("\n".join(blok))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kod", default=ROOT)
    ap.add_argument("--wyj", required=True)
    a = ap.parse_args()
    kod = os.path.abspath(a.kod)
    import teach_s2_dryrun as D
    assert "harness" not in sys.modules and "harness.teach_map" not in sys.modules
    sys.path.insert(0, kod)                                            # harness z katalogu kodu (pakiet przestrzeni nazw)
    from harness import teach_map as TM
    assert os.path.dirname(os.path.dirname(os.path.abspath(TM.__file__))) == kod, TM.__file__
    plik_obs = os.path.join(kod, "harness/nadir_obs.py")
    tekst = on_flags_tekst(plik_obs)

    def zaladuj(env, outp):
        old_env, old_argv = dict(os.environ), sys.argv
        for k in list(os.environ):
            if k.startswith(("NADIR_", "NAD3_", "TEACH_")):
                os.environ.pop(k)
        os.environ.update(env)
        sys.argv = ["nadir_obs.py", "--world", "w", "--model", "m", "--out", outp]
        try:
            spec = importlib.util.spec_from_file_location(f"nobs_flaga_{time.monotonic_ns()}", plik_obs)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.argv = old_argv
            os.environ.clear(); os.environ.update(old_env)
        assert os.path.dirname(os.path.dirname(os.path.abspath(mod.teach_map.__file__))) == kod
        ns = {"teach_flaga": mod.teach_flaga}                           # on_flags dosłownie z pliku, woła prawdziwą teach_flaga
        exec(tekst, ns)
        stemple = []

        def teach_flaga_przez_on_flags(cs, t_sim):                      # wejście epizodu → wiadomość DDS ze stemplem epoki
            ts = int(round((t_sim + OFF0 + OFF_V * t_sim) * 1e6))
            stemple.append((round(t_sim, 6), ts / 1e6, bool(cs)))
            ns["on_flags"](types.SimpleNamespace(cs_gnss_pos=int(bool(cs)), timestamp=ts))
        mod.teach_flaga = teach_flaga_przez_on_flags                   # epizod woła mod.teach_flaga(v, t)
        mod._stemple = stemple
        STAN["mod"] = mod
        return mod

    STAN = {}
    D.zaladuj = zaladuj
    ep0 = D.epizod

    def epizod(*x, **y):
        r = ep0(*x, **y)
        STAN["nf"], STAN["ev"] = r[1], r[4]
        return r
    D.epizod = epizod
    import teach_analyze as A                                          # zapis wyniku analizatora: numpy bool_ (ścieżka zdegenerowana)
    _j = A.json
    A.json = types.SimpleNamespace(**{k: getattr(_j, k) for k in ("load", "loads", "dumps")},
                                   dump=lambda o, f, **kw: _j.dump(o, f, default=lambda x: x.item() if hasattr(x, "item") else str(x), **kw))
    w = D.syntetyczny_lot()
    mod, nf, ev = STAN["mod"], STAN["nf"], STAN["ev"]
    t_spadku = w["spadek_ulg"]
    zamk = [r for r in nf if r["teach"].get("georef")]
    t_z = zamk[0]["sim"] if zamk else None
    import teach_s2_cien as SC                                         # okno bramki obrazu (PRE §6): od cięcia do końca misji, bez zejścia
    ev_tr = SC.A.jl(os.path.join(ROOT, D.LOT, "trace.jsonl"), "event")
    ep_st = next(e for e in ev_tr if e.get("ev") == "episode_start")
    t_k = max(r["sim"] for r in SC.A.jl(os.path.join(ROOT, D.LOT, "rama.jsonl"))
              if r.get("ep") == ep_st["episode_id"] and r.get("phase") in SC.MISJA and not r.get("desc"))
    po = [r for r in nf if t_spadku <= r["sim"] <= t_k]
    po_wszystkie = [r for r in nf if t_z is not None and r["sim"] >= t_z]
    przyj = sum(1 for r in po if r["fx"]["ok"])
    sim_mapy = [x["sim"] for x in mod._prod.kadry]
    ostatni = max(sim_mapy) if sim_mapy else None
    w.update({"kod": kod, "teach_map": os.path.abspath(TM.__file__), "on_flags_tekst": tekst,
              "stemple_flagi_pierwsze_i_ostatnie": mod._stemple[:2] + mod._stemple[-2:],
              "przesuniecie_stempla_s": [round(s[1] - s[0], 3) for s in (mod._stemple[0], mod._stemple[-1])],
              "ts_flagi_producent_t_flagi": mod._prod.t_flagi, "klatka_zamkniecia": t_z,
              "okno_oceny": [t_spadku, t_k], "kadry_okna": len(po), "przyjete_okna": przyj,
              "kadry_od_zamkniecia_do_konca_nagrania": len(po_wszystkie),
              "przyjete_od_zamkniecia_do_konca_nagrania": sum(1 for r in po_wszystkie if r["fx"]["ok"]),
              "frakcja_przyjetych": round(przyj / len(po), 4) if po else None,
              "ostatni_kadr_mapy": ostatni, "ostatni_kadr_mapy_wobec_spadku_ulg_s": None if ostatni is None else round(ostatni - t_spadku, 4),
              "odrzucony_z_bufora": zamk[0]["teach"].get("odrzucony_z_bufora") if zamk else None,
              "ts_flagi_w_wierszach": sorted({r.get("ts_flagi") for r in nf if r.get("ts_flagi") is not None})[:4]})
    an = w["analizator"]
    w["PASS_TEACH3"] = (w["zamkniecia"] == 1 and w["mapa_kadry"] > 0 and po and przyj / len(po) >= 0.90 and an["wazny"] is True
                        and all(e.get(b, True) for e in an["epizody"] for b in ("B1", "B2", "B3", "B4"))
                        and ostatni is not None and ostatni < t_spadku and w["datagramy_odebrane"] == w["klatki"])
    w["OSTROSC_zero_przyjetych"] = w["poprawki_przyjete"] == 0
    json.dump(w, open(a.wyj, "w"), ensure_ascii=False, indent=1, default=str)
    print({k: v for k, v in w.items() if k not in ("analizator", "on_flags_tekst")}, flush=True)
    print("analizator", json.dumps(an, default=str)[:1500])


if __name__ == "__main__":
    main()
