#!/usr/bin/env python3
"""harness/feed_vision_proc.py — CIENKI KLIENT FEED=V2 (PRE_DET §6, ANEKS_DET-2 §4.3).

Żyje w procesie ławki (bench_flight, przez rejestr feedów). ZERO rclpy/egzekutorów/GT —
wyłącznie niebl okujący odbiór datagramów UDS od harness/percep_proc.py i serwowanie
kontraktu R1 VERBATIM (ten sam dict co FeedB._out / FeedVision.sample):
  {trk_pos_ned, trk_vel_ned, track_age_s, track_valid, feed_sha}.
Semantyka konsumenta NIETKNIĘTA (track_valid + age>1.0 s ⇒ hover-hold w net_controller).

Matematyka wieku = FeedVision.sample w sim-time, rozcięta przez IPC:
  age(sim_now) = (sim_now − t_frame_ostatniej_wiadomości) + s.track_age_s(t_frame).
trk_vel/pozycja = ZOH z ostatniej wiadomości (odchyłka okna linreg ≤ ~0.07 s — nota
percep_proc). Brak wiadomości ⇒ stan pusty (valid=False, age=1e9) — fail-silent →
fail-safe jak tryb „martwa" z 2A.

Log E2E (bramka runtime „stempel klatki → próbka u klienta"): przy PIERWSZEJ konsumpcji
nowej wiadomości wiersz {t_frame, sim_now, e2e_s} do log_path (sim-time, miara sędziego).
"""
from __future__ import annotations

import json
import os
import socket


class FeedVisionProc:
    def __init__(self, sock_path, log_path=None):
        self.sock_path = sock_path
        if os.path.exists(sock_path):
            os.unlink(sock_path)
        self._sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self._sk.bind(sock_path)
        self._sk.setblocking(False)
        from harness.det_v2 import feed_sha_v2            # jeden punkt prawdy sha (det_v2.py)
        self.feed_sha = feed_sha_v2()
        self._last = None                                  # ostatnia wiadomość "s"
        self._logged_t = None
        self._log = open(log_path, "w") if log_path else None
        self.n_msgs = 0

    def _drain(self):
        newest = None
        while True:
            try:
                data, _ = self._sk.recvfrom(65536)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                break
            try:
                m = json.loads(data.decode())
            except ValueError:
                continue
            if m.get("t") == "s":
                self.n_msgs += 1
                if newest is None or m["t_frame"] >= newest["t_frame"]:
                    newest = m
        if newest is not None:
            self._last = newest

    def sample(self, sim_now):
        self._drain()
        if self._last is None:
            return {"trk_pos_ned": [0.0, 0.0, 0.0], "trk_vel_ned": [0.0, 0.0, 0.0],
                    "track_age_s": 1e9, "track_valid": False, "feed_sha": self.feed_sha}
        m = self._last
        s = m["s"]
        if self._log and m["t_frame"] != self._logged_t:
            self._logged_t = m["t_frame"]
            self._log.write(json.dumps({"t_frame": m["t_frame"], "sim_now": round(sim_now, 4),
                                        "e2e_s": round(sim_now - m["t_frame"], 4),
                                        "fresh_total": m.get("n_fresh")}) + "\n")
            self._log.flush()
        age = (sim_now - m["t_frame"]) + s["track_age_s"]
        return {"trk_pos_ned": s["trk_pos_ned"], "trk_vel_ned": s["trk_vel_ned"],
                "track_age_s": round(age, 4), "track_valid": bool(s["track_valid"]),
                "feed_sha": self.feed_sha}

    def close(self):
        try:
            self._sk.close()
        finally:
            if os.path.exists(self.sock_path):
                os.unlink(self.sock_path)
            if self._log:
                self._log.close()
                self._log = None
