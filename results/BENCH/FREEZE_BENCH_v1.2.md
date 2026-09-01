# FREEZE_BENCH v1.2 — fix interruptible run_episode (§4 wyjątek: wada bramki/movera)

Delta względem v1.1 WYŁĄCZNIE `harness/intruder_motion.py` (fix v1.2: `run_episode` przerywalny przez
`should_stop` — mover poprzedniego epizodu przestaje nadpisywać pozę startową następnego; przyczyna
rezydualnego d_min<4 w re-shakeout boot1 = kłótnia movera ep_prev z bramką startu ep_next, NIE egzekutor/orbita).

harness/intruder_motion.py: 0397fa80… (v1.1) → 937ae17c1fc4178d7320a8f1a4cc5d5ba667277897dd486261db440b7f2d297a (v1.2)

NIEZMIENIONE (=v1.1): bench_flight df1250ad…, EGZEKUTOR 840514361e…, PARAMETRY 12c14adb…, sędzia 8ec0fcfb…,
feed 674d78ab…, cechy 9adc1505…, scenarios fe4f2aeb…, manifest e0527026…, piny. SR-3: egzekutor/parametry BAJT-W-BAJT.
