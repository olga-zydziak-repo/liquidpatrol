#!/usr/bin/env python3
"""results/TRANSIT_RECON/tools/transit_r3.py — R3 PROMPT_TRANSIT_S0: przestrzeń
choreografii skanu (projekt, BEZ budowy) — wycena rachunkiem na GT.

Dźwignia rozważana WYŁĄCZNIE jako nowy wrapper nad fantom_scan (percepcja/admisja/
profil II b94cdeae/kwarantanna e435ed7e NIETYKALNE — nowy plik, wpis rejestru
additive). Ograniczenia wspólne wszystkich wariantów: slew 60°/s, stare 1.2 s,
dwell 2.0 s (wartości FROZEN akw_scan.py:39-42 — choreografia zmienia WYŁĄCZNIE
sekwencję nagłówków stare, nie reżim ω·dt; admisja w rampie nie istnieje —
dowód smoke S1 AKW: 0/235 przy 3.96°/kl, akw_scan.py:24-25).

OKNO ADMITOWALNE (progi EMPIRYCZNE z kampanii FANTOM S2, pomiar drift_ceiling
na 3267 klatkach fresh 12 epizodów): nos w stare ∧ cel w stożku ±43.45° ∧
dh ∈ [5, 18] m (minimalne dh JAKIEJKOLWIEK realnej klatki fresh = 5.01 m — bliżej
cel za duży dla MTI max_area_frac 0.20 i etykiety central; dalej poza zasięgiem
charakteryzowanym) ∧ dryf w kadrze ≤ 5°/kl (p99 fresh; ENTRY empiryczne do ~6.8)
przez ≥1.0 s ciągłe (precedens fantom_recon r3: MTI warmup + k=3). t_admit_pred =
koniec pierwszego okna. Klasa okna: RADIAL (kąt prędkości celu do −LOS < 25° —
najazd czołowy; admisja MTI przy 5 Hz = rzut monetą, empiria R1: c08_s02 TAK,
c08_s03/s04 NIE) albo CROSS.

Warianty: CH0 (baseline profil II: krok +40° CCW), CH90 (krok +90° CCW),
CH180 (naprzemienny co 180°), CHFAN (wachlarz ±40° rosnąco), CHA_ORACLE
(baza = azymut korytarza nadejścia — GÓRNA GRANICA, polityka nierealizowalna:
brak prioru), CHORB (mikro-orbita r=2/3 m v=0.5/0.75 m/s wokół home + yaw CH0;
d_min ślepego przejścia liczony po siatce 24 faz startowych).

Kalibracja przyrządu: CH0 vs REALNE t_acq kontroli i T6 (kolumna obok).
Pokrycie 360°: najdłuższa przerwa rewizyty azymutu (siatka 5°) w [0, 34] s.
Wyjście: results/TRANSIT_RECON/r3_choreografie.json.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from poscig_recon import Episode, interp, vel_of, _SCEN   # READ-ONLY

OUTD = os.path.join(ROOT, "results", "TRANSIT_RECON")

HALF_CONE = 43.45
DWELL = 2.0
SLEW = 60.0
STARE = 1.2
DH_LO, DH_HI = 5.0, 18.0      # [m] pas admisji — empiryczny (min dh fresh = 5.01)
DRIFT_MAX = 5.0               # [°/kl] p99 dryfu klatek fresh
WIN_S = 1.0                   # [s] ciągłe okno (precedens fantom_recon r3)
HORIZON = 34.0                # [s] horyzont rachunku (t* ~11; zapas na rewizyty)
RADIAL_DEG = 25.0

T6 = ["c08_s03", "c08_s04", "c10_s02", "c11_s02", "c11_s03", "c11_s04"]
CTRL = ["c08_s01", "c08_s02", "c09_s03", "c09_s04", "c10_s01", "c10_s04"]


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def schedule(seq_deg, base=0.0):
    """[(psi, t_od, t_do)] okien stare dla sekwencji nagłówków (deg, względem bazy).
    dwell 2.0 s na bazie (stare), potem rampy 60°/s między kolejnymi nagłówkami."""
    out = [(base, 0.0, DWELL)]
    t = DWELL
    cur = 0.0
    for h in seq_deg:
        ramp = abs(wrap(h - cur)) / SLEW
        t += ramp
        out.append((base + h, t, t + STARE))
        t += STARE
        cur = h
        if t > HORIZON + 5:
            break
    return out


def seq_step(step, n=40):
    return [(i * step) % 360 for i in range(1, n)]


def seq_fan(n=40):
    s = []
    k = 1
    while len(s) < n:
        s.append((40 * k) % 360)
        s.append((-40 * k) % 360)
        k += 1
    return s[:n]


def seq_alt180(n=40):
    s = []
    a = 0
    for i in range(n):
        a = (a + (180 if i % 2 == 0 else 220)) % 360   # 0→180→40→220→80→260…
        s.append(a)
    return s


CHOREO = {
    "CH0_40ccw": lambda base: schedule(seq_step(40), base),
    "CH90_90ccw": lambda base: schedule(seq_step(90), base),
    "CH90_baza45": lambda base: schedule(seq_step(90), base + 45.0),   # stres: korytarze między nagłówkami
    "CH87_minimalny5": lambda base: schedule(seq_step(86.9), base),    # krok = stożek (zero klina, min czas 360°)
    "CH180_naprzemienny": lambda base: schedule(seq_alt180(), base),
    "CHFAN_wachlarz40": lambda base: schedule(seq_fan(), base),
}


def min_360_table():
    """Czas ZAKOŃCZENIA pokrycia stare całego perymetru (koniec ostatniego potrzebnego
    stare + wymóg okna 1.0 s) per krok — rachunek zamknięty w nietykalnych
    (dwell 2.0 + slew 60°/s + stare 1.2 s, stożek 86.9°). Forma zamknięta minimum:
    nowy łuk do pokrycia po dwell = 360−86.9 = 273.1°; t_end(n) = dwell + 273.1/slew
    + n·stare = 6.552 + 1.2·n, min n bez klina = ceil(273.1/86.9) = 4 ⇒ t_end 11.35 s,
    koniec okna 1.0 s najgorszego azymutu = 11.15 s. DEADLINE admisji celu radialnego
    v=1.0: dh≥5 (podłoga empiryczna) ⇒ okno musi SKOŃCZYĆ się ≤ (15−5)/1.0 = 10.0 s."""
    rows = []
    for step in (40, 60, 68.3, 72, 80, 86.9, 90, 120):
        n_extra = math.ceil((360.0 - 2 * HALF_CONE) / step)   # stares poza dwell
        t_end = DWELL + n_extra * (step / SLEW + STARE)
        wedge = step > 2 * HALF_CONE
        rows.append({"step_deg": step, "n_stare_po_dwell": n_extra,
                     "koniec_360_s": round(t_end, 2),
                     "koniec_okna_1s_najgorszego_azymutu_s": round(t_end - STARE + WIN_S, 2),
                     "klin_staly": wedge})
    return {"deadline_dh5_radial_v1_s": 10.0,
            "min_forma_zamknieta": {"t_end_s": 11.35, "koniec_okna_s": 11.15,
                                    "n": 4, "step_opt_deg": 68.3},
            "tabela": rows}


def stare_psi_at(sched, t):
    for psi, a, b in sched:
        if a <= t <= b:
            return psi
    return None


def windows_for(epi, sched, hz, own_of=None, t_hold0=0.0):
    """Okna admitowalne wg progów empirycznych; own_of(t)->[x,y] (domyślnie home)."""
    dt = 1.0 / hz
    need = max(2, int(round(WIN_S * hz)))
    t = t_hold0
    rows = []
    while t <= HORIZON:
        psi = stare_psi_at(sched, t - t_hold0)
        g = interp(epi.intr, epi.t0 + t)
        own = own_of(t) if own_of else (0.0, 0.0)
        dx, dy = g[0] - own[0], g[1] - own[1]
        dh = math.hypot(dx, dy)
        az = math.degrees(math.atan2(dy, dx))
        ok = False
        berr = None
        if psi is not None:
            berr = wrap(az - psi)
            ok = abs(berr) <= HALF_CONE and DH_LO <= dh <= DH_HI
        rows.append({"t": t, "ok": ok, "berr": berr, "az": az, "dh": dh})
        t += dt
    # dryf [°/kl] + runy
    wins = []
    cur = []
    for i, r in enumerate(rows):
        drift = abs(wrap(rows[i]["az"] - rows[i - 1]["az"])) if i else 0.0
        good = r["ok"] and drift <= DRIFT_MAX
        if good:
            cur.append(r)
        else:
            if len(cur) >= need:
                wins.append(cur)
            cur = []
    if len(cur) >= need:
        wins.append(cur)
    out = []
    for w in wins:
        tm = (w[0]["t"] + w[-1]["t"]) / 2
        tv = vel_of(epi.intr, epi.t0 + tm)
        own = own_of(tm) if own_of else (0.0, 0.0)
        g = interp(epi.intr, epi.t0 + tm)
        los = (own[0] - g[0], own[1] - g[1])       # cel→dron
        ang = None
        nv, nl = math.hypot(tv[0], tv[1]), math.hypot(*los)
        if nv > 0.05 and nl > 1e-6:
            c = max(-1, min(1, (tv[0] * los[0] + tv[1] * los[1]) / (nv * nl)))
            ang = math.degrees(math.acos(c))
        out.append({"t_od": round(w[0]["t"], 2), "t_do": round(w[-1]["t"], 2),
                    "n_kl": len(w), "dh_od_do": [round(w[0]["dh"], 1), round(w[-1]["dh"], 1)],
                    "klasa": ("RADIAL" if (ang is not None and ang <= RADIAL_DEG) else "CROSS")})
    return out


def revisit_max_gap(sched):
    """Najdłuższa przerwa pokrycia stare dla azymutu (siatka 5°) w [0, HORIZON]."""
    worst = 0.0
    for azd in range(0, 360, 5):
        covered = []
        for psi, a, b in sched:
            if abs(wrap(azd - psi)) <= HALF_CONE and a < HORIZON:
                covered.append((a, min(b, HORIZON)))
        covered.sort()
        last = 0.0
        gap = 0.0
        for a, b in covered:
            gap = max(gap, a - last)
            last = max(last, b)
        gap = max(gap, HORIZON - last)
        worst = max(worst, gap)
    return round(worst, 1)


def orbit_dmin(epi, r_orb, v_orb, t_dmin_hint):
    """Ślepe przejście vs dron na mikro-orbicie: min_t dist(cel, dron) po 24 fazach."""
    om = v_orb / r_orb
    res = []
    for k in range(24):
        ph0 = k * math.pi / 12
        best = 1e9
        t = 0.0
        while t <= HORIZON:
            g = interp(epi.intr, epi.t0 + t)
            ox = r_orb * math.cos(ph0 + om * t)
            oy = r_orb * math.sin(ph0 + om * t)
            d = math.hypot(g[0] - ox, g[1] - oy)      # poziomo; dz~0-1.6 pomijalne wobec progu 4
            best = min(best, d)
            t += 0.1
        res.append(best)
    res.sort()
    return {"r": r_orb, "v": v_orb, "dmin_fazowo_min": round(res[0], 2),
            "dmin_fazowo_med": round(res[12], 2), "dmin_fazowo_max": round(res[-1], 2),
            "frakcja_faz_dmin_ge_4": round(sum(1 for x in res if x >= 4.0) / 24, 2)}


def main():
    os.makedirs(OUTD, exist_ok=True)
    r1 = json.load(open(os.path.join(OUTD, "r1_anatomia.json")))
    r2 = json.load(open(os.path.join(OUTD, "r2_tstar.json")))
    meta = {e["sid"]: e for e in r1["episodes"]}
    tstar = {e["sid"]: e["t_star_s"] for e in r2["episodes"]}

    out = {"progi": {"dh": [DH_LO, DH_HI], "drift_deg_kl": DRIFT_MAX, "win_s": WIN_S,
                     "stozek": HALF_CONE, "dwell": DWELL, "slew": SLEW, "stare": STARE},
           "min_360": min_360_table(),
           "revisit_max_gap_s": {}, "episodes": {}, "orbit": {}, "podsumowanie": {}}
    print("min_360:", json.dumps(out["min_360"], indent=1))

    for name, mk in CHOREO.items():
        out["revisit_max_gap_s"][name] = revisit_max_gap(mk(0.0))

    conv = {}
    for grp, lst in (("T6", T6), ("CTRL", CTRL)):
        for sid in lst:
            epi = Episode("FANTOM_S2", "V2", sid)
            m = meta[sid]
            hz = m["hz_percep"]
            th0 = m["t_hold0_rel"]
            ts = tstar[sid]
            row = {"group": grp, "hz": hz, "t_hold0": th0, "t_star": ts,
                   "t_acq_real": m["t_acq_s"], "bearing": m["bearing_cell_deg"], "ch": {}}
            variants = dict(CHOREO)
            for name, mk in variants.items():
                wins = windows_for(epi, mk(0.0), hz, t_hold0=th0)
                first = wins[0] if wins else None
                t_admit = first["t_do"] if first else None
                row["ch"][name] = {
                    "okna_do_t_star": [w for w in wins if ts is None or w["t_do"] <= ts],
                    "t_admit_pred": t_admit,
                    "konwersja_geom": bool(t_admit is not None and ts is not None
                                           and t_admit <= ts),
                    "klasa_1_okna": (first["klasa"] if first else None)}
            # CHA_ORACLE: baza = azymut korytarza (górna granica)
            wins = windows_for(epi, schedule(seq_step(40), base=m["bearing_cell_deg"]),
                               hz, t_hold0=th0)
            first = wins[0] if wins else None
            row["ch"]["CHA_ORACLE"] = {
                "okna_do_t_star": [w for w in wins if ts is None or w["t_do"] <= ts],
                "t_admit_pred": (first["t_do"] if first else None),
                "konwersja_geom": bool(first is not None and ts is not None
                                       and first["t_do"] <= ts),
                "klasa_1_okna": (first["klasa"] if first else None)}
            out["episodes"][sid] = row
            for name, ch in row["ch"].items():
                conv.setdefault(name, {"T6_geom": 0, "T6_radial_only": 0, "CTRL_admit": 0,
                                       "CTRL_pozniej_niz_real": 0})
                if grp == "T6" and ch["konwersja_geom"]:
                    conv[name]["T6_geom"] += 1
                    if ch["klasa_1_okna"] == "RADIAL":
                        conv[name]["T6_radial_only"] += 1
                if grp == "CTRL":
                    if ch["t_admit_pred"] is not None:
                        conv[name]["CTRL_admit"] += 1
                        if (m["t_acq_s"] is not None
                                and ch["t_admit_pred"] > m["t_acq_s"] + 2.0):
                            conv[name]["CTRL_pozniej_niz_real"] += 1
            tp = {n: row["ch"][n]["t_admit_pred"] for n in row["ch"]}
            print(f"[R3] {grp} {sid} bear={m['bearing_cell_deg']:3d} hz={hz} t*={ts} "
                  f"t_acq_real={m['t_acq_s']} | " +
                  " ".join(f"{n}={tp[n]}" for n in sorted(tp)))
    out["podsumowanie"] = conv

    # CHORB: geometria d_min mikro-orbity na T6 (pytanie: czy zdejmuje drona z trasy)
    for sid in T6:
        epi = Episode("FANTOM_S2", "V2", sid)
        out["orbit"][sid] = [orbit_dmin(epi, 2.0, 0.5, None),
                             orbit_dmin(epi, 3.0, 0.75, None)]
        print(f"[R3/orb] {sid} " + json.dumps(out["orbit"][sid]))

    json.dump(out, open(os.path.join(OUTD, "r3_choreografie.json"), "w"), indent=1)
    print("revisit_max_gap_s:", out["revisit_max_gap_s"])
    print("podsumowanie:", json.dumps(conv, indent=1))
    print("zapisano r3_choreografie.json")


if __name__ == "__main__":
    main()
