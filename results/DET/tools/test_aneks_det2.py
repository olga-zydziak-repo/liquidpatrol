#!/usr/bin/env python3
"""results/DET/tools/test_aneks_det2.py — testy budowy S3 (ANEKS_DET-2 §4.3) przed lotem.

Uruchamianie (rclpy + B0SP):
  PYTHONPATH=.b0deps/lib/python3.12/site-packages:.:$PYTHONPATH python3 -m pytest \
    results/DET/tools/test_aneks_det2.py -v
(klasa rclpy env — poza automatyczną regresją dirs, jak test_aneks3).
"""
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# AF_UNIX ogranicza sun_path do ~108 B — ścieżka scratchpada sesji jest za długa,
# stąd krótki katalog tymczasowy (w locie OUTDIR bootów ~65 zn., limit niegroźny).
import tempfile
SCRATCH = tempfile.mkdtemp(prefix="det2_")


def _mk_client(tag, log=False):
    from harness.feed_vision_proc import FeedVisionProc
    sp = os.path.join(SCRATCH, f"t_{tag}.sock")
    lp = os.path.join(SCRATCH, f"t_{tag}_e2e.jsonl") if log else None
    return FeedVisionProc(sock_path=sp, log_path=lp), sp, lp


def _send(sp, obj):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    s.sendto(json.dumps(obj).encode(), sp)
    s.close()


def test_kontrakt_dict():
    """Kontrakt R1 VERBATIM: stan pusty → invalid; po próbce → pola + wiek w sim;
    hold-last ze starzeniem; feed_sha stały (jeden punkt prawdy det_v2.feed_sha_v2)."""
    cli, sp, _ = _mk_client("contract")
    try:
        s0 = cli.sample(100.0)
        assert set(s0) == {"trk_pos_ned", "trk_vel_ned", "track_age_s", "track_valid", "feed_sha"}
        assert s0["track_valid"] is False and s0["track_age_s"] >= 1e8
        from harness.det_v2 import feed_sha_v2
        assert s0["feed_sha"] == feed_sha_v2()

        _send(sp, {"t": "s", "t_frame": 100.0, "t_update_sim": 100.02,
                   "s": {"trk_pos_ned": [1.0, 2.0, -10.0], "trk_vel_ned": [0.1, 0.0, 0.0],
                         "track_age_s": 0.0, "track_valid": True, "feed_sha": "x"},
                   "n_frames": 1, "n_fresh": 1})
        time.sleep(0.05)
        s1 = cli.sample(100.1)
        assert s1["track_valid"] is True and s1["trk_pos_ned"] == [1.0, 2.0, -10.0]
        assert abs(s1["track_age_s"] - 0.1) < 1e-6          # (sim_now − t_frame) + age(t_frame)
        s2 = cli.sample(101.5)                               # hold-last, wiek rośnie w sim
        assert s2["trk_pos_ned"] == [1.0, 2.0, -10.0] and abs(s2["track_age_s"] - 1.5) < 1e-6
        # nowsza wiadomość wygrywa po t_frame (dren wielu datagramów naraz)
        _send(sp, {"t": "s", "t_frame": 101.0, "t_update_sim": 101.02,
                   "s": {"trk_pos_ned": [3.0, 2.0, -10.0], "trk_vel_ned": [0.0, 0.0, 0.0],
                         "track_age_s": 0.4, "track_valid": True, "feed_sha": "x"},
                   "n_frames": 2, "n_fresh": 1})
        _send(sp, {"t": "meta", "feed_sha_v2": "ignorowane"})
        time.sleep(0.05)
        s3 = cli.sample(101.2)
        assert s3["trk_pos_ned"][0] == 3.0 and abs(s3["track_age_s"] - 0.6) < 1e-6
    finally:
        cli.close()
    assert not os.path.exists(sp)                            # teardown sprząta socket


def test_uds_latencja_dostarczenia():
    """Dostarczenie datagramu + konsumpcja ≪ 0.25 s (sanity toru IPC, wall)."""
    cli, sp, _ = _mk_client("lat")
    try:
        lats = []
        for i in range(500):
            t0 = time.monotonic()
            _send(sp, {"t": "s", "t_frame": float(i), "t_update_sim": float(i),
                       "s": {"trk_pos_ned": [0, 0, 0], "trk_vel_ned": [0, 0, 0],
                             "track_age_s": 0.0, "track_valid": True, "feed_sha": "x"},
                       "n_frames": i, "n_fresh": 0})
            cli.sample(float(i))
            lats.append(time.monotonic() - t0)
        lats.sort()
        assert lats[int(len(lats) * 0.95)] < 0.01, f"p95 UDS {lats[int(len(lats)*0.95)]:.4f}s"
    finally:
        cli.close()


def test_kolizja_egzekutora_klient_bez_rclpy():
    """Klasa C1/N3-C: wątek-lustro ławki spinuje egzekutor GLOBALNY rclpy, klient V2
    (zero rclpy) działa równolegle bez wyjątków; percepcja żyje w OSOBNYM procesie
    (test cyklu życia niżej), więc kolizja egzekutorów jest niemożliwa z konstrukcji."""
    import rclpy
    from rclpy.node import Node
    rclpy.init()
    bench = Node("bench_like_det2")
    run = [True]

    def spin_bench():
        while run[0]:
            rclpy.spin_once(bench, timeout_sec=0.02)

    th = threading.Thread(target=spin_bench, daemon=True)
    th.start()
    try:
        cli, sp, _ = _mk_client("coll")
        try:
            for i in range(50):
                _send(sp, {"t": "s", "t_frame": float(i), "t_update_sim": float(i),
                           "s": {"trk_pos_ned": [1, 1, -9], "trk_vel_ned": [0, 0, 0],
                                 "track_age_s": 0.0, "track_valid": True, "feed_sha": "x"},
                           "n_frames": i, "n_fresh": i})
                s = cli.sample(float(i) + 0.05)
                assert s["track_valid"] is True
            assert cli.n_msgs == 50
        finally:
            cli.close()
    finally:
        run[0] = False
        th.join(timeout=2.0)
        bench.destroy_node()
        rclpy.shutdown()


def test_cykl_zycia_percep_proc():
    """spawn percep_proc (własny proces/kontekst; YOLO det_v2 load) → meta-datagram do
    klienta → SIGTERM → czyste wyjście + summary. Topic obrazu martwy (bez sim) —
    testujemy proces, nie percepcję."""
    cli, sp, _ = _mk_client("life")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}/.b0deps/lib/python3.12/site-packages:{ROOT}:" + env.get("PYTHONPATH", "")
    log = os.path.join(SCRATCH, "t_life_percep.jsonl")
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, "harness/percep_proc.py"),
                          "--topic", "/t_det2_dead_topic", "--world", "world_demo_A3",
                          "--sock", sp, "--log", log],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        meta = None
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline and meta is None:
            try:
                data, _ = cli._sk.recvfrom(65536)
                m = json.loads(data.decode())
                if m.get("t") == "meta":
                    meta = m
            except (BlockingIOError, InterruptedError):
                time.sleep(0.2)
        assert meta is not None, "brak meta-datagramu od percep_proc w 60 s"
        from harness.det_v2 import DET_V2_SHA, feed_sha_v2
        assert meta["det_v2_sha"] == DET_V2_SHA
        assert meta["feed_sha_v2"] == feed_sha_v2()
        p.send_signal(signal.SIGTERM)
        rc = p.wait(timeout=15)
        assert rc == 0, f"percep_proc rc={rc}"
        summ = json.load(open(log + ".summary.json"))
        assert summ["det_v2_sha"] == DET_V2_SHA and summ["n_img_cb"] == 0
    finally:
        if p.poll() is None:
            p.kill()
        cli.close()
