"""r01/config.py — SCENTRALIZOWANY config R0.1 (jedno źródło prawdy).

A2 (aneks): obwiednia osłony i geometria misji w JEDNYM miejscu — admisja i osłona
nie mogą się rozjechać (rozbieżność portu z LiquidSight, gdzie geo_lim był zaszyty 2×).
Wszystkie liczby = nowy habitat PX4 (NIE przeniesione z LiquidSight). Ratyfikowane PRE_R01
z aneksami A1–A4 (commit b0c793b).

Nierówność zawierania (A2, §5/§8 PRE_R01):
    R_route + Δ ≤ R_E ≤ R_GF - zapas
    Δ = v_max·t_react + v_max²/(2·a_brake)
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math

# --- Geometria misji (perymetr) ---------------------------------------------
BOX_SIDE_M = 40.0                 # bok kwadratu perymetru (środek w Home)
HALF = BOX_SIDE_M / 2.0           # 20 m — narożniki w (±20, ±20)
ALT_M = 10.0                      # wysokość patrolu AGL (NED z = -ALT)
CRUISE_V = 3.0                    # prędkość przelotu [m/s]
R_ROUTE = math.hypot(HALF, HALF)  # 28.284 m — maks. promień trasy od Home (narożnik)

# --- Założenia marginesu reakcji (A2 — margines WYLICZONY, nie z ręki) -------
V_MAX = 3.0                       # clamp prędkości poziomej [m/s]
T_REACT_S = 0.20                  # tick 50 ms + aktywacja ≤125 ms (zmierzone recon R1)
A_BRAKE = 2.0                     # [m/s²] konserwatywne; ZMIERZONE 2.65 (brake_test) ≥ 2.0 → zwalidowane
DELTA_MARGIN = V_MAX * T_REACT_S + (V_MAX ** 2) / (2.0 * A_BRAKE)   # 2.85 m

# --- Obwiednia osłony R_E (z nierówności zawierania) -------------------------
R_E = 32.0                        # ≥ R_ROUTE + DELTA_MARGIN = 31.13 ; z zapasem
V_E = 20.0                        # obwiednia pionowa osłony [m]

# --- Natywny geofence PX4 NA ZEWNĄTRZ (A3) ----------------------------------
GF_BUFFER = 5.0
GF_MAX_HOR_DIST = R_E + GF_BUFFER  # 37 m
GF_MAX_VER_DIST = V_E + GF_BUFFER  # 25 m
GF_ACTION = 2                      # 2=Hold (v1.16); alt 3=Return

# --- Tick osłony / strumień -------------------------------------------------
TICK_HZ = 20.0
DT = 1.0 / TICK_HZ                 # 0.05 s
COM_OF_LOSS_T = 1.0               # [s] próg utraty offboard. UWAGA prowieniencja przyrządu (R0.2 §III):
                                  # R0.1 S4 reakcja 1.234 s I ~1.03 s mierzone MAVSDK flight_mode (HEARTBEAT
                                  # ~1 Hz, lag 0–1 s). Precyzyjnie (NavStatusSub/XRCE, R0.2 G5 stream=
                                  # ekwiwalent S4): reakcja utraty transportu = 1.383 s. Okno 0.9–1.5 s
                                  # skalibrowane na laggy kanale — trafne przypadkiem (próbka R0.1 miała mały lag).

# --- Świeżość komend --------------------------------------------------------
STALE_CMD_S = 2.0                 # komenda starsza => REFUSE(STALE_CMD)

# --- HMAC (admisja) ---------------------------------------------------------
# Placeholder klucza R0.1 (nie sekret produkcyjny — mechanizm i odtwarzalność).
HMAC_KEY = b"liquidpatrol-r01-key-v1"


@dataclass(frozen=True)
class ShieldConfig:
    r_e: float = R_E
    v_e: float = V_E
    a_brake: float = A_BRAKE
    v_max: float = V_MAX
    dt: float = DT
    stale_cmd_s: float = STALE_CMD_S
    delta_margin: float = DELTA_MARGIN

    def containment_ok(self, r_route: float = R_ROUTE) -> bool:
        """A2: sprawdza domknięcie nierówności zawierania trasa+margines ⊂ obwiednia."""
        return (r_route + self.delta_margin) <= self.r_e and self.r_e + GF_BUFFER <= GF_MAX_HOR_DIST


def corner_waypoints():
    """4 narożniki perymetru w NED (x=Północ, y=Wschód), z=-ALT. Pętla zamknięta."""
    return [(HALF, HALF, -ALT_M), (HALF, -HALF, -ALT_M),
            (-HALF, -HALF, -ALT_M), (-HALF, HALF, -ALT_M)]
