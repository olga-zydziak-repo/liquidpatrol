#!/usr/bin/env python3
"""bench/demo_logger.py — logger demonstracji (PROMPT_BENCH_BUILD E, PRE §4 + ANEKS P1).

Jeden wiersz na tick (20 Hz) do `demo.jsonl`, zaokrąglenie 3 miejsca. Kontrakt danych modelu:
własny stan (EKF), feed, wyjście egzekutora `cmd_v_ned`, flagi (phase, stall, shas).
`trk_vel_ned` LOGOWANE, ale NIE jest cechą lotu (cechy = 8-wym `bench/features.py`, ANEKS P1).
"""
import json

from bench.features import features, FEATURE_NAMES

REQUIRED = ("t_sim", "tick", "episode_id", "scenario_id", "seed", "attempt",
            "own_pos_ned", "own_vel_ned", "trk_pos_ned", "trk_vel_ned", "track_age_s", "track_valid",
            "cmd_v_ned", "phase", "stall", "controller", "controller_sha", "feed_sha", "executor_params_sha")


def _r3(v):
    if isinstance(v, (list, tuple)):
        return [round(float(x), 3) for x in v]
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return round(float(v), 3)
    return v


def make_row(t_sim, tick, ep_meta, own_pos, own_vel, feed_sample, cmd_v, phase, stall,
             controller, controller_sha, executor_params_sha):
    """Buduje wiersz demo. ep_meta = {episode_id, scenario_id, seed, attempt}. Zwraca dict (bez null w REQUIRED)."""
    row = {
        "t_sim": _r3(t_sim), "tick": int(tick),
        "episode_id": ep_meta["episode_id"], "scenario_id": ep_meta["scenario_id"],
        "seed": ep_meta["seed"], "attempt": ep_meta["attempt"],
        "own_pos_ned": _r3(own_pos), "own_vel_ned": _r3(own_vel),
        "trk_pos_ned": _r3(feed_sample["trk_pos_ned"]), "trk_vel_ned": _r3(feed_sample["trk_vel_ned"]),
        "track_age_s": _r3(feed_sample["track_age_s"]), "track_valid": bool(feed_sample["track_valid"]),
        "cmd_v_ned": _r3(cmd_v), "phase": phase, "stall": int(stall),
        "controller": controller, "controller_sha": controller_sha,
        "feed_sha": feed_sample["feed_sha"], "executor_params_sha": executor_params_sha,
    }
    return row


def feature_state_from_row(row):
    """Stan wejściowy dla features() z wiersza demo (ta sama ścieżka co w locie)."""
    return {"own_pos_ned": row["own_pos_ned"], "own_vel_ned": row["own_vel_ned"],
            "trk_pos_ned": row["trk_pos_ned"], "track_age_s": row["track_age_s"],
            "track_valid": row["track_valid"]}


class DemoLogger:
    def __init__(self, path):
        self.path = path
        self._f = open(path, "w")
        self.n = 0

    def log(self, row):
        for k in REQUIRED:
            assert row.get(k) is not None, f"demo row: pole '{k}' == None (zabronione)"
        self._f.write(json.dumps(row) + "\n")
        self.n += 1

    def close(self):
        self._f.close()
