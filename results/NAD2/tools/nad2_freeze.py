#!/usr/bin/env python3
"""results/NAD2/tools/nad2_freeze.py — PROMPT_NAD2_S1 §1.4: narzędzie FREEZE tabeli U (PRE_NAD2 §4; 0 bootów).

Liczby ZAMROŻONE = PRE_NAD2 §4 (PRE_NAD2.md, sha256 eea6fcc8…) ze sprostowaniem F_jeden z ANEKS_NAD2-1 §2.2 (sha256
92d4dfcb…; kanon czasu nogi = timestamp_sample próbki EKF, §2.1); narzędzie je ODTWARZA z danych S4 i zapisuje pełną tabelę
z sumą sha:
  - G (przyrost EKF, okno przesuwne, poziomo) — results/NAD2_RECON/r2_przyrost.json G_kum (krawędzie 0.25…1.05 s);
  - F_para — results/NAD2_RECON/r5_tabela.json (T1Z2C0, F para po regule n<100);
  - F_jeden — NOWE: rozwiązanie jednym znacznikiem (z korektą T1) harness/nadir_fix.Rama(litera="NAD2") w KAŻDEJ klatce
    z przyjętą obserwacją okna bez GNSS 12 cięć S4 (faza misji przed zejściem), błąd zakotwiczenia poziomo
    |p_jeden − GT(t_a)|, t_a = czas próbki EKF migawki (dopasowanie po wartości, R1), per koszyk najbliższego znacznika;
    reguła PRE §4: pole o n < 100 = max(własna, maksimum bieżące niższych koszyków, pula trybu); potem maksimum bieżące.
    Różnica > 0.01 m wobec PRE w którymkolwiek koszyku ⇒ STOP (kod 3), plik nie powstaje.
U = 1.5·(F + G); u′ = U + Δ_D5; R = R_E − d_stop − u′. Wyjście: results/NAD2/s1/freeze_U.json (+ sha256 tabeli w polu
„sha256_tabeli” = sha256 kanonicznego JSON tabeli: json.dumps(tabela, sort_keys=True, separators=(",", ":"))).
"""
import hashlib
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools")]
import nad2_dane as D
from harness import nadir_fix as NF

OUT = os.path.join(ROOT, "results/NAD2/s1/freeze_U.json")
PRE = os.path.join(ROOT, "PRE_NAD2.md")
PRE_SHA256 = "eea6fcc82b1a14b9dfacd710ec4c6c0f426bbbea34b549ab4c1511de9567e634"
KRAW = (0.25, 0.45, 0.65, 0.85, 1.05)
PRE_G = (0.6251, 1.0722, 1.4583, 1.7894, 2.0638)
PRE_F_PARA = (0.1968, 0.2372, 0.2372, 0.2372, 0.2577)
PRE_F_JEDEN = (0.2562, 0.3376, 0.4445, 0.4527, 0.4527)   # ANEKS_NAD2-1 §2.2 (sprostowanie PRE §4; było 0.253/0.329/0.440/0.442/0.442)
ANEKS = os.path.join(ROOT, "ANEKS_NAD2-1.md")
ANEKS_SHA256 = "92d4dfcbbd55cccae9cc6df1058bb229c47cddc7e61f0a01bac9ea88c6b5f33b"
ZAPAS, R_E, D_STOP, DD5, TAU_STAR = 1.5, 32.0, 2.85, 1.524, 1.05
TOL, N_MIN = 0.01, 100


def f_jeden(pole_t="timestamp_sample"):
    """pole_t — konwencja chwili zakotwiczenia t_a: czas próbki EKF z pola timestamp_sample (dom.; R1/R3 reconu) albo
    timestamp (publikacja, ~4 ms później); diagnoza STOP liczy obie."""
    raw = {k: [] for k in range(5)}
    for n in D.CIECIA_S4:
        b = D.Boot(n)
        rama = NF.Rama(litera="NAD2")
        ts = np.array([r["sim"] for r in b.rama]); mi = np.array([b.misja(r) for r in b.rama])
        for r in b.nf:
            fx = rama.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            if not fx["ok"] or b.klasa(r["sim"]) != "bez_GNSS":
                continue
            i = int(np.clip(np.searchsorted(ts, r["sim"]), 0, len(ts) - 1))
            if i > 0 and abs(ts[i - 1] - r["sim"]) < abs(ts[i] - r["sim"]):
                i -= 1
            if not (mi[i] and abs(ts[i] - r["sim"]) <= 0.1):
                continue
            k, _ = b.dopasuj(r["ekf_pos"], r["sim"], okno=(-0.3, 0.3))
            t_a = (float(b.vts[k]) if pole_t == "timestamp_sample" else float(b.vt[k])) if k is not None else r["sim"]
            pj = np.array(fx["jeden"]["p_ne"])
            raw[fx["kosz"]].append(float(np.linalg.norm(pj - b.gt(t_a)[0][:2])))
    pula = max(v for x in raw.values() for v in x)
    F, opis, bieg = [], {}, 0.0
    for k in range(5):
        own = max(raw[k]) if raw[k] else 0.0
        val = own if len(raw[k]) >= N_MIN else max(own, bieg, pula)
        bieg = max(bieg, val)
        F.append(round(bieg, 4))
        opis[k] = {"n": len(raw[k]), "max_wlasny": round(own, 4), "pole": round(val, 4), "F": round(bieg, 4),
                   "regula": "wlasna" if len(raw[k]) >= N_MIN else "n<100: max(wlasna, biezace nizszych, pula trybu)"}
    return F, opis


def main():
    assert hashlib.sha256(open(PRE, "rb").read()).hexdigest() == PRE_SHA256, "sha PRE_NAD2"
    assert hashlib.sha256(open(ANEKS, "rb").read()).hexdigest() == ANEKS_SHA256, "sha ANEKS_NAD2-1"
    r2 = json.load(open(os.path.join(D.OUT, "r2_przyrost.json")))
    G = [round(r2["G_kum"]["poziomo"][str(k)], 4) for k in KRAW]
    r5 = json.load(open(os.path.join(D.OUT, "r5_tabela.json")))
    Fp = [round(r5["warianty"]["T1Z2C0"]["F"]["para"][str(k)]["F"], 4) for k in range(5)]
    Fj, opis_j = f_jeden()
    rozb = {"G": [round(a - b, 4) for a, b in zip(G, PRE_G)], "F_para": [round(a - b, 4) for a, b in zip(Fp, PRE_F_PARA)],
            "F_jeden": [round(a - b, 4) for a, b in zip(Fj, PRE_F_JEDEN)]}
    print("G", G, "\nF_para", Fp, "\nF_jeden", Fj, opis_j, "\nrozbieżności wobec PRE", rozb)
    if any(abs(x) > TOL for x in rozb["F_jeden"]):
        Fj2, opis2 = f_jeden("timestamp")
        diag = {"STOP": "F_jeden nie odtwarza się w tolerancji 0.01 m (PROMPT_NAD2_S1 §1.4)", "PRE_F_jeden": list(PRE_F_JEDEN),
                "konwencja_timestamp_sample": {"F_jeden": Fj, "opis": opis_j, "rozbieznosc": rozb["F_jeden"]},
                "konwencja_timestamp": {"F_jeden": Fj2, "opis": opis2,
                                        "rozbieznosc": [round(a - b, 4) for a, b in zip(Fj2, PRE_F_JEDEN)]},
                "G_rozbieznosc": rozb["G"], "F_para_rozbieznosc": rozb["F_para"], "pre_sha256": PRE_SHA256}
        json.dump(diag, open(os.path.join(os.path.dirname(OUT), "freeze_STOP_diagnoza.json"), "w"), ensure_ascii=False, indent=1)
        print("STOP: F_jeden nie odtwarza się w tolerancji 0.01 m (PROMPT_NAD2_S1 §1.4); diagnoza obu konwencji:",
              {k: diag[k]["rozbieznosc"] for k in ("konwencja_timestamp_sample", "konwencja_timestamp")})
        sys.exit(3)
    assert all(abs(x) <= 1e-4 for x in rozb["G"] + rozb["F_para"]), rozb
    # tabela ZAMROŻONA = liczby PRE §4 (odtworzone powyżej)
    tab = {"krawedzie_tau_s": list(KRAW), "G": list(PRE_G), "F": {"para": list(PRE_F_PARA), "jeden": list(PRE_F_JEDEN)},
           "zapas": ZAPAS, "delta_D5": DD5, "R_E": R_E, "d_stop": D_STOP, "tau_star_s": TAU_STAR}
    U = {tr: [[round(ZAPAS * (tab["F"][tr][k] + PRE_G[i]), 6) for k in range(5)] for i in range(5)] for tr in ("para", "jeden")}
    tab["U"] = U
    tab["u_prim"] = {tr: [[round(U[tr][i][k] + DD5, 6) for k in range(5)] for i in range(5)] for tr in U}
    tab["R"] = {tr: [[round(R_E - D_STOP - tab["u_prim"][tr][i][k], 6) for k in range(5)] for i in range(5)] for tr in U}
    can = json.dumps(tab, sort_keys=True, separators=(",", ":"))
    out = {"tabela": tab, "sha256_tabeli": hashlib.sha256(can.encode()).hexdigest(), "pre": "PRE_NAD2.md", "pre_sha256": PRE_SHA256,
           "aneks": "ANEKS_NAD2-1.md", "aneks_sha256": ANEKS_SHA256, "kanon_czasu": "timestamp_sample",
           "tau_w_oslonie": "przedział z τ + 0.012 s; REFUSE(τ*) przy τ ≥ τ* − 2·dt = 0.95 s (ANEKS_NAD2-1 §2.3, §2.5)",
           "odtworzenie": {"G": G, "F_para": Fp, "F_jeden": Fj, "F_jeden_opis": opis_j, "rozbieznosci_wobec_PRE": rozb, "tolerancja_m": TOL},
           "indeksy": "U[tryb][przedział τ i][koszyk k]; przedział i: [0,0.25], (0.25,0.45], (0.45,0.65], (0.65,0.85], (0.85,1.05]"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("sha256_tabeli", out["sha256_tabeli"], "u′ τ≤0.25:", {tr: tab["u_prim"][tr][0] for tr in U}, "R:", {tr: tab["R"][tr][0] for tr in U})


if __name__ == "__main__":
    main()
