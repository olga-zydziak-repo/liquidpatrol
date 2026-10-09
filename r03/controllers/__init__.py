#!/usr/bin/env python3
"""r03/controllers — pakiet źródeł setpointów (INFRA-3 A1).

`make_controller(name, **kw)` — fabryka z rejestru (dziś: "route" → RouteFollower).
`controller_sha(ctrl)` — sha256 pliku modułu kontrolera (do meta/manifest, weryfikowalny pointer).

Rejestr rozszerza ławka/sieć DOPISANIEM klasy — bez dotykania osłony/pętli (SR-9).
"""
import hashlib
import inspect

from r03.controllers.base import SetpointSource
from r03.controllers.route_follower import RouteFollower
from r03.controllers.orbit_executor import OrbitExecutor
from r03.controllers.net_controller import NetController
from r03.controllers.liq_controller import LiqGru, LiqMlp20
from r03.controllers.akw_scan import AkwScan

_REGISTRY = {
    "route": RouteFollower,
    "orbit": OrbitExecutor,
    "net": NetController,
    "gru": LiqGru,          # LIQ (PRE_LIQ §7, SR-9): kontrola rekurencji, wagi net/frozen/gru.npz
    "mlp20": LiqMlp20,      # LIQ (PRE_LIQ §7, SR-9): kontrola okna k=20, wagi net/frozen/mlp20.npz
    "net_akw": AkwScan,     # AKW (PRE_AKW §2, SR-9): skan yaw w hold, delegat NetController (wagi ncp FROZEN)
}


def make_controller(name, **kw):
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"nieznany CONTROLLER={name!r}; znane={sorted(_REGISTRY)}")
    return cls(**kw)


def controller_sha(ctrl):
    """sha256 pliku modułu, w którym zdefiniowano klasę kontrolera."""
    path = inspect.getfile(type(ctrl))
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
