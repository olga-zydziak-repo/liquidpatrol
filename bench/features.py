#!/usr/bin/env python3
"""bench/features.py — kanoniczny wektor cech lotu (ANEKS_BENCH-0 P1).

8 wymiarów, BEZ prędkości intruza:
  [rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, track_age_s, track_valid]
rel = trk_pos_ned − own_pos_ned. JEDNA funkcja używana i w locie (egzekutor/logger) i w treningu —
zero rozjazdu train/flight. `trk_vel_ned` NIE jest cechą (zostaje w demo.jsonl do analizy).

Wejście: dict (wiersz demo / stan) LUB obiekt z atrybutami. Wymagane pola/atrybuty:
  own_pos_ned[3], own_vel_ned[3], trk_pos_ned[3], track_age_s, track_valid.
"""

FEATURE_NAMES = ("rel_x", "rel_y", "rel_z", "own_vn", "own_ve", "own_vd", "track_age_s", "track_valid")


def _get(src, key):
    if isinstance(src, dict):
        return src[key]
    return getattr(src, key)


def features(row_or_state):
    """Zwraca listę [8] float. Ta sama wartość niezależnie od ścieżki wejścia (dict vs obiekt)."""
    own_p = _get(row_or_state, "own_pos_ned")
    own_v = _get(row_or_state, "own_vel_ned")
    trk_p = _get(row_or_state, "trk_pos_ned")
    age = _get(row_or_state, "track_age_s")
    valid = _get(row_or_state, "track_valid")
    rel = [float(trk_p[i]) - float(own_p[i]) for i in range(3)]
    return [rel[0], rel[1], rel[2],
            float(own_v[0]), float(own_v[1]), float(own_v[2]),
            float(age), float(1.0 if valid else 0.0)]
