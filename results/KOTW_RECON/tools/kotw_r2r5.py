#!/usr/bin/env python3
"""results/KOTW_RECON/tools/kotw_r2r5.py — R1 agregat, R2 (błąd jednej poprawki), R5 (piła w budżecie) PROMPT_KOTW_S0.

Wejścia (odczyt): r1_widocznosc_raw.json (kotw_r1.py), r2_yaw_s4.json (kotw_yaw.py),
results/KONT/s2/s2_freeze_bf.json (ae19f66c: eps_b_obwiednia [m, ×1.5 wliczone, koszyki 1 s, 0–69 s], delta_D5 1.524),
results/KONT_RECON/r4_margin.json (tabela_scenariuszy[c]["m"], m_p50 5.79).

R2 — model najgorszego przypadku (ograniczenia, nie σ), kamera z pinu f = 269.5 px:
  poprzecznie  e_lat = D·tan(δψ) + D·px/f                   (błąd yaw estymatora + błąd centroidu)
  radialnie    e_rad = min(e_rozmiar, e_elewacja)
     e_rozmiar  = D²·px/(f·W)                                (zasięg z pozornej szerokości W)
     e_elewacja = Δz/sin²(e)·(px/f + δθ) + δz/tan(e)          (zasięg poziomy z kąta depresji i wysokości, e = atan(Δz/d))
  ε_fix = hypot(e_lat, e_rad); Δz = 12 − h (patrol, alt_p50 z R1).
  Warianty: OPT (px 1, δψ 2°, δθ 0.5°, δz 0.2 m) i ZMIERZ (px 2, δψ 5.5° = max |błędu| yaw w kontynuacjach S4, δθ 0.5°, δz 0.2 m);
  δθ (pochylenie) i δz (wysokość z lidaru/baro) są ZAŁOŻENIAMI; zmierzony bias wysokości 2d S1 1.8 m w osobnej kolumnie.
R5 — per komórka (scenario_id) i per (h, W, wariant): τ = najdłuższa WEWNĘTRZNA przerwa okien „central_W” w fazie orbit
  (cenzurowane osobno), D = najmniejszy zasięg okna poprzedzającego przerwę; domyka się ⇔ ε_fix(D) + ε_b(τ) + Δ_D5 ≤ m_komórki;
  τ ≥ 70 s ⇒ nie domyka (bez ekstrapolacji). Kombinacja dopuszczalna ⇔ domyka się w ≥ 50% komórek ORAZ w najgorszej
  przerwie orbity całej siatki przy m_p50.
Użycie: kotw_r2r5.py <katalog KOTW_RECON>
"""
import json, math, os, sys

ROOT = "/home/olga/projects/liquidpatrol"
F = 320.0 / math.tan(0.87)
OUT = sys.argv[1]
r1 = json.load(open(os.path.join(OUT, "r1_widocznosc_raw.json")))
fz = json.load(open(os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")))
mg = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))
EPS, D5, MP50 = fz["eps_b_obwiednia"], fz["delta_D5"], fz["m_p50"]
MCELL = {c: v["m"] for c, v in mg["tabela_scenariuszy"].items()}
WAR = {"OPT": dict(px=1, psi=2.0, th=0.5, dz=0.2), "ZMIERZ": dict(px=2, psi=5.5, th=0.5, dz=0.2),
       "ZMIERZ_bias_h1.8": dict(px=2, psi=5.5, th=0.5, dz=1.8)}
HS, WS = ["0.5", "2.0", "5.0"], [0.5, 1.0, 2.0]


def eps_b(t):
    k = int(math.floor(t))
    return EPS[k] if k < len(EPS) else None


def efix(D, h, W, v):
    dz = 12.0 - float(h)
    d = math.sqrt(max(D * D - dz * dz, 0.01))
    e = math.atan2(dz, d)
    lat = D * math.tan(math.radians(v["psi"])) + D * v["px"] / F
    roz = D * D * v["px"] / (F * W)
    ele = dz / math.sin(e) ** 2 * (v["px"] / F + math.radians(v["th"])) + v["dz"] / math.tan(e)
    rad = min(roz, ele)
    return math.hypot(lat, rad), dict(lat=round(lat, 2), rozmiar=round(roz, 2), elewacja=round(ele, 2))


def pct(x, p):
    x = sorted(x)
    return round(x[min(len(x) - 1, int(p * len(x)))], 2) if x else None


# ---------- R1 agregat ----------
E = r1["epizody"]
agg = {"n_epizodow": len(E), "kampanie": {}, "per_h": {}}
for e in E:
    agg["kampanie"][e["kampania"]] = agg["kampanie"].get(e["kampania"], 0) + 1
for h in HS:
    for key in ["central", "kadr"] + [f"central_W{w}" for w in WS]:
        start, kon, wew, okn = [], [], {}, {}
        frac = {}
        for e in E:
            P = e["h"][h][key]["przerwy"]
            for i, p in enumerate(P):
                (start if i == 0 else kon if i == len(P) - 1 else wew.setdefault(p["faza"], [])).append(p["dl"])
            for w in e["h"][h][key]["okna"]:
                okn.setdefault(w["faza"], []).append(w)
            for f, v in e["h"][h][key]["frac_widoczny_per_faza"].items():
                frac.setdefault(f, []).append(v)
        agg["per_h"].setdefault(h, {})[key] = {
            "epizody_bez_okna": sum(1 for e in E if not e["h"][h][key]["okna"]),
            "przerwa_startowa_s": {"p50": pct(start, .5), "p95": pct(start, .95), "max": max(start)},
            "przerwa_koncowa_cenz_s": {"p50": pct(kon, .5), "p95": pct(kon, .95), "max": max(kon)},
            "przerwy_wewnetrzne_s": {f: {"n": len(v), "p50": pct(v, .5), "p95": pct(v, .95), "max": max(v)} for f, v in wew.items()},
            "okna": {f: {"n": len(v), "dl_p50": pct([w["dl"] for w in v], .5), "dl_p95": pct([w["dl"] for w in v], .95),
                         "zasieg_min_p50": pct([w["zasieg_min"] for w in v], .5), "zasieg_min": min(w["zasieg_min"] for w in v),
                         "zasieg_max": max(w["zasieg_max"] for w in v)} for f, v in okn.items()},
            "frac_widoczny_per_faza_srednia": {f: round(sum(v) / len(v), 4) for f, v in frac.items()}}
json.dump(agg, open(os.path.join(OUT, "r1_widocznosc.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R2 ----------
r2 = {"F_px": round(F, 2), "warianty": WAR, "tabela": [], "tau_min_poprawy": {}}
for D in (10, 15, 20, 25, 30, 35):
    for h in HS:
        for W in WS:
            row = {"D": D, "h": float(h), "W": W, "w_px": round(F * W / D, 1)}
            for n, v in WAR.items():
                ef, sk = efix(D, h, W, v)
                row[n] = round(ef, 2); row[n + "_skladowe"] = sk
                tm = next((t for t in range(len(EPS)) if EPS[t] > ef), None)
                row[n + "_tau_min_s"] = tm
            r2["tabela"].append(row)
json.dump(r2, open(os.path.join(OUT, "r2_poprawka.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R5 ----------
cells = {}
for e in E:
    cells.setdefault(e["scenario"], []).append(e)
r5 = {"m_p50": MP50, "delta_D5": D5, "kombinacje": []}
for h in HS:
    for W in WS:
        key = f"central_W{W}"
        for n, v in WAR.items():
            per, glob_worst = {}, None
            for c, eps in cells.items():
                worst = None
                for e in eps:
                    P, O = e["h"][h][key]["przerwy"], e["h"][h][key]["okna"]
                    for i in range(1, len(P) - 1):
                        if P[i]["faza"] != "orbit":
                            continue
                        cand = (P[i]["dl"], O[i - 1]["zasieg_min"], e["boot"], e["ep"])
                        if worst is None or cand[0] > worst[0]:
                            worst = cand
                if worst is None:
                    per[c] = {"tau": None, "domyka": False, "powod": "brak wewnętrznej przerwy orbity (≤ 1 okno)"}
                    continue
                tau, D, b, ep = worst
                eb = eps_b(tau)
                ef = efix(D, h, W, v)[0]
                m = MCELL.get(c)
                ok = eb is not None and m is not None and ef + eb + D5 <= m
                per[c] = {"tau": tau, "D": D, "boot": b, "ep": ep, "eps_fix": round(ef, 2), "eps_b": eb, "m": m,
                          "suma": round(ef + (eb or 99) + D5, 2), "domyka": ok}
                if glob_worst is None or tau > glob_worst["tau"]:
                    glob_worst = dict(per[c], komorka=c)
            n_ok = sum(1 for p in per.values() if p["domyka"])
            gw = glob_worst
            gw_ok = gw is not None and gw["eps_b"] is not None and gw["eps_fix"] + gw["eps_b"] + D5 <= MP50
            r5["kombinacje"].append({"h": float(h), "W": W, "wariant": n, "komorki": len(per), "domyka_komorki": n_ok,
                                     "frac": round(n_ok / len(per), 3), "najgorsza_orbita": gw, "najgorsza_orbita_domyka_przy_m_p50": gw_ok,
                                     "dopuszczalna": n_ok / len(per) >= 0.5 and gw_ok, "per_komorka": per})
json.dump(r5, open(os.path.join(OUT, "r5_pila.json"), "w"), ensure_ascii=False, indent=1)
for k in r5["kombinacje"]:
    g = k["najgorsza_orbita"]
    print(k["h"], k["W"], k["wariant"], f"{k['domyka_komorki']}/{k['komorki']}", "najgorsza:", g and (g["komorka"], g["tau"], g["D"], g["eps_fix"], g["eps_b"], g["suma"]), "dopuszczalna:", k["dopuszczalna"])
