#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_kontr.py — kontrprzykłady otwarte H-PION: zapis per tick, odporność, eksport toru (PROMPT_PETLA_S0 §6).

Kandydaci: biegi ze zdarzeniem „ucieczka wysokości” w napędzie N, wariant „siec”, rodziny otwarte (postoj, wahadlo, odcinki,
krazenie; części r45_czesci) oraz najlepszy tor z szukania R4 (szukanie_r4.json). Ranking: najwcześniejsze zdarzenie (t_ev),
remis — większe max |rel_z − 2|. Trzy najlepsze:
  - odtworzenie wsadu z tym samym ziarnem i zapis per tick wskazanego indeksu (pl_bieg.KOLUMNY_LOGU) → kontr_<k>_log.npy;
    zgodność z wynikiem wsadu (t_ev, max_dz) sprawdzona;
  - odporność: 20 powtórzeń z zapisanym torem intruza (tor stały, otwarty), szum włączony z innym ziarnem (k = 0…19),
    start toru przesunięty o s_k = −2 + 4k/19 s (tor wcześniej / później względem drona; poza zakresem — koniec toru trzymany);
  - eksport toru do formatu manifestu lotu (epizod c10_s01 z results/TEACH2/scenario_manifest_teach2L.json jako wzór pól;
    odcinki stałej prędkości z toru 20 Hz, x = N, y = E, heading_deg = atan2(E, N), z = 10), sprawdzian kroku (≤ v·0.1 s + 0.001 m)
    i promienia (≤ 11.001 m) na siatce 0.1 s wg ANEKS_TEACH2-1 przez bench.scenarios.position_at.
Wyjście: results/PETLA_RECON/kontr.json, kontr_<k>_log.npy, kontr_<k>_manifest.json.
"""
import copy
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_bieg as PB                                     # noqa: E402
import pl_intruz as PI                                   # noqa: E402
import pl_naped as PN                                    # noqa: E402
import pl_r45 as R45                                     # noqa: E402

sys.path.insert(0, PB.PN.PD.ROOT)
from bench import scenarios as S                         # noqa: E402

OUT = PB.OUT
MAN = os.path.join(PB.PN.PD.ROOT, "results/TEACH2/scenario_manifest_teach2L.json")


class Zapis:
    """Tor stały (otwarty) z zapisu (T, 3) z przesunięciem startu o `shift` s."""

    def __init__(self, tor, B, shift=0.0):
        self.tor, self.B, self.k = tor, B, int(round(shift / PN.DT))

    def pos3(self):
        i = int(np.clip(self.k, 0, len(self.tor) - 1))
        return np.tile(self.tor[i], (self.B, 1))

    def krok(self, p):
        self.k += 1
        return self.pos3()


def bieg_zapis(tor, shift, ziarno, napedy):
    B = 1
    I = Zapis(tor, B, shift)
    sz = PN.Szum(B, np.random.default_rng(ziarno), wl=True)
    P = PN.Petla(B, napedy["N"], np.array([[0.0, 0.0, -12.0]]), np.zeros((B, 3)), PB.wiek_med(), sz, "siec")
    q = I.pos3(); t_ev, maxz = None, 0.0
    for k in range(int(300 / PN.DT)):
        t = k * PN.DT
        P.krok(q)
        dz = abs(q[0, 2] - P.p[0, 2] - 2.0)
        if t >= PB.T_OC:
            maxz = max(maxz, dz)
            if t_ev is None and dz > PB.PROG:
                t_ev = t
        q = I.krok(P.p)
    return t_ev, maxz


def segmenty(tor, dt=PN.DT, tol=1e-6):
    q = tor[:, :2]
    v = np.diff(q, axis=0) / dt
    seg, i0 = [], 0
    for i in range(1, len(v) + 1):
        if i == len(v) or np.abs(v[i] - v[i0]).max() > tol:
            vv = v[i0]; sp = float(np.hypot(*vv))
            seg.append({"t0": round(i0 * dt, 6), "t1": round(i * dt, 6), "x0": float(q[i0, 0]), "y0": float(q[i0, 1]),
                        "heading_deg": float(math.degrees(math.atan2(vv[1], vv[0]))) if sp > 0 else 0.0, "v": round(sp, 9)})
            i0 = i
    return seg


def eksport(tor, k):
    man = json.load(open(MAN))
    ep = copy.deepcopy(next(e for e in man["episodes"] if e["scenario_id"] == "c10_s01"))
    ep["segments"] = segmenty(tor)
    ep["ep_dur_s"] = 1000.0
    ep["start_pos"] = [float(tor[0, 0]), float(tor[0, 1]), 10.0]
    ep.pop("wahadlo", None)
    ep["petla_kontrprzyklad"] = {"k": k, "zrodlo": "results/PETLA_RECON/kontr.json"}
    vmax = max(s["v"] for s in ep["segments"])
    t = np.arange(0.0, ep["segments"][-1]["t1"] + 1e-9, 0.1)
    p = np.array([S.position_at(ep, x)[:2] for x in t])
    krok = float(np.max(np.hypot(*np.diff(p, axis=0).T)))
    r = float(np.max(np.hypot(p[:, 0], p[:, 1])))
    d_zap = float(np.max(np.hypot(*(p - tor[np.minimum((t / PN.DT).round().astype(int), len(tor) - 1), :2]).T)))
    spr = {"krok_max": krok, "prog_kroku": vmax * 0.1 + 0.001, "krok_ok": krok <= vmax * 0.1 + 0.001, "promien_max": r,
           "promien_ok": r <= 11.001, "n_odcinkow": len(ep["segments"]), "zgodnosc_z_zapisem_max_m": d_zap}
    json.dump({"episode": ep, "sprawdzian": spr}, open(os.path.join(OUT, f"kontr_{k}_manifest.json"), "w"), indent=1)
    return spr


def kandydaci():
    out = []
    for i, z in enumerate(R45.zadania()):
        w, v, r, n, s = z
        if w != "siec" or n != "N" or r not in PI.OTWARTE:
            continue
        a = np.load(os.path.join(R45.CZ, R45.nazwa(z) + ".npz"))
        for j in np.where(np.isfinite(a["t_ev"]))[0]:
            out.append({"zrodlo": R45.nazwa(z), "rodzina": r, "vmax": v, "szum": s, "ziarno": int(a["ziarno"]), "indeks": int(j),
                        "t_ev": float(a["t_ev"][j]), "max_dz": float(a["max_dz"][j]), "kier": float(a["kier"][j])})
    sz = json.load(open(os.path.join(OUT, "szukanie_r4.json")))["najlepszy"]
    if sz["miary"]["t_ev"] is not None and np.isfinite(sz["miary"]["t_ev"]):
        out.append({"zrodlo": "szukanie_r4", "rodzina": "tor", "vmax": 1.0, "szum": True, "ziarno": sz["ziarno"], "indeks": sz["indeks"],
                    "t_ev": sz["miary"]["t_ev"], "max_dz": sz["miary"]["max_dz"], "kier": sz["miary"]["kier"], "param": sz["param"]})
    return sorted(out, key=lambda c: (c["t_ev"], -c["max_dz"]))


def main():
    napedy = json.load(open(os.path.join(OUT, "r3_naped.json")))["napedy"]
    kand = kandydaci()
    wyn = {"kandydaci_n": len(kand), "kandydaci": kand, "kontrprzyklady": []}
    for k, c in enumerate(kand[:3]):
        if c["rodzina"] == "tor":
            # wsad populacji (300) z tym samym ziarnem: szum wiersza `indeks` zależy tylko od ziarna i B, tor intruza tylko od param
            idx = c["indeks"]
            res = PB.bieg("tor", "N", True, 1.0, B=300, ziarno=c["ziarno"], param=np.tile(c["param"], (300, 1)), log_idx=[idx])
        else:
            res = PB.bieg(c["rodzina"], "N", c["szum"], c["vmax"], B=900, ziarno=c["ziarno"], log_idx=[c["indeks"]])
            idx = c["indeks"]
        log = res["logi"][idx]
        np.save(os.path.join(OUT, f"kontr_{k}_log.npy"), log)
        zg = {"t_ev_wsad": c["t_ev"], "t_ev_odtw": float(res["t_ev"][idx]) if np.isfinite(res["t_ev"][idx]) else None,
              "max_dz_wsad": c["max_dz"], "max_dz_odtw": float(res["max_dz"][idx])}
        tor = log[:, 1:4]
        odp = []
        for r_ in range(20):
            sh = -2.0 + 4.0 * r_ / 19
            te, mz = bieg_zapis(tor, sh, 4242 + r_, napedy)
            odp.append({"shift_s": round(sh, 3), "ziarno_szumu": 4242 + r_, "t_ev": te, "max_dz": mz})
        spr = eksport(tor, k)
        wyn["kontrprzyklady"].append(dict(c, odtworzenie=zg, odpornosc_n=sum(o["t_ev"] is not None for o in odp), odpornosc=odp,
                                          eksport=spr, log=f"results/PETLA_RECON/kontr_{k}_log.npy",
                                          manifest=f"results/PETLA_RECON/kontr_{k}_manifest.json", kolumny_logu=PB.KOLUMNY_LOGU))
        print(k, c["zrodlo"], c["indeks"], zg, "odporność", wyn["kontrprzyklady"][-1]["odpornosc_n"], "/20", spr, flush=True)
        json.dump(wyn, open(os.path.join(OUT, "kontr.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
