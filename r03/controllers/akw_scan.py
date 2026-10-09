#!/usr/bin/env python3
"""r03/controllers/akw_scan.py — wrapper skanu akwizycyjnego yaw (noga AKW, PRE_AKW §2, SR-9).

`AkwScan(SetpointSource)`, name="net_akw": buduje wewnętrzny `NetController(**kw)`
(guard SR-2 sha wag NIETKNIĘTY — biegnie w konstruktorze delegata) i deleguje `step()`.
WYŁĄCZNIE gdy cmd delegata ma `extra.phase == "hold"` podmienia pole `yaw` na profil
skanu ψ(t); każda inna ścieżka zwraca cmd delegata BEZ ZMIAN (pass-through bajtowy,
test PRE_AKW §3.1). Jedyna zmiana w systemie = WARTOŚĆ pola yaw w fazie hold (pole
w kontrakcie od zawsze; konwersja rad→deg na granicy mavsdk, bench_flight ANEKS_2A-1 N1).

Profil (FROZEN PRE_AKW §2, doprecyzowanie wiążące ψ_last z PROMPT_AKW_S1 §1): ciągły,
jednokierunkowy CCW (konwencja kodu: rotacja (-y,x) w płaszczyźnie (N,E) = yaw atan2
ROSNĄCY, jak orbit_executor CCW), ω = 30°/s. Wrapper zapamiętuje ψ_last = ostatnio
WYEMITOWANY yaw z każdego ticku (track: atan2 delegata; skan: własna rampa); wejście
w hold → dwell 2.0 s trzymania ψ_last (okno odzysku REFRESH przed odkręceniem nosa;
θ_age 3.0 − TRACK_LOSS 1.0) → rampa ψ(t) = ψ_last + ω·t_skanu — ciągłość, nigdy powrót
do 0. Rampa liczona wewnętrznie UNWRAPPED, emisja wrapowana do (−π, π] (granica MAVSDK
w benchu bez zmian). reset() zeruje stan skanu i ψ_last = 0.0 — pierwszy hold epizodu
⇒ dwell na 0.0, rampa od 0 (spójne z fizyką startu nosem na północ). Zegar profilu =
now_s pętli (ten sam, który delegat dostaje w step).

Env `AKW_SCAN_DPS` / `AKW_DWELL_S` WYŁĄCZNIE diagnostyczne: kampania i smoke latają
na wartościach FROZEN (driver ich nie ustawia; odstępstwo od FROZEN jest flagowane
w atrybucie `scan_frozen` i na stderr). Zmiana wartości = ANEKS, nie env.
"""
import math
import os
import sys

from r03.controllers.base import SetpointSource
from r03.controllers.net_controller import NetController

AKW_SCAN_DPS_FROZEN = 30.0   # ω skanu [deg/s], CCW (yaw atan2 rosnący) — FROZEN PRE_AKW §2
AKW_DWELL_S_FROZEN = 2.0     # dwell po wejściu w hold [s] — FROZEN PRE_AKW §2


def _wrap_pi(a):
    """Zawija kąt do (-π, π] (granica mavsdk dostaje degrees(yaw))."""
    return math.atan2(math.sin(a), math.cos(a))


class AkwScan(SetpointSource):
    name = "net_akw"

    def __init__(self, **kw):
        self._net = NetController(**kw)
        self.scan_dps = float(os.environ.get("AKW_SCAN_DPS", AKW_SCAN_DPS_FROZEN))
        self.dwell_s = float(os.environ.get("AKW_DWELL_S", AKW_DWELL_S_FROZEN))
        self.scan_frozen = (self.scan_dps == AKW_SCAN_DPS_FROZEN
                            and self.dwell_s == AKW_DWELL_S_FROZEN)
        if not self.scan_frozen:
            print(f"[akw_scan] UWAGA: parametry poza FROZEN (dps={self.scan_dps}, "
                  f"dwell={self.dwell_s}) — tryb diagnostyczny, NIE kampania/smoke",
                  file=sys.stderr)
        self._omega = math.radians(self.scan_dps)
        self.reset()

    # -- delegacja atrybutów spoza kontraktu (set_feed, begin_reset, arm, weights_sha, phase …)
    def __getattr__(self, item):
        return getattr(self._net, item)

    def reset(self):
        self._net.reset()
        self._hold_t0 = None     # now_s wejścia w bieżący odcinek hold
        self._base_yaw = None    # ψ_last sprzed odcinka hold (baza rampy, unwrapped)
        self._last_yaw = 0.0     # ψ_last = ostatnio WYEMITOWANY yaw (PROMPT_AKW_S1 §1)

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
            psi = _wrap_pi(self._base_yaw + self._omega * (dt - self.dwell_s))
        self._last_yaw = psi
        out = dict(cmd)
        out["yaw"] = psi
        return out
