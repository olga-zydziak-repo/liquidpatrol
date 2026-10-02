#!/usr/bin/env python3
"""r03/controllers/liq_controller.py — ramiona kontrolne nogi LIQ (PRE_LIQ §1/§7, PROMPT_LIQ_S1 §4).

Klon kontraktu NetController (set_feed/step/reset/begin_reset — r03/controllers/net_controller.py,
przyrząd zamkniętej nogi NET NIETKNIĘTY): utrata tracka → hover-hold; faza approach/orbit progiem
ENTER_HI; tgt = pos + v·T_LOOKAHEAD (projekcja dla R-G osłony); clip_v w kontrolerze (N1).
Inferencja: GRU21 (stan, reset per epizod) albo MLPk20 (okno k=20, zero-padding) z net/models_liq.

GUARD TOŻSAMOŚCI WAG (wzór SR-2): sha256 net/frozen/<arm>.npz vs FREEZE_SHA_LIQ — rozjazd ⇒
RuntimeError ODMOWA LOTU. Wartości FREEZE_SHA_LIQ = FREEZE_LIQ.md (commit S1, przed lotami).

Rejestracja (SR-9, +2 wpisy addytywne w r03/controllers/__init__.py):
  CONTROLLER=gru    → LiqGru    (wagi net/frozen/gru.npz)
  CONTROLLER=mlp20  → LiqMlp20  (wagi net/frozen/mlp20.npz)
"""
import hashlib
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from bench.features import features
from net import dataset as D
from net.models_liq import GRU21, MLPk20
from r03.controllers.common import clip_v
from r03.controllers.net_controller import T_LOOKAHEAD, TRACK_LOSS_S, ENTER_HI

# FREEZE_LIQ (net/frozen/FREEZE_LIQ.md): sha wag lecących — rozjazd ⇒ odmowa lotu.
FREEZE_SHA_LIQ = {
    "gru": "5ec027555b8fc0bf12007a3dea0fdb5629fc46cdbbd859150b6963c4cdaac383",
    "mlp20": "74b5ae7d041bb776c9352c19f80582ecaea6bb8c429cae6d5e1a89a2ea8a6c8e",
}


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


class _LiqBase:
    ARM = None

    def __init__(self, params=None, orbit_dir="CCW", vmax=3.0, home_ned=(0.0, 0.0, None), **kw):
        self.vmax = float(vmax)
        self.arm = self.ARM
        wpath = os.path.join(_ROOT, "net", "frozen", f"{self.arm}.npz")
        if not os.path.exists(wpath):
            raise RuntimeError(f"[liq_controller] brak wag {wpath} — ODMOWA LOTU")
        got = _sha(wpath)
        if got != FREEZE_SHA_LIQ[self.arm]:
            raise RuntimeError(f"[liq_controller] weights_sha {self.arm} rozjazd z FREEZE_LIQ "
                               f"({got[:16]}≠{FREEZE_SHA_LIQ[self.arm][:16]}) — ODMOWA LOTU (SR-2)")
        self.weights_sha = got
        self.model = (GRU21 if self.arm == "gru" else MLPk20).load(wpath)
        self.mean = self.model.input_mean
        self.std = self.model.input_std
        self._feed = None
        self.reset()

    def reset(self):
        self.phase = "approach"
        self._feed = None
        if self.arm == "gru":
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
        if self.arm == "gru":
            y, self._h, _ = self.model.step_np(xs[None, :], self._h)
        else:
            self._win.pop(0); self._win.append(xs)
            y = self.model.forward(np.concatenate(self._win)[None, :])
        raw = [float(y[0, 0]), float(y[0, 1]), float(y[0, 2])]
        return clip_v(raw, self.vmax)

    def _cmd(self, v, tgt, dist, yaw, phase, extra):
        return {"tgt_ned": (tgt[0], tgt[1], tgt[2]), "v_ned": (v[0], v[1], v[2]), "yaw": yaw,
                "seg_i": 0, "dist": dist, "wps": None, "extra": {"phase": phase, **extra}}

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        own = [float(pos_ned[0]), float(pos_ned[1]), float(pos_ned[2])]
        vel = [float(vel_ned[0]), float(vel_ned[1]), float(vel_ned[2])]
        fd = self._feed
        if fd is None or (not fd.get("track_valid")) or fd.get("track_age_s", 1e9) > TRACK_LOSS_S:
            return self._cmd([0.0, 0.0, 0.0], (own[0], own[1], own[2]), None, 0.0, "hold",
                             {"track_valid": bool(fd and fd.get("track_valid")),
                              "track_age_s": (fd.get("track_age_s") if fd else None), "d": None})
        trk = fd["trk_pos_ned"]
        relx, rely = trk[0] - own[0], trk[1] - own[1]
        d = math.hypot(relx, rely)
        yaw = math.atan2(rely, relx)
        phase = "orbit" if d <= ENTER_HI else "approach"
        v = self._infer(own, vel)
        tgt = (own[0] + v[0] * T_LOOKAHEAD, own[1] + v[1] * T_LOOKAHEAD, own[2] + v[2] * T_LOOKAHEAD)
        return self._cmd(v, tgt, round(d, 3), yaw, phase,
                         {"d": round(d, 3), "track_valid": True,
                          "track_age_s": round(fd["track_age_s"], 3), "arm": self.arm})


class LiqGru(_LiqBase):
    ARM = "gru"


class LiqMlp20(_LiqBase):
    ARM = "mlp20"
