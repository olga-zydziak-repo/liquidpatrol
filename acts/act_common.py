#!/usr/bin/env python3
"""acts/act_common.py — DEMO-B B4 (PROMPT_D_BUILD_4 §1): wspólny rdzeń runnerów per-akt (testowalny).

Zawiera CZĘŚCI DETERMINISTYCZNE (bez ROS/SITL): trajektoria intruza f(sim_t) ze spec, budowa
manifestu (hashe z plików), assert A4 (`token_gated=True`). Runnery per-akt (`run_A1/A2/A3.py`)
wstrzykują to w Runner z gate_run_r02/r03. Orkiestrator wieloaktowy OUT (A3-aneks): per-akt.

Konwencja ramki: intruz NED (x,y,z_down) — zgodna z `gt_intruder_fn` w gate_run_r02 (np. (7,0,-11.5)).
Live SITL teleportuje ten sam NED przez set_pose (mechanizm MODEL, zgodny z charakteryzacją REGATE).
"""
from __future__ import annotations
import hashlib
import math
import os

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
CERTS = os.path.join(ROOT, "r01", "proofs", "certs")


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_spec(act):
    return yaml.safe_load(open(os.path.join(_HERE, f"{act}_spec.yaml")))


def assert_token_gated(runner):
    """A4 (ANEKS_D1/D2): akty biegną WYŁĄCZNIE z token_gated=True. Start z False ⇒ twardy błąd."""
    if not getattr(runner, "token_gated", False):
        raise RuntimeError("A4 VIOLATION: runner aktu wystartował z token_gated=False (wymagane True)")


def _lerp(a, b, u):
    return [a[i] + (b[i] - a[i]) * u for i in range(3)]


def _to_ned(xyz_enu):
    """intruder_*_enu (z-up) → NED (z-down). x,y konwencji świata; dla dead-ahead (y=0) bez obrotu."""
    return [float(xyz_enu[0]), float(xyz_enu[1]), -float(xyz_enu[2])]


def intruder_ned_fn(spec):
    """Zwraca fn(sim_t)->[x,y,z] NED z faz spec (A1/A2). None gdy intruz poza sceną (parking niski
    NIE jest None — jest widoczny w kadrze filmowym, ale poza kopertą detekcji). A3: intruz absent → None."""
    if spec.get("intruder") == "absent":
        return lambda t: None
    g = spec["geometry"]; tl = spec["timeline_s"]
    ring = _to_ned(g["intruder_ring_enu"])
    osc = float(g.get("intruder_lateral_osc_m", 1.0))
    park = _to_ned(g.get("intruder_parking_enu", [7.0, 0.0, 3.0]))
    far = _to_ned(g["intruder_far_enu"]) if "intruder_far_enu" in g else None

    def ring_with_osc(t):
        y = osc * math.sin(2 * math.pi * 0.3 * t)
        return [ring[0], ring[1] + y, ring[2]]

    def fn(t):
        # A1: park → approach → ring_hold → park
        appr = tl.get("intruder_approach"); hold = tl.get("intruder_ring_hold") or tl.get("ep0_ring_hold")
        if appr and hold:
            if t < appr[0]:
                return park
            if appr[0] <= t < appr[1]:
                return _lerp(park, ring, (t - appr[0]) / max(appr[1] - appr[0], 1e-6))
        # A2: fazy leave/return/ep1
        leave = tl.get("intruder_leave"); ret = tl.get("intruder_return"); ep1 = tl.get("ep1_ring_hold")
        if leave and far is not None:
            ep0 = tl.get("ep0_ring_hold")
            if ep0 and ep0[0] <= t < ep0[1]:
                return ring_with_osc(t)
            if leave[0] <= t < ret[0] if ret else False:
                return far
            if ret and ret[0] <= t < ret[1]:
                return _lerp(far, ring, (t - ret[0]) / max(ret[1] - ret[0], 1e-6))
            if ep1 and ep1[0] <= t <= ep1[1]:
                return ring_with_osc(t)
            if ep1 and t > ep1[1]:
                return park
        # A1 ring hold
        if hold and hold[0] <= t <= hold[1]:
            return ring_with_osc(t)
        if hold and t > hold[1]:
            return park
        return park
    return fn


def build_manifest(act, world_sdf, head_sha, *, token_gated, contention, seed=None, trace_schema_v=2,
                   aneks_h=None):
    """Manifest per akt (§1). Hashe świata/spec/certów CZYTANE Z PLIKÓW (nie wpisane)."""
    spec_path = os.path.join(_HERE, f"{act}_spec.yaml")
    world_hash = sha256_file(world_sdf) if os.path.exists(world_sdf) else None
    certs = {}
    for c in ("P1", "P4", "P5"):
        p = os.path.join(CERTS, f"{c}.json")
        if os.path.exists(p):
            import json
            certs[c] = json.load(open(p))["model_sha256"][:16]
    return {"act": act, "head": head_sha, "world_sdf": world_sdf, "world_hash": world_hash,
            "spec": f"acts/{act}_spec.yaml", "spec_hash": sha256_file(spec_path),
            "certs": certs, "token_gated": bool(token_gated), "contention": contention,
            "seed": seed, "trace_schema_v": trace_schema_v, "aneks_h": aneks_h or {}}


def grant_delay_s(spec, default=3.0):
    """Opóźnienie grantu po ENTRY (beat operatora) z triggera spec 'on_entry + X'."""
    for b in spec.get("operator_beats", []):
        trig = str(b.get("trigger", ""))
        if "on_entry" in trig and "+" in trig:
            try:
                return float(trig.split("+")[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
    return default
