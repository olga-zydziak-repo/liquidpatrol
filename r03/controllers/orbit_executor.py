#!/usr/bin/env python3
"""r03/controllers/orbit_executor.py — egzekutor podejścia i orbity (SetpointSource, name="orbit").

Prawo D3 (PRE_BENCH): podejście v = V_MAX·wersor(rel) z hamowaniem do wejścia w pasmo; orbita = styczna
v_tan + korekcja radialna k_r·(d−r_orb) obcięta + feedforward k_ff·trk_vel + k_z·(z_orb−z); saturacja
|v| ≤ V_MAX ZAWSZE (common.clip_v). Fazy approach/orbit/reset; reset = powrót do hoveru na home; utrata
tracka > track_loss_s ⇒ hold (hover w miejscu).

Wejścia WYŁĄCZNIE: argumenty `step` + `set_feed(sample)`. Bez losowości, bez GT, bez importów gz.
Wszystko w NED [N,E,D] (z = Down). z_orb_ned = −z_orb_alt.
"""
import math

from r03.controllers.base import SetpointSource
from r03.controllers.common import clip_v, clip_scalar, unit2


class OrbitExecutor(SetpointSource):
    name = "orbit"

    def __init__(self, params, orbit_dir="CCW", vmax=3.0, home_ned=(0.0, 0.0, None)):
        self.p = dict(params)
        self.vmax = float(vmax)
        self.orbit_dir = orbit_dir
        self.r_orb = self.p["r_orb_m"]
        self.band = (self.p["band_lo_m"], self.p["band_hi_m"])
        self.v_tan = self.p["v_tan_ms"]
        self.z_orb_ned = -self.p["z_orb_alt_m"]
        self.home_ned = [home_ned[0], home_ned[1],
                         home_ned[2] if home_ned[2] is not None else -self.p["home_hover_alt_m"]]
        self.k_r = self.p["k_r"]; self.k_ff = self.p["k_ff"]; self.k_z = self.p["k_z"]
        self.brake_gain = self.p["brake_gain"]; self.radial_clip = self.p["radial_clip_ms"]
        self.track_loss_s = self.p["track_loss_s"]; self.enter_hi = self.p["enter_band_hi_m"]
        self._feed = None
        self.phase = "approach"

    def reset(self):
        self.phase = "approach"
        self._feed = None

    def begin_reset(self):
        self.phase = "reset"

    def set_feed(self, sample):
        self._feed = sample

    def _cmd(self, v_ned, tgt_ned, dist, yaw, phase, extra):
        v = clip_v(v_ned, self.vmax)                       # saturacja ZAWSZE
        return {"tgt_ned": (tgt_ned[0], tgt_ned[1], tgt_ned[2]),
                "v_ned": (v[0], v[1], v[2]), "yaw": yaw,
                "seg_i": 0, "dist": dist, "wps": None,
                "extra": {"phase": phase, **extra}}

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        own = [float(pos_ned[0]), float(pos_ned[1]), float(pos_ned[2])]
        fd = self._feed
        # utrata tracka / brak feedu → HOLD (hover w miejscu)
        if fd is None or (not fd.get("track_valid")) or fd.get("track_age_s", 1e9) > self.track_loss_s:
            return self._cmd([0.0, 0.0, 0.0], (own[0], own[1], self.z_orb_ned), 0.0, 0.0, "hold",
                             {"track_valid": bool(fd and fd.get("track_valid")),
                              "track_age_s": (fd.get("track_age_s") if fd else None), "d": None})

        if self.phase == "reset":
            dx, dy = self.home_ned[0] - own[0], self.home_ned[1] - own[1]
            dh = math.hypot(dx, dy)
            spd = clip_scalar(self.brake_gain * dh, 0.0, self.vmax)
            ux, uy = unit2(dx, dy)
            vz = self.k_z * (self.home_ned[2] - own[2])
            return self._cmd([spd * ux, spd * uy, vz], self.home_ned, dh, 0.0, "reset",
                             {"d": round(dh, 3), "track_valid": True})

        trk = fd["trk_pos_ned"]; tvel = fd["trk_vel_ned"]
        relx, rely = trk[0] - own[0], trk[1] - own[1]
        d = math.hypot(relx, rely)
        yaw = math.atan2(rely, relx)                        # twarz ku intruzowi
        # wersory: toward intruder (inward) = rel_h/d; radial_out = -rel_h/d
        inx, iny = (relx / d, rely / d) if d > 1e-6 else (0.0, 0.0)
        outx, outy = -inx, -iny
        # orbit target point (nearest): intruz + r_orb·radial_out
        tgt = (trk[0] + self.r_orb * outx, trk[1] + self.r_orb * outy, self.z_orb_ned)

        if self.phase == "approach":
            if d <= self.enter_hi:
                self.phase = "orbit"
            else:
                spd = clip_scalar(self.brake_gain * (d - self.r_orb), 0.0, self.vmax)
                vz = self.k_z * (self.z_orb_ned - own[2])
                return self._cmd([spd * inx, spd * iny, vz], tgt, d, yaw, "approach",
                                 {"d": round(d, 3), "track_valid": True,
                                  "track_age_s": round(fd["track_age_s"], 3)})

        # ORBIT
        if self.orbit_dir == "CCW":
            tanx, tany = -outy, outx
        else:                                               # CW
            tanx, tany = outy, -outx
        v_tan = [self.v_tan * tanx, self.v_tan * tany]
        radial_err = d - self.r_orb
        v_rad_mag = clip_scalar(self.k_r * radial_err, -self.radial_clip, self.radial_clip)
        v_rad = [v_rad_mag * inx, v_rad_mag * iny]          # >0 gdy d>r_orb → inward
        v_ff = [self.k_ff * tvel[0], self.k_ff * tvel[1]]
        vh = [v_tan[0] + v_rad[0] + v_ff[0], v_tan[1] + v_rad[1] + v_ff[1]]
        vz = self.k_z * (self.z_orb_ned - own[2])
        return self._cmd([vh[0], vh[1], vz], tgt, d, yaw, "orbit",
                         {"d": round(d, 3), "radial_err": round(radial_err, 3), "track_valid": True,
                          "track_age_s": round(fd["track_age_s"], 3)})
