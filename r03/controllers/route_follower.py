#!/usr/bin/env python3
"""r03/controllers/route_follower.py — JEDYNY dziś istniejący kontroler (INFRA-3 A1).

Odtwarza DOKŁADNIE (bit-w-bit) blok setpointów wypięty z `gate_run_r03` (baza 3065b8b, linie 225–230
+ 291). Kolejność operacji zachowana wprost:

    wp = wps[seg_i % len(wps)]            # STARY wp (przed inkrementem)
    dx, dy = wp - pos ; dist = hypot      # wektor/odległość do STAREGO wp
    if dist < wp_reach and not descending: seg_i += 1   # inkrement PO policzeniu dx/dy/dist/tgt
    tgt = (wp[0], wp[1], -alt)            # setpoint pozycji ze STAREGO wp
    v_ned = vmax·(dx,dy)/dist  (0,0 gdy dist ≤ 1e-3)    # setpoint prędkości ze STAREGO wp

Zwracane `seg_i` = PO inkremencie (tak czyta go trigger K1: `_cur = wps[seg_i]`; trigger S4: `seg_i >= 1`).
`tgt`/`v_ned`/`dist` liczone ze STAREGO wp. ŻADNYCH poprawek tej logiki (A1.1: jeśli błąd — nota, nie fix).
"""
import math

from r03.controllers.base import SetpointSource


class RouteFollower(SetpointSource):
    name = "route"

    def __init__(self, wps, vmax, alt, wp_reach_m=1.0):
        self.wps = list(wps)
        self.vmax = vmax
        self.alt = alt
        self.wp_reach_m = wp_reach_m
        self.seg_i = 0

    def reset(self) -> None:
        self.seg_i = 0

    def step(self, tick, pos_ned, vel_ned, now_s, descending) -> dict:
        wps = self.wps
        wp = wps[self.seg_i % len(wps)]
        dx, dy = wp[0] - pos_ned[0], wp[1] - pos_ned[1]
        dist = math.hypot(dx, dy)
        if dist < self.wp_reach_m and not descending:
            self.seg_i += 1
        tgt = (wp[0], wp[1], -self.alt)
        vn, ve = (self.vmax * dx / dist, self.vmax * dy / dist) if dist > 1e-3 else (0.0, 0.0)
        return {"tgt_ned": tgt, "v_ned": (vn, ve, 0.0), "yaw": 0.0,
                "seg_i": self.seg_i, "dist": dist, "wps": wps, "extra": {}}
