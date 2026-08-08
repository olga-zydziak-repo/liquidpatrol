#!/usr/bin/env python3
"""r02/test_deadman.py — DETERMINISTYCZNY test własności DEAD-MAN (bez SITL/GPU).

Egzekwuje regresję domykaną w tej rundzie: „martwa osłona ⇒ streamer MILKNIE ⇒ warstwa-0 przejmuje".
Testuje REALNĄ metodę Runner._streamer (fix#2 + dead-man) na atrapie self — mierzy, że:
  (A) przy ŻYWEJ osłonie (odświeżanie _last_refresh) streamer publikuje ciągle, dead-man NIE tripuje,
  (B) przy MARTWEJ osłonie (brak odświeżania) stream cichnie po ~deadman_s (N=6 ticków=0.3 s),
      a _deadman_tripped=True. To warunek egzekwowany kodem pod założeniem żywotności osłony P1/P2.
"""
import time, threading
from types import SimpleNamespace
import r02.gate_run_r02 as G

PERIOD = G.PERIOD  # 0.05

class MockXrce:
    def __init__(self): self.stamps = []
    def publish_setpoint(self, sp): self.stamps.append(time.monotonic())

def make_fake():
    f = SimpleNamespace()
    f._sp_lock = threading.Lock()
    f._latest_sp = [0.0, 0.0, -11.5]
    f._last_refresh = time.monotonic()
    f._deadman_armed = True
    f._deadman_tripped = False
    f._stream_stop = threading.Event()
    f._stream_last = None
    f.stream_max_dt = 0.0
    f.stream_pub_count = 0
    f.DEADMAN_TICKS = 6
    f.deadman_s = f.DEADMAN_TICKS * PERIOD   # 0.3 s
    f.xrce = MockXrce()
    return f

def run():
    f = make_fake()
    th = threading.Thread(target=G.Runner._streamer, args=(f,), daemon=True)
    th.start()
    # FAZA A — osłona ŻYWA: odświeżaj _last_refresh co ~PERIOD przez 1.0 s
    t0 = time.monotonic()
    while time.monotonic() - t0 < 1.0:
        with f._sp_lock: f._last_refresh = time.monotonic()
        time.sleep(PERIOD)
    pub_A = len(f.xrce.stamps); tripped_A = f._deadman_tripped
    # FAZA B — osłona MARTWA: przestań odświeżać, streamer żyje. Zmierz kiedy cichnie.
    death_t = time.monotonic()
    time.sleep(1.2)
    f._stream_stop.set(); th.join(timeout=1.0)
    # analiza fazy B
    after = [s - death_t for s in f.xrce.stamps if s > death_t]
    last_pub_after = max(after) if after else 0.0
    n_after = len(after)
    trip_ok = f._deadman_tripped
    # publikacje po śmierci powinny ustać ~deadman_s; po deadman_s+margines — cisza
    silent_after = [d for d in after if d > f.deadman_s + 2*PERIOD]
    print(f"[FAZA A żywa]  publikacje={pub_A} (ciągłe) dead-man_tripped={tripped_A} (oczek. False)")
    print(f"[FAZA B martwa] publikacje_po_smierci={n_after} ostatnia_po={last_pub_after:.3f}s "
          f"deadman_s={f.deadman_s} tripped={trip_ok} (oczek. True)")
    print(f"[cisza] publikacje po deadman_s+2tick: {len(silent_after)} (oczek. 0 → stream zamilkł)")
    ok = (pub_A > 15 and not tripped_A and trip_ok and last_pub_after <= f.deadman_s + 3*PERIOD
          and len(silent_after) == 0)
    print(f"\nDEAD-MAN PROPERTY: {'PASS' if ok else 'FAIL'} "
          f"(żywa⇒publikuje bez tripu; martwa⇒cichnie w {f.deadman_s}s±{3*PERIOD:.2f})")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(run())
