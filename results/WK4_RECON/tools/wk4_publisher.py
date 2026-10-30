#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_publisher.py — publikator przebiegu turbulencji do świata (droga A, R1).

Plik serii PRZYPIĘTY sha256 (inny plik ⇒ ODMOWA, exit 5). Sterowany CZASEM SYMULACJI z topiku
/world/<W>/clock (nie zegarem ściennym): w chwilach k/rate czasu symulacji publikuje na /world/<W>/wind
(gz.msgs.Wind, enable_wind=true) próbkę i = floor((t_sim − t_off)/dt), obciętą do [0, N−1]:
przed t_off trzyma próbkę 0, po końcu przebiegu trzyma ostatnią (R1e: plugin trzyma ostatnią wartość).
Startuje PRZED światem (czeka na zegar bez limitu), kończy na SIGTERM. Log: jsonl (t_sim, wx, wy, wz, i).

Użycie: wk4_publisher.py <seria.json> <sha256> <świat> <t_off_s> <log.jsonl> [rate_Hz=20]
"""
import hashlib
import json
import signal
import sys
import time

from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.wind_pb2 import Wind
from gz.transport13 import Node


def main():
    path, sha_exp, world, t_off, logp = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
    rate = float(sys.argv[6]) if len(sys.argv) > 6 else 20.0
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if sha != sha_exp:
        print(f"[wk4_pub] ODMOWA: sha serii {sha} != {sha_exp}", flush=True)
        sys.exit(5)
    d = json.load(open(path))
    dt, wx, wy, wz = d["dt"], d["wx"], d["wy"], d["wz"]
    n = len(wx)
    stop = [False]
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__(0, True))
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__(0, True))
    node = Node()
    tsim = {"t": None}
    # NIE subskrybuj zegara przed startem serwera: px4-rc.gzsim:33 uznaje świat za działający, gdy
    # `gz topic -l` pokazuje /world/.*/clock (także sam subskrybent) — wtedy PX4 nie startuje gz
    # (próba n_D4b: „Timed out waiting for Gazebo world"). Czekamy na serwis scene/info serwera.
    while not stop[0] and f"/world/{world}/scene/info" not in node.service_list():
        time.sleep(0.5)
    node.subscribe(Clock, f"/world/{world}/clock",
                   lambda m: tsim.__setitem__("t", m.sim.sec + m.sim.nsec * 1e-9))
    pub = node.advertise(f"/world/{world}/wind", Wind)
    print("[wk4_pub] serwer świata wstał — subskrypcja zegara i publikacja", flush=True)
    log = open(logp, "w", buffering=1)   # liniowo: log kompletny także przy kill po locie
    log.write(json.dumps({"t": "meta", "seria": path, "sha256": sha, "swiat": world, "t_off": t_off,
                          "rate": rate, "dt": dt, "n": n}) + "\n")
    print(f"[wk4_pub] seria {d.get('profil')} sha {sha[:16]} n={n} t_off={t_off} rate={rate} — czekam na zegar",
          flush=True)
    k_next = 0
    while not stop[0]:
        t = tsim["t"]
        if t is None:                    # przed startem świata: uśpienie 0.2 s (proc_gate run_boota: <2 % CPU)
            time.sleep(0.2)
            continue
        if t < k_next / rate:
            time.sleep(0.002)
            continue
        k_next = int(t * rate) + 1
        i = min(max(int((t - t_off) / dt), 0), n - 1)
        m = Wind()
        m.linear_velocity.x, m.linear_velocity.y, m.linear_velocity.z = wx[i], wy[i], wz[i]
        m.enable_wind = True
        pub.publish(m)
        log.write(json.dumps([round(t, 4), wx[i], wy[i], wz[i], i]) + "\n")
    log.close()
    print("[wk4_pub] stop", flush=True)


if __name__ == "__main__":
    main()
