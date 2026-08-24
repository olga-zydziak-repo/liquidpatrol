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

---

# ANEKS_SHA — INFRA-1 ANEKS_INFRA1-4 (X1 okno checku + X3/X4 kampania) · 2026-08-24

**Poprawka przyrządu, nie harnessu — SI-1 nietknięte.**

## X1: infra1_shakeout_check.py — okno deep-stall = PX4 start → arm na osi sim, ŹRÓDŁO ulog (nie trace)
Powód: poprzednie okno [gt0_trace, arm] było ~3 s (trace startuje po 90 s settle) → mierzyło odcinek
start-modułu→arm, nie preflight. Nowe: pyulog ULog.start_timestamp → actuator_armed(0→1), oś sim
wspólna z rtf_stream (lockstep gz clock, C1). Fallback do trace gdy ulog/pyulog niedostępny.

## X2 (wynik): E boot3 przeliczony — deep-stalle w oknie preflight→arm:
  - STARE okno [89.94, 93.16] (~3 s): 0 deep-stalli → było PASS
  - NOWE okno [0.0, 93.16] (pełny preflight, ulog): 5 deep-stalli (sim 2.1/2.1/24.4/56.6/88.9)
  arm_ok=TRUE pozostaje FAKTEM (boot3 zaarmował @sim 93.16). Sub-bramka stall FAIL to artefakt
  kontencji gate2 (boot3 biegł pod 10 workerami) — dlatego X3 wymaga czystej maszyny dla I3.

## X3/X4: infra1_campaign.sh — I3 wyłącznie na czystej maszynie
  X3: przed 1. bootem load1 < 1.0 ∧ brak cudzych zadań (gate2/obcy proc >50% CPU) — inaczej REFUSE (exit 6).
  X4: przed każdym bootem to samo — kontencja w środku ⇒ ABORT serii (exit 5), licz OD NOWA (nie doliczaj).

## Piny frozen (BEZ ZMIAN):
```
4e0dc0afffda099837a002191a5540fd95d6de13cb88e7233433d67b1b998ae1  k1/k1_judge.py
1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2  r01/shield.py
4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a  r03/config.py
72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a  r03/gate_run_r03.py
```

## Diff verbatim infra1_shakeout_check.py (X1):
```diff
diff --git a/tools/infra1_shakeout_check.py b/tools/infra1_shakeout_check.py
index 3779b7c..00d1409 100644
--- a/tools/infra1_shakeout_check.py
+++ b/tools/infra1_shakeout_check.py
@@ -28,23 +28,46 @@ def main():
     a = ap.parse_args()
     d = a.dir
 
-    # arm_ok + okno preflight→arm z trace
+    # X1 (ANEKS_INFRA1-4): okno deep-stall = PX4 start → arm na OSI SIM, ŹRÓDŁO = ulog (nie trace).
+    # Poprzednie okno [gt0_trace, arm] było ~3 s (trace startuje po 90 s settle) → mierzyło odcinek
+    # start-modułu→arm, nie preflight. Nowe okno obejmuje pełny preflight (PX4 start → arm) na tej samej
+    # osi sim co rtf_stream (lockstep gz clock, dowód C1). Fallback do trace gdy ulog niedostępny.
     armed_sim = None
     arm_ok = False
-    gt0_sim = None
+    px4_start_sim = None
+    window_source = None
     try:
-        for line in open(os.path.join(d, "trace.jsonl"), errors="replace"):
-            line = line.strip()
-            if not line:
-                continue
-            r = json.loads(line)
-            if r.get("t") == "gt" and gt0_sim is None:
-                gt0_sim = r.get("sim")
-            if r.get("t") == "event" and r.get("ev") == "armed":
-                arm_ok = True
-                armed_sim = r.get("sim")
+        from pyulog import ULog
+        import numpy as np
+        u = ULog(os.path.join(d, "boot.ulg"), ["actuator_armed"])
+        px4_start_sim = float(u.start_timestamp) / 1e6
+        ds = u.get_dataset("actuator_armed")
+        ts = ds.data["timestamp"]; ar = ds.data["armed"]
+        idx = np.where(ar == 1)[0]
+        if len(idx):
+            arm_ok = True
+            armed_sim = float(ts[idx[0]]) / 1e6
+        window_source = "ulog"
     except Exception as e:
-        print(f"[shakeout] trace read err: {e}")
+        print(f"[shakeout] ulog read err ({e}) → fallback trace")
+
+    if window_source is None:  # fallback: stare źródło (trace) gdy brak ulog/pyulog
+        gt0 = None
+        try:
+            for line in open(os.path.join(d, "trace.jsonl"), errors="replace"):
+                line = line.strip()
+                if not line:
+                    continue
+                r = json.loads(line)
+                if r.get("t") == "gt" and gt0 is None:
+                    gt0 = r.get("sim")
+                if r.get("t") == "event" and r.get("ev") == "armed":
+                    arm_ok = True
+                    armed_sim = r.get("sim")
+            px4_start_sim = gt0
+            window_source = "trace(fallback)"
+        except Exception as e:
+            print(f"[shakeout] trace read err: {e}")
 
     # n_timejumps z px4.log (ta sama fraza co diagnoza)
     n_tj = 0
@@ -58,7 +81,7 @@ def main():
     # głębokie stalle rtf<0.5 w oknie preflight→arm (jeśli brak armed_sim, całe okno do końca rtf)
     deep_pre = None
     try:
-        lo = gt0_sim if gt0_sim is not None else -1e18
+        lo = px4_start_sim if px4_start_sim is not None else -1e18
         hi = armed_sim if armed_sim is not None else 1e18
         deep_pre = 0
         for line in open(os.path.join(d, "rtf_stream.jsonl"), errors="replace"):
@@ -84,7 +107,8 @@ def main():
     out = {"verdict": verdict, "arm_ok": arm_ok, "gate": "arm_ok ∧ deep_stalls==0 (timejump raportowany)",
            "n_timejumps": n_tj, "tj_reported_only": True, "tj_advisory_max": TJ_MAX, "tj_within_advisory": tj_ok,
            "deep_stalls_preflight_to_arm": deep_pre, "deep_stall_rtf_thr": DEEP_STALL_RTF,
-           "window_sim": [gt0_sim, armed_sim], "interpretation": interp, "dir": d}
+           "window_sim": [px4_start_sim, armed_sim], "window_source": window_source,
+           "interpretation": interp, "dir": d}
     with open(os.path.join(d, "shakeout_check.json"), "w") as f:
         json.dump(out, f, indent=2)
     print(json.dumps(out, indent=2, ensure_ascii=False))
```

## Diff verbatim infra1_campaign.sh (X3/X4):
```diff
diff --git a/tools/infra1_campaign.sh b/tools/infra1_campaign.sh
index a50f153..60c34ec 100755
--- a/tools/infra1_campaign.sh
+++ b/tools/infra1_campaign.sh
@@ -7,6 +7,10 @@ set -uo pipefail
 ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
 START="${1:-1}"; COUNT="${2:-10}"
 COOLDOWN_S="${COOLDOWN_S:-300}"
+# ANEKS_INFRA1-4 X3/X4: I3 wyłącznie na CZYSTEJ maszynie.
+IDLE_MAX_FIRST="${IDLE_MAX_FIRST:-1.0}"   # X3: load1 < 1.0 przed PIERWSZYM bootem (spoczynek)
+CONTENTION_MAX="${CONTENTION_MAX:-2.0}"   # X4: tripwire kontencji między bootami (po sweep+cooldown maszyna ~idle)
+FOREIGN_PAT="${FOREIGN_PAT:-src.runner.gate2}"  # znane cudze zadanie; + heurystyka %CPU poniżej
 LOG="$ROOT/results/K1/INFRA1/campaign.log"
 mkdir -p "$ROOT/results/K1/INFRA1"
 export K1_SESSION_BOOT_COUNT="${K1_SESSION_BOOT_COUNT:-1}" K1_ENV_RESTART="${K1_ENV_RESTART:-wsl-shutdown}"
@@ -16,11 +20,39 @@ sweep(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4 ' 2>/dev/null; pkill
   pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -f infra1_empty_flight 2>/dev/null
   pkill -9 -f rtf_sampler 2>/dev/null; sleep 3; }
 
+# X4: kontencja = znane cudze zadanie żyje LUB obcy proces >50% CPU spoza naszego stacku. Zwraca 0=jest.
+foreign_busy(){
+  pgrep -f "$FOREIGN_PAT" >/dev/null 2>&1 && { echo "foreign=$FOREIGN_PAT"; return 0; }
+  local hit
+  hit=$(ps -eo pcpu,args --sort=-pcpu 2>/dev/null | awk 'NR>1 && $1>50' \
+    | grep -vE 'run_k1_boot|px4|gz sim|ruby.*gz|MicroXRCE|mavsdk|rtf_sampler|infra1_empty_flight|infra1_campaign|pyulog|ulog|python3 -c|awk |grep |ps ' \
+    | head -1)
+  [ -n "$hit" ] && { echo "foreign_cpu=[$hit]"; return 0; }
+  return 1
+}
+
 echo "=== INFRA-1 campaign START=$START COUNT=$COUNT cooldown=${COOLDOWN_S}s $(date) ===" | tee -a "$LOG"
+
+# X3: bramka czystego startu — gate2 zakończone ∧ load spoczynkowy < IDLE_MAX_FIRST przed 1. bootem.
+_l1=$(cut -d' ' -f1 /proc/loadavg); _fb=$(foreign_busy || true)
+if foreign_busy >/dev/null 2>&1 || awk "BEGIN{exit !($_l1 >= $IDLE_MAX_FIRST)}"; then
+  echo "[campaign] X3 REFUSE start: load1=$_l1 (max $IDLE_MAX_FIRST) foreign=[$_fb] — maszyna NIE spoczynkowa. I3 tylko na czystej." | tee -a "$LOG"
+  exit 6
+fi
+echo "[campaign] X3 OK: load1=$_l1 < $IDLE_MAX_FIRST, brak cudzych zadań — start serii." | tee -a "$LOG"
+
 n="$START"; done_ct=0; attempts_this=0
 while [ "$done_ct" -lt "$COUNT" ]; do
+  # X4: kontencja w środku dziesiątki skaża porównywalność → przerwij serię, licz OD NOWA (nie doliczaj).
+  _l1=$(cut -d' ' -f1 /proc/loadavg)
+  if _fb=$(foreign_busy); then
+    echo "[campaign] X4 ABORT: kontencja w środku serii (done=$done_ct/$COUNT): $_fb load1=$_l1 — SERIA SKAŻONA, licz od nowa (nie doliczam)." | tee -a "$LOG"; exit 5
+  fi
+  if awk "BEGIN{exit !($_l1 >= $CONTENTION_MAX)}"; then
+    echo "[campaign] X4 ABORT: load1=$_l1 ≥ $CONTENTION_MAX po cooldown (done=$done_ct/$COUNT) — obca kontencja, SERIA SKAŻONA, licz od nowa." | tee -a "$LOG"; exit 5
+  fi
   orph=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); orph=${orph:-0}
-  echo "[campaign] boot$n : orphans_pre=$orph load1=$(cut -d' ' -f1 /proc/loadavg) $(date)" | tee -a "$LOG"
+  echo "[campaign] boot$n : orphans_pre=$orph load1=$_l1 $(date)" | tee -a "$LOG"
   sweep
   bash k1/run_k1_boot.sh E 0.0 "$n" > "$ROOT/results/K1/INFRA1/boot${n}.launch.log" 2>&1
   rc=$?
```
