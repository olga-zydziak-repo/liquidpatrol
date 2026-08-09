"""r03/config.py — config R0.3a (GPS-DENIED, forma A-episode). Zamrożone liczby z ANEKS-4.

Reguła D11 (§3ter/§3quater PRE_R03A): kurczymy WŁASNĄ TRASĘ, koperta R_E NIETYKANA.
    R_route' = R_E − d_stop − ε_cap ;  half-side' = R_route'/√2
Stałe bazowe (R_E, DELTA_MARGIN=d_stop, V_MAX, ALT) importowane z r01/config.py (frozen, NIETKNIĘTY).

ε_cap = 37/4 = 9.25 m  (reguła D10: 1.5×max(ε_pos episode dwufazowy) = 1.5×6.023 → ćwiartka w górę).
  Pomiar: results/R03/recon/B1bis/episode/metrics_episode2.jsonl (5 ważnych lotów; max p_s2=6.023 m).
  A-episode [A4]: ε_pos ≤ ε_cap pod WYMUSZONYM profilem epizodu (flaga→debounce→REFUSE→velocity-descent
  dwufazowy→touchdown). A-plateau bezwarunkowe OBALONE (§3ter). Walidacja w bramce D13c.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import math

from r01.config import (R_E, DELTA_MARGIN, V_MAX, ALT_M, V_E, TICK_HZ, DT)

# --- ε_cap (D10, ZAMROŻONE ANEKS-4) -----------------------------------------
EPS_CAP = float(Fraction(37, 4))        # 9.25 m
EPS_CAP_FR = "37/4"

# --- geometria zredukowanej trasy (D11) -------------------------------------
D_STOP = DELTA_MARGIN                    # 2.85 m (react + brake, R0.1 frozen)
R_ROUTE_P = R_E - D_STOP - EPS_CAP       # 32 − 2.85 − 9.25 = 19.90 m
HALF_P = R_ROUTE_P / math.sqrt(2.0)      # 14.07 m — połowa boku zredukowanego kwadratu
SR_B1P_MIN_HALFSIDE = 3.0 * D_STOP       # 8.55 m — próg degeneracji (SR-B1', §5quater)

# --- admisja event-based (D12) ----------------------------------------------
DEBOUNCE_TICKS = 2                       # 2 ticki @ TICK_HZ = 0.10 s (zwalidowana flaga → REFUSE)
HYST_M_S = 5.0                           # histereza: 5 s ciągłego ¬dead_reckoning do re-ALLOW
POS_REFUSE_BOUND_S = DEBOUNCE_TICKS * DT + DT   # (a) D13: debounce + 1 tick = 0.15 s

# --- akcja bezpieczna: zejście STEROWANE PRĘDKOŚCIĄ, dwufazowe (D5 zrew. §3quater) ---
# AUTO.LAND (position-hold) WYKLUCZONY (flyaway 42 m pod DR). Lista zamknięta komend osłony:
#   {velocity-setpoint (patrol/OBSERVE), velocity-descent (POS_DEGRADED)}.
V_DESC_FAST = 1.5                        # MPC_Z_VEL_MAX_DN (limit VRS PX4) — faza 1 do H_SWITCH
V_DESC_LAND = 0.7                        # MPC_LAND_SPEED — faza 2 do touchdown
H_SWITCH_AGL = 2.0                       # [m] przełączenie faz zejścia
EKF2_HGT_REF_HABITAT = 0                 # Baro (default 1=GPS degraduje pod denialiem, §3quater)


def containment_ok_r03() -> bool:
    """D11 + SR-B1': trasa zredukowana zawiera się w kopercie i nie degeneruje."""
    return (R_ROUTE_P + D_STOP + EPS_CAP) <= R_E + 1e-9 and HALF_P >= SR_B1P_MIN_HALFSIDE


def corner_waypoints_r03():
    """4 narożniki ZREDUKOWANEJ trasy w NED (x=Północ, y=Wschód), z=-ALT. Pętla zamknięta."""
    h = HALF_P
    return [(h, h, -ALT_M), (h, -h, -ALT_M), (-h, -h, -ALT_M), (-h, h, -ALT_M)]


@dataclass(frozen=True)
class ShieldConfigR03:
    r_e: float = R_E                     # koperta NIETYKANA
    eps_cap: float = EPS_CAP
    r_route_p: float = R_ROUTE_P
    half_p: float = HALF_P
    debounce_ticks: int = DEBOUNCE_TICKS
    hyst_m_s: float = HYST_M_S
    dt: float = DT
