#!/usr/bin/env python3
"""results/2A/tools/shadow_feed_live.py — runner SHADOW etapu A (PROMPT_2A_S2 §1).

FEED-V LIVE (harness/feed_vision.FeedVisionLive, frozen 0ce7569c) jako CIEŃ: subskrybuje
zbridżowany topic kamery pokładowej + stan pokładowy (EKF /fmu/out/vehicle_local_position,
attitude /fmu/out/vehicle_attitude — zaszyte w FeedVisionLive, tu tylko echo do meta),
produkuje próbki kontraktu R1 i LOGUJE do shadow_feed.jsonl. KONTROLERA NIE KARMI —
lot jedzie na FEED=B (default bench_flight); jedyne wyjście runnera = pliki w OUTDIR.
Reguła nadrzędna: zero GT w tym procesie.

Zero edycji frozen kodu (SR §0.3). Dwa punkty kompozycji:
  1. LogProxy — plik loga FEED-V podmieniony na proxy, które dokleja do każdego wiersza
     `t_update_sim` = zegar sim gz W CHWILI zapisu. _ingest (feed_vision.py:175) pisze
     PO aktualizacji tracku, więc t_update_sim − t_frame = latencja end-to-end
     capture→update (render→gz pub→bridge→ROS→YOLO→MTI→admisja→pozycja) w czasie SIM —
     dokładnie pole, które czyta percep_judge.judge_shadow (percep_judge.py:131-132).
  2. ShadowFeed._on_image — nadpisanie metody LIVE: dekymacja zrzutu klatek (2 Hz → jpg,
     materiał etapu B/sanity-klatek) + opcjonalna dekymacja CAŁEGO toru do --det-hz
     (wariant retry PRE_2A §3 A(ii): det 5 Hz) + pomiar wall push_frame. Rdzeń toru
     (YOLO→MTI→admisja→pinhole→kontrakt) = frozen push_frame 1:1.

Pierwszy wiersz shadow_feed.jsonl = meta (weights_sha SR-2, feed_sha vs FREEZE_2A, topic
kamery, źródła stanu pokładowego, det_hz) — sędzia pomija go bezpiecznie (brak 'locked').
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FEED_SHA_FREEZE = "d6a3367b210f47e79b2ea9b33151235d3a2a0ac21c4ad2b93dfa93092673a895"  # FREEZE_2A po N2 (ANEKS_2A-1)
STATE_SOURCES = {"pos_ekf": "/fmu/out/vehicle_local_position",
                 "att": "/fmu/out/vehicle_attitude"}          # echo z feed_vision.py:241-244 (zaszyte)

_sim = [0.0]          # zegar sim gz (jak bench_flight._clock_cb)
_stop = [False]


class LogProxy:
    """Plik loga FEED-V z doklejką t_update_sim (zegar sim gz w chwili zapisu = po aktualizacji
    tracku w _ingest). Kompozycja zamiast edycji frozen feed_vision. Wiersz nie-JSON → passthrough."""

    def __init__(self, path):
        self._f = open(path, "w")

    def write(self, s):
        try:
            rec = json.loads(s)
            if _sim[0] > 0.0:
                rec["t_update_sim"] = round(_sim[0], 4)
            self._f.write(json.dumps(rec) + "\n")
        except (ValueError, TypeError):
            self._f.write(s)

    def write_raw(self, s):
        self._f.write(s)
        self._f.flush()

    def flush(self):
        self._f.flush()

    def close(self):
        self._f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="zbridżowany topic kamery (ROS)")
    ap.add_argument("--world", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--frames-hz", type=float, default=2.0)
    ap.add_argument("--det-hz", type=float, default=None,
                    help="dekymacja toru (wariant retry PRE §3: 5); brak = każda klatka (15 Hz)")
    a = ap.parse_args()

    frames_dir = os.path.join(a.outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    log_path = os.path.join(a.outdir, "shadow_feed.jsonl")

    # zegar sim gz (wzór bench_flight.py:184/220) — do t_update_sim
    from gz.transport13 import Node as GzNode
    from gz.msgs10.clock_pb2 import Clock
    gn = GzNode()
    gn.subscribe(Clock, f"/world/{a.world}/clock", lambda m: _sim.__setitem__(0, m.sim.sec + m.sim.nsec / 1e9))

    import cv2
    from harness.feed_vision import FeedVisionLive, YoloDetector

    class ShadowFeed(FeedVisionLive):
        """Cień FEED-V: frozen tor + zrzut klatek + dekymacja det_hz + pomiar wall. _ready
        bramkuje klatki do czasu podpięcia LogProxy (konstruktor nadklasy startuje spin)."""
        _ready = False

        def __init__(self, topic, detector, det_hz=None, frames_hz=2.0):
            self._det_period = (1.0 / det_hz) if det_hz else None
            self._frames_period = (1.0 / frames_hz) if frames_hz else None
            self._last_proc = None
            self._last_saved = None
            self.n_saved = 0
            self.n_skip_preready = 0
            self.n_skip_dethz = 0
            self.proc_ms = []
            super().__init__(image_topic=topic, detector=detector, log_path=None,
                             node_name="feed_v_shadow")

        def attach_log(self, proxy):
            self._log = proxy
            self._ready = True

        def _on_image(self, msg):
            if not self._ready:
                self.n_skip_preready += 1
                return
            sim = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
            if (self._det_period and self._last_proc is not None
                    and sim - self._last_proc < self._det_period - 1e-3):
                self.n_skip_dethz += 1
                return
            mono = self._imgmsg_to_mono(msg)
            self._last_proc = sim
            if self._frames_period and (self._last_saved is None
                                        or sim - self._last_saved >= self._frames_period - 1e-3):
                cv2.imwrite(os.path.join(frames_dir, f"f_{sim:012.3f}.jpg"), mono)
                self._last_saved = sim
                self.n_saved += 1
            w0 = time.monotonic()
            self.push_frame(sim, mono)
            self.proc_ms.append(round((time.monotonic() - w0) * 1000.0, 2))

    det = YoloDetector()                      # guard SR-2 w konstruktorze (sha ≠ FREEZE ⇒ ODMOWA)
    print(f"[shadow] weights_sha={det.weights_sha} (SR-2 PASS) device={det.device}", flush=True)
    feed = ShadowFeed(a.topic, det, det_hz=a.det_hz, frames_hz=a.frames_hz)
    if feed.feed_sha != FEED_SHA_FREEZE:
        raise RuntimeError(f"[shadow] feed_sha rozjazd z FREEZE_2A: {feed.feed_sha}")
    print(f"[shadow] feed_sha={feed.feed_sha} == FREEZE_2A", flush=True)
    print(f"[shadow] topic={a.topic} state_sources={STATE_SOURCES} det_hz={a.det_hz or 'full(15)'}",
          flush=True)

    proxy = LogProxy(log_path)
    proxy.write_raw(json.dumps({
        "t": "meta", "role": "SHADOW (kontrolera nie karmi; lot na FEED=B)",
        "weights_sha": det.weights_sha, "feed_sha": feed.feed_sha,
        "image_topic": a.topic, "state_sources": STATE_SOURCES,
        "det_hz": a.det_hz, "frames_hz": a.frames_hz, "world": a.world}) + "\n")
    feed.attach_log(proxy)

    signal.signal(signal.SIGTERM, lambda *_: _stop.__setitem__(0, True))
    signal.signal(signal.SIGINT, lambda *_: _stop.__setitem__(0, True))
    t_hb = time.monotonic()
    while not _stop[0]:
        time.sleep(0.5)
        if time.monotonic() - t_hb >= 15.0:
            t_hb = time.monotonic()
            print(f"[shadow] sim={_sim[0]:.1f} frames={feed.n_frames} boxes={feed.n_boxes} "
                  f"fresh={feed.n_fresh} saved={feed.n_saved}", flush=True)

    feed.close()
    pm = sorted(feed.proc_ms)
    summ = {"n_frames": feed.n_frames, "n_boxes": feed.n_boxes, "n_fresh": feed.n_fresh,
            "n_frames_saved": feed.n_saved, "n_skip_preready": feed.n_skip_preready,
            "n_skip_dethz": feed.n_skip_dethz,
            "push_frame_wall_ms": ({"n": len(pm), "p50": pm[len(pm) // 2],
                                    "p95": pm[int(len(pm) * 0.95)], "max": pm[-1]} if pm else None),
            "weights_sha": det.weights_sha, "feed_sha": feed.feed_sha,
            "image_topic": a.topic, "state_sources": STATE_SOURCES,
            "det_hz": a.det_hz, "sim_last": round(_sim[0], 3)}
    with open(os.path.join(a.outdir, "shadow_summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(f"[shadow] DONE {json.dumps(summ)}", flush=True)


if __name__ == "__main__":
    main()
