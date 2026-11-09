#!/usr/bin/env python3
"""results/NADIR_RECON/tools/nadir_r2r5.py — agregat R1, tabela R2, R4(i), R5 PROMPT_NADIR_S0.

Wejścia: r1_pokrycie_raw.json.gz (nadir_r1.py, pełna postawa), opcjonalnie surowy plik NADIR_SAMYAW=1 (kontrola rachunku
CC bez przechyłów — w repo tylko jego agregat), s2_freeze_bf.json (ae19f66c), r4_margin.json.
R5 per kombinacja (s × przesunięcie siatki × bramka detekcji × wariant błędu × tryb):
  komórka domyka się ⇔ każdy jej epizod ma ≥ 1 obserwację ∧ max u(t) po fazach misji (approach/hold/orbit) ≤ m_komórki,
    u(t) = ε_fix(ostatnia obserwacja) + ε_b(τ) + Δ_D5 (nadir_r1.piła); zejścia D5 poza u (Δ_D5 już je wycenia — liczone
    osobno jako pokrycie);
  najgorsza orbita siatki = epizod o największym τ w fazie orbit (τ zaokr. 0.1 s, remis ⇒ największe u w orbicie);
    jego komórka musi się domknąć;
  start: każdy epizod ε_fix(1. obs.) + ε_b(τ_start) + Δ_D5 ≤ R_E − D_STOP − r_max(przed 1. obs.);
  bezterminowość: max τ w fazach misji < 70 s (krzywa ε_b bez ekstrapolacji);
  asocjacja po siatce (tylko CEN5 — bez ID): max e_as < s/2;
  dopuszczalna ⇔ ≥ 24/48 komórek ∧ najgorsza orbita ∧ start ∧ bezterminowość (∧ asocjacja dla CEN5).
Użycie: nadir_r2r5.py <katalog NADIR_RECON> [surowy_samyaw.json]
"""
import gzip, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nadir_r1 as N   # funkcje eps_fix, stałe WAR/F/EPS/D5

ROOT = "/home/olga/projects/liquidpatrol"
OUT = sys.argv[1]
raw = json.load(gzip.open(os.path.join(OUT, "r1_pokrycie_raw.json.gz"), "rt"))
mg = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))
R_E, D_STOP = float(mg["R_E"]), float(mg["D_STOP"])
MCELL = {c: v["m"] for c, v in mg["tabela_scenariuszy"].items()}
EPS, D5 = N.EPS, N.D5
MISJA = ("approach", "hold", "orbit")


def pct(x, p):
    x = sorted(x)
    return round(float(x[min(len(x) - 1, int(p * len(x)))]), 3) if x else None


def eb(t):
    k = int(t)
    return float(EPS[k]) if k < len(EPS) else None


# ---------- R1 ----------
def agreg(K, filtr):
    out = {}
    for cfg, o in K.items():
        if cfg.startswith("_"):
            continue
        res = {}
        grupy = {}
        for key, a in o["fazy"].items():
            kamp, f = key.split("|")
            if not filtr(kamp):
                continue
            for g in (f, "MISJA") if f in MISJA else (f,):
                grupy.setdefault(g, []).append(a)
        for g, L in grupy.items():
            n = sum(a["n"] for a in L)
            prz1 = [x for a in L for x in a.get("przerwy_1", [])]
            prz2 = [x for a in L for x in a.get("przerwy_2", [])]
            rh = [x for a in L for x in a["rh"]]; th = [x for a in L for x in a["theta"]]; px = [x for a in L for x in a.get("px_W1", [])]
            r = {"n_probek": n, "frac_ge1": round(sum(a["n1"] for a in L) / n, 4), "frac_ge2": round(sum(a["n2"] for a in L) / n, 4),
                 "przerwy_1_gt0.25s": {"n": len(prz1), "p50": pct(prz1, .5), "p95": pct(prz1, .95)},
                 "max_przerwa_1": round(max(a.get("max_przerwa_1", 0) for a in L), 3),
                 "przerwy_2_gt0.25s": {"n": len(prz2), "p50": pct(prz2, .5), "p95": pct(prz2, .95)},
                 "max_przerwa_2": round(max(a.get("max_przerwa_2", 0) for a in L), 3),
                 "r_h_najblizszego": {"p50": pct(rh, .5), "p95": pct(rh, .95), "max": max(rh) if rh else None},
                 "kat_padania_deg": {"p50": pct(th, .5), "p95": pct(th, .95), "max": max(th) if th else None}}
            if px:
                r["px_boku"] = {f"W{w:g}": {"p5": round(pct(px, .05) * w, 1), "p50": round(pct(px, .5) * w, 1),
                                            **{f"frac_ge{t}": round(float(np.mean(np.array(px) * w >= t)), 4) for t in (5, 12, 18)}}
                                for w in N.WS}
            res[g] = r
        if filtr("FANTOM_S2") and filtr("KONT_S4"):
            res["profil_wysokosci"] = {b: {"n": p["n"], "frac_ge1": round(p["n1"] / p["n"], 4), "frac_ge2": round(p["n2"] / p["n"], 4)}
                                       for b, p in o["profil_alt"].items()}
        out[cfg] = res
    return out


K = raw["konfiguracje"]
r1 = {"wszystkie": agreg(K, lambda k: True), "FANTOM_S2": agreg(K, lambda k: k == "FANTOM_S2")}
tl = K["_postawa"]
r1["postawa_odchylenie_od_pionu_deg"] = {"boot_p50_median": pct([x["tilt_p50"] for x in tl], .5),
                                         "boot_p95_max": max(x["tilt_p95"] for x in tl), "max": max(x["tilt_max"] for x in tl), "boots": len(tl)}
json.dump(r1, open(os.path.join(OUT, "r1_pokrycie.json"), "w"), ensure_ascii=False, indent=1)
if len(sys.argv) > 2:
    ry = json.load(open(sys.argv[2]))["konfiguracje"]
    json.dump({"opis": "kontrola: postawa zredukowana do samego yaw (NADIR_SAMYAW=1), warunki rachunku CC",
               "wszystkie": agreg(ry, lambda k: True), "FANTOM_S2": agreg(ry, lambda k: k == "FANTOM_S2")},
              open(os.path.join(OUT, "r1_pokrycie_samyaw.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R4(i) ----------
r4 = {}
for s, r in raw["r4_kamera_misji"].items():
    r4[s] = {"frac_znacznik_w_kadrze": round(r["n_kadr"] / r["n"], 4), "frac_w_stozku_centralnym": round(r["n_central"] / r["n"], 4),
             "frac_w_stozku_orbita": round(r["n_central_orbit"] / r["n_orbit"], 4),
             "frac_w_stozku_zasieg_5_18": round(r["n_central_5_18"] / r["n"], 4),
             "zasieg_m": {"p5": pct(r["zasieg"], .05), "p50": pct(r["zasieg"], .5)},
             "depresja_deg_skrot": {"p50": pct(r["dep"], .5), "p95": pct(r["dep"], .95), "max": max(r["dep"])},
             "px_krotszego_boku": {f"W{w:g}": {"p50": round(pct(r["pxw1"], .5) * w, 1), "p95": round(pct(r["pxw1"], .95) * w, 1),
                                               "max": round(max(r["pxw1"]) * w, 1)} for w in N.WS},
             "intruz_do_5deg": {"frac": round(r["hit5"] / r["n_int"], 4), "frac_orbita_wzgl_wszystkich": round(r["hit5_orbit"] / r["n_int"], 4),
                                "frac_w_pasmie_5_18": round(r["hit5_5_18"] / r["n_int"], 5)}}
json.dump(r4, open(os.path.join(OUT, "r4_kamera_misji.json"), "w"), ensure_ascii=False, indent=1)

# ---------- R2 tabela analityczna (dron poziomo; dane z lotu w r5 per kombinacja) ----------
r2 = {"F_px": round(N.F, 2), "psi_zmierz_deg": N.PSI_Z, "warianty": N.WAR, "tabela": [], "para_bez_mnozenia": []}
for alt in (12.0, 8.4):
    for rh in (0, 2, 4, 6, 8, 10, 12, 14):
        D = math.hypot(alt, rh); cth = alt / D; tth = rh / alt
        a = lambda x: np.array([x])
        row = {"alt": alt, "r_h": rh, "theta_deg": round(math.degrees(math.acos(cth)), 1), "px_W1": round(N.F * cth / D, 1)}
        for vn, v in N.WAR.items():
            row[f"{vn}|1"] = round(float(N.eps_fix(v, a(D), a(cth), a(tth), a(rh), a(alt), None, None)[0]), 3)
            for s in (10.0, 15.0, 20.0):
                rp = math.hypot(rh, s); Dp = math.hypot(alt, rp)
                ed = math.hypot(D / cth, Dp / (alt / Dp)) * v["px"] / N.F
                row[f"{vn}|2|L{s:g}"] = round(float(N.eps_fix(v, a(D), a(cth), a(tth), a(rh), a(alt), a(s), a(ed))[0]), 3)
            v0 = dict(v, psi=0.0)
            row[f"{vn}|bez_yaw"] = round(float(N.eps_fix(v0, a(D), a(cth), a(tth), a(rh), a(alt), None, None)[0]), 3)
        r2["tabela"].append(row)
# KOTW-owa formuła pary (przecięcie okręgów zasięgu, ε2 = √(a²+b²+2ab|cosγ|)/sinγ) wobec nadir: przy stromym widoku
# każdy znacznik daje pełną pozycję 2D (rad ≈ lat), więc para nie przecina pierścieni — służy tylko do kursu i skali.
for vn, v in N.WAR.items():
    for alt, rh, s in ((12.0, 6.0, 10.0), (12.0, 6.0, 15.0), (12.0, 10.0, 20.0)):
        D = math.hypot(alt, rh); cth = alt / D; rp = math.hypot(rh, s); Dp = math.hypot(alt, rp)
        a = lambda x: np.array([x])
        ed = math.hypot(D / cth, Dp / (alt / Dp)) * v["px"] / N.F
        e2 = float(N.eps_fix(v, a(D), a(cth), a(rh / alt), a(rh), a(alt), a(s), a(ed))[0])
        e0 = float(N.eps_fix(dict(v, psi=0.0), a(D), a(cth), a(rh / alt), a(rh), a(alt), None, None)[0])
        r2["para_bez_mnozenia"].append({"wariant": vn, "alt": alt, "r_h": rh, "L": s, "eps2": round(e2, 3), "eps1_przy_idealnym_kursie": round(e0, 3),
                                        "stosunek": round(e2 / e0, 3), "dpsi_z_pary_deg": round(math.degrees(math.atan(ed / s)), 3)})

# ---------- R5 ----------
komb = []
for cfg, o in K.items():
    if cfg.startswith("_"):
        continue
    s = float(cfg.split("_")[0][1:])
    E = o["epizody"]
    cells = {}
    for e in E:
        cells.setdefault(e["scenario"], []).append(e)
    for key in E[0]["W"]:
        gn, vn, tryb = key.split("|")
        per = {}
        for c, eps_ in cells.items():
            m = MCELL.get(c)
            us = []
            for e in eps_:
                r = e["W"][key]
                for f in MISJA:
                    if f in r and r[f]["u_max"] is not None:
                        us.append((r[f]["u_max"], f, r[f]["u_tau"], r[f]["u_efix"], e["boot"], e["ep"]))
            brak = any(e["W"][key]["obs_frac"] == 0 for e in eps_)
            umax = max(us) if us else None
            ok = (not brak) and umax is not None and m is not None and umax[0] <= m
            per[c] = {"m": m, "u_max": umax[0] if umax else None, "faza": umax[1] if umax else None, "tau": umax[2] if umax else None,
                      "eps_fix": umax[3] if umax else None, "boot": umax[4] if umax else None, "domyka": ok}
        # najgorsza orbita: największe τ w orbicie; remis (przy nadirze typowo τ ≈ 0 w wielu epizodach) łamany największym u
        orb = [((e["W"][key]["orbit"]["tau_max"] if "orbit" in e["W"][key] and e["W"][key]["orbit"]["tau_max"] is not None else 1e9),
                (e["W"][key]["orbit"]["u_max"] or 0.0) if "orbit" in e["W"][key] else 0.0, i, e) for i, e in enumerate(E)]
        tw, _, _, ew = max(orb, key=lambda x: (round(x[0], 1), x[1], -x[2]))
        worst = {"komorka": ew["scenario"], "boot": ew["boot"], "ep": ew["ep"], "tau_orbit_max": tw if tw < 1e9 else None,
                 "domyka": per[ew["scenario"]]["domyka"], "u_max_komorki": per[ew["scenario"]]["u_max"], "m": per[ew["scenario"]]["m"]}
        st_ok, st_w = True, None
        for e in E:
            r = e["W"][key]
            if r["start_tau"] is None:
                ok_s = False; tau_s = None
            else:
                tau_s = r["start_tau"]; b_ = eb(tau_s)
                ok_s = b_ is not None and r["start_efix"] + b_ + D5 <= R_E - D_STOP - r["start_rmax"]
            st_ok &= ok_s
            if st_w is None or (tau_s if tau_s is not None else 1e9) > (st_w["tau"] if st_w["tau"] is not None else 1e9):
                st_w = {"tau": tau_s, "domyka": ok_s, "boot": e["boot"], "ep": e["ep"]}
        taus = [e["W"][key][f]["tau_max"] for e in E for f in MISJA if f in e["W"][key] and e["W"][key][f]["tau_max"] is not None]
        tmax = max(taus) if taus else None
        bez = tmax is not None and tmax < 70.0
        eas = [e["W"][key]["e_as_max"] for e in E if e["W"][key]["e_as_max"] is not None]
        eas_max = max(eas) if eas else None
        as_ok = eas_max is not None and eas_max < s / 2
        d5 = [e["W"][key]["zejscie_D5"]["tau_max"] for e in E if "zejscie_D5" in e["W"][key] and e["W"][key]["zejscie_D5"]["tau_max"] is not None]
        efx = [e["W"][key]["eps_fix_p50"] for e in E if "eps_fix_p50" in e["W"][key]]
        n_ok = sum(1 for p in per.values() if p["domyka"])
        dop = n_ok >= 24 and worst["domyka"] and st_ok and bez and (as_ok or not gn.startswith("CEN"))
        komb.append({"siatka": cfg, "bramka": gn, "wariant": vn, "tryb": tryb, "komorki_domyka": n_ok, "komorki": len(per),
                     "najgorsza_orbita": worst, "start_domyka_wszystkie": st_ok, "start_najdluzszy": st_w,
                     "tau_max_misja": tmax, "bezterminowosc": bez, "e_as_max": eas_max, "asocjacja_siatka_ok": as_ok,
                     "zejscia_D5_tau_max": max(d5) if d5 else None,
                     "eps_fix_p50_epizodow_med": pct(efx, .5), "obs_frac_med": pct([e["W"][key]["obs_frac"] for e in E], .5),
                     "u_max_siatki": max((p["u_max"] for p in per.values() if p["u_max"] is not None), default=None),
                     "dopuszczalna": dop, "per_komorka": per})
json.dump({"R_E": R_E, "D_STOP": D_STOP, "delta_D5": D5, "kombinacje": komb}, open(os.path.join(OUT, "r5_pila.json"), "w"),
          ensure_ascii=False, indent=1)
json.dump(r2, open(os.path.join(OUT, "r2_poprawka.json"), "w"), ensure_ascii=False, indent=1)
print("kombinacji", len(komb), "dopuszczalnych", sum(k["dopuszczalna"] for k in komb))
