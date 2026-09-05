#!/usr/bin/env python3
"""r03/controllers/net_controller.py — kontroler lotu SIECI (pozycja 4, PROMPT_NET_FLY N-F0).

Ramię z env NET_ARM=ncp|mlp. Ładuje ZAMROŻONE wagi z `net/frozen/<arm>.npz` i LICZY sha przy starcie;
niezgodność z FREEZE_NET ⇒ ODMOWA LOTU (RuntimeError, log przyczyny). Cechy przez `bench.features`
(import). NCP: stan ukryty resetowany na starcie epizodu (reset()). MLP: okno k=5 zero-padding na starcie.
Wyjście: głowa tanh×V_MAX + clip_v (pas i szelki). Utrata tracka >track_loss_s ⇒ hover-hold (jak egzekutor).
ZERO importów gz, zero GT. Pozycja 4 NICZEGO nie trenuje (SR-3).

tgt_ned dla osłony: własna pozycja + v_ned·T_LOOKAHEAD (projekcja intencji prędkościowej — osłona R-G
sprawdza radial(target); egzekutor używał punktu orbity, sieć używa projekcji prędkości, różnica w D0).
"""
import hashlib
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from r03.controllers.base import SetpointSource
from r03.controllers.common import clip_v
from bench.features import features
from net import dataset as D
from net.models import TinyMLP, NCP20

# FREEZE_NET (ANEKS_NET-1 §4 / -2): sha wag lecących — rozjazd ⇒ odmowa lotu.
FREEZE_SHA = {
    "ncp": "0337d5eae1471bb99ef329d939be195a9ea846017045b8ddac22f3d97bc2ae36",
    "mlp": "1d1900235724e938557cf9c614e39935483d51edd75f174cce7c8fb3d72f2270",
}
T_LOOKAHEAD = 1.0            # s — projekcja tgt = pos + v·T (dla R-G osłony)
TRACK_LOSS_S = 1.0          # jak egzekutor (executor_params track_loss_s)
ENTER_HI = 10.0             # próg approach→orbit (jak enter_band_hi_m)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


class NetController(SetpointSource):
    name = "net"

    def __init__(self, params=None, orbit_dir="CCW", vmax=3.0, home_ned=(0.0, 0.0, None), **kw):
        self.vmax = float(vmax)
        self.arm = os.environ.get("NET_ARM", "ncp").lower()
        if self.arm not in ("ncp", "mlp"):
            raise RuntimeError(f"[net_controller] NET_ARM={self.arm!r} nieznane (ncp|mlp)")
        wpath = os.path.join(_ROOT, "net", "frozen", f"{self.arm}.npz")
        if not os.path.exists(wpath):
            raise RuntimeError(f"[net_controller] brak wag {wpath} — ODMOWA LOTU")
        got = _sha(wpath)
        if got != FREEZE_SHA[self.arm]:
            raise RuntimeError(f"[net_controller] weights_sha {self.arm} rozjazd z FREEZE_NET "
                               f"({got[:16]}≠{FREEZE_SHA[self.arm][:16]}) — ODMOWA LOTU (SR-2)")
        self.weights_sha = got
        self.model = (NCP20 if self.arm == "ncp" else TinyMLP).load(wpath)
        self.mean = self.model.input_mean
        self.std = self.model.input_std
        self._feed = None
        self.reset()

    def reset(self):
        self.phase = "approach"
        self._feed = None
        if self.arm == "ncp":
            self._h = np.zeros((1, self.model.H))
        else:
            self._win = [np.zeros(8) for _ in range(self.model.K)]

    def begin_reset(self):
        self.phase = "reset"

    def set_feed(self, sample):
        self._feed = sample

    def _infer(self, own, vel):
        row = {"own_pos_ned": own, "own_vel_ned": vel,
               "trk_pos_ned": self._feed["trk_pos_ned"], "track_age_s": self._feed["track_age_s"],
               "track_valid": self._feed["track_valid"]}
        x = np.array(features(row), dtype=np.float64)
        xs = (D.clip_age(x) - self.mean) / self.std
        if self.arm == "ncp":
            y, self._h, _ = self.model.step_np(xs[None, :], self._h)
            raw = [float(y[0, 0]), float(y[0, 1]), float(y[0, 2])]
        else:
            self._win.pop(0); self._win.append(xs)
            X = np.concatenate(self._win)[None, :]
            y = self.model.forward(X)
            raw = [float(y[0, 0]), float(y[0, 1]), float(y[0, 2])]
        return clip_v(raw, self.vmax)

    def _cmd(self, v, tgt, dist, yaw, phase, extra):
        return {"tgt_ned": (tgt[0], tgt[1], tgt[2]), "v_ned": (v[0], v[1], v[2]), "yaw": yaw,
                "seg_i": 0, "dist": dist, "wps": None, "extra": {"phase": phase, **extra}}

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        own = [float(pos_ned[0]), float(pos_ned[1]), float(pos_ned[2])]
        vel = [float(vel_ned[0]), float(vel_ned[1]), float(vel_ned[2])]
        fd = self._feed
        # utrata tracka → hover-hold (jak egzekutor)
        if fd is None or (not fd.get("track_valid")) or fd.get("track_age_s", 1e9) > TRACK_LOSS_S:
            return self._cmd([0.0, 0.0, 0.0], (own[0], own[1], own[2]), None, 0.0, "hold",
                             {"track_valid": bool(fd and fd.get("track_valid")),
                              "track_age_s": (fd.get("track_age_s") if fd else None), "d": None})
        trk = fd["trk_pos_ned"]
        relx, rely = trk[0] - own[0], trk[1] - own[1]
        d = math.hypot(relx, rely)
        yaw = math.atan2(rely, relx)                         # twarz ku intruzowi (kosmetyka, jak egzekutor)
        phase = "orbit" if d <= ENTER_HI else "approach"
        v = self._infer(own, vel)
        tgt = (own[0] + v[0] * T_LOOKAHEAD, own[1] + v[1] * T_LOOKAHEAD, own[2] + v[2] * T_LOOKAHEAD)
        return self._cmd(v, tgt, round(d, 3), yaw, phase,
                         {"d": round(d, 3), "track_valid": True,
                          "track_age_s": round(fd["track_age_s"], 3), "arm": self.arm})
