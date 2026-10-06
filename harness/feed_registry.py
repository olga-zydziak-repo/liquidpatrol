#!/usr/bin/env python3
"""harness/feed_registry.py — rejestr producentów feedu (noga 2A, PRE_2A §2 D6; wzór SR-9
= r03/controllers/__init__.py make_controller).

`make_feed(name, *, seed, world)` → (feed, holder):
  feed   — obiekt kontraktu R1: .sample(sim_now) → {trk_pos_ned, trk_vel_ned, track_age_s,
           track_valid, feed_sha}; konsumenci (kontrolery przez set_feed) NIETKNIĘCI.
  holder — obiekt trzymany przy życiu przez wołającego (dla "B": TrackFeedGz z subskrypcją
           pose/info — lustro dzisiejszych DWÓCH linii bench_flight; dla "V": sam feed).

Rejestr rozszerza się DOPISANIEM wpisu — bez dotykania pętli lotu (SR-9).
  "B" → FeedB konstrukcja DZISIEJSZA 1:1 (bench_flight.py:309-310 przed edycją 2A):
        FeedB(seed, f=10.0) + TrackFeedGz(world, feed).
  "V" → FEED-V LIVE (harness/feed_vision.py, PRE_2A D1/D2/D4): topic kamery z env
        FEED_V_TOPIC (fallback LIVE_DETECTOR_TOPIC — konwencja run_act_live); seed
        przyjmowany i IGNOROWANY (percepcja deterministyczna względem klatek — nota).
"""
from harness.track_feed import FeedB, TrackFeedGz


def _mk_b(seed, world):
    feed = FeedB(seed, f=10.0)
    tf = TrackFeedGz(world, feed)          # subskrybuje pose/info → feed (1:1 z bench_flight)
    return feed, tf


def _mk_v(seed, world):
    from harness.feed_vision import FeedVisionLive   # import leniwy: torch/rclpy tylko gdy FEED=V
    import os
    log = os.environ.get("FEED_V_LOG")                # shadow-log (etap A/B) — opcjonalny
    feed = FeedVisionLive(log_path=log)
    return feed, feed


def _mk_v2(seed, world):
    """FEED=V2 (PRE_DET §6, ANEKS_DET-2): percepcja w OSOBNYM procesie (harness/
    percep_proc.py, det_v2 + rdzeń FeedVision read-only); tu wyłącznie cienki klient
    UDS — zero rclpy/torch w procesie ławki. Ścieżki z env DETV2_SOCK / DETV2_CLIENT_LOG
    (ustawia driver etapowy). seed ignorowany jak w V (percepcja deterministyczna
    względem klatek)."""
    from harness.feed_vision_proc import FeedVisionProc   # import leniwy
    import os
    feed = FeedVisionProc(sock_path=os.environ["DETV2_SOCK"],
                          log_path=os.environ.get("DETV2_CLIENT_LOG"))
    return feed, feed


_REGISTRY = {
    "B": _mk_b,     # FEED-B emulowany (ANEKS_BENCH-0 D1) — default, zachowanie dzisiejsze
    "V": _mk_v,     # FEED-V percepcyjny (PRE_2A) — kamera pokładowa → YOLO → MTI → pinhole
    "V2": _mk_v2,   # FEED-V2 (PRE_DET): det_v2 w osobnym procesie percepcji, klient UDS
}


def make_feed(name, *, seed, world):
    mk = _REGISTRY.get(name)
    if mk is None:
        raise ValueError(f"nieznany FEED={name!r}; znane={sorted(_REGISTRY)}")
    return mk(seed, world)
