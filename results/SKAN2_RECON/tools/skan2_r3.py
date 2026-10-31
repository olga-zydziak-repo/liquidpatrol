#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r3.py — R3 PROMPT_SKAN2_S0: forma zamknięta przeglądu perymetru.

(0) Odtworzenie 11.15 s (transit_r3.py:114-132): n = ceil(273.1/krok), t_end = dwell + n·(krok/slew + stare),
    koniec okna 1.0 s najgorszego azymutu = t_end − stare + 1.0. Stożek ENTRY ±43.45° (RECON_AKW.md:91).
(A) LITERA PROMPTU: t_worst(krok, stare, dwell) = t_end z oknem równym stare (cel musi być w stare
    najgorszego azymutu przez cały stare) oraz wariant TRANSIT (okno 1.0 s, gdy stare ≥ 1.0);
    dopuszczalna ⇔ t_worst ≤ 9.5 s ∧ stare ≥ S + L (S = p90 uspokojenia R2, L = p90 latencji R1).
(B) MODEL ADMISJI W RAMPIE (odchylenie nazwane; R1/R5: 22/36 ENTRY na celu w rampie @14.7 Hz):
    czołowa krawędź stożka dochodzi do najgorszego azymutu po obrocie 273.1° od końca dwell; obrót
    T_rot(θ) = k·(krok/slew + stare) + r/slew (k = floor(θ/krok), r = reszta); admisja do L później,
    o ile cel pozostaje w stożku ≥ L (czas w stożku = obrót o 86.9° od tej chwili).
    t_adm = dwell + T_rot(273.1) + L; dopuszczalna ⇔ t_adm ≤ 9.5 ∧ t_w_stozku ≥ L. Wiersz stare = 0 = obrót
    ciągły 60°/s (profil I w nowej kadencji). L w (B) = p90 z R1 dla warstw (bez wiatru / z wiatrem).
(B-kal) jak (B), ale zamiast L — offset O zmierzony na profilu FROZEN (skan2_r3_kal.py: obs − dwell − T_rot,
    warstwa bez wiatru, akwizycja w pierwszym przejściu): O_max; dopuszczalna ⇔ dwell + T_rot + O_max ≤ 9.5 ∧
    t_w_stozku ≥ O_max. Chybienie pierwszego przejścia (1/7 bez wiatru) raportowane obok, nie w tabeli.
Wejścia: r1_L.json, r2_S.json, r3_kalibracja.json (jeśli istnieje).  Wyjście: r3_tabela.json + wydruk.
"""
import json
import math
import os

OUT = "/home/olga/projects/liquidpatrol/results/SKAN2_RECON"
HALF = 43.45
ARC = 360.0 - 2 * HALF          # 273.1°
SLEW = 60.0
DEADLINE = 10.0
MARGIN = 0.5


def t_end(step, stare, dwell):
    n = math.ceil(round(ARC / step, 6))
    return n, dwell + n * (step / SLEW + stare)


def t_rot(theta, step, stare):
    if stare == 0.0:
        return theta / SLEW
    k = int(theta // step)
    r = theta - k * step
    return k * (step / SLEW + stare) + (r / SLEW if r > 1e-9 else 0.0)


def time_in_cone(step, stare, theta0):
    """czas obrotu o 2·HALF od chwili, gdy obrócono już o theta0 (krawędź czołowa na celu)."""
    return t_rot(theta0 + 2 * HALF, step, stare) - t_rot(theta0, step, stare)


def main():
    L = json.load(open(os.path.join(OUT, "r1_L.json")))
    S = json.load(open(os.path.join(OUT, "r2_S.json")))["warstwy"]
    s_p90 = max(S[k]["T15_final_p90"] for k in ("a", "a2_bez_wiatru", "a2_wiatr"))
    # L litery: (a) stare ma < 10 zdarzeń ⇒ uzupełnione (b) — liczone tu z dwóch plików
    lit = json.load(open(os.path.join(OUT, "r1_zdarzenia_stare.json")))
    ev_a = [e for eps in lit["a"].values() for ep in eps for e in ep["zdarzenia"] if e["Z0"] and e["Z0"] >= 5]
    ev_b = [e for e in L["b_zdarzenia"] if e["Z0"] >= 5]
    xs = sorted([(e["fresh_on"] if not e["uciete"] else math.inf) for e in ev_a + ev_b])
    l_lit = xs[math.ceil(0.9 * len(xs)) - 1]
    l_bw = L["any|a+a2bw+b|Z0>=5"]["fresh_on"]["p90"]
    l_w = L["any|a2_wiatr|Z0>=5"]["fresh_on"]["p90"]          # None ⇒ +∞ (ucięte ≥ 10%)
    l_w_adm = L["any|a2_wiatr|Z0>=5"]["fresh_on_przyjete"]["p90"]
    res = {"S_p90": s_p90, "L_litera_a+b": l_lit, "n_L_litera": len(xs), "L_bez_wiatru_any": l_bw,
           "L_wiatr_any": l_w, "L_wiatr_any_przyjete_p90": l_w_adm}
    n0, te0 = t_end(68.3, 1.2, 2.0)
    res["odtworzenie"] = {"n": n0, "t_end": round(te0, 2), "koniec_okna_1s": round(te0 - 1.2 + 1.0, 2),
                          "forma_aneksu": round(2 + ARC / 60 + 1.2 * 4 - 0.2, 2)}
    rows_a, rows_b = [], []
    for step in (40.0, 50.0, 60.0, 68.3):
        for stare in (0.4, 0.5, 0.7, 0.9, 1.2):
            for dwell in (1.0, 2.0):
                n, te = t_end(step, stare, dwell)
                t_w_stare = te                                  # okno = cały stare najgorszego azymutu
                t_w_1s = te - stare + 1.0 if stare >= 1.0 else None   # definicja TRANSIT (okno 1.0 s)
                need = s_p90 + l_lit
                rows_a.append({"krok": step, "stare": stare, "dwell": dwell, "n": n,
                               "t_worst_okno_stare": round(t_w_stare, 2),
                               "t_worst_okno_1s_TRANSIT": t_w_1s and round(t_w_1s, 2),
                               "S+L_litera": round(need, 3),
                               "dopuszczalna": t_w_stare <= DEADLINE - MARGIN and stare >= need})
        for stare in (0.0, 0.4, 0.5, 0.7, 0.9, 1.2):
            for dwell in (1.0, 2.0):
                tr = t_rot(ARC, step, stare)
                tic = time_in_cone(step, stare, ARC)
                for nm, lv in (("bez_wiatru", l_bw), ("wiatr", l_w if l_w is not None else math.inf)):
                    t_adm = dwell + tr + lv
                    rows_b.append({"krok": step if stare > 0 else "ciągły", "stare": stare, "dwell": dwell,
                                   "warstwa_L": nm, "L": lv if lv != math.inf else None,
                                   "t_rot_273": round(tr, 2), "t_w_stozku": round(tic, 2),
                                   "t_adm_najgorszy": round(t_adm, 2) if t_adm != math.inf else None,
                                   "dopuszczalna": t_adm <= DEADLINE - MARGIN and tic >= lv})
    # usuń duplikaty wierszy 'ciągły' (krok nie gra roli)
    seen, rb = set(), []
    for r in rows_b:
        k = (r["krok"], r["stare"], r["dwell"], r["warstwa_L"])
        if k not in seen:
            seen.add(k); rb.append(r)
    kp = os.path.join(OUT, "r3_kalibracja.json")
    if os.path.exists(kp):
        kal = json.load(open(kp))
        fp = [r["offset"] for r in kal["wiersze"] if r["warstwa"] in ("a", "a2_bez_wiatru")
              and r["bearing"] != 0 and r["dh_przy_pred"] >= 5.0 and r["offset"] < 5.0]
        miss = [r for r in kal["wiersze"] if r["warstwa"] in ("a", "a2_bez_wiatru")
                and r["bearing"] != 0 and r["dh_przy_pred"] >= 5.0 and r["offset"] >= 5.0]
        o_max = max(fp)
        res["O_kal"] = {"n_pierwsze_przejscie": len(fp), "O_sorted": sorted(fp), "O_max": o_max,
                        "chybienia_pierwszego_przejscia": len(miss)}
        rk = []
        for r in rb:
            if r["warstwa_L"] != "bez_wiatru":
                continue
            ta = r["dwell"] + r["t_rot_273"] + o_max
            rk.append({**{k: r[k] for k in ("krok", "stare", "dwell", "t_rot_273", "t_w_stozku")},
                       "O_max": o_max, "t_adm_kal": round(ta, 2),
                       "frac_rampy": (round((r["krok"] / SLEW) / (r["krok"] / SLEW + r["stare"]), 2)
                                      if r["stare"] > 0 else 1.0),
                       "dopuszczalna_kal": ta <= DEADLINE - MARGIN and r["t_w_stozku"] >= o_max})
        res["B_kal"] = rk
        res["B_kal_dopuszczalne"] = [r for r in rk if r["dopuszczalna_kal"]]
    res["A_litera"] = rows_a
    res["A_dopuszczalne"] = [r for r in rows_a if r["dopuszczalna"]]
    res["B_rampa"] = rb
    res["B_dopuszczalne"] = [r for r in rb if r["dopuszczalna"]]
    json.dump(res, open(os.path.join(OUT, "r3_tabela.json"), "w"), indent=1)
    print({k: res[k] for k in ("S_p90", "L_litera_a+b", "n_L_litera", "L_bez_wiatru_any", "L_wiatr_any",
                               "L_wiatr_any_przyjete_p90", "odtworzenie")})
    print("A dopuszczalne:", len(res["A_dopuszczalne"]))
    for r in rows_a:
        if r["dwell"] == 2.0 or r["t_worst_okno_stare"] <= 9.5:
            print("A", r)
    if "B_kal" in res:
        print("O_kal", res["O_kal"]); print("B-kal dopuszczalne:", len(res["B_kal_dopuszczalne"]))
        for r in sorted(res["B_kal_dopuszczalne"], key=lambda r: r["t_adm_kal"]):
            print("Bk", r)
    print("B dopuszczalne:", len(res["B_dopuszczalne"]))
    for r in res["B_dopuszczalne"]:
        print("B", r)


if __name__ == "__main__":
    main()
