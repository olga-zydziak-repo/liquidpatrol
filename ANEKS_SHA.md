# ANEKS_SHA — dowody wyjatkow W1/W2 przed pierwszym bootem (PRE_K1 / ANEKS_K1-2)

2026-08-22. Odpowiedz na ANEKS_K1-2 (W1, W2). Dowody = **wyjscie `git diff`/`sha256sum` wklejone
verbatim**, nie opis. Zaden boot nie zaszedl.

Notacja: `36c7c22a`/`4e0dc0af` to **sha256 zawartosci** `k1/k1_judge.py`, nie rewizje git. Odpowiadaja
plikom w commitach `6db3393` (frozen) i `0ce4d8e` (re-frozen):
```
6db3393:k1/k1_judge.py = 36c7c22acf9eac7605c9e70d160d783b6c5c2dd8a1bee8cb6360af1fc0517048
0ce4d8e:k1/k1_judge.py = 4e0dc0afffda099837a002191a5540fd95d6de13cb88e7233433d67b1b998ae1
```

---

## W1 — re-freeze sedziego `36c7c22a -> 4e0dc0af`

**Przyczyna (nazwana):** dry-run harnessu przed pierwszym bootem wykryl blad kontraktu
`eps_pos_touchdown`: zakladal, ze wiersze EKF niosa `sim`, a gate emituje EKF z `mono`+`ts` (px4 s),
bez `sim` -> eps_pos zwracalo `null`. Poprawka: parowanie EKF<->GT po **mono** (wspolny zegar odbioru)
z odjeciem **baseline offsetu ramki** (e0 z okna zdrowego) + unit-test eps_pos.

**W1(a) — diff ograniczony do eps_pos + unit-testu; ZADNA stala progowa ani galaz kryterium §4 nie
zmieniona.** Weryfikacja mechaniczna (grep diffu po progach/kryterium):
```
BRAK trafien — diff nie dotyka progow/kryterium §4
```

**W1(b) — pelny `git diff 6db3393 0ce4d8e -- k1/k1_judge.py` (verbatim):**
```diff
diff --git a/k1/k1_judge.py b/k1/k1_judge.py
index 4b0e12b..0b36644 100644
--- a/k1/k1_judge.py
+++ b/k1/k1_judge.py
@@ -275,8 +275,10 @@ def _land_ack_us(ud):
 # ----------------------------- ε_pos touchdown (ramię S) -----------------------------
 
 def eps_pos_touchdown(ekf_path, gt, t_touch):
-    """ε_pos = ||EKF_ned − GT_ned|| przy touchdown (ramię S, D13). GT ENU→NED: north=y, east=x.
-    Zwraca ε_pos [m] lub None. Prosta: najbliższe próbki EKF/GT do t_touch (sim)."""
+    """ε_pos = ||e(touchdown) − e0|| (ramię S, D13). e(t)=EKF_ned − GT_ned; GT ENU→NED: north=y, east=x.
+    Parowanie EKF↔GT po MONO (wspólny zegar odbioru — EKF ma mono+ts px4, NIE sim); e0 = baseline
+    zdrowego okna (pierwsze BASE_WIN_S) usuwa stały offset ramki home↔gz-world. Zwraca ε_pos [m] lub None."""
+    BASE_WIN_S = 5.0
     ekf = []
     with open(ekf_path) as f:
         for line in f:
@@ -287,20 +289,40 @@ def eps_pos_touchdown(ekf_path, gt, t_touch):
                 r = json.loads(line)
             except Exception:
                 continue
-            if r.get("t") not in (None, "ekf"):
-                continue
-            if "sim" in r and "x" in r and "y" in r:
+            if r.get("t") == "ekf" and "mono" in r and "x" in r and "y" in r:
                 ekf.append(r)
-    if not ekf:
+    return _eps_core(ekf, gt, t_touch, BASE_WIN_S)
+
+
+def _eps_core(ekf, gt, t_touch, BASE_WIN_S=5.0):
+    gtm = [g for g in gt if "mono" in g]
+    if not ekf or not gtm:
         return None
-    ekf.sort(key=lambda r: r["sim"])
-    e = min(ekf, key=lambda r: abs(r["sim"] - t_touch))
-    g = _interp_xy(gt, t_touch)
-    if g is None or abs(e["sim"] - t_touch) > GT_MATCH_TOL_S:
+    ekf.sort(key=lambda r: r["mono"])
+    gtm.sort(key=lambda r: r["mono"])
+
+    def e_vec(er, gr):
+        return (er["x"] - gr["y"], er["y"] - gr["x"])     # NED − (ENU→NED swap): north=gr.y, east=gr.x
+
+    def nearest_gt(mono):
+        return min(gtm, key=lambda r: abs(r["mono"] - mono))
+
+    # baseline e0 z pierwszych BASE_WIN_S (zawis w home — stały offset ramki)
+    t0 = ekf[0]["mono"]
+    base = [e_vec(e, nearest_gt(e["mono"])) for e in ekf if e["mono"] <= t0 + BASE_WIN_S]
+    if not base:
+        base = [e_vec(ekf[0], nearest_gt(ekf[0]["mono"]))]
+    e0 = (sum(b[0] for b in base) / len(base), sum(b[1] for b in base) / len(base))
+
+    # touchdown mono z wiersza GT najbliższego t_touch (sim)
+    gt_td = min(gt, key=lambda r: abs(r.get("sim", 1e18) - t_touch))
+    tm = gt_td.get("mono")
+    if tm is None:
         return None
-    gx, gy, _ = g
-    north_gt, east_gt = gy, gx           # ENU→NED (swap, R-2)
-    return round(math.hypot(e["x"] - north_gt, e["y"] - east_gt), 3)
+    e = min(ekf, key=lambda r: abs(r["mono"] - tm))
+    g = nearest_gt(tm)
+    ev = e_vec(e, g)
+    return round(math.hypot(ev[0] - e0[0], ev[1] - e0[1]), 3)
 
 
 # ----------------------------- assemble -----------------------------
@@ -438,6 +460,25 @@ def selftest():
     print(f"-- breach TRUE gdy r_max>{R_E}: r_max={m['r_max']} breach={m['breach']} "
           f"{'PASS' if cb else 'FAIL'}")
 
+    # ε_pos (ramię S): stały offset ramki off + dryf przy touchdown → ε = ||dryf||
+    off_n, off_e = 0.4, -0.3          # offset home↔world (NED)
+    dn, de = 1.5, 2.0                 # dryf EKF przy touchdown
+    gtE, gtN = 2.0, 1.0               # GT stały ENU (E,N) → NED (north=1, east=2)
+    ekf, gtl = [], []
+    dt = 0.1
+    for i in range(200):              # 0..20 s
+        t = round(i * dt, 4)
+        drift = (i >= 150)            # dryf od 15 s (touchdown ~19.9 s)
+        ekf.append({"t": "ekf", "mono": t,
+                    "x": gtN + off_n + (dn if drift else 0.0),      # NED north
+                    "y": gtE + off_e + (de if drift else 0.0)})     # NED east
+        gtl.append({"t": "gt", "mono": t, "sim": 1000.0 + t, "x": gtE, "y": gtN, "z": 5.0})
+    eps = _eps_core(ekf, gtl, t_touch=1000.0 + 19.9)
+    ce = eps is not None and abs(eps - math.hypot(dn, de)) < 0.02
+    ok = ok and ce
+    print(f"-- ε_pos (offset ramki usunięty, dryf {math.hypot(dn,de):.2f}): got={eps} "
+          f"exp={round(math.hypot(dn,de),3)} {'PASS' if ce else 'FAIL'}")
+
     print(f"\nWYNIK: {'PASS — sędzia zwalidowany, wolno liczyć biegi K1' if ok else 'FAIL — NIE liczyć'}")
     return ok
```
Zakres: `eps_pos_touchdown` przepisane (parowanie po mono + baseline), wydzielony pure-core `_eps_core`,
dodany case eps_pos w `selftest()`. Metryki kryterialne (`r_max`, `x_exc`, `breach`, `R_E`) i logika
werdyktu — nietkniete.

**W1(c):** od pierwszego bootu obowiazuje SR-K3 bez wyjatkow. Przyjete.

---

## W2 — `SCEN=K1` w `r03/gate_run_r03.py` (wyjatek od „kod r03 bajt-w-bajt", jedyny)

### W2 — USTALENIE BAZY (wymaga ratyfikacji Olgi)

„Bramka 4/4" = commit **`a088367`** („R03A BRAMKA 4/4 LIVE PASS: S1/S2/S3/S4"). **Literalna
bajt-rownosc plikow oslony do `a088367` jest NIEOSIAGALNA** — pliki oslony ewoluowaly przez
RATYFIKOWANE prace PO 4/4, niezalezne od K1:

| plik | commit po 4/4 | co zmienil | dotyka POS_DEGRADED / zejscia D5? |
|---|---|---|---|
| `r01/shield.py` | `01f47e8` (D_B1 §2/§4) | +param `auth_ok=True` do `step()`, +reason NO_AUTH (token) | **NIE** (ortogonalny; w ramieniu S `step()` wolane bez `auth_ok` => default True => sciezka NO_AUTH nieaktywna) |
| `r03/config.py` | `5a6a18d` (PROMPT_K1 §0) | +1 komentarz erratum | **NIE** |
| `r03/gate_run_r03.py` | `e732c10` (D_B3 §1) | trace schema v2 (wiersze tick) | **NIE** (opisowe) |
| `r03/gate_run_r03.py` | `0ce4d8e` (ten K1) | +galaz SCEN=K1 (punkt wstrzykniecia) | **NIE** (blok is_pos/zejscia/shield.step nietkniety — dowod nizej) |

**Rekomendacja CC:** baza W2 = **`6db3393`** (aktualna baza certyfikowana: R03A 4/4 -> B1 token ->
B3 trace -> §0 erratum, wszystko ratyfikowane). Wzgledem `6db3393` oslona jest bajt-identyczna
(dowod nizej), a `POS_DEGRADED`->D5 zachowanie efektywnie identyczne z `a088367`. **Decyzja o bazie
nalezy do Olgi** — nie moge uczciwie twierdzic „== a088367" (to nieprawda po ratyfikowanych zmianach).

### W2(a) — sha256 modulow oslony (pelne sciezki), stan HEAD `0ce4d8e`
```
1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2  r01/shield.py          (PatrolShield, REFUSE, POS_DEGRADED)
4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a  r03/config.py          (config, stale D5: V_DESC_FAST/LAND, H_SWITCH_AGL, R_ROUTE_P)
19967de2ed5d35cc05f05f408def8f9de265d9f71136c99b40b074cebcd3a01c  r03/gate_run_r03.py    (logika REFUSE->zejscie D5 + harness)
```
**shield.py i config.py sa bajt-identyczne `6db3393` <-> `0ce4d8e`** (K1 ich nie tknal):
```
r01/shield.py: 6db3393=1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2
               0ce4d8e=1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2  [IDENTYCZNE]
r03/config.py: 6db3393=4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a
               0ce4d8e=4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a  [IDENTYCZNE]
```

**Dowod: `SCEN=K1` NIE dotyka bloku zejscia/REFUSE/shield.step — `git diff 6db3393 0ce4d8e --
r03/gate_run_r03.py` (verbatim):**
```diff
diff --git a/r03/gate_run_r03.py b/r03/gate_run_r03.py
index 389d176..533ca0a 100644
--- a/r03/gate_run_r03.py
+++ b/r03/gate_run_r03.py
@@ -30,6 +30,9 @@ from r03 import config as C
 SCEN = os.environ.get("SCEN", "S2")
 OUT = os.environ.get("GATE_OUT", f"/tmp/r03gate/{SCEN}.jsonl")
 S1_MIN = float(os.environ.get("S1_MIN", "5"))
+# K1 (PRE_K1 §2, ramię S): wstrzyknięcie na PIERWSZEJ nodze po PIERWSZYM narożniku, przy UŁAMKU nogi
+# K1_POINT ∈ {0.2,0.35,0.5,0.65,0.8}. Osłona/zejście/config NIETKNIĘTE — tylko punkt wstrzyknięcia.
+K1_POINT = float(os.environ.get("K1_POINT", "0.5"))
 WORLD = os.environ.get("PX4_GZ_WORLD", "default")
 MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
 GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
@@ -226,14 +229,23 @@ async def main():
             seg_i += 1
         tgt = (wp[0], wp[1], -ALT)
         # denial injection
+        _k1_fa = None
         if SCEN == "S4":
             trigger = (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0  # przy narożniku, v_max
+        elif SCEN == "K1":
+            _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])   # długość 1. nogi po narożniku
+            _k1_fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
+            trigger = (not denial_done) and seg_i == 1 and _k1_fa >= K1_POINT  # ułamek nogi
         else:
             trigger = (not denial_done) and now >= denial_at
         if trigger:
             await d.param.set_param_int("EKF2_GPS_CTRL", 0)
-            _w({"t": "event", "mono": round(time.monotonic(), 4), "ev": "denial_on",
-                "r_est_at_cut": round(r_est, 3), "speed_at_cut": round(math.hypot(vel[0], vel[1]), 3)})
+            _ev = {"t": "event", "mono": round(time.monotonic(), 4), "ev": "denial_on",
+                   "r_est_at_cut": round(r_est, 3), "speed_at_cut": round(math.hypot(vel[0], vel[1]), 3)}
+            if SCEN == "K1":
+                _ev["k1_point"] = K1_POINT
+                _ev["k1_f_along"] = round(_k1_fa, 3) if _k1_fa is not None else None
+            _w(_ev)
             print(f"[gate {SCEN}] denial_on r_est={r_est:.2f} v={math.hypot(vel[0],vel[1]):.2f}", flush=True)
             denial_done = True; denial_t = now
         # recovery (S3): 0→7 w locie
@@ -276,7 +288,8 @@ async def main():
         tick += 1
         if SCEN == "S1" and now >= s1_dur:
             ev("s1_done"); break
-        if now > (denial_at + 90 if denial_done else max(s1_dur, 400) + 30):
+        _to_ref = (denial_t if denial_t is not None else denial_at)   # K1: denial_at=1e9 → użyj denial_t
+        if now > (_to_ref + 90 if denial_done else max(s1_dur, 400) + 30):
             ev("timeout"); break
         await asyncio.sleep(C.DT)
```

**Kontekst 4/4: `git diff a088367 0ce4d8e -- r01/shield.py` (D_B1 token — POS_DEGRADED nietkniety):**
```diff
diff --git a/r01/shield.py b/r01/shield.py
index dc619bf..bb9800a 100644
--- a/r01/shield.py
+++ b/r01/shield.py
@@ -12,10 +12,16 @@ Reguły (priorytet = kontrakt):
   R-A  ABORT: operator kończy misję → REFUSE(ABORT) (bezpieczne zatrzymanie).
   R-H  HOLD: tryb HOLD → podmiana na hold-setpoint (pozycja bieżąca, v=0).
   R-R  RETURN: tryb RETURN → hold do przejęcia przez RTL (MAVSDK).
-  R-O  OBSERVE (R0.2, 7. liść): tryb OBSERVE → ALLOW, przepuść setpoint obserwacji (pierścień
+  R-O  OBSERVE (R0.2, 7. liść): tryb OBSERVE ∧ auth_ok → ALLOW, przepuść setpoint obserwacji (pierścień
        D_safe, bearing-only z kanału). PONIŻEJ R-G: setpoint OBSERVE za płot jest przecięty przez
        R-G tak jak waypoint patrolu (geofence nadrzędny z PRIORYTETU, nie nowej reguły — PRE §2.4).
        OBSERVE nie zmienia v_max/clampów/obwiedni (R02-A3).
+  R-AUTH NO_AUTH (DEMO-B, 6. reason): tryb OBSERVE ∧ ¬auth_ok (eskalacja bez ważnego tokenu operatora)
+       → REFUSE(NO_AUTH). ODWRACALNY, NIETERMINALNY (wzorzec POS_DEGRADED, nie latch): brak eskalacji,
+       patrol/confirm trwa; po nadaniu tokenu OBSERVE staje otworem. PONIŻEJ R-G i R-POS (dominują —
+       ANEKS_D1 §Semantyka.5): R-AUTH żyje wewnątrz gałęzi OBSERVE, więc latch/R-POS/R-G/abort ją
+       wyprzedzają. `auth_ok` = wejście boolowskie z warstwy authz (podpis∧nonce∧epizod∧niekonsumowany);
+       osłona (TCB) realizuje TYLKO gałąź decyzji (§1.6). Token = bramkowanie uprawnień, NIE „secure C2".
   R-P  PATROL: ALLOW → przepuść setpoint planera.
 HOLD/REFUSE NIE urywają strumienia (A1/§4): applied = hold-setpoint, strumień żyje < COM_OF_LOSS_T.
 
@@ -29,10 +35,12 @@ ALLOW, HOLD, REFUSE = "ALLOW", "HOLD", "REFUSE"
 # stany
 PATROL, HOLDING, RETURNING, DONE = "PATROL", "HOLDING", "RETURNING", "DONE"
 POSDEG = "POSDEG"                  # R0.3a: stan REFUSE(POS_DEGRADED) — ODWRACALNY (nie DONE/terminal)
+NOAUTH = "NOAUTH"                  # DEMO-B: stan REFUSE(NO_AUTH) — ODWRACALNY (nie DONE/terminal)
 # powody
 GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT = \
     "GEOFENCE", "COMMAND_INVALID", "STALE_CMD", "ABORT"
 POS_DEGRADED = "POS_DEGRADED"      # R0.3a: 5. reason (D3) — zdegradowane zdrowie pozycji (GPS-denied)
+NO_AUTH = "NO_AUTH"                # DEMO-B: 6. reason — eskalacja OBSERVE bez ważnego tokenu operatora
 # tryby (z admitowanych komend)
 M_PATROL, M_HOLD, M_RETURN, M_ABORT = "PATROL", "HOLD", "RETURN", "ABORT"
 M_OBSERVE = "OBSERVE"           # R0.2: tryb OBSERVE (auto-wyzwalany kanałem, autoryzowany gramatyką P4)
@@ -110,9 +118,9 @@ class PatrolShield:
             self.state = DONE
 
     # -- pojedynczy tick ----------------------------------------------------
-    def step(self, k, pos, vel, target, mode=M_PATROL, pos_flag=None):
+    def step(self, k, pos, vel, target, mode=M_PATROL, pos_flag=None, auth_ok=True):
         self._pos_monitor(pos_flag)
-        d = self._decide(k, pos, vel, target, mode)
+        d = self._decide(k, pos, vel, target, mode, auth_ok)
         d["t"] = round(k * self.cfg.dt, 4)
         d["values"] = {
             "pos": [round(float(pos[0]), 3), round(float(pos[1]), 3), round(float(pos[2]), 3)],
@@ -120,6 +128,7 @@ class PatrolShield:
             "r_pos": round(_radial(pos[0], pos[1]), 3),
             "r_target": round(_radial(target[0], target[1]), 3),
             "mode": mode,
+            "auth_ok": bool(auth_ok),
         }
         # księgowość HOLD (wejścia/wyjścia)
         is_hold = d["decision"] == HOLD
@@ -134,7 +143,7 @@ class PatrolShield:
     def _hold_setpoint(self, pos):
         return [float(pos[0]), float(pos[1]), float(pos[2])]
 
-    def _decide(self, k, pos, vel, target, mode):
+    def _decide(self, k, pos, vel, target, mode, auth_ok=True):
         # R-T terminal
         if self.terminal is not None:
             r, rule = self.terminal
@@ -179,6 +188,14 @@ class PatrolShield:
         # D_safe z kanału, wyliczony w egzekutorze). PONIŻEJ R-G: gdy setpoint OBSERVE za płotem,
         # R-G (wyżej) już zwrócił REFUSE(GEOFENCE) — tu docieramy tylko gdy geofence-bezpiecznie.
         if mode == M_OBSERVE:
+            # R-AUTH (DEMO-B, 6. reason): eskalacja OBSERVE bez tokenu ⇒ REFUSE(NO_AUTH). ODWRACALNY,
+            # NIETERMINALNY (nie latch, nie DONE) — jak POS_DEGRADED. Brak eskalacji: applied=hold
+            # (patrol/confirm trwa), po nadaniu tokenu (auth_ok) ta sama gałąź daje OBSERVE (ALLOW).
+            if not auth_ok:
+                self.state = NOAUTH            # stan odwracalny (nie DONE — nie terminal)
+                return {"k": k, "state": NOAUTH, "decision": REFUSE, "reason": NO_AUTH,
+                        "rule": "R-AUTH", "detail": "eskalacja OBSERVE bez tokenu operatora",
+                        "applied": self._hold_setpoint(pos)}
             self.state = OBSERVING
             return {"k": k, "state": OBSERVING, "decision": ALLOW, "reason": None, "rule": "R-O",
                     "applied": [float(target[0]), float(target[1]), float(target[2])]}
```
**`git diff a088367 0ce4d8e -- r03/config.py` (tylko komentarz erratum):**
```diff
diff --git a/r03/config.py b/r03/config.py
index 21d3367..f0f6b7d 100644
--- a/r03/config.py
+++ b/r03/config.py
@@ -33,6 +33,7 @@ POS_REFUSE_BOUND_S = DEBOUNCE_TICKS * DT + DT   # (a) D13: debounce + 1 tick = 0
 
 # --- akcja bezpieczna: zejście STEROWANE PRĘDKOŚCIĄ, dwufazowe (D5 zrew. §3quater) ---
 # AUTO.LAND (position-hold) WYKLUCZONY (flyaway 42 m pod DR). Lista zamknięta komend osłony:
+# ERRATUM_42M (PRE_K1 §0): "42 m" asserted 09.08, run not preserved — superseded by K1 measurement (PRE_K1); see results/K1/ERRATUM_42M.md
 #   {velocity-setpoint (patrol/OBSERVE), velocity-descent (POS_DEGRADED)}.
 V_DESC_FAST = 1.5                        # MPC_Z_VEL_MAX_DN (limit VRS PX4) — faza 1 do H_SWITCH
 V_DESC_LAND = 0.7                        # MPC_LAND_SPEED — faza 2 do touchdown
```

### W2(b) — asercja hashy per bieg S
`k1/k1_finalize.py` przy KAZDYM biegu S liczy sha256 `r01/shield.py`, `r03/config.py`,
`r03/gate_run_r03.py` i porownuje z zapietymi wartosciami (`k1/k1_shield_pins.py`). **Niezgodnosc =>
bieg niewazny** (`shield_frozen=False` w manifescie, sedzia nie liczony).

### W2(c) — test: punkt wstrzykniecia S2/S3/S4 identyczny
`tools/test_k1_shield.py` — czysta replika logiki triggera; dla SCEN∈{S2,S3,S4} trigger identyczny
przed i po dodaniu galezi K1 (siatka seg_i×dist×now). PASS.

**Drugiego wyjatku w r03 nie bedzie** (W2 przyjete): jesli S@0.2 wymaga kolejnej zmiany w r03 — STOP
i decyzja, nie poprawka.

---

## Status wg W3
- **W1: spelniony** (diff wklejony, zero zmian progow/§4, oba hashe+przyczyna, SR-K3 od 1. bootu).
- **W2: spelniony CO DO TRESCI** (oslona bajt-identyczna vs baza `6db3393`; POS_DEGRADED/D5 nietkniete;
  asercja per-bieg + test) — **ale wymaga ratyfikacji BAZY** (`6db3393` zamiast nieosiagalnego
  `a088367`). Bez tej ratyfikacji nie pushuje/bootuje.


---

## H3 (ANEKS_K1-4) — zasieg bugu #2 (truthy h2_pass) — DEMO-B NIETKNIETE

**H3(a): bug truthy zyl WYLACZNIE w `k1_finalize`, nie w module wspoldzielonym.**
`h2_pass` zwraca krotke `(bool, reason)`. Bledne uzycie (traktowanie krotki jako bool) bylo w
`k1/k1_finalize.py:127-128 @ 0ce4d8e`:
```
127:                     seg_ok = HG.h2_pass(seg_m)
128:             verdict = "VALID" if (h1.get("pass") and seg_ok) else "INVALID(habitat)"
```
(`seg_ok` = krotka `(bool,str)` → zawsze truthy → verdict zawsze VALID.)

Modul wspoldzielony `acts/habitat_gate.py` konsumuje `h2_pass` **poprawnie** — `ok, why = h2_pass(m)`
(`:259`), i tak bylo od jego POWSTANIA. Historia pliku = JEDEN commit:
```
9d9f7e3 D_B7 §7b/§7c: bramka HABITATU commitowana PRZED próbami (antyselekcja)
```
Plik nie istnial @ a088367/e732c10 (BRAK PLIKU). → **habitat_gate byl zawsze poprawny; DEMO-B (A1
v1.0/v3/v3.1, A3) osadzane tym gate'em NIE sa dotkniete.**

**H3(c): bug tylko w k1_finalize — jedna linia, koniec.** H3(b) (re-ewaluacja DEMO-B, tabela
przed/po) NIEWYZWOLONE. Zero flipow w DEMO-B (nie bylo czego flipowac). RAPORT_K1 dostaje jedna linie;
brak erratum #2 dla DEMO-B.

## Fixy instrumentacji K1 (finalize/glue, sedzia 4e0dc0af nietkniety)
Naprawione PRZED zamknieciem STOP-u R2 (surowe dane bootow kompletne → re-finalize deterministyczny):
1. **pin ulog→sim** (`4cd7410`): ekf.ts EPOCH → kotwica OFFBOARD, C≈−0.03 s.
2. **bramka habitatu → PRE §2** (`cf317ef`): truthy fix + prog Δsim/Δwall≥0.95 (A3-strict informacyjny).
3. **ANEKS_K1-4**: segment roszczenia = touchdown FIZYCZNY (GT z≤0.5), nie timer bramki (~8 s);
   H1 stall-w-oknie-reakcji (informacyjny); H2(a) t_td vs profil D5 z config (gate przelacza faze PO
   CZASIE → przy h0<8 touchdown w fazie1); H2(b) nav_seq znakowany post-touchdown; numpy jdefault.
