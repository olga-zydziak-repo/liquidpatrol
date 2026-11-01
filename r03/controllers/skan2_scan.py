#!/usr/bin/env python3
"""r03/controllers/skan2_scan.py — profil skanu przeliczony na kadencję 14.7 Hz
(noga SKAN-II „admisja w rampie", PRE_SKAN2 §2, PROMPT_SKAN2_S1 §1, SR-9).

`SkanScan(SetpointSource)`, name="net_skan2": buduje wewnętrzny `FantomScan(**kw)`
(kwarantanna startu K1 i delegat AkwScan NIETKNIĘTE; guard SR-2 sha wag biegnie
w konstruktorach delegatów) i deleguje `set_feed`, `__getattr__` i `step()`.
WYŁĄCZNIE gdy cmd delegata ma `extra.phase == "hold"` podmienia pole `yaw` na własny
profil (nadpisuje profil II delegata w każdym ticku hold, z własnym ψ_last); każda inna
ścieżka zwraca TEN SAM obiekt cmd delegata (pass-through — tożsamość, test T1).
Telemetria kwarantanny `q_*` delegata przechodzi bez zmian; na tickach hold dodane
wyłącznie klucze `s2_dwell_s`, `s2_t_scan`.

Litera profilu (PRE_SKAN2 §2, stałe w pliku, BEZ env): krok 68.3° CCW (yaw atan2
rosnący, jak AkwScan), rampa 60°/s (1.1383 s), stare 0.4 s, cykl 1.5383 s; dwell
1.0 s WYŁĄCZNIE przy pierwszym hold epizodu (po reset()), 2.0 s przy każdym kolejnym
wejściu w hold (okno odzysku REFRESH z PRE_AKW). Wzór offsetu = AkwScan._scan_offset
z własnymi stałymi; profil unwrapped, emisja przez `_wrap_pi` z akw_scan.
reset() ⇒ ψ_last = 0.0, pierwszy hold znowu z dwell 1.0 s.
"""
import math

from r03.controllers.base import SetpointSource
from r03.controllers.akw_scan import _wrap_pi
from r03.controllers.fantom_scan import FantomScan

SKAN2_STEP_DEG = 68.3          # krok [deg], CCW — PRE_SKAN2 §2
SKAN2_SLEW_DPS = 60.0          # rampa kroku [deg/s]
SKAN2_STARE_S = 0.4            # stare po kroku [s]
SKAN2_DWELL_START_S = 1.0      # dwell przy pierwszym hold epizodu [s]
SKAN2_DWELL_LOSS_S = 2.0       # dwell po utracie (każdy kolejny hold) [s]


class SkanScan(SetpointSource):
    name = "net_skan2"

    def __init__(self, **kw):
        self._fan = FantomScan(**kw)
        self.s2_step_deg = SKAN2_STEP_DEG
        self.s2_slew_dps = SKAN2_SLEW_DPS
        self.s2_stare_s = SKAN2_STARE_S
        self.s2_dwell_start_s = SKAN2_DWELL_START_S
        self.s2_dwell_loss_s = SKAN2_DWELL_LOSS_S
        self._step_rad = math.radians(SKAN2_STEP_DEG)
        self._slew = math.radians(SKAN2_SLEW_DPS)
        self._step_t = SKAN2_STEP_DEG / SKAN2_SLEW_DPS        # 1.1383 s
        self._cycle_t = self._step_t + SKAN2_STARE_S           # 1.5383 s
        self.reset()

    # -- delegacja atrybutów spoza kontraktu (q_active, scan_mode, arm, weights_sha …)
    def __getattr__(self, item):
        return getattr(self._fan, item)

    def reset(self):
        self._fan.reset()
        self._hold_t0 = None     # now_s wejścia w bieżący odcinek hold
        self._base_yaw = None    # ψ_last sprzed odcinka hold (baza cyklu, unwrapped)
        self._last_yaw = 0.0     # ψ_last = ostatnio WYEMITOWANY yaw
        self._first_hold = True  # pierwszy hold epizodu ⇒ dwell 1.0 s
        self._dwell = None       # dwell bieżącego odcinka hold

    def set_feed(self, sample):
        self._fan.set_feed(sample)

    def _scan_offset(self, t_scan):
        """Przyrost yaw [rad, unwrapped] po t_scan [s] od końca dwell (wzór AkwScan)."""
        n = int(t_scan // self._cycle_t)
        ph = t_scan - n * self._cycle_t
        in_step = min(ph, self._step_t) * self._slew
        return n * self._step_rad + in_step

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        cmd = self._fan.step(tick, pos_ned, vel_ned, now_s, descending)
        if cmd["extra"].get("phase") != "hold":
            self._hold_t0 = None
            self._last_yaw = cmd["yaw"]
            return cmd
        if self._hold_t0 is None:
            self._hold_t0 = now_s
            self._base_yaw = self._last_yaw
            self._dwell = SKAN2_DWELL_START_S if self._first_hold else SKAN2_DWELL_LOSS_S
            self._first_hold = False
        dt = now_s - self._hold_t0
        if dt <= self._dwell:
            psi = _wrap_pi(self._base_yaw)
            t_scan = 0.0
        else:
            t_scan = dt - self._dwell
            psi = _wrap_pi(self._base_yaw + self._scan_offset(t_scan))
        self._last_yaw = psi
        out = dict(cmd)
        out["yaw"] = psi
        out["extra"] = dict(cmd["extra"])
        out["extra"]["s2_dwell_s"] = self._dwell
        out["extra"]["s2_t_scan"] = round(t_scan, 4)
        return out
