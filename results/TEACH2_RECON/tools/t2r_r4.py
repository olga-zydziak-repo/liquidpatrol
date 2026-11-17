#!/usr/bin/env python3
"""results/TEACH2_RECON/tools/t2r_r4.py — PROMPT_TEACH2_S0 §6 R4: obciążenie mapy z 100 / 146 / 200 s nauki (0 bootów).

Lot długi NAD2 results/NAD2/s4/L_c10_s01 (wiersze nf z migawką EKF, poza GT z trace — tylko render), łaty S, M, J po kolei w jednym
procesie (warunki jak W3 z S1: proces przypięty do jednego rdzenia — uruchamiać przez taskset -c RDZEŃ — cv2 jednowątkowo).
Faza mapy: klatki z flagą 1 do czasu epizodu 100 / 146 / 200 s (moduł sam pomija klatki poniżej 6 m). Przy każdej długości stan
producenta klonowany (t2r_dane.klon) trzy razy; każdy klon zamyka mapę (kadr z bufora + Producent._zamknij — ścieżka zamknięcia
lotu) — czas zamknięcia ×3 (mediana, max); pierwszy klon lokalizuje potem 100 s klatek z flagą 0. Błędu się nie ocenia (lot bez
GNSS od 34 s epizodu; georeferencja bez sensu fizycznego).
Miary per długość i łata: kadry mapy, klatki kluczowe, wiązania; czas zamknięcia; czas na klatkę w fazie mapy (wywołanie
Producent.obserwacja bez renderu) w pierwszych i ostatnich 30 s fazy mapy; czas na klatkę w lokalizacji; pamięć procesu (VmRSS
przed zamknięciem, VmHWM); klatki, które przyszłyby w trakcie zamknięcia (5 Hz: ceil(czas / 0.2 s)).
Użycie: t2r_r4.py ŁATA (jedna łata na proces — pamięć procesu nieskażona poprzednią łatą).
Wyjście: results/TEACH2_RECON/r4_<łata>.json; klatki fazy mapy > 200 ms wypisane (kadr kluczowy, liczba dopasowań).
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2r_dane as D                                      # noqa: E402

TM, N3, R2 = D.TM, D.N3, D.R2
LOT = os.path.join(D.ROOT, "results/NAD2/s4/L_c10_s01")
DLUGOSCI = (100.0, 146.0, 200.0)
LOK_S = 100.0


def vm(nazwa):
    for l in open("/proc/self/status"):
        if l.startswith(nazwa):
            return round(int(l.split()[1]) / 1024, 1)


def q(x):
    return {"n": len(x), "p50": round(float(np.median(x)), 2), "p95": round(float(np.quantile(x, .95)), 2),
            "max": round(float(max(x)), 2)} if x else None


def main():
    import cv2
    cv2.setNumThreads(1)
    ev = N3.jl(LOT, "trace.jsonl", "event")
    t_ep = next(e["sim"] for e in ev if e.get("ev") == "episode_start")
    g = R2.GT(LOT)
    kl = []
    for r in N3.jl(LOT, "nadir_obs.jsonl", "nf"):
        if r["sim"] - t_ep > max(DLUGOSCI) + LOK_S:
            break
        p, qq, _ = g(r["sim"])
        kl.append({"sim": r["sim"], "ekf_q": r.get("ekf_q"), "ekf_pos": r.get("ekf_pos"), "gt_p": p, "gt_q": qq})
    out = {"lot": "L_c10_s01", "t_episode_start": t_ep, "rdzen": os.sched_getaffinity(0), "cv2_watki": cv2.getNumThreads(),
           "sumy_toru": TM.sumy_toru(), "wariant": D.WARIANT, "laty": {}}
    out["rdzen"] = sorted(out["rdzen"])
    for lata in sys.argv[1].split(",") if len(sys.argv) > 1 else ("S", "M", "J"):
        t0 = time.time()
        ren = D.Render(lata)
        P = TM.Producent(wariant=D.WARIANT)
        ms_mapa = []                                          # (t_ep kadru włączonego, ms wywołania)
        wolne = []                                            # klatki fazy mapy > 200 ms
        wyn = {}
        i = 0
        for L in DLUGOSCI:
            while i < len(kl) and kl[i]["sim"] - t_ep <= L:
                k = kl[i]
                pos = k["ekf_pos"]
                img = ren(k) if (pos is not None and -pos[2] >= TM.H_MIN) else None
                a = time.perf_counter()
                P.obserwacja(k["sim"], img, k["ekf_q"], pos, 1)
                dt = (time.perf_counter() - a) * 1e3
                w = P.rejestr.get("wlaczony")
                if w is not None:
                    ms_mapa.append((w["sim"] - t_ep, dt))
                    if dt > 200.0:
                        wolne.append({"t_ep": round(w["sim"] - t_ep, 2), "ms": round(dt, 1), "kf": w["kf"], "n_dop": w["n_dop"],
                                      "ms_cechy": w["ms_cechy"], "ms_dop": w["ms_dop"]})
                i += 1
            ost = kl[i - 1]["sim"]
            rss = vm("VmRSS")
            zam, georef, Q0 = [], None, None
            for rep in range(3):
                Q = D.klon(P)
                a = time.perf_counter()
                if Q.bufor is not None:
                    Q._wlacz_do_mapy(Q.bufor)
                    Q.bufor = None
                Q._zamknij(ost)
                zam.append(round((time.perf_counter() - a) * 1e3, 2))
                georef = Q.georef
                if rep == 0:
                    Q0 = Q
                else:
                    del Q
            ms_lok, n_lok = [], 0
            j = i
            while j < len(kl) and kl[j]["sim"] - t_ep <= L + LOK_S:
                k = kl[j]
                img = ren(k)
                a = time.perf_counter()
                Q0.obserwacja(k["sim"], img, k["ekf_q"], k["ekf_pos"], 0)
                ms_lok.append((time.perf_counter() - a) * 1e3)
                n_lok += 1
                j += 1
            del Q0
            t_m = [t for t, _ in ms_mapa]
            pierwsze = [m for t, m in ms_mapa if t <= t_m[0] + 30.0]
            ostatnie = [m for t, m in ms_mapa if t > L - 30.0]
            wyn[f"{int(L)}"] = {"n_kadrow_mapy": georef["n_kadrow_mapy"], "n_kf": georef["n_kf"], "n_wiazan": georef["n_wiazan"],
                                "n_wiazan_przyjetych": georef["n_wiazan_przyjetych"], "n_dop_pozno": georef["n_dop_pozno"],
                                "zamkniecie_ms": zam, "zamkniecie_mediana_ms": round(float(np.median(zam)), 2),
                                "zamkniecie_max_ms": max(zam),
                                "georef_ms_wiazania_rozwiazanie": [georef["ms_wiazania"], georef["ms_rozwiazanie"]],
                                "klatki_w_trakcie_zamkniecia": math.ceil(max(zam) / 200.0),
                                "ms_mapa_pierwsze_30s": q(pierwsze), "ms_mapa_ostatnie_30s": q(ostatnie), "ms_lokalizacja": q(ms_lok),
                                "n_lok": n_lok, "vmrss_mb_przed_zamknieciem": rss, "vmhwm_mb": vm("VmHWM"),
                                "pierwszy_kadr_mapy_ep": round(t_m[0], 2), "ostatni_kadr_ep": round(ost - t_ep, 2)}
            print(time.strftime("%T"), lata, int(L), json.dumps(wyn[f"{int(L)}"], ensure_ascii=False), flush=True)
        out["laty"][lata] = dict(wyn, zegar_s=round(time.time() - t0, 1), wolne_mapa_gt_200ms=wolne)
        json.dump(out, open(os.path.join(D.OUT, f"r4_{lata}.json"), "w"), ensure_ascii=False, indent=1)
    print("S2_zachodzi", any(v["146"]["zamkniecie_max_ms"] > 1000.0 for v in out["laty"].values()), flush=True)


if __name__ == "__main__":
    main()
