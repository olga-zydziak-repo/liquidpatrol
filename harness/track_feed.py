#!/usr/bin/env python3
"""harness/track_feed.py — FEED-B: emulowany track-feed intruza (ANEKS_BENCH-0 D1, PRE §2 D1).

JEDYNY konsument GT po stronie kontrolera. FEED-B (aneks D1, wygrywa z PRE):
  f = 10 Hz, L = 0.20 s (bufor czasowy w SIM), σ_xy = 0.5 / σ_z = 0.3 (Gauss iid), p_drop = 0.05 (hold-last,
  track_age rośnie), pozycja SUROWA (bez EMA), trk_vel = REGRESJA LINIOWA na oknie 1.0 s w CZASIE SIM.
RNG z ziarna epizodu. Wszystkie okna/opóźnienia w sim-time (ANEKS P2) — stall wall NIE wydłuża okna.

`FeedB` — czysty (NED in/out), testowalny bez gz. `TrackFeedGz` — subskrybuje /world/W/pose/info,
konwertuje pozę intruza gz-ENU → NED (`enu2drv`→`drv2ned`), karmi FeedB. sim-time z header.stamp próbki.
"""
import hashlib
import json


def _slope(ts, xs):
    """Nachylenie regresji liniowej x(t) (least squares). ts,xs równej długości ≥2; inaczej 0.0."""
    n = len(ts)
    if n < 2:
        return 0.0
    mt = sum(ts) / n
    mx = sum(xs) / n
    num = sum((ts[i] - mt) * (xs[i] - mx) for i in range(n))
    den = sum((ts[i] - mt) ** 2 for i in range(n))
    return num / den if den > 1e-12 else 0.0


class FeedB:
    def __init__(self, seed, f=10.0, L=0.20, sigma_xy=0.5, sigma_z=0.3, p_drop=0.05, vel_window_s=1.0):
        import random
        self.f = f; self.L = L; self.sigma_xy = sigma_xy; self.sigma_z = sigma_z
        self.p_drop = p_drop; self.vel_window_s = vel_window_s
        self._rng = random.Random(int(seed) * 7919 + 13)
        self._gt = []            # [(sim_t, [x,y,z])] surowa poza ZASTOSOWANA (NED)
        self._issued = []        # [(sim_t, [x,y,z])] świeże wystawione (do regresji)
        self._last_pos = None
        self._last_fresh_sim = None
        self._last_valid = False
        self._last_issue_sim = None
        self.n_feed_ticks = 0            # ile decyzji feedu (fresh+drop+brak-gt), bez hold-między-tickami
        self.n_drops = 0                 # ile zaników (hold-last przez p_drop)
        self.params = {"profile": "B", "f_hz": f, "L_s": L, "sigma_xy_m": sigma_xy, "sigma_z_m": sigma_z,
                       "p_drop": p_drop, "vel_window_s": vel_window_s, "pos": "raw", "trk_vel": "linreg_1s_sim"}
        self.feed_sha = hashlib.sha256(json.dumps(self.params, sort_keys=True).encode()).hexdigest()

    def push_gt(self, sim_t, pos_ned):
        self._gt.append((float(sim_t), [float(pos_ned[0]), float(pos_ned[1]), float(pos_ned[2])]))
        cutoff = sim_t - (self.L + self.vel_window_s + 1.0)
        if len(self._gt) > 8 and self._gt[0][0] < cutoff:
            self._gt = [g for g in self._gt if g[0] >= cutoff]

    def _interp_gt(self, target_sim):
        if not self._gt:
            return None
        if target_sim <= self._gt[0][0]:
            return None
        if target_sim >= self._gt[-1][0]:
            return list(self._gt[-1][1])
        for i in range(1, len(self._gt)):
            t0, p0 = self._gt[i - 1]; t1, p1 = self._gt[i]
            if t0 <= target_sim <= t1:
                a = (target_sim - t0) / (t1 - t0) if t1 > t0 else 0.0
                return [p0[k] + a * (p1[k] - p0[k]) for k in range(3)]
        return list(self._gt[-1][1])

    def _trk_vel(self, sim_now):
        lo = sim_now - self.vel_window_s
        win = [(t, p) for (t, p) in self._issued if t >= lo]
        if len(win) < 2:
            return [0.0, 0.0, 0.0]
        ts = [t for t, _ in win]
        return [_slope(ts, [p[k] for _, p in win]) for k in range(3)]

    def _out(self, pos, age, valid, sim_now):
        return {"trk_pos_ned": [round(pos[0], 4), round(pos[1], 4), round(pos[2], 4)] if pos else [0.0, 0.0, 0.0],
                "trk_vel_ned": [round(v, 4) for v in self._trk_vel(sim_now)],
                "track_age_s": round(age, 4), "track_valid": bool(valid),
                "feed_sha": self.feed_sha}

    def sample(self, sim_now):
        """Zwraca próbkę feedu dla kontrolera w chwili sim_now (sim-time). Kadencja f (między — hold-last)."""
        period = 1.0 / self.f
        if self._last_issue_sim is not None and (sim_now - self._last_issue_sim) < period - 1e-9:
            age = (sim_now - self._last_fresh_sim) if self._last_fresh_sim is not None else 1e9
            return self._out(self._last_pos, age, self._last_valid, sim_now)
        self._last_issue_sim = sim_now
        self.n_feed_ticks += 1
        gt = self._interp_gt(sim_now - self.L)
        if gt is None:                                        # brak GT (przed pierwszą próbką / za wcześnie)
            self._last_valid = self._last_pos is not None
            age = (sim_now - self._last_fresh_sim) if self._last_fresh_sim is not None else 1e9
            return self._out(self._last_pos, age, self._last_valid, sim_now)
        if self._rng.random() < self.p_drop and self._last_pos is not None:   # zanik → hold-last, age rośnie
            self.n_drops += 1
            age = sim_now - self._last_fresh_sim
            return self._out(self._last_pos, age, True, sim_now)
        noisy = [gt[0] + self._rng.gauss(0.0, self.sigma_xy),
                 gt[1] + self._rng.gauss(0.0, self.sigma_xy),
                 gt[2] + self._rng.gauss(0.0, self.sigma_z)]
        self._last_pos = noisy; self._last_fresh_sim = sim_now; self._last_valid = True
        self._issued.append((sim_now, noisy))
        lo = sim_now - self.vel_window_s - 0.5
        if len(self._issued) > 4 and self._issued[0][0] < lo:
            self._issued = [s for s in self._issued if s[0] >= lo]
        return self._out(noisy, 0.0, True, sim_now)


class TrackFeedGz:
    """Wrapper gz: subskrybuje /world/W/pose/info, wyciąga 'intruder', konwertuje gz-ENU→NED, karmi FeedB.
    sim-time z header.stamp. Używany w procesie gate'a (bench_flight). Nie importowany przez kontrolery."""

    def __init__(self, world, feed: FeedB):
        from gz.transport13 import Node as GzNode
        from gz.msgs10.pose_v_pb2 import Pose_V
        from common.frames import enu2drv, drv2ned
        self._enu2drv = enu2drv; self._drv2ned = drv2ned
        self.feed = feed
        self.node = GzNode()
        self.node.subscribe(Pose_V, f"/world/{world}/pose/info", self._cb)

    def _cb(self, msg):
        sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
        for p in msg.pose:
            if p.name == "intruder":
                gz = [p.position.x, p.position.y, p.position.z]     # gz-ENU [E,N,U]
                ned = self._drv2ned(self._enu2drv(gz))              # ENU→DRV→NED
                self.feed.push_gt(sim, ned)
                return
