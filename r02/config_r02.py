"""r02/config_r02.py — SCENTRALIZOWANY config R0.2 (jedno źródło prawdy, wzorzec A2).

Zasada A2 (jedno źródło): współdzielona OBWIEDNIA/DYNAMIKA (v_max, R_E, a_brake, t_react,
V_E, tick) NIE jest tu duplikowana — importowana z `r01.config`. OBSERVE respektuje te same
wartości co patrol (R02-A3). Tu żyją WYŁĄCZNIE nowe stałe R0.2: kanał celu i tryb OBSERVE.

Stałe habitatu (θ_age, D_safe, L_deliver, T_ack, ε_FP, f_fov, move_thr) — **[PROWIZORYCZNE,
związane z pomiarem w bramce] wg R02-A4**: albo pomiar habitatu (histogram age-at-ENTRY / luk
detekcji na żywym mono 320×240), albo jawnie prowizoryczne. Reguły wyboru zamrożone w PRE_R02 §2.3.
Liczby NIE kopiowane z G2 (G2 = prowieniencja SEMANTYKI, nie liczby; „liczby się nie przenoszą", A2).
Prowizoryczne wartości = punkt startowy kalibracji (r02/calibrate_channel.py), zamrożenie przed bramką.

BEZ conf w kanale (R02-A1/D1). conf żyje wyłącznie w telemetrii/logach detektora, nigdy w kanale.
"""
from __future__ import annotations
from dataclasses import dataclass

# --- Współdzielone z R0.1 (A2: import, NIE duplikacja) -----------------------
from r01.config import V_MAX, R_E, V_E, A_BRAKE, T_REACT_S, TICK_HZ, DT, ALT_M  # noqa: F401

# --- Detektor / strumień (B0 potwierdzone) ----------------------------------
DET_HZ = 1.0                      # kadencja detektora (B0: p95 13–22 ms ≪ tick 1 s, ogromny zapas)
DET_DT = 1.0 / DET_HZ             # 1.0 s — okres między klatkami detektora
IMG_W, IMG_H = 320, 240          # mono widzialna (RAPORT_R01 §6; < sufit mostu 256 KB)

# --- ENTRY strukturalny (R1-B, 0ter — ZAMROŻONE) ----------------------------
ENTRY_K = 3                       # k=3 kolejne klatki @1 Hz (≈3 s); rewizja tylko pomiarem G1/G2
# move_thr: maks. ruch środka boxa (znormalizowany) między klatkami serii k, by uznać „spójną
# lokalizację". [PROWIZORYCZNE/A4] — do kalibracji z rozkładu przesunięć intruza @1 Hz w FOV.
ENTRY_MOVE_THR = 0.15             # 15% przekątnej kadru na klatkę (intruz v≈3 m/s, 1 Hz)
# edge-margin (RE-FREEZE 0ter, Krok 2/C — WYPROWADZONE z chmur charakteryzacji, A1-preserving):
#   kandydat ENTRY musi być CENTRALNY: edge_dist = min(cx,1-cx,cy,1-cy) ≥ margin. Derywacja:
#   sygnał operacyjny centralny (edge≈0.38, sweep 5-9 m); szum 57% przy krawędzi (edge<0.10).
#   Odrzuca 57% szumu bez conf. UWAGA: sam NIE domyka ε_FP=0 — szum CENTRALNY (edge≥0.10) sięga
#   conf 0.158 i persistuje do 7 klatek (RAPORT_G_R02 §3b). conf-floor = Krok 2b (rewizja A1/D1).
ENTRY_EDGE_MARGIN = 0.10         # geometryczny (NIE conf) — zachowuje A1

# --- Kanał ZOH-age (semantyka §2.3 — [PROWIZORYCZNE/A4]) ---------------------
# L_deliver: latencja dostarczenia detekcji do kanału (kamera→most→detektor→kanał). Podłoga age.
#   B0 zmierzył inferencję (p95 ≤22 ms); L_deliver = E2E (transport+inferencja) — pomiar R3/bramka.
L_DELIVER_S = 0.10                # 100 ms prowizorycznie (transport BEST_EFFORT + inferencja)
# θ_age: sufit wieku — age_s>θ_age ⇒ cel wygasły ⇒ wyjście z OBSERVE. Reguła wyboru (PRE §2.3):
#   P95 naturalnych luk detekcji na żywym strumieniu. [PROWIZORYCZNE/A4] — kalibracja przed bramką.
THETA_AGE_S = 3.0                 # 3 s prowizorycznie (≈3 ticki detektora @1 Hz zmostkowane ZOH)

# --- OBSERVE (R4, §2.4 — [PROWIZORYCZNE/A4]) --------------------------------
# D_safe: dystans bezpieczny dron↔intruz w OBSERVE (bez zbliżania). Reguła: z FOV + margines.
D_SAFE_M = 8.0                    # 8 m prowizorycznie (>> obwiednia intruza; do ustalenia z FOV)
# T_ack: dopuszczalny czas od wejścia intruza w FOV do ENTRY (G2). = k·DET_DT + L_deliver + margines.
T_ACK_S = ENTRY_K * DET_DT + L_DELIVER_S + 1.0   # ≈4.1 s (k=3 klatki + dostawa + margines)
# f_fov: min. udział klatek z celem w FOV podczas OBSERVE (G2 PASS). [PROWIZORYCZNE/A4].
F_FOV = 0.8                       # ≥80% klatek w-polu
# ε_FP: dopuszczalne fałszywe ENTRY na pustej scenie [zdarzenia/min] (G1). Cel 0.
EPS_FP_PER_MIN = 0.0              # 0 fałszywych locków na pustej scenie (cel; G1 mierzy jawnie)

# --- Estymata celu w NED (bearing-only, BEZ rdzenia uczonego — R-DIV-3) ------
# Rzut kierunku z (cx,cy) na stałą wysokość intruza + pierścień D_safe.
# ZNALEZISKO R3 (harness): bearing-only rzut wymaga PARALAKSY PIONOWEJ — gdy dron i intruz na tej
# samej wysokości, wiązka jest pozioma i nie przecina płaszczyzny intruza (brak zasięgu → estymata
# fantomowa). PRE §2.4 „rzut na stałą wysokość intruza" ZAKŁADA separację. Habitat: patrol z=ALT_M
# (10 m), intruz operuje NIŻEJ (realistyczne anti-UAV — dron patroluje wyżej, obserwuje w dół).
INTRUDER_ALT_M = 6.0             # intruz 4 m poniżej patrolu (paralaksa dla bearing-only); driver --z 6

# Rejestr stałych [A4] do zamrożenia (raport kalibracji wypełnia „źródło"/„zmierzone").
A4_HABITAT_CONSTS = (
    "THETA_AGE_S", "D_SAFE_M", "L_DELIVER_S", "T_ACK_S", "F_FOV", "EPS_FP_PER_MIN", "ENTRY_MOVE_THR",
)


@dataclass(frozen=True)
class ChannelConfig:
    """Config kanału ZOH-age (5-dim, BEZ conf). Współdzieli DT z osłoną."""
    entry_k: int = ENTRY_K
    entry_move_thr: float = ENTRY_MOVE_THR
    entry_edge_margin: float = ENTRY_EDGE_MARGIN   # Krok 2/C: kandydat ENTRY musi być centralny
    l_deliver_s: float = L_DELIVER_S
    theta_age_s: float = THETA_AGE_S
    det_dt: float = DET_DT

    def sane(self) -> bool:
        """Higiena: k≥2 (streak ma sens), podłoga<sufit, próg ruchu w [0,1], margin w [0,0.5)."""
        return (self.entry_k >= 2 and 0.0 < self.l_deliver_s < self.theta_age_s
                and 0.0 < self.entry_move_thr <= 1.0 and 0.0 <= self.entry_edge_margin < 0.5)
