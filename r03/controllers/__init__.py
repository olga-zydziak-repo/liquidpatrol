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

_REGISTRY = {
    "route": RouteFollower,
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
