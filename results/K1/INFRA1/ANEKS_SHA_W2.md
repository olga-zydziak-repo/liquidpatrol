# ANEKS_SHA — INFRA-1 ANEKS_INFRA1-3 W2 (rewert I2b, P0a) · 2026-08-24

Jedna zmiana (SI-1): rewert bramki-oczekiwania I2b w `run_k1_boot.sh` (moduł lotu bezwarunkowo po sleep 90).
Zachowane: I2a (bramka obciążenia), gałąź E (infra1_empty_flight), diagnostyka timejump_pre/post.
Poprawka kryterium (W3): `infra1_shakeout_check.py` — timejump raportowany, bramka = arm ∧ 0 deep-stalli.

## Piny frozen (BEZ ZMIAN):
```
4e0dc0afffda099837a002191a5540fd95d6de13cb88e7233433d67b1b998ae1  k1/k1_judge.py
1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2  r01/shield.py
4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a  r03/config.py
72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a  r03/gate_run_r03.py
```

## Diff verbatim run_k1_boot.sh:
```diff
diff --git a/k1/run_k1_boot.sh b/k1/run_k1_boot.sh
index 63cdb62..4826b55 100755
--- a/k1/run_k1_boot.sh
+++ b/k1/run_k1_boot.sh
@@ -65,27 +65,15 @@ echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]"
 for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
 setsid nohup python3 -m acts.rtf_sampler --world "$WORLD" --out "$OUTDIR/rtf_stream.jsonl" > "$OUTDIR/rtf_sampler.log" 2>&1 &
 RTF=$!
-# INFRA-1 I2b: arm po ZBIEŻNOŚCI estymatora, nie po zegarze. Sygnał JUŻ logowany (nie nowa telemetria):
-# commander 'Ready for takeoff!' w px4.log — obecny w bootach udanych (N4/S2), NIEobecny w env-failach
-# (S4/5/6, które utknęły w Preflight Fail: High Gyro Bias / horizontal velocity unstable po time-jumpach
-# lockstepu). Min settle 90 s ZACHOWANE (nie armuj wcześniej niż 90 s — porównywalność z lotami sprzed
-# hartowania). Timeout 300 s od startu bootu ⇒ env-fail „jak dotąd" (nie armujemy na chorej maszynie).
-echo "[K1 $ARM p$POINT b$BOOT_N] settle min 90 s (I2b)"; sleep 90
-CONV_DEADLINE=$(( BOOT_T0 + 300 )); CONV_OK=0
-while [ "$(date +%s)" -lt "$CONV_DEADLINE" ]; do
-  if grep -q 'Ready for takeoff' "$OUTDIR/px4.log" 2>/dev/null; then CONV_OK=1; break; fi
-  sleep 3
-done
-CONV_S=$(( $(date +%s) - BOOT_T0 )); [ "$CONV_OK" = "1" ] || CONV_S=-1
-echo "$CONV_S" > "$OUTDIR/convergence_s.txt"
-echo "[K1 $ARM p$POINT b$BOOT_N] convergence ok=$CONV_OK conv_s=${CONV_S}s"
+# INFRA-1 ANEKS_INFRA1-3 W2 (P0a): REWERT I2b. Moduł lotu startuje BEZWARUNKOWO po 90 s settle —
+# stan znany-dobry (N boot4 / S4-6 / R0.3a armowały). I2b czekał na 'Ready for takeoff' PRZED startem
+# modułu lotu, co tworzyło DEADLOCK: 'Ready'⇐pre_flight_checks_pass⇐wyczyszczenie 'No connection to GCS'
+# ⇐klient MAVSDK⇐moduł lotu, który I2b odraczał (dowód C2, RAPORT_INFRA2 §C2). I2a (bramka obciążenia,
+# wyżej) ZACHOWANA — nie brała udziału w deadlocku. timejump raportowany (nie bramkujący, per C1).
+echo "[K1 $ARM p$POINT b$BOOT_N] settle 90 s preflight EKF"; sleep 90
 grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"
 
-if [ "$CONV_OK" != "1" ]; then
-  # I2b: brak zbieżności w 300 s ⇒ env-fail, NIE armujemy (nie startujemy modułu lotu).
-  echo "[gate] ENV-FAIL: brak 'Ready for takeoff' w 300 s — nie armuje na chorej maszynie (I2b)" > "$OUTDIR/act.log"
-  RC=2; HARNESS_FILE="$ROOT/k1/run_k1_boot.sh"
-elif [ "$ARM" = "S" ]; then
+if [ "$ARM" = "S" ]; then
   SCEN="K1" K1_POINT="$POINT" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
     PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r03.gate_run_r03 > "$OUTDIR/act.log" 2>&1
   RC=$?; HARNESS_FILE="$ROOT/r03/gate_run_r03.py"
```

## Diff verbatim infra1_shakeout_check.py:
```diff
diff --git a/tools/infra1_shakeout_check.py b/tools/infra1_shakeout_check.py
index efc89ea..3779b7c 100644
--- a/tools/infra1_shakeout_check.py
+++ b/tools/infra1_shakeout_check.py
@@ -2,13 +2,17 @@
 """
 tools/infra1_shakeout_check.py — INFRA-1 ANEKS_INFRA1-2 N3: ZAMROŻONE kryterium shakeoutu po resecie.
 
-Kryterium (zamrożone PRZED uruchomieniem shakeoutu, commit przed resetem):
-  PASS ⟺ arm_ok ∧ n_timejumps ≤ 1 ∧ (brak głębokiego stalla rtf<0.5 w oknie preflight→arm)
+Kryterium (ANEKS_INFRA1-3 W3, poprawka wynikająca z C1/C2):
+  PASS ⟺ arm_ok ∧ (brak głębokiego stalla rtf<0.5 w oknie preflight→arm)
   FAIL ⟺ cokolwiek innego.
-Interpretacja (też zamrożona):
-  PASS ⇒ zły stan lockstepu był PRZEJŚCIOWy po restarcie → wracamy do I3 (dziesiątka) na NIEZMIENIONYM kodzie.
-  FAIL ⇒ pętla timejump = TRWAŁA własność habitatu → STOP, osobny dokument INFRA-2 (most gz↔PX4).
+  n_timejumps: RAPORTOWANY, NIE bramkujący — C1 wykazał, że „time jump" to artefakt licznika uxrce
+  Timesync (Timesync.cpp:69) referowanego do zegara ściennego; nie dotyka osi sim (Δt IMU 4000µs
+  jednorodny) ani EKF. Dlatego przestaje bramkować (był fałszywym negatywem dla zdrowych bootów).
+Interpretacja:
+  PASS ⇒ maszyna armuje end-to-end → wracamy do I3 (dziesiątka) na harnessie po rewercie I2b (P0a).
+  FAIL ⇒ dopiero wtedy wracamy do pytania o habitat, z S boot4/5/6 jako jedynym realnym trybem awarii.
 Dokładnie JEDEN shakeout — brak powtórki (powtarzanie do skutku = selekcja).
+Uwaga: poprzedni werdykt N3 (na harnessie I2b) WYCOFANY jako nieważny (mierzył deadlock, nie arm).
 
 Użycie: python3 tools/infra1_shakeout_check.py --dir results/K1/E/p0_0/bootS
 """
@@ -70,14 +74,15 @@ def main():
     except Exception:
         deep_pre = None
 
-    tj_ok = (n_tj is not None and n_tj <= TJ_MAX)
+    tj_ok = (n_tj is not None and n_tj <= TJ_MAX)  # RAPORTOWANE, już nie bramkuje (W3)
     stall_ok = (deep_pre is not None and deep_pre == 0)
-    verdict = "PASS" if (arm_ok and tj_ok and stall_ok) else "FAIL"
-    interp = ("PRZEJŚCIOWY zły lockstep po restarcie → wracamy do I3 (10 liczonych), kod NIEZMIENIONY"
+    verdict = "PASS" if (arm_ok and stall_ok) else "FAIL"  # W3: timejump zdjęty z bramki (artefakt uxrce, C1)
+    interp = ("maszyna armuje end-to-end → wracamy do I3 (10 liczonych) na harnessie po rewercie I2b"
               if verdict == "PASS" else
-              "TRWAŁA pętla timejump = własność habitatu → STOP, osobny dokument INFRA-2 (most gz↔PX4)")
+              "FAIL → pytanie o habitat, z S boot4/5/6 jako jedynym realnym trybem awarii")
 
-    out = {"verdict": verdict, "arm_ok": arm_ok, "n_timejumps": n_tj, "tj_max": TJ_MAX,
+    out = {"verdict": verdict, "arm_ok": arm_ok, "gate": "arm_ok ∧ deep_stalls==0 (timejump raportowany)",
+           "n_timejumps": n_tj, "tj_reported_only": True, "tj_advisory_max": TJ_MAX, "tj_within_advisory": tj_ok,
            "deep_stalls_preflight_to_arm": deep_pre, "deep_stall_rtf_thr": DEEP_STALL_RTF,
            "window_sim": [gt0_sim, armed_sim], "interpretation": interp, "dir": d}
     with open(os.path.join(d, "shakeout_check.json"), "w") as f:
```
