#!/usr/bin/env python3
"""results/KOTW_RECON/r2/tools/kotw2_r2r5.py — R1′ agregat, R2′ (poprawka z 1 i 2 kotwic), R5′ (piła na obwodzie), R4′ agregat.

Wejścia: r1p_obwod_raw.json (kotw2_obwod.py), r2p_yaw.json (kotw2_yaw.py), s2_freeze_bf.json (ae19f66c), r4_margin.json.
Model 1 kotwicy = model reconu 1 (results/KOTW_RECON/tools/kotw_r2r5.py, przepisany tu, nie importowany — tamten plik
wykonuje rachunek przy imporcie): e_lat = D·tan δψ + D·px/f; e_rad = min(D²·px/(f·W), Δz/sin²e·(px/f + δθ) + δz/tan e);
ε1 = hypot(e_lat, e_rad); Δz = 12 − h.
Model 2 kotwic (NOWY, kurs nieobserwowany niepotrzebny): zasięgi poziome do obu kotwic z e_rad każdej (bez członu yaw),
pozycja z przecięcia dwóch okręgów; ograniczenie najgorszego przypadku dla pierścieni o półszerokościach e_a, e_b
przecinających się pod kątem γ (kąt w dronie między kotwicami): ε2 = sqrt(e_a² + e_b² + 2·e_a·e_b·|cos γ|) / sin γ.
(Kurs wynika potem z namiaru — obserwowalny razem z pozycją.)
Warianty: OPT (px 1, δψ 2°, δθ 0.5°, δz 0.2 m), ZMIERZ (px 2, δψ = max |residuum| yaw w kontynuacjach S4 z r2p_yaw.json,
δθ 0.5°, δz 0.2 m), ZMIERZ_h1.8 (jak ZMIERZ, δz 1.8 m).
R5′ per kombinacja (geometria R_a/n/φ0/h × próg rozdzielczości {brak, 10 px} × W {0.5, 1} × wariant × tryb {1, 2}):
  orbita: per komórka najgorsza wewnętrzna przerwa orbity τ, ε_fix z okna ją poprzedzającego; komórka domyka się ⇔
    każdy jej epizod ma ≥ 1 okno ∧ ε_fix + ε_b(τ) + Δ_D5 ≤ m_komórki (τ = 0 gdy brak wewnętrznych przerw orbity);
  start: per epizod przerwa od t0 do 1. okna τ_s, margines startu m_s = R_E − D_STOP − r_max(przerwa); ε_fix = ε pierwszego
    okna (przybliżenie: jakości poprawki sprzed epizodu dane epizodowe nie niosą); domyka się ⇔ we WSZYSTKICH epizodach;
  dopuszczalna ⇔ ≥ 24/48 komórek ∧ najgorsza orbita siatki domyka się w swojej komórce ∧ start domyka się.
  τ ≥ 70 s ⇒ nie domyka (bez ekstrapolacji).
Użycie: kotw2_r2r5.py <katalog r2>
"""
import json, math, os, sys

ROOT = "/home/olga/projects/liquidpatrol"
OUT = sys.argv[1]
F = 320.0 / math.tan(0.87)
raw = json.load(open(os.path.join(OUT, "r1p_obwod_raw.json")))
yaw = json.load(open(os.path.join(OUT, "r2p_yaw.json")))
fz = json.load(open(os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")))
mg = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))
EPS, D5, MP50 = fz["eps_b_obwiednia"], fz["delta_D5"], fz["m_p50"]
R_E, D_STOP = float(mg["R_E"]), float(mg["D_STOP"])
MCELL = {c: v["m"] for c, v in mg["tabela_scenariuszy"].items()}
PSI_Z = max(v["residuum_kont"]["absmax"] for v in yaw.values())
WAR = {"OPT": dict(px=1, psi=2.0, th=0.5, dz=0.2), "ZMIERZ": dict(px=2, psi=PSI_Z, th=0.5, dz=0.2),
       "ZMIERZ_h1.8": dict(px=2, psi=PSI_Z, th=0.5, dz=1.8)}
WS = (0.5, 1.0)


def eps_b(t):
    k = int(math.floor(t))
    return EPS[k] if k < len(EPS) else None


def erad(D, h, W, v):
    dz = 12.0 - h
    d = math.sqrt(max(D * D - dz * dz, 0.01))
    e = math.atan2(dz, d)
    return min(D * D * v["px"] / (F * W), dz / math.sin(e) ** 2 * (v["px"] / F + math.radians(v["th"])) + v["dz"] / math.tan(e))


def eps1(D, h, W, v):
    lat = D * math.tan(math.radians(v["psi"])) + D * v["px"] / F
    return math.hypot(lat, erad(D, h, W, v))


def eps2(ra, rb, gdeg, h, W, v):
    g = math.radians(gdeg)
    if math.sin(g) < 1e-3:
        return float("inf")
    a, b = erad(ra, h, W, v), erad(rb, h, W, v)
    return math.sqrt(a * a + b * b + 2 * a * b * abs(math.cos(g))) / math.sin(g)


def efix(o, h, W, v, tryb):
    return eps2(o["r_a"], o["r_b"], o["gamma_deg"], h, W, v) if tryb == "2" else eps1(o["zasieg_min"], h, W, v)


def pct(x, p):
    x = sorted(x)
    return round(x[min(len(x) - 1, int(p * len(x)))], 2) if x else None


K = raw["konfiguracje"]
# ---------- R1′ agregat + R4′ ----------
r1 = {}
r4 = {}
for cfg, E in K.items():
    h = float(cfg.split("_h")[1])
    for prog, Wk in (("brak", "None"), ("10px_W1", "1.0"), ("10px_W0.5", "0.5")):
        a = {}
        for tryb in ("1", "2"):
            st = [e["W"][Wk][tryb]["przerwy"][0]["dl"] for e in E]
            orb = [p["dl"] for e in E for p in e["W"][Wk][tryb]["przerwy"][1:-1] if p["faza"] == "orbit"]
            zas = [o["zasieg_min"] for e in E for o in e["W"][Wk][tryb]["okna"]]
            a[tryb] = {"epizody_bez_okna": sum(1 for e in E if not e["W"][Wk][tryb]["okna"]),
                       "start": {"p50": pct(st, .5), "p95": pct(st, .95), "max": max(st)},
                       "orbita_wewn": {"n": len(orb), "p50": pct(orb, .5), "p95": pct(orb, .95), "max": max(orb) if orb else None},
                       "zasieg_najblizszej_w_oknie": {"p5": pct(zas, .05), "p50": pct(zas, .5), "p95": pct(zas, .95)}}
        a["frac_orbita_1"] = round(sum(e["W"][Wk]["frac_1_orbit"] for e in E) / len(E), 4)
        a["frac_orbita_2"] = round(sum(e["W"][Wk]["frac_2_orbit"] for e in E) / len(E), 4)
        g = [o["gamma_deg"] for e in E for o in e["W"][Wk]["2"]["okna"]]
        a["gamma_okien_2_p50"] = pct(g, .5)
        r1.setdefault(cfg, {})[prog] = a
    n = sum(e["r4"]["n"] for e in E if "r4" in e); hit = sum(e["r4"]["hit"] for e in E if "r4" in e)
    no = sum(e["r4"]["n_orbit"] for e in E if "r4" in e); ho = sum(e["r4"]["hit_orbit"] for e in E if "r4" in e)
    per = {}
    for e in E:
        if "r4" in e:
            c = per.setdefault(e["scenario"], [0, 0]); c[0] += e["r4"]["hit"]; c[1] += e["r4"]["n"]
    fr = sorted(v[0] / v[1] for v in per.values() if v[1])
    r4[cfg] = {"frac_wszystko": round(hit / n, 5), "frac_orbita": round(ho / no, 5), "probek_hit": hit,
               "hit_swiadek_ned_cmd_gt1m": sum(e["r4"]["hit_swiadek_ned_cmd_gt1m"] for e in E if "r4" in e),
               "komorki_z_hit": sum(1 for v in per.values() if v[0]), "frac_komorki_p50": pct(fr, .5), "frac_komorki_max": round(fr[-1], 5),
               "najgorsza_komorka": max(per.items(), key=lambda kv: kv[1][0] / max(kv[1][1], 1))[0]}
json.dump({"r1p": r1, "r4p": r4}, open(os.path.join(OUT, "r1p_obwod.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R2′ ----------
r2 = {"F_px": round(F, 2), "psi_zmierz_deg": PSI_Z, "warianty": WAR, "jedna": [], "dwie": []}
for D in (15, 20, 25, 30, 35, 40, 45):
    for h in (2.0, 4.0):
        for W in WS:
            r2["jedna"].append({"D": D, "h": h, "W": W, "w_px": round(F * W / D, 1), **{n: round(eps1(D, h, W, v), 2) for n, v in WAR.items()}})
for (ra, rb) in ((20, 25), (25, 30), (30, 35), (35, 40)):
    for g in (20, 40, 60, 80):
        for h in (2.0, 4.0):
            r2["dwie"].append({"r_a": ra, "r_b": rb, "gamma_deg": g, "h": h,
                               **{n: round(eps2(ra, rb, g, h, 1.0, v), 2) for n, v in WAR.items()}})
json.dump(r2, open(os.path.join(OUT, "r2p_poprawka.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R5′ ----------
komb = []
for cfg, E in K.items():
    h = float(cfg.split("_h")[1])
    cells = {}
    for e in E:
        cells.setdefault(e["scenario"], []).append(e)
    for prog, Wvis in (("brak", None), ("10px", "W")):
        for W in WS:
            Wk = "None" if Wvis is None else str(W)
            for n_, v in WAR.items():
                for tryb in ("1", "2"):
                    per, worst = {}, None
                    for c, eps_ in cells.items():
                        m = MCELL.get(c)
                        if any(not e["W"][Wk][tryb]["okna"] for e in eps_):
                            per[c] = {"domyka": False, "powod": "epizod bez okna"}
                            continue
                        cw = None
                        for e in eps_:
                            P, O = e["W"][Wk][tryb]["przerwy"], e["W"][Wk][tryb]["okna"]
                            for i in range(1, len(P) - 1):
                                if P[i]["faza"] == "orbit":
                                    cand = (P[i]["dl"], efix(O[i - 1], h, W, v, tryb), e["boot"], e["ep"])
                                    if cw is None or cand[0] > cw[0]:
                                        cw = cand
                        if cw is None:
                            best = min(efix(o, h, W, v, tryb) for e in eps_ for o in e["W"][Wk][tryb]["okna"])
                            cw = (0.0, best, None, None)
                        tau, ef, b, ep = cw
                        eb = eps_b(tau)
                        ok = eb is not None and m is not None and ef + eb + D5 <= m
                        per[c] = {"tau": tau, "eps_fix": round(ef, 2), "eps_b": eb, "m": m, "suma": round(ef + (eb if eb is not None else 99) + D5, 2),
                                  "domyka": ok, "boot": b, "ep": ep}
                        if worst is None or tau > worst["tau"]:
                            worst = dict(per[c], komorka=c)
                    # start
                    st_ok, st_worst = True, None
                    for e in E:
                        P, O = e["W"][Wk][tryb]["przerwy"], e["W"][Wk][tryb]["okna"]
                        tau_s = P[0]["dl"]; ms = R_E - D_STOP - P[0]["r_max"]
                        ef = efix(O[0], h, W, v, tryb) if O else float("inf")
                        eb = eps_b(tau_s)
                        s_ok = eb is not None and ef + eb + D5 <= ms
                        if not s_ok:
                            st_ok = False
                        if st_worst is None or tau_s > st_worst["tau"]:
                            st_worst = {"tau": tau_s, "m_start": round(ms, 2), "eps_fix": round(ef, 2) if ef != float("inf") else None,
                                        "eps_b": eb, "domyka": s_ok, "boot": e["boot"], "ep": e["ep"]}
                    n_ok = sum(1 for p in per.values() if p["domyka"])
                    w_ok = worst is not None and worst["domyka"]
                    komb.append({"geometria": cfg, "prog_px": prog, "W": W, "wariant": n_, "tryb": tryb,
                                 "komorki_domyka": n_ok, "komorki": len(per), "najgorsza_orbita": worst, "najgorsza_orbita_domyka": w_ok,
                                 "start_domyka_wszystkie": st_ok, "start_najdluzsza": st_worst,
                                 "dopuszczalna": n_ok >= 24 and w_ok and st_ok, "per_komorka": per})
json.dump({"m_p50": MP50, "delta_D5": D5, "R_E": R_E, "D_STOP": D_STOP, "kombinacje": komb}, open(os.path.join(OUT, "r5p_pila.json"), "w"),
          ensure_ascii=False, indent=1)
dop = [k for k in komb if k["dopuszczalna"]]
print("kombinacji", len(komb), "dopuszczalnych", len(dop))
for k in sorted(komb, key=lambda k: (-k["dopuszczalna"], -k["komorki_domyka"]))[:15]:
    w = k["najgorsza_orbita"] or {}
    print(k["dopuszczalna"], k["geometria"], k["prog_px"], k["W"], k["wariant"], k["tryb"], f"{k['komorki_domyka']}/48",
          "orb:", w.get("komorka"), w.get("tau"), w.get("eps_fix"), w.get("suma"), w.get("m"), "start:", k["start_domyka_wszystkie"], k["start_najdluzsza"]["tau"])
