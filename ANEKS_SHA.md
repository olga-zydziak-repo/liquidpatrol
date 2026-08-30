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

## §W3 — naprawa defektu K1_POINT (ANEKS_K1-6 F2) — diff verbatim, gałąź K1 wyłącznie

**Defekt (stale-dist):** po `if dist < 1.0: seg_i += 1` wyrażenie `f_along` liczyło `(_leg - dist)/_leg`
ze STALE `dist` (odległość do STAREGO celu = narożnik-0, <1.0 m) → `f_along ∈ [0.965, 1.0]` na 1. ticku
`seg_i==1` → wstrzyknięcie odpalało NATYCHMIAST przy narożniku-0 dla KAŻDEGO `K1_POINT ≤ 0.96`.
Skutek: `K1_POINT` ignorowany, pięć punktów {0.2,0.35,0.5,0.65,0.8} kolapsowało do jednego (r≈19 m).
Dowód z danych: S@0.2 boot2 i N@0.2 boot1 — oba `k1_f_along=0.966`, r_est≈18.96/18.99 (identyczne).

**Naprawa:** `f_along` liczony względem AKTUALNEGO celu `wps[seg_i]` PO inkrementacji (osobny
`_cur_dist`); `dist`/tgt/setpoint NIETKNIĘTE. Zmiana OGRANICZONA do gałęzi `SCEN=="K1"` (gate) /
triggera K1 (ramię N). Blok is_pos/zejścia/shield.step NIETKNIĘTY. S2/S3/S4 identyczne (test
`test_injection_point_S2_S3_S4_unchanged` PASS). Oba ramiona: rdzeń `(_leg - _cur_dist)/_leg`
bajt-identyczny (test `test_K1_branch_identical_both_arms` PASS). Trajektoria syntetyczna: dla
5 punktów `|f_along − K1_POINT| ≤ 0.0025` (test `test_K1_point_honored_on_trajectory` PASS);
wariant narożnikowy `f≈0` nie odpala (`test_K1_corner_variant_not_passthrough` PASS).

### k1/k1_arm_n.py (ramię N)
```diff
@@ async def main():
         if dist < 1.0:
             seg_i += 1
-        # trigger K1: pierwsza noga po pierwszym narożniku (seg_i==1), ułamek nogi
+        # trigger K1: ... f_along względem AKTUALNEGO celu wps[seg_i] po inkrementacji (defekt stale-dist)
         _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
-        _fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
+        _cur = wps[seg_i % len(wps)]
+        _cur_dist = math.hypot(_cur[0] - pos[0], _cur[1] - pos[1])
+        _fa = (_leg - _cur_dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
         if (not injected) and seg_i == 1 and _fa >= K1_POINT:
```

### r03/gate_run_r03.py (ramię S) — gałąź `elif SCEN == "K1":`
```diff
         elif SCEN == "K1":
+            # ANEKS_K1-6 F2: f_along względem AKTUALNEGO celu wps[seg_i] po seg_i+=1 (osobny _cur_dist)
             _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
-            _k1_fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
+            _cur = wps[seg_i % len(wps)]
+            _cur_dist = math.hypot(_cur[0] - pos[0], _cur[1] - pos[1])
+            _k1_fa = (_leg - _cur_dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
             trigger = (not denial_done) and seg_i == 1 and _k1_fa >= K1_POINT  # ułamek nogi
```

### SHIELD_PINS re-baseline (F2c) — TYLKO gate; shield.py/config.py NIEZMIENIONE
```diff
-    "r03/gate_run_r03.py": "19967de2ed5d35cc05f05f408def8f9de265d9f71136c99b40b074cebcd3a01c",
+    "r03/gate_run_r03.py": "72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a",
```
shield.py `1c584964…`, config.py `4c440e42…` — bez zmian (weryfikacja: `k1_shield_pins.py` self-check
3/3 OK). Test `test_shield_pins_frozen` PASS z nowym pinem gate.

## §W4 — checkpoint geometryczny (ANEKS_K1-6 F3) + relabel diag (F4) + stalle (F1)
- **F3:** `k1_finalize` liczy `spec_check` = `|k1_f_along − K1_POINT| ≤ 0.02 ∧ |r_est_at_cut − r_geom| ≤ 2 m`.
  Niezgodność ⇒ `run_valid=False`, `invalid_reason="spec-mismatch"`, `kind="diag"`, gdy `f≥0.9` →
  `point_label="corner0-passthrough"`. (Sędzia 4e0dc0af NIETKNIĘTY — to warstwa finalize/manifest.)
- **F1:** manifest per boot: `stalls` (rtf<0.5 z rtf_stream) + `n_deep_ge2s` + `period_hint_s`.
  Stall ~32 s = artefakt środowiska (D8), OBECNY W OBU RAMIONACH (S boot2 też: 4 deep, period ~32 s) —
  niezależny od ramienia; N boot1 INVALID(habitat) tylko dlatego, że jeden stall trafił w krótkie okno
  roszczenia. Bez zmian w harnessie/kryterium (F1).
- **F4:** S@0.2 boot2 i N@0.2 boot1 przeetykietowane `kind=diag`, `point_label=corner0-passthrough`,
  `run_valid=False` (mislabel f≈0.97 sprzed naprawy). `sha_harness` NIETKNIĘTY (kod, którym latano).
  Wyłączone z tabel §I; w §V jako ślad instrumentu. Budżet (S,0.2)/(N,0.2) = 3 loty OD NOWA; licznik
  env-fail (N) zostaje 2 (środowisko, nie punkt). Relabel = z logu eventów, jednakowy dla obu ramion.

## §W5 — ANEKS_K1-7 G1/G2: r-check zdjęty jako bramka + check parowania S↔N

**G1 (mój błąd projektowy w ANEKS_K1-6 F3):** człon r-geometrii ZDJĘTY jako bramka. Model `r_expected`
= promień idealnej łamanej — błędny przy skracaniu narożnika (GT: r od ~20.7 na wierzchołku do ~12.9
w zakręcie na TEJ SAMEJ nodze; przy f≈0.2 punkt leży w transiencie skrętu). `f_along` już kotwiczy
geometrię punktu. Nowa bramka: **`run_valid = habitat VALID ∧ |k1_f_along − K1_POINT| ≤ 0.02`**.
`r_est`, `speed`, `heading`, wektor v (`inj_info`) zostają w manifeście WYŁĄCZNIE informacyjnie
(`spec_check.r_geom_informational=True`, `r_ok` liczony ale nie bramkuje). `k1_finalize` (sędzia
4e0dc0af NIETKNIĘTY). **S@0.2 boot3 = WAŻNY (1/5)**: habitat VALID ∧ f_along=0.21 (|Δ|=0.01).

**G2 (warstwa agregatu, NIE sędzia):** check parowania S↔N — progi ZAMROŻONE przed 1. biegiem N:
`|r_inj_S − r_inj_N| ≤ 1.0 m ∧ |‖v‖_inj_S − ‖v‖_inj_N| ≤ 0.3 m/s ∧ |Δheading| ≤ 10°`
(`k1_aggregate.PAIR_TOL`). Kinematyka z `manifest.inj_info` (oba ramiona z EKF — spójny instrument;
N nie loguje speed_at_cut w evencie, więc oba z EKF w finalize). Niezgodność ⇒ punkt NIESPAROWANY,
oba loty → diag, punkt wykluczony z kryterium i liczony ponownie w budżecie. `pairing_check()` +
integracja w `aggregate(runs, inj_by)` + 4 selftesty PASS. `--manifests` glob w main.

## §W6 — ANEKS_K1-7 G4: prędkość w zakręcie > założenie twierdzenia (STOP przed N@0.2)

**Egzekucja limitu (cytat):** oba ramiona zadają setpoint znormalizowany:
`vn, ve = (VMAX*dx/dist, VMAX*dy/dist)` (`k1_arm_n.py:213`, `gate_run_r03.py:291`) → ‖(vn,ve)‖ = VMAX
= **NORMA**, nie per-oś. Vertical zadany = 0. `V_MAX = 3.0` (`r01/config.py:24`, „clamp prędkości
poziomej"). **`speed_at_cut = hypot(vel[0], vel[1])`** (`gate_run_r03.py:249`) = FAKTYCZNA estymata EKF.

**Założenie twierdzenia (cytat):** `DELTA_MARGIN = d_stop = V_MAX·T_REACT_S + V_MAX²/(2·A_BRAKE) =
0.6 + 2.25 = 2.85 m` (`r01/config.py:27`), z `V_MAX=3.0`. Twierdzenie zawierania:
`(r_est ≤ R_route') ∧ (ε_pos ≤ ε_cap) ∧ (r_true ≤ r_est+ε_pos) ⇒ r_true + d_stop ≤ R_E`
(`RAPORT_R03A.md:19`, `PRE_R03A.md:14/154-156`). `d_stop` = FIZYCZNA droga hamowania → zależy od
FAKTYCZNEJ ‖v‖. Twierdzenie zakłada więc ‖v‖ ≤ V_MAX = 3.0.

**Pomiar @ wstrzyknięciu 0.2 (S boot3):** commanded=3.0 · EKF=3.738 · **GT (fizyczna)=5.37 m/s**.
d_stop przy tych: 2.85 (zał.) / 4.24 (EKF) / **8.28 m (GT)**. Cruise na prostej ≈3.16 (GT); spike do
5.37 jest transientem skręcania (0.2 w zakręcie, wektor v NIE ∥ noga — ANEKS_K1-7 G3). EKF
NIEDOSZACOWUJE GT (3.74 vs 5.37).

**Werdykt G4:** norma ≤3.0 egzekwowana na ZADANEJ, ale FAKTYCZNA (3.74 EKF / 5.37 GT) przekracza
V_MAX=3.0 przyjęte przez d_stop twierdzenia. To NIE „inne źródło" (nie pion, nie jednostki) — to
faktyczna > zadana w zakręcie. **Wykracza poza K1 (scope P2-ε w R0.3a); nie do przypisu → STOP przed
N@0.2, osobna decyzja Olgi.** Bez lotu N.

## §W7 — ANEKS_K1-8 V2–V5: obwiednia V_env, checkpoint, erratum #2

**V2 (offline, S@0.2 boot3, 4 źródła):** ‖v_GT‖ = central diff pozycji GT (ENU, gz), Δt=sim (lockstep),
pół-okno 0.2 s. Tabela regime'ów: prosta GT 3.16 · **zakręt GT 5.34** · takeoff 5.26 · descent 5.79 ·
landing-skid 7.94. EKF /fmu i ulog vlp = TEN SAM estymator → zakręt 3.74 (zaniżają GT o ~1.6). setpoint
=3.0 (konstr.). r_apex_max(GT, narożnik-0)=20.654. GT czysty (cięciwa zaniża na krzywej → 5.34 dolne).
**V3 (prereg):** V_true_max(zakręt,GT)=5.342 → V_env=6.0 → d_stop(6.0)=10.2 (T_REACT=0.20/A_BRAKE=2.0,
r01/config.py:25-26) → **C_margin = 32−(20.654+10.2) = 1.146 > 0 → K1 BIEGNIE DALEJ.** Realny koincydentny
max(r+d_stop(v))=23.94 (margines 8.06). Checkpoint per boot `vmax_check`: ‖v_GT‖_max(offboard→denial) ≤
V_env=6.0; przekroczenie=FLAGA (nie unieważnia, §4 bez zmian). boot3: v_gt_max_cruise=5.342 PASS.
**V4:** `ERRATUM_VMAX.md` + adnotacje in-place RAPORT_R03A (nagłówek + linia „11.69 m") i RAPORT_D_B5.
**V5:** stała-ograniczenie-fizyczne ⇒ zmierzone max w manifeście + asercja obwiedni. „Limit zadany ≠
limit faktyczny" ∈ „asercja ≠ pomiar". `k1_finalize.V_ENV=6.0` (zamrożona), `_gt_cruise_vmax`.

## §W8 — ANEKS_K1-9 R2/R3/R4: checkpoint A_BRAKE, parowanie+wysokość, nota landing-skid

**R2 (checkpoint A_BRAKE, ramię S):** z ‖v_GT‖ po REFUSE — t_brake do ‖v‖<0.3, a_meas=v_REFUSE/t_brake,
flaga a_meas ≥ A_BRAKE=2.0 (`k1_finalize._abrake_check`). Przekroczenie w dół = FLAGA (nie unieważnia,
§4 bez zmian; do RAPORT §IV jako naruszenie przesłanki). Policzone WSTECZ (zero lotów):
- **boot3** (f=0.2, turn-exit): v_refuse=5.473 · t_brake=2.94 s · **a_meas=1.862 < 2.0 → FLAGA** (pass=false).
- **boot2** (corner0-passthrough f=0.966, apex wolny): v_refuse=3.228 · t_brake=1.312 · **a_meas=2.461 ≥ 2.0 → PASS**.
Wniosek: przesłanka A_BRAKE spełniona przy niskiej v wstrzyknięcia, NARUSZONA przy szybkim turn-exit
(0.2). Osłona odpowiada zejściem D5 (nie hamowaniem poziomym) → dron zachowuje pęd poziomy schodząc.

**R3 (parowanie + wysokość):** `PAIR_TOL += dz_m:0.5` (ZAMROŻONE). `pairing_check` liczy
|z_inj_S − z_inj_N| ≤ 0.5 m na `inj_info.z_gt` (wysokość fizyczna GT). `inj_info` dostaje z_gt/z_ekf.
Selftest dz PASS. Jeśli 0.2 wypada w climbie — własność geometrii (G3), ale oba ramiona w tym samym climbie.

**R4 (nota do RAPORT §V):** landing-skid EKF 16.6 m/s pod denialem (GT fiz. 7.9) — poza scope K1, ale to
MECHANIZM, na którym natywny blind-land pracuje (EKF diverguje pod GPS-denied); wróci przy interpretacji
ramienia N po 5/5.

**R1:** V3 ratyfikowane — V_env=6.0 zamrożone, C_margin=1.146 podany wprost obok 11.69 w RAPORT_R03A
(adnotacja) i ERRATUM_VMAX.md.

## §W9 — ANEKS_K1-10 P2: dstop_check (dosłowna przesłanka twierdzenia na locie)

`k1_finalize` (ramię S, nie sędzia): `dstop_check = x_exc ≤ v_REFUSE_GT·0.20 + v_REFUSE_GT²/(2·2.0)`.
FAIL nie unieważnia biegu — wchodzi do §I obok wyniku („przesłanka naruszona") i §IV. Wstecz:
- **boot2** (corner0-passthrough): x_exc=2.264 ≤ bound 3.251 → **PASS**.
- **boot3** (f=0.2 turn-exit): x_exc=16.518 vs bound 8.583 → **FAIL** (v_REFUSE=5.473).
P3: FAIL nie zmienia N@0.2 ani nie zatrzymuje serii (gwarancja globalna V3 stoi na OBWIEDNI V_env, nie
na 1 locie). RAPORT_K1: „przy wyjściu z zakrętu z v>5 m/s droga po REFUSE przekracza bound — wynik
o OSŁONIE, nie o instrumencie". 3. taki FAIL w serii ⇒ STOP + rewizja A_BRAKE w erratum #2 (nie w PRE).
P1: flaga a_meas (boot3 1.862<2.0) zostaje w RAPORT §IV z adnotacją „miara uśrednia ogon regulatora".

## §W10 — ANEKS_K1-11: decyzje R2 (budżet N, status 0.2, poprawka agregacji)

**D1 (N@0.2):** lecieć dalej w budżecie (2/3 zostały), protokół B4 bez zmian. Większa ekspozycja N na
D8 (okno claim ~8 s vs S ~3 s) = własność mierzonych mechanizmów, NIE powód do zmiany kryterium
habitatu; zdanie do RAPORT §IV (już zapisane po S boot2).

**D2 (parowanie tylko na ważnych + budżet bez resetu):** `k1_aggregate` — parowanie i kryterium
liczone WYŁĄCZNIE na bootach `run_valid is True` (filtr po siostrzanym `manifest.json`; diag=False,
niedokończony/stary=None i judge bez manifestu WYKLUCZONE). Status per-punkt: `paired` /
`UNPAIRED` (oba ramiona ważne lecz kinematyka poza tol) / `incomplete` (brak ważnego boota ramienia).
Budżet per (ramię,punkt) = **3 loty ŁĄCZNIE, BEZ resetu** z powodu niesparowania (doprecyzowanie G2).
Punkt bez ważnej pary po wyczerpaniu obu budżetów = UNPAIRED (final).

**D3 (0.2 zostaje):** punkt 0.2 pozostaje w spec i w kryterium — żadnego przesuwania ani „informacyjny".
Dane 0.2 (oba ramiona, wszystkie booty, z dstop_check w tym FAIL 16.518 S boot3) idą do RAPORT §I
niezależnie od statusu parowania, z etykietą statusu.

**D4 (poprawka agregacji, ZAMROŻONA przed 0.35–0.8):** werdykt §4 liczony na punktach SPAROWANYCH;
wymóg **≥4 sparowanych z 5**; mianowniki (+)/(±)/(0) = liczba sparowanych. `<4` ⇒ werdykt
**NIEWYKONANE** (`k1_executable=False`) → STOP + osobna decyzja (kandydaci wtedy: parowanie przez
wspólny stan startowy zamiast wspólnego f, albo N-tylko charakteryzacja bez kontrastu). Nowe pola:
`paired_of=5`, `min_paired_required=4`, `k1_executable`, per-row `status`. Jawność: poprawka powstała
po 1 nieudanym zestawieniu na 0.2 i PRZED danymi z pozostałych punktów; jeśli po serii jedynym
niesparowanym okaże się 0.2, RAPORT mówi to wprost razem z dstop FAIL (czytelnik ocenia, czy
wykluczenie działa na korzyść osłony). 3 nowe selftesty (14/14 PASS).

**D5 (licznik dstop-FAIL, P3):** **dstop FAIL #1/3 = S@0.2 boot3** (x_exc 16.518 > bound 8.583,
v_REFUSE 5.473). Do §I (obok wyniku, „przesłanka naruszona") i §IV; przy 5/5 wraca jako wynik o
osłonie przy szybkim wyjściu z zakrętu, nie jako przypis. **3. taki FAIL ⇒ STOP + rewizja A_BRAKE w
erratum #2.** Licznik biegnie tu: [FAIL#1 S@0.2 boot3].

**D6:** push f3709d3 (Olga) → cooldown → N@0.2 boot4 → standardowy STOP R2 po każdej próbie punktu.

## §W11 — ANEKS_K1-13: skażony boot, bramka flight-quality (J1–J5)

**J1 (S@0.2 boot3 → diag flight-quality):** re-finalize in-place → run_valid False, kind diag,
invalid_reason `flight-quality-drift`. Kryterium jawne/symetryczne/ślepe na wynik: r@offboard=10.27
przy ≤1.33 u 5/6 bootów (dryf ~10 m N w takeoffie). judge.json/habitat.json BAJT-IDENTYCZNE
(deterministyczne); spec_check/inj_info/dstop/abrake/vmax/sha NIETKNIĘTE. Dane w §V + `e1_divergence.png`.

**J2 (dstop FAIL #1 NIE znika, licznik NIE zeruje):** [FAIL#1 S@0.2 boot3] zostaje — zmienia się
ZNACZENIE nie ISTNIENIE. Przestaje być „zachowaniem punktu 0.2", zostaje POMIAREM przesłanki przy
v_REFUSE=5.47: z tej prędkości osłona przejechała x_exc=16.5 m > bound 8.6 — prawda o osłonie
niezależnie od tego, jak dron doszedł do 5.47. Podwójna adnotacja §I/§IV: **dojście skażone, liczba
realna.** Zerowanie działałoby na korzyść osłony → NIE robimy. Licznik: [FAIL#1 S@0.2 boot3].

**J3 (V_env=6.0 zamrożone):** premisa V_true_max=5.34 ze skażonego S boot3; czyste booty sugerują
niższą obwiednię, ale obniżanie po danych = strojenie marginesu na korzyść gwarancji → NIE. Adnotacja
w ERRATUM_VMAX: obwiednia konserwatywna, zmierzona na locie z dryfem; C_margin=1.146 = DOLNE oszacowanie.

**J4 (bramka pre-injection, ZAMROŻONA):** `k1_finalize` — `preinj_check`: r@offboard=hypot(x,y) GT
najbliższego eventu `offboard` ≤ **2.0 m** (separacja 1.33 vs 10.27). Symetryczna dla ramion, mierzona
PRZED wstrzyknięciem, ślepa na wynik. Naruszenie ⇒ run_valid False + `flight-quality-drift` (diag);
lot LICZY się do budżetu (poleciał — duch SR-K5). Sędzia 4e0dc0af NIETKNIĘTY. Zweryfikowane: boot3
FAIL(10.27), boot4 PASS(1.329). pytest test_k1 7/7 + test_k1_shield 5/5.

**J5 (przyczyna dryfu — ROZSTRZYGNIĘTE, ulog S boot3):** w oknie takeoff-climb (ulog ~102–109 s po
„Takeoff detected"@96.04): `vehicle_local_position.xy_reset_counter` 4→5 @t=102.14 s ze skokiem
pozycji ~5.5 m (reset poziomy EKF), koincydentnie z health-failami `High Gyro Bias`@103.37 +
`High Accelerometer Bias`@105.38 i skokiem `timesync time jump`@108.65 (rodzina ~32 s = D8:
13.28/55.09/86.98/108.65). Reset EKF zaburzył position-hold takeoffu → fizyczny dryf ~10 m.
INTERMITTENT (rodzina D8/timesync), **bramka J4 chwyta**. Zdanie do §IV.

**J6 budżety:** (S,0.2) 1/3 zużyty (boot3 diag flight-quality), 2 zostają; (N,0.2) 2/3, 1 zostaje;
N boot4 = ważny kandydat pary (r@inj=18.08). Po pushu (1cee41d + commit J1–J5): re-lot S@0.2 →
parowanie z N boot4.


## §W12 — INFRA-3 A1: rozcięcie kontroler/osłona (re-baseline pinu gate → PO STOP-1) [A1b: sha256, diff verbatim]

Nienoga badawcza (pozycja 1a planu). Źródło setpointów wypięte z pętli osłony do `r03/controllers/`
(ławka/sieć wpinają kontroler bez dotykania osłony, SR-9). Osłona (`r01/shield.py`), config (`r03/config.py`),
sędzia K1 (`k1/k1_judge.py`), sędzia DEMO-B (`tools/act_judge.py`) — sha256 NIEZMIENIONE.

**Pakiet** `r03/controllers/`: `base.py` (interfejs `SetpointSource`, kontrakt PROMPT_INFRA3 §A1.1 —
`step(tick, pos_ned, vel_ned, now_s, descending)` zwraca `tgt_ned`/`v_ned`/`yaw`/`seg_i`/`dist`/`wps`/`extra`),
`route_follower.py` (`RouteFollower` = JEDYNY dziś kontroler, odtwarza DOKŁADNIE stary blok 3065b8b 225–230+291),
`__init__.py` (`make_controller`/`controller_sha`).

**sha256 (etykieta przyrządu: sha256 zawartości pliku, NIE id bloba git):**

| plik | @3065b8b (stary) | @31fe970 (nowy) |
|---|---|---|
| `r03/gate_run_r03.py` | `72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a` | `c3ccabe04b9cae8ea57cfa899b8e363451fe9a6b4dbaffc8b1b0910ad192b729` |
| `k1/k1_finalize.py` | `cfe1d95dcbfc2e02dfa23dbfce1cb45659fe65bb1708527309b044b3037b4201` | `8c4682a1a3b13dd181fa43cf34bf877919b85c8c1781e51f46cde56e7ff45079` |
| `r03/controllers/base.py` | — (nowy) | `7fc45cf2216d4a9eae86fa9ee714d70354fafbc64721f76bff7c0575bb9fb8f9` |
| `r03/controllers/route_follower.py` | — (nowy) | `e0fcc7d2d8728c6c6be9f88c756127c453cd8c3184a76a8b9ef3929b19716266` |
| `r03/controllers/__init__.py` | — (nowy) | `940081f754eca5aa49ad8bed6a059ed9c77b6fec59b756339bd89d7e5e4cc16f` |

`controller_sha` w meta/manifeście (route) = sha256 `route_follower.py` = `e0fcc7d2…` (potwierdzone `controller_sha(ctrl)`).
KOREKTA A1b: w pierwotnym STOP-1 sha `k1_finalize` podano jako `944a2f1…` — to było id bloba git, NIE sha256.
sha256 stary = `cfe1d95d…` (zgodne z pomiarem CC), nowy = `8c4682a1…`. Reszta shas w STOP-1 była już sha256.

**Diff `r03/gate_run_r03.py` + `k1/k1_finalize.py` (verbatim, `git diff 3065b8b 31fe970`):**
```diff
diff --git a/k1/k1_finalize.py b/k1/k1_finalize.py
index 944a2f1..0955cf0 100644
--- a/k1/k1_finalize.py
+++ b/k1/k1_finalize.py
@@ -508,6 +508,8 @@ def main():
         "stamps": stamps,
         "harness_valid": (meta or {}).get("harness_valid"),
         "harness_poison": (meta or {}).get("harness_poison"),
+        "controller": (meta or {}).get("controller"),            # INFRA-3 A1: przepisanie z meta (SR-2 dozwolone)
+        "controller_sha": (meta or {}).get("controller_sha"),    # INFRA-3 A1: przepisanie z meta (SR-2 dozwolone)
         "habitat_verdict": hab,
         "certs_selfcheck": certs,
         "provenance_arm_s": (PROVENANCE_ARM_S if a.arm == "S" else None),
diff --git a/r03/gate_run_r03.py b/r03/gate_run_r03.py
index a1f4ae6..26fec23 100644
--- a/r03/gate_run_r03.py
+++ b/r03/gate_run_r03.py
@@ -26,6 +26,7 @@ from mavsdk.action import ActionError
 
 from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
 from r03 import config as C
+from r03.controllers import make_controller, controller_sha   # INFRA-3 A1: źródło setpointów wypięte z pętli
 
 SCEN = os.environ.get("SCEN", "S2")
 OUT = os.environ.get("GATE_OUT", f"/tmp/r03gate/{SCEN}.jsonl")
@@ -155,10 +156,19 @@ async def main():
     shield.pos_debounce_ticks = C.DEBOUNCE_TICKS
     shield.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
 
+    # KONTROLER (INFRA-3 A1): źródło setpointów wypięte z pętli osłony; wybór env CONTROLLER
+    # (default "route" ⇒ S1–S4/K1 bit-identyczne — RouteFollower odtwarza stary blok 225–230+291).
+    # Osłona/zejście/trigger K1/S4 NIETKNIĘTE — czytają cmd["seg_i"/"dist"/"wps"], semantyka bez zmian.
+    ctrl = make_controller(os.environ.get("CONTROLLER", "route"),
+                           wps=C.corner_waypoints_r03(), vmax=VMAX, alt=ALT)
+    ctrl.reset()
+    _ctrl_sha = controller_sha(ctrl)
+
     fh = open(OUT, "w"); _f = fh; _running = True
     _w({"t": "meta", "scen": SCEN, "schema_v": TRACE_SCHEMA_V, "eps_cap": C.EPS_CAP, "R_E": shield.cfg.r_e,
         "half_p": C.HALF_P, "vmax": VMAX, "debounce": C.DEBOUNCE_TICKS,
         "harness_valid": (not poison), "harness_poison": poison,
+        "controller": ctrl.name, "controller_sha": _ctrl_sha,
         "note": "osłona w pętli; GT=sędzia; velocity-descent dwufazowy na POS_DEGRADED"})
     gn.subscribe(Pose_V, GT_TOPIC, gt_cb)
 
@@ -221,13 +231,10 @@ async def main():
         vel = (float(m.vx), float(m.vy), 0.0)
         dr = bool(m.dead_reckoning)
         r_est = math.hypot(pos[0], pos[1])
-        # waypoint / dist (potrzebne PRZED triggerem S4)
-        wp = wps[seg_i % len(wps)]
-        dx, dy = wp[0] - pos[0], wp[1] - pos[1]
-        dist = math.hypot(dx, dy)
-        if dist < 1.0 and not descending:
-            seg_i += 1
-        tgt = (wp[0], wp[1], -ALT)
+        # setpoint z kontrolera (INFRA-3 A1); trigger S4/K1 czyta cmd (semantyka bez zmian).
+        # RouteFollower odtwarza stary blok: wp(stary)→dx,dy,dist→inkrement seg_i→tgt(stary), seg_i PO inkremencie.
+        cmd = ctrl.step(tick, pos, vel, now, descending)
+        seg_i = cmd["seg_i"]; dist = cmd["dist"]; tgt = cmd["tgt_ned"]; wps = cmd["wps"]
         # denial injection
         _k1_fa = None
         if SCEN == "S4":
@@ -288,7 +295,7 @@ async def main():
                 if re_allow_t is not None and (now - re_allow_t) > 3.0:
                     ev("s3_reallow_confirmed"); break
             else:
-                vn, ve = (VMAX * dx / dist, VMAX * dy / dist) if dist > 1e-3 else (0.0, 0.0)
+                vn, ve = cmd["v_ned"][0], cmd["v_ned"][1]   # INFRA-3 A1: setpoint prędkości z kontrolera
                 await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
         tick += 1
         if SCEN == "S1" and now >= s1_dur:
```

**Dozwolone hunki `gate_run_r03.py` (§C1 ANEKS_INFRA3-1):** (i) import pakietu; (ii) konstrukcja `ctrl`
z env `CONTROLLER` default `route` + `reset()`; (iii) meta +`controller`/+`controller_sha`; (iv) blok
wp/dx/dy/dist/seg_i/tgt → `ctrl.step(...)` z odczytem `seg_i`/`dist`/`wps` (triggery S4/K1); (v) wiersz
ALLOW `set_velocity_ned` z `cmd["v_ned"]`. ŻADNEGO hunku w gałęzi `is_pos`/zejścia D5, `shield.step`,
denialu/recovery, timeoutach, `outcome`/restore — potwierdzone diffem powyżej. `k1_finalize.py` = 2 linie
przepisania `controller`/`controller_sha` meta→manifest (SR-2 dozwolone); sędzia 4e0dc0af i logika werdyktu NIETKNIĘTE.

**Pin gate: `72619513…` → `c3ccabe04b9cae8ea57cfa899b8e363451fe9a6b4dbaffc8b1b0910ad192b729`.** Re-baseline
w `k1/k1_shield_pins.py` DOPIERO w A2.0 (po skuteczności ANEKS_INFRA3-1 §C3). `base.py` (`7fc45cf2…`) wchodzi
do `SHIELD_PINS` jako 4. wpis (D2: kontrakt kontroler↔osłona = warstwa osłony). `route_follower.py` i przyszłe
kontrolery NIE pinowane — tożsamość niesie `controller_sha` per boot.

**Weryfikacja (offline, bez SITL):**
- test równoważności `tests_controller_split.py` (A1.3 + asercja C2): **4221 ticków / 11 lotów S/K1 bit-w-bit
  IDENTYCZNE** (tgt, v_ned, seg_i, dist); test syntetyczny narożnika PASS; **asercja C2 `descending=True ∧
  dist<1.0 ⇒ seg_i BEZ inkrementu` (obie impl.) PASS** — jedyna gałąź klauzuli bramkującej niećwiczona przez
  korpus; R0.3a v1 pominięte. **pytest 5/5.**
- regresja glue (A1.4): `judge.json` BAJT-IDENTYCZNY (kopia `results/K1/S/p0_65/boot3`, stary gate przywrócony
  w drzewie → pin się zgadza). Manifest porównywany Z WYŁĄCZENIEM pól pomiarowych chwili uruchomienia
  (`session`: mem_free/loadavg — snapshot środowiska, nie odchylenie D5); realna różnica = tylko nowe pola
  `controller`/`controller_sha` (null dla starego trace). Przepisanie meta→manifest zweryfikowane na trace z
  wstrzykniętym meta (`controller_sha` wychodzi w manifeście → A2.3 spełnialne po locie).

## §W13 — INFRA-3 B1: wrapper bootu programu `harness/run_boot.sh` (mechanizmy + źródło)

Nienoga badawcza. Kompozycja ISTNIEJĄCYCH mechanizmów w JEDNYM wrapperze; przyrządy zamkniętych serii
(`k1/run_k1_boot.sh`, `acts/run_act.sh`, `acts/run_A3.sh`) NIETKNIĘTE. Każdy mechanizm ↔ plik źródłowy:

| krok | mechanizm | skopiowane/wywołane z |
|---|---|---|
| 1 | B4 orphany+cooldown+b4_state, `proc_inventory{,_pre}.txt` | `k1/run_k1_boot.sh:22–31` (marker program-wide `results/.last_boot_end` + fallback `results/K1/`) |
| 1 | **BRAMKA PROCESOWA §3** (`harness/proc_gate.py` + `proc_allowlist.txt`) | NOWY (ANEKS_INFRA3-3 §3): `top -b -n 2 -d 5`, cudzy proces >2% CPU lub loadavg>1.5 ⇒ env-block+stub, exit 3 |
| 2 | certs_selfcheck (gate_r03) | `k1/run_k1_boot.sh:33–37` |
| 3 | higiena GPS / CAL_MAG (zawsze) | `acts/ensure_gps_enabled.py`, `acts/ensure_mag_baseline.py` (jak `run_k1_boot.sh:39–45`) |
| 4 | bramka obciążenia I2a (LOAD_MAX 8.0, 10 min) | `k1/run_k1_boot.sh:47–64` (semantyka env-block bez zmian) |
| 5 | świat + hash (`harness/world_hash.sh`) | `acts/run_act.sh:16–17` (worlds/) + stock z `PX4-Autopilot/Tools/simulation/gz/worlds/` |
| 6 | stack, headless, /clock, RTF, watchdog EKF2 (BEZWARUNKOWY, max 2 reinity), settle (MIN 90), timejump_pre | `k1/run_k1_boot.sh:66–91` (`run_stack.sh`, `acts.rtf_sampler`, `tools/infra2_ekf_watchdog.py`) |
| 7 | intruz spawn + `model_in_state` (dowód R02C), film bridge (opc.) | `acts/run_act.sh:30–38` (`gz service create` na `r02/intruder_model.sdf`, `gz model --list`) |
| 8 | moduł lotu (gate_r03 / arm_n / empty), passthrough SCEN/K1_POINT/CONTROLLER | `k1/run_k1_boot.sh:93–107` (gate_run_r03 / k1_arm_n / `tools/infra1_empty_flight.py`) |
| 9 | post: term RTF/watchdog, timejump_post, health, ulog→boot.ulg + **ulog_sha.txt** (sha256+rozmiar) | `k1/run_k1_boot.sh:109–117` + sha256 pointer (NOWY, §B1.1 pkt 9) |
| 10 | finalize wg FLIGHT + **łapacz klasy stub** (`harness/stub_manifest.py`) + augment (`harness/augment_manifest.py`) | `k1/k1_finalize.py` / `tools/infra1_empty_finalize.py`; stub=lekcja R5 (brak manifestu ≠ brak bootu) |
| 11 | marker końca program-wide `results/.last_boot_end` | `k1/run_k1_boot.sh:135` (ścieżka program-wide) |

sha256 nowych plików (@B1):
- `harness/run_boot.sh` `9e87a1df34167326ca69537f16a93cbf27c76cb6c48ac3591f948f944ee2634f`
- `harness/proc_gate.py` `764bd3cdb21ff1d23b7f6186cd05ef05db37144d9b27b7e3972c42b842aeecbc`
- `harness/proc_allowlist.txt` `33c80992fc4b59a42c10a3f2bdfaa5ba412c179550aebfef3fec5cdb5276a161`
- `harness/stub_manifest.py` `9d963eb4246b07cad2ce7f9c4c25d648b7b265f6d028c4624df613e85168ea33`
- `harness/augment_manifest.py` `88e637208213793f0de925eb5ec3c442f9f3a34221a84cd77b24aa25b0bcec56`
- `harness/world_hash.sh` `c765e3d17883066fec68ae3d949ad871de906a91abd1d497214b1dab7cd4c342`

Augmentacja manifestu (world_hash/ulog_sha/ulog_bytes/model_in_state) = warstwa wrappera, NIE dotyka sędziego
ani logiki finalize (sędziowie 4e0dc0af/79b1e936 NIETKNIĘTE). Test `tests_harness_infra3.py` B1.2 (i)–(v) 6/6 PASS.
B1 NIE dotyka niczego pinowanego (SR-3 nie dotyczy — brak zmian w gate/osłonie/config); STOP-u brak, B2 startuje od razu.
