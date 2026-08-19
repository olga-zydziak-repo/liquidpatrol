#!/usr/bin/env python3
"""r02/intruder_driver.py — deterministyczny sterownik pozy intruza (R1, PRE §2.1).

Poza intruza = f(SIM-TIME) przez gz set_pose: czyta /world/<w>/clock (sim-time), liczy pozę ze
skryptu trajektorii i ustawia ją. DETERMINIZM: poza jest czystą funkcją sim-time (bez fizyki/losu)
⇒ ta sama sim-time ⇒ ta sama poza między biegami (powtarzalność scenariuszy). Model (nie gz <actor>):
gz <actor> bez <skin> segfaultuje serwer (results/R02/RAPORT_R1.md §błąd).

Trajektoria (seed=ID scenariusza podmienia parametry): przelot boczny przed kamerą +x,
y ∈ [YMIN,YMAX] na wysokości Z, prędkość V (m/s), w pętli. Domyślnie x=12, z=10.

Uruchom: python3 -m r02.intruder_driver --world default --seconds 20 [--log out.jsonl]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time


def scripted_pose(sim_t, x=12.0, z=10.0, ymin=-15.0, ymax=15.0, v=3.0):
    """Poza = f(sim_t): trójkątna fala po y (tam-i-z-powrotem), okres = 2*(ymax-ymin)/v."""
    span = ymax - ymin
    period = 2.0 * span / v
    tau = sim_t % period
    y = ymin + v * tau if tau <= span / v else ymax - v * (tau - span / v)
    return (x, y, z)


def gz_clock(world, timeout=4.0):
    """Zwraca bieżący sim-time [s] z /world/<w>/clock (sec+nsec)."""
    r = subprocess.run(["gz", "topic", "-e", "-t", f"/world/{world}/clock", "-n", "1"],
                       capture_output=True, text=True, timeout=timeout)
    import re
    m = re.search(r"sec:\s*(-?\d+).*?nsec:\s*(\d+)", r.stdout, re.S)
    return int(m.group(1)) + int(m.group(2)) * 1e-9 if m else None


def set_pose(world, x, y, z, timeout=4.0):
    req = f'name: "intruder", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{w: 1.0}}'
    subprocess.run(["gz", "service", "-s", f"/world/{world}/set_pose",
                    "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
                    "--timeout", "3000", "--req", req],
                   capture_output=True, text=True, timeout=timeout)


class GzPoseClient:
    """ANEKS_D5 §6a: TRWAŁY klient set_pose in-process (gz.transport13) — ZERO spawnów subprocess w pętli
    ruchu intruza (poprzednio `subprocess.run(gz service)` per-call → churn transportu gz → stalle RTF,
    RAPORT_D_B5 §AKT-9). §6b: subskrybuje zegar symu `/world/W/clock` → sim_t() dla FAZY ruchu z sim-time.

    §7a (rezyduum request-reply): request SYNCHRONICZNY blokował ~108 ms/wywołanie (RTF_avg 0.919, kadencja
    9.25 Hz — RAPORT §AKT-10). Fix: NIEBLOKUJĄCY zapis pozy — WORKER z gniazdem „tylko najnowsza poza"
    (drop stale, kolejność zachowana bo jeden worker) + request FIRE-AND-FORGET (krótki timeout, reply
    ignorowany; serwer i tak wykonuje handler set_pose). Producent (pętla ruchu) NIE czeka → intr_ned świeży
    @kadencja pętli; worker APLIKUJE pozy @apply_hz. Wybór (worker+FF) vs samo-FF-w-pętli: worker izoluje
    ewent. resztkową latencję od świeżości intr_ned i daje czysty pomiar kadencji APLIKOWANEJ (n_apply)."""

    def __init__(self, world, name="intruder", async_apply=True, apply_hz=20.0, ff_timeout_ms=40):
        import threading as _th
        import gz.transport13 as _T
        from gz.msgs10 import pose_pb2, boolean_pb2, clock_pb2
        self._Pose = pose_pb2.Pose
        self._Bool = boolean_pb2.Boolean
        self.node = _T.Node()
        self.service = f"/world/{world}/set_pose"
        self.name = name
        self._sim_t = None
        self.node.subscribe(clock_pb2.Clock, f"/world/{world}/clock", self._on_clock)
        # §7a: nieblokujący apply
        self.async_apply = async_apply
        self._ff_timeout_ms = ff_timeout_ms
        self._latest = None                 # (x,y,z) — „tylko najnowsza poza"
        self._lock = _th.Lock()
        self._stop = _th.Event()
        self.n_apply = 0                    # liczba APLIKACJI worker'a (nie producenta)
        self.n_ok = 0                       # ANEKS_D6 §3: ile request zwróciło ok=True (poza dowiedziona)
        self.last_lat_ms = None             # ostatnia latencja request (diagnoza 108 ms, §7a read-only)
        self._apply_t0 = None
        if async_apply:
            self._worker = _th.Thread(target=self._apply_loop, args=(apply_hz,), daemon=True)
            self._worker.start()

    def _on_clock(self, msg):
        self._sim_t = msg.sim.sec + msg.sim.nsec * 1e-9

    def sim_t(self):
        """Ostatni sim-time [s] z zegara symu, albo None (zanim pierwsza próbka dojdzie)."""
        return self._sim_t

    def _mk(self, xyz):
        req = self._Pose()
        req.name = self.name
        req.position.x = float(xyz[0]); req.position.y = float(xyz[1]); req.position.z = float(xyz[2])
        req.orientation.w = 1.0
        return req

    def _apply_loop(self, hz):
        period = 1.0 / hz
        self._apply_t0 = time.time()
        while not self._stop.is_set():
            it0 = time.time()
            with self._lock:
                p = self._latest
            if p is not None:
                t0 = time.time()
                try:                          # ANEKS_D6 §3 wariant C: KONSUMUJ reply (drain, nie akumuluj) —
                    ok, _ = self.node.request(self.service, self._mk(p), self._Pose, self._Bool, self._ff_timeout_ms)
                    if ok:                    # timeout 40 ms wystarcza na reply (req_lat ~0.3 ms) → reply zdjęte
                        self.n_ok += 1        # z kolejki transportu, brak akumulacji → cel dipów 3× (§AKT-11).
                except Exception:
                    ok = False
                self.last_lat_ms = round((time.time() - t0) * 1000.0, 1)
                self.n_apply += 1
            time.sleep(max(0.0, period - (time.time() - it0)))

    def applied_hz(self):
        """§7a: ZMIERZONA kadencja APLIKOWANA (aplikacje worker'a / czas). None gdy sync."""
        if not self.async_apply or self._apply_t0 is None:
            return None
        return round(self.n_apply / max(time.time() - self._apply_t0, 1e-6), 2)

    def ok_rate(self):
        """§3: frakcja request z ok=True (dowód że pozy SIĘ APLIKUJĄ w symie, nie tylko wysyłają)."""
        if not self.async_apply or self.n_apply == 0:
            return None
        return round(self.n_ok / self.n_apply, 3)

    def set_pose(self, x, y, z, timeout_ms=100):
        """§7a async: NIEBLOKUJĄCE — aktualizuje „najnowszą pozę" (worker aplikuje). §6 sync: blokujący request."""
        if self.async_apply:
            with self._lock:
                self._latest = (float(x), float(y), float(z))
            return True
        ok, _ = self.node.request(self.service, self._mk((x, y, z)), self._Pose, self._Bool, timeout_ms)
        return ok

    def close(self):
        self._stop.set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="default")
    ap.add_argument("--seconds", type=float, default=20.0)   # sim-sekundy działania
    ap.add_argument("--rate", type=float, default=15.0)       # wall-Hz aktualizacji
    ap.add_argument("--x", type=float, default=12.0)
    ap.add_argument("--z", type=float, default=10.0)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    t0 = gz_clock(args.world)
    if t0 is None:
        print("[driver] BRAK zegara symu — świat żywy?", file=sys.stderr); sys.exit(2)
    logf = open(args.log, "w") if args.log else None
    dt = 1.0 / args.rate
    while True:
        st = gz_clock(args.world)
        if st is None:
            break
        if st - t0 >= args.seconds:
            break
        x, y, z = scripted_pose(st, x=args.x, z=args.z)
        set_pose(args.world, x, y, z)
        if logf:
            logf.write(json.dumps({"sim_t": round(st, 3), "cmd": [round(x, 3), round(y, 3), round(z, 3)]}) + "\n")
        time.sleep(dt)
    if logf:
        logf.close()
    print(f"[driver] koniec po ~{args.seconds}s sim (poza=f(sim_t), deterministycznie).")


if __name__ == "__main__":
    main()
