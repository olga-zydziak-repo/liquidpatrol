#!/usr/bin/env python3
"""r03/controllers/akw_scan.py — wrapper skanu akwizycyjnego yaw (noga AKW, PRE_AKW §2, SR-9).

`AkwScan(SetpointSource)`, name="net_akw": buduje wewnętrzny `NetController(**kw)`
(guard SR-2 sha wag NIETKNIĘTY — biegnie w konstruktorze delegata) i deleguje `step()`.
WYŁĄCZNIE gdy cmd delegata ma `extra.phase == "hold"` podmienia pole `yaw` na profil
skanu ψ(t); każda inna ścieżka zwraca cmd delegata BEZ ZMIAN (pass-through bajtowy,
test PRE_AKW §3.1). Jedyna zmiana w systemie = WARTOŚĆ pola yaw w fazie hold (pole
w kontrakcie od zawsze; konwersja rad→deg na granicy mavsdk, bench_flight ANEKS_2A-1 N1).

Profil (FROZEN ANEKS_AKW-1 §5 ŚCIEŻKA II — step-and-stare; reguła prerejestrowana
zastosowana mechanicznie po desku S2a: κ₉₀ kandydaci 0.0/0.0/2.1 ⇒ ω_safe ≤13.53 <14):
jednokierunkowy CCW (konwencja kodu: rotacja (-y,x) w płaszczyźnie (N,E) = yaw atan2
ROSNĄCY, jak orbit_executor CCW). Wejście w hold → dwell 2.0 s trzymania ψ_last (okno
odzysku REFRESH przed odkręceniem nosa; θ_age 3.0 − TRACK_LOSS 1.0) → cykl krokowy:
obrót o 40° rampą 60°/s (0.667 s) → STARE 1.2 s (nos nieruchomy: ω·dt = 0 ⇒ admisja
jak przy nosie nieruchomym — reżim dowiedziony całym programem) → kolejny krok; pełny
przegląd 360° = 9 kroków ≈ 16.8 s. ψ_last = ostatnio WYEMITOWANY yaw z każdego ticku
(track: atan2 delegata; skan: własny profil) — baza cyklu, ciągłość, nigdy powrót do 0;
reakwizycja → utrata ⇒ NOWY dwell i cykl od bieżącego ψ_last. Profil liczony wewnętrznie
UNWRAPPED, emisja wrapowana do (−π, π] (granica MAVSDK w benchu bez zmian). reset()
zeruje stan skanu i ψ_last = 0.0 — pierwszy hold epizodu ⇒ dwell na 0.0, cykl od 0
(spójne z fizyką startu nosem na północ). Zegar profilu = now_s pętli (ten sam, który
delegat dostaje w step). Historia wartości: ω=30°/s ciągły (PRE_AKW §2, sha 2237cc7c)
→ FAIL bramki A smoke S1 (admisja = f(ω·dt), 3.96°/kl w wolnym modzie ⇒ 0/235).

Env `AKW_DWELL_S` WYŁĄCZNIE diagnostyczne: kampania i smoke latają na wartościach
FROZEN (driver bramkowy ODMAWIA przy env AKW_*; odstępstwo flagowane w atrybucie
`scan_frozen` i na stderr). Parametry kroku/stare BEZ env — zmiana wartości = ANEKS.
"""
import math
import os
import sys

from r03.controllers.base import SetpointSource
from r03.controllers.net_controller import NetController

AKW_SCAN_MODE_FROZEN = "step_stare"  # ANEKS_AKW-1 §5 ścieżka II (było: ciągły 30°/s)
AKW_STEP_DEG_FROZEN = 40.0           # krok [deg], CCW (yaw atan2 rosnący) — FROZEN §5
AKW_SLEW_DPS_FROZEN = 60.0           # prędkość rampy kroku [deg/s] — FROZEN §5
AKW_STARE_S_FROZEN = 1.2             # stare po kroku [s] (ω·dt=0) — FROZEN §5
AKW_DWELL_S_FROZEN = 2.0             # dwell po wejściu w hold [s] — FROZEN PRE_AKW §2 (bez zmian)


def _wrap_pi(a):
    """Zawija kąt do (-π, π] (granica mavsdk dostaje degrees(yaw)). atan2 przy sin(a)
    float-owo ujemnym ~0 potrafi zwrócić dokładnie -π (siatka ticków 0.05 s vs krok
    2/3 s profilu II trafia w tę krawędź) — domknięcie do +π egzekwuje kontrakt."""
    y = math.atan2(math.sin(a), math.cos(a))
    return math.pi if y == -math.pi else y


class AkwScan(SetpointSource):
    name = "net_akw"

    def __init__(self, **kw):
        self._net = NetController(**kw)
        self.scan_mode = AKW_SCAN_MODE_FROZEN
        self.step_deg = AKW_STEP_DEG_FROZEN
        self.slew_dps = AKW_SLEW_DPS_FROZEN
        self.stare_s = AKW_STARE_S_FROZEN
        self.dwell_s = float(os.environ.get("AKW_DWELL_S", AKW_DWELL_S_FROZEN))
        self.scan_frozen = (self.dwell_s == AKW_DWELL_S_FROZEN)
        if not self.scan_frozen:
            print(f"[akw_scan] UWAGA: parametry poza FROZEN (dwell={self.dwell_s}) "
                  f"— tryb diagnostyczny, NIE kampania/smoke", file=sys.stderr)
        self._step_rad = math.radians(self.step_deg)
        self._slew = math.radians(self.slew_dps)
        self._step_t = self.step_deg / self.slew_dps          # 0.667 s
        self._cycle_t = self._step_t + self.stare_s           # 1.867 s
        self.reset()

    # -- delegacja atrybutów spoza kontraktu (set_feed, begin_reset, arm, weights_sha, phase …)
    def __getattr__(self, item):
        return getattr(self._net, item)

    def reset(self):
        self._net.reset()
        self._hold_t0 = None     # now_s wejścia w bieżący odcinek hold
        self._base_yaw = None    # ψ_last sprzed odcinka hold (baza cyklu, unwrapped)
        self._last_yaw = 0.0     # ψ_last = ostatnio WYEMITOWANY yaw (PROMPT_AKW_S1 §1)

    def _scan_offset(self, t_scan):
        """Przyrost yaw [rad, unwrapped] cyklu step-and-stare po t_scan [s] od końca dwell:
        n pełnych cykli → n·step; w cyklu: rampa 60°/s przez 0.667 s, potem stare (stała)."""
        n = int(t_scan // self._cycle_t)
        ph = t_scan - n * self._cycle_t
        in_step = min(ph, self._step_t) * self._slew
        return n * self._step_rad + in_step

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        cmd = self._net.step(tick, pos_ned, vel_ned, now_s, descending)
        if cmd["extra"].get("phase") != "hold":
            self._hold_t0 = None
            self._base_yaw = None
            self._last_yaw = cmd["yaw"]
            return cmd
        if self._hold_t0 is None:
            self._hold_t0 = now_s
            self._base_yaw = self._last_yaw
        dt = now_s - self._hold_t0
        if dt <= self.dwell_s:
            psi = _wrap_pi(self._base_yaw)
        else:
            psi = _wrap_pi(self._base_yaw + self._scan_offset(dt - self.dwell_s))
        self._last_yaw = psi
        out = dict(cmd)
        out["yaw"] = psi
        return out
