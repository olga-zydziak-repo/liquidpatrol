#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_rachunek.py — R4 rachunek złożenia (PROMPT_BLIZNIAK_S0 §6; rachunek, nie dowód; 0 bootów).

Wejście: profil S(v, d₁) z r3_B30_<A|B>.json (szczebel E3); d₁ = 15.0 w profilu oznacza brak d₁ (pomijane). Dla prędkości intruza v_q ∈ {0.5, 1.0} bierzemy najmniejsze dowiedzione
v > v_q z siatki {0.6, 1.0, 1.2} i jego d₁ (dystans z cech).
Ograniczenie dystansu z cech (napęd N: opóźnienie L = 7 ticków = 0.35 s, inercja τ = 0.3 s; prędkość własna |v| ≤ 3.2 m/s):
od chwili przekroczenia d₁ składowa komendy ku celowi ≥ v; najgorszy start — prędkość od celu 3.2 m/s:
  faza opóźnienia:  ΔD₁ ≤ (3.2 + v_q)·L,
  faza inercji:     v_r(t) = v − (v + 3.2)·e^{−t/τ}; dystans rośnie do t* = τ·ln((v + 3.2)/(v − v_q)),
                    ΔD₂ = ∫₀^{t*} (v_q − v_r) dt = (v_q − v)·t* + τ·(v + 3.2)·(1 − e^{−t*/τ}) = (v_q − v)·t* + τ·(3.2 + v_q).
  D_cech ≤ d₁ + ΔD₁ + ΔD₂ (założenie A1: komenda ku celowi przekłada się na prędkość radialną bez strat na obrót wersora).
Dystans prawdziwy: D ≤ D_cech + ε_rel, ε_rel = 1.364 m (PĘTLA R2, zmierzone na lotach po 30 s).
Ściana z GNSS (R-G-NOM 27.30 m): ρ* = 27.30 − D (U′ = 0 przy GNSS — założenie). Przedział 0 bez GNSS (24.84 m): ρ* = 24.84 − U′(0) − D,
U′(0) = 2.786 (P9_teach, przesłanka istniejącego dowodu).
"""
import json
import math
import os

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
L, TAU, VMAX, EPS, U0 = 0.35, 0.3, 3.2, 1.364, 2.786


def main():
    wyn = {}
    for w in ("A", "B"):
        fn = os.path.join(OUT, f"r3_B30_{w}.json")
        if not os.path.exists(fn):
            continue
        pr = json.load(open(fn))["E3"]["profil_d1"]
        out = {}
        for vq in (0.5, 1.0):
            kand = [(float(v), pr[v]) for v in ("0.6", "1.0", "1.2") if pr.get(v) is not None and pr[v] < 15.0 and float(v) > vq]
            if not kand:
                out[str(vq)] = {"uwaga": "brak dowiedzionego v > v_q"}
                continue
            best = None
            for v, d1 in kand:
                t = TAU * math.log((v + VMAX) / (v - vq))
                dD1 = (VMAX + vq) * L
                dD2 = (vq - v) * t + TAU * (VMAX + vq)
                Dc = d1 + dD1 + dD2
                rec = {"v": v, "d1": d1, "dD_opoznienie": dD1, "dD_inercja": dD2, "D_cech": Dc, "D_prawdziwy": Dc + EPS,
                       "rho_sciana_GNSS_27_30": 27.30 - (Dc + EPS), "rho_przedzial0_24_84": 24.84 - U0 - (Dc + EPS)}
                if best is None or rec["D_cech"] < best["D_cech"]:
                    best = rec
            out[str(vq)] = best
        out["skladniki"] = {"profil S": "dowiedziony (E3, 𝒟, 𝒞)", "przesłanki P1–P3": "zmierzone (99.1% / 99.6% ticków)",
                            "napęd N (L, τ)": "zmierzony (PĘTLA R3)", "A1 przełożenie komendy na v_r": "założone",
                            "ε_rel 1.364 m": "zmierzone (PĘTLA)", "U′(0) 2.786 m": "przesłanka dowodu P9_teach",
                            "wysokość z regulatora (P4)": "założona", "intruz ≤ v_q": "założone (klasa)"}
        wyn[w] = out
    json.dump(wyn, open(os.path.join(OUT, "r4_rachunek.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(wyn, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
