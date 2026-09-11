"""r01/proofs/fv_mirror.py — LUSTRO 1:1 jądra osłony (noga FV, PRE_FV §4, B1).

Przepisanie 1:1 czterech elementów jądra decyzyjnego ze STANEM ZREIFIKOWANYM jako jawny wektor
(RECON_FV R2: produkcja `r01/shield.py` mutuje atrybuty instancji — jądro deterministyczne, ale
nie-czyste w sygnaturze). Lustro jest CZYSTE (stan wejściem/wyjściem), więc dowodliwe i różnicowalne
wobec produkcji BEZ dotykania pinów (import produkcji dozwolony — PRE_FV §2).

Elementy odwzorowane (źródła 1:1):
  - `_braking_dist`         ← r01/shield.py:97-99
  - `_geofence_violation`   ← r01/shield.py:101-112 (+ `_radial` r01/shield.py:51-52)
  - `_pos_monitor`          ← r01/shield.py:76-94 (stan: pos_bad/pos_healthy/pos_refuse/n_pos_enter)
  - `safe_descend_step`     ← r03/controllers/safe_descend.py:15-49 (produkcja JUŻ czysta — kopia 1:1)

Progi/stałe czytane z configu (nie z pamięci — reguła V5): patrz `shield_thresholds()` / `d5_cfg()`.
Semantykę operacyjną (resety liczników, kolejność porównań, brzegi nierówności) definiuje KOD, nie
ten plik i nie pamięć (PRE_FV §2 „zasada semantyki").
"""
from __future__ import annotations
import math


# ---- _radial + _braking_dist -------------------------------------------------
def _radial(x, y) -> float:
    """1:1 r01/shield.py:51-52."""
    return math.hypot(float(x), float(y))


def braking_dist(vel, v_max, a_brake) -> float:
    """1:1 r01/shield.py:97-99 (`_braking_dist`). vh=min(hypot(vx,vy),v_max); vh²/(2·a_brake)."""
    vh = min(math.hypot(float(vel[0]), float(vel[1])), v_max)
    return (vh * vh) / (2.0 * a_brake)


# ---- _geofence_violation -----------------------------------------------------
def geofence_violation(pos, vel, target, r_e, v_e, v_max, a_brake):
    """1:1 r01/shield.py:101-112. Zwraca (bool, detail) — łańcuchy detail bajtowo jak produkcja.

    Bariera: cel poza R_E LUB pozycja+hamowanie>R_E (poziom), oraz pion |z|>V_E.
    """
    tr = _radial(target[0], target[1])
    if tr > r_e:
        return True, f"cel poza R_E ({tr:.1f}>{r_e:.0f})"
    pr = _radial(pos[0], pos[1])
    if pr + braking_dist(vel, v_max, a_brake) > r_e:
        return True, f"pozycja+hamowanie poza R_E ({pr:.1f}+brake>{r_e:.0f})"
    if abs(float(target[2])) > v_e or abs(float(pos[2])) > v_e:
        return True, f"pion poza V_E (>{v_e:.0f})"
    return False, None


# ---- _pos_monitor (stan zreifikowany) ----------------------------------------
def new_pos_state():
    """Stan monitora pozycji zreifikowany. Odpowiednik atrybutów instancji ustawianych w
    r01/shield.py:reset (:68-71): _pos_bad, _pos_healthy, _pos_refuse, n_pos_enter."""
    return {"pos_bad": 0, "pos_healthy": 0, "pos_refuse": False, "n_pos_enter": 0}


def pos_monitor_step(st, pos_flag, debounce_ticks, hyst_ticks):
    """1:1 r01/shield.py:76-94 (`_pos_monitor`). pos_flag=None ⇒ monitor nieaktywny (bez zmian).
    st mutowany i zwracany (jak safe_descend_step). debounce_ticks/hyst_ticks = progi z produkcji."""
    if pos_flag is None:
        return st
    if pos_flag:
        st["pos_bad"] += 1
        st["pos_healthy"] = 0
        if st["pos_bad"] >= debounce_ticks and not st["pos_refuse"]:
            st["pos_refuse"] = True
            st["n_pos_enter"] += 1
    else:
        st["pos_bad"] = 0
        if st["pos_refuse"]:
            st["pos_healthy"] += 1
            if st["pos_healthy"] >= hyst_ticks:
                st["pos_refuse"] = False
                st["pos_healthy"] = 0
    return st


# ---- safe_descend_step (kopia 1:1 — produkcja już czysta) --------------------
def new_descend_state():
    """1:1 r03/controllers/safe_descend.py:15-17 (`new_state`)."""
    return {"descending": False, "desc_t0": None, "h_switched": False, "td": False}


def safe_descend_step_mirror(st, now, cfg):
    """1:1 r03/controllers/safe_descend.py:20-49 (`safe_descend_step`), monotonic→now (już w produkcji).
    Zwraca (vdesc, events, touchdown, st)."""
    events = []
    if not st["descending"]:
        st["descending"] = True
        st["desc_t0"] = now
        events.append("refuse_pos_land")
    el = now - st["desc_t0"]
    if el < cfg["desc_fast_dur"]:
        vdesc = cfg["v_desc_fast"]
    else:
        if not st["h_switched"]:
            events.append("h_switch")
            st["h_switched"] = True
        vdesc = cfg["v_desc_land"]
    touchdown = False
    if el >= cfg["desc_total"] and not st["td"]:
        events.append("touchdown")
        st["td"] = True
        touchdown = True
    return vdesc, events, touchdown, st


# ---- progi/stałe z configu (jedyne źródło; cyt. plik:linia) ------------------
def shield_thresholds():
    """Progi osłony z PRODUKCJI (nie z pamięci). Wartości odczytane z żywej instancji PatrolShield
    po reset() — dokładnie te, których używa `_pos_monitor` (r01/shield.py:72-74) i `_geofence_violation`
    (przez self.cfg). r_e/v_e/v_max/a_brake/dt z r01/config.py:ShieldConfig (:56-64)."""
    from r01.shield import PatrolShield
    s = PatrolShield()
    s.reset()
    return {
        "r_e": s.cfg.r_e, "v_e": s.cfg.v_e, "v_max": s.cfg.v_max,
        "a_brake": s.cfg.a_brake, "dt": s.cfg.dt,
        "debounce_ticks": s.pos_debounce_ticks,   # r01/shield.py:72 (==2)
        "hyst_ticks": s.pos_hyst_ticks,            # r01/shield.py:73-74 (int(round(5/dt)))
    }


def d5_cfg():
    """Profil D5 jak w PRODUKCJI (bench_flight.py:73-75 == gate_run_r03.py:223-224,278-279).
    Stałe: V_DESC_FAST/V_DESC_LAND/H_SWITCH_AGL (r03/config.py:38-40), ALT_M (r01/config.py:19)."""
    import r03.config as C
    dfd = max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST)
    return {
        "v_desc_fast": C.V_DESC_FAST,
        "v_desc_land": C.V_DESC_LAND,
        "desc_fast_dur": dfd,
        "desc_total": dfd + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5,
    }
