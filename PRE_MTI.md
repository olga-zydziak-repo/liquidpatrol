# PRE_MTI — brama ENTRY: struktura ∧ MTI (recon read-only → PRE → TWARDY STOP)

Data: 2026-08-15. Reżim: **recon nieinwazyjny → pre-rejestracja → STOP** (dyscyplina A2). Geneza:
`RAPORT_LIVEFED_CHAR` (B0/B2: conf ≪ θ_conf na każdym zasięgu, admit@θ=0.0 ⇒ conf-floor MARTWY; rider C-A4)
+ A1 (0b ODRZUCONE DEFINITYWNIE — strata to rozdzielczość, nie kadrowanie). **conf zdegradowany do telemetrii
pasywnej; jedyna realna brama ENTRY = STRUKTURA ∧ MTI.** MTI = klasyczna wizja (różnicowanie klatek,
morfologia, komponenty spójne), **zero komponentów uczonych**. `θ_conf` NIETYKALNY.

Zasady nadrzędne (SR-M3): `θ_conf`, `DEADMAN_TICKS=6`, kryteria `PRE_R02C` (≥7 m coverage ≥0.8 / ε_FP=0,
wyłącznie w locie), ANEKS-4, config r03, frozen R0.1/R0.2/R0.3, certy P1/P5 — **nietykalne**. **Ta sesja NIE
buduje MTI** (SR-M2) — recon → PRE → ratyfikacja Olgi → build (osobny prompt). Wszystkie liczby czasowe z
etykietą przyrządu. ANEKS-H obowiązuje każdemu przyszłemu biegowi (SR-M5).

---

## R1 — KOMPENSACJA EGO-MOTION (rdzeń trudności)

W OBSERVE ruszają się jednocześnie platforma i cel → MTI bez derotacji ma tryb porażki „wszystko się rusza".
Inwentarz źródeł (zmierzony na żywym stacku 2026-08-15, ten sam co A1):

### Attitude — źródło i kadencja
| źródło | topik | Hz (zmierzone) | zegar | pole | ocena dla MTI |
|---|---|---|---|---|---|
| **XRCE-DDS** | `/fmu/out/vehicle_attitude` | **100.0** (std 2 ms) | PX4 (lockstep z gz) | `q[4]` FRD→NED + `timestamp`/`timestamp_sample` µs | **WŁAŚCIWE** — ten sam zegar co klatka, 100 Hz |
| MAVSDK | `attitude_euler` | 20 (`set_rate_attitude_euler(20)`) | `mav` (ścienny) | euler deg | **ZŁE** dla parowania — inny zegar, 5× rzadziej |
| — | `/fmu/out/vehicle_angular_velocity` | **NIE mostkowany** (dds_topics.yaml l.44 zakomentowany) | — | — | brak żyroskopu → derotacja z Δquaternion |

`exec_lib.Mav.att()` (l.158–163) ekstrahuje pełne yaw/pitch/roll (rozszerzone w torze C), ale **z MAVSDK
(mav, ścienny)** — do naprowadzania OBSERVE OK, **do derotacji MTI NIE** (zły zegar). MTI subskrybuje XRCE.

### Kamera — intrinsics (z `mono_cam/model.sdf`, montaż `x500_mono_cam`)
- `horizontal_fov=1.74 rad` (99.7°), 640×480, `update_rate=15 Hz`, near 0.1 / far 3000, forward = body **+X**.
- Pinhole: **fx = fy = 270.0 px, cx = 320, cy = 240** (piksele kwadratowe); V-FOV pochodna = 1.453 rad (83.3°,
  pół 41.6°). Detektor liczy natywne 640×480 (`imgsz=640`), NIE 320×240 (config `IMG_W/H` to spec, nie strumień).
- Montaż `CameraJoint type=fixed`, pose `.12 .03 .242 0 0 0` (sztywno do kadłuba, zero rotacji). **Ramię
  dźwigni 0.12 m przód** → pod rotacją wprowadza drobną translację (paralaksa ~0.12 m) — ≪ 7 m cel, ale nazwane.

### ZNACZNIKI CZASU — PUŁAPKA (zmierzona, NIE założona)
Trzy zegary, DWA różne domeny:
- **Klatka** (`ros_gz_bridge` `header.stamp`): **sim-time UPŁYNIONY** — zmierzone `sec:96` (96 s od startu symu).
  Detektor czyta to jako `sim_t` (`detector_node._sim_t`).
- **`vehicle_attitude.timestamp`**: **PX4 epoch-µs** — zmierzone `1786749193062991` (≈ 1786749193 s epoch).
- **gz `/clock`**: **epoch** — zmierzone `1786749191.98 s` (= start_epoch + upłynięcie; start ≈ 1786749095).

**Klatka i attitude są OBIE gz-lockstep** (sim), ale klatka podaje UPŁYNIONY sim-time, a attitude epoch-µs.
Offset stały **O = start_epoch ≈ sim_start** (= `/clock`_epoch − klatka_upłynięta, oba gz-źródłowe). Przy
**time-jump = 0 (H.1)** O jest STABILNY w biegu ⇒ **BRAK dryfu 0.77% między tymi dwoma** (dryf/skew 0.3 s z
B1-bis pochodził z kanału ŚCIENNEGO/MAVSDK-GT, nie z XRCE-vs-gz). To znosi pułapkę — pod warunkiem że MTI
używa `vehicle_attitude` (XRCE), NIE MAVSDK.

**Parowanie klatka↔attitude (DECYZJA do ratyfikacji):**
- Zamień `vehicle_attitude.timestamp` → sim-upłynięty przez zmierzony na starcie biegu offset O
  (O := `/clock`_epoch − pierwsza_klatka_upłynięta; assert stabilności O przez bieg).
- Nearest-neighbor do `header.stamp` klatki, **tolerancja ≤ ½ okresu attitude = 5 ms @100 Hz**.
- Budżet błędu przy `v=3 m/s`: 5 ms → 1.5 cm → **0.13° az @6.84 m ≈ 0.81 px** (SUB-PIKSELOWE). 100 Hz XRCE
  czyni residuum parowania nieistotnym — inaczej niż 20 Hz MAVSDK (25 ms → ~4 px).

### SR-M1 — unit-test instrumentu (WYMAGANY przed jakąkolwiek liczbą na realnych klatkach)
Syntetyka ruchoma: znana rotacja kamery (yaw/pitch/roll) na sztucznej scenie → derotacja z tej samej rotacji
→ residuum diff ≈ 0 (poza szumem numerycznym); wstrzyknięty ruchomy obiekt → residuum NIEZEROWE tylko na nim.
PASS wymagany. Dodatkowo: **assert stabilności offsetu O** (dryf < tolerancja) i **time-jump=0 gate** per bieg
(inaczej `harness_invalid`). **SR-M1 FAIL ⇒ STOP** (bez zsynchronizowanej derotacji MTI nie ma sensu).

---

## R2 — KANDYDAT ALGORYTMU + JEGO WŁASNE FAŁSZYWKI

**Najprostszy działający potok (do ratyfikacji):**
1. Para klatek `f[t], f[t−Δ]` z surowego strumienia **15 Hz** (nie kadencji detektora 1 Hz; Δ = 1–2 klatki).
2. Derotacja `f[t−Δ]→f[t]`: homografia rotacyjna `H = K · R(Δq) · K⁻¹` (K z intrinsics R1; `R(Δq)` z delty
   sparowanych kwaternionów XRCE). Translacja/paralaksa NIE kompensowana (rotacja-only — nazwana słabość).
3. `residual = |f[t] − warp(f[t−Δ])|` → próg → **morfologia** (open→close, usuń sól-pieprz) → **komponenty
   spójne** → filtr rozmiaru + spójności czasowej (komponent utrzymuje się ≥m klatek, ruch środka spójny).
4. Wyjście = maski/komponenty ruchome → **AND-gate z kandydatem STRUKTURALNYM** (rider C-A3): ENTRY tylko gdy
   box strukturalny (edge-margin + k=3) **pokrywa się** z komponentem MTI. MTI NIGDY samodzielnie.

**Własne źródła FP MTI (każde = kandydat na filtr albo zmierzona słabość):**
- **paralaksa tekstury gruntu** (translacja niekompensowana homografią rotacyjną) — DOMINUJĄCA w teksturze;
- cień własnego drona; rozmycie/przesłona śmigieł; artefakty krawędzi kadru (odsłonięte brzegi po warpie —
  maskować ramkę); residuum derotacji przy szybkim yaw; linia horyzontu pod pitchem.

### ZAGROŻENIE WIERNOŚCI DO PREREJESTROWANIA (istotne dla dema)
Obecny świat (`default.sdf`) jest **jednolicie szary** (overlay A1 potwierdza: płaskie niebo/grunt) → MTI
trywialnie łatwe (brak tekstury = brak paralaksy = brak FP). **Świat dema będzie TEKSTUROWANY** → paralaksa
gruntu eksploduje FP MTI. **Charakteryzacja MTI na płaskim tle NIE przenosi się na dema.** Zapis w PRE
(oba, nie jedno):
- **(a) WYMÓG:** charakteryzacja ε_FP MTI (R3) w świecie DOCELOWYM/teksturowanym przed jakimkolwiek
  roszczeniem operacyjnym; ORAZ
- **(b) GRANICA ROSZCZENIA:** wynik na `default.sdf` etykietowany „low-texture; FP-w-teksturze NIEZMIERZONE;
  brama struktura∧MTI ogranicza FP MTI iloczynem, ale nie zeruje paralaksy w teksturze".

To NIE jest do odkrycia w nodze D — jest tutaj, prerejestrowane.

---

## R3 — ε_FP PRZECIW NOWEJ BRAMIE (REDEFINICJA KRYTERIUM, nie złagodzenie)

Obecne `ε_FP = 0` jest spełnione **WAKUOWO**: B2 `admit@θ = 0.0` na każdym zasięgu — kanał conf nie dopuszcza
NICZEGO, więc zero fałszywek trywialne. Po wejściu MTI conf-floor jest martwy (C-A4), a **brama = struktura ∧
MTI**. Kryterium (−) MUSI być mierzone przeciw TEJ bramie:

- **Co liczy się jako FP:** fałszywe **ENTRY** (lock kanału `n_false_entry`, `target_channel.py`) gdy NIE ma
  realnego intruza — brama struktura∧MTI zaświeciła na nie-celu (paralaksa/cień/śmigło przeszły edge-margin +
  k=3 + komponent MTI).
- **Sceny (obie, w locie, OBSERVE-motion — bo bez ego-motion MTI nie ma sygnału):** (a) **pusta** (bez
  intruza); (b) **ruchome tło** (świat teksturowany / ruch gruntu w kadrze pod ego-motion) — to jest ostry
  test, nie pusta szarość.
- **Długość biegu:** próg 0/min wymaga długiego biegu by ograniczyć rate — **≥5 min pusta + ≥5 min ruchome-tło
  na boot, ≥3 booty** (siatka R5). Rate = `Σ n_false_entry / Σ minut`.
- **Próg = 0 BEZ ZMIAN.** To ZMIANA ZNACZENIA kryterium (przeciw jakiej bramie mierzone), nie jego poluzowanie.

---

## R4 — WPIĘCIE W AUTOMAT + ZAKRES RE-CERTYFIKACJI (z modelu/spec, nie z pamięci)

**Teza (zweryfikowana w kodzie):** `θ_conf` i warunek ENTRY są **POZA** zakresem certów P1/P5.
- Certy wiążą `PatrolShield.step` z modelem z3 `tau` (P1) i konformancją kod↔model (P5): wejścia
  `(pos, vel, target, mode, pos_flag)`, decyzje `{ALLOW,HOLD,REFUSE}`, reasony
  `{GEOFENCE,COMMAND_INVALID,STALE_CMD,ABORT,POS_DEGRADED}`, stany `{PATROL,HOLDING,RETURNING,DONE,OBSERVING,
  POSDEG}` (`conformance.py:3–6, 13–31, 59–70`). `target` = wartość kanału **5-dim** `(cx,cy,w,h,age)`.
- `conf`, θ_conf, edge-margin, k=3 **oraz MTI** żyją UPSTREAM w `detector_node → TargetChannel._on_frame_
  unlocked` (`target_channel.py:105–140`). Cytat inwariantu: config_r02.py:37–38 — *„WYŁĄCZNIE admisja ENTRY
  UPSTREAM kanału — conf NIGDY w wartości kanału (5-dim), osłonie, P1/P5 (A1/D1 stoją)"*; target_channel.py:1–5
  — kanał 5-dim BEZ conf.

**Wpięcie MTI:** druga brama ENTRY w `_on_frame_unlocked`, obok edge-margin i conf-floor — box wchodzi do
serii k tylko gdy pokrywa się z komponentem MTI (AND). To **NIE zmienia** `shield.step`, `tau`, ani kontraktu
kanału 5-dim → **zero re-certów P1/P5.** `DEADMAN_TICKS=6` nietknięte.

**Zakres re-weryfikacji (NIE cert-level, ale wymagany):**
- `r02/test_channel.py` (12 testów ENTRY-admisji) — rozszerzyć o box MTI-bramkowany (ENTRY tylko przy
  koincydencji struktura∧MTI; brak MTI ⇒ brak serii).
- ε_FP re-pomiar wg R3 (nie test jednostkowy — bieg bramkowy).
- **Nietknięte:** shield/tau/P1/P5, kanał 5-dim, osłona, dead-man, geofence, POS.

---

## R5 — KRYTERIUM DWUSTRONNE DO ZAMROŻENIA (do ratyfikacji)

> **(+)** zasięg skuteczny **≥ 7 m** przy **coverage ≥ 0.8**, na bramie **struktura ∧ MTI**, **w locie**
> (OBSERVE-motion), **≥3 świeże booty**.
> **(−)** **ε_FP = 0** wg definicji R3 (struktura∧MTI; pusta ORAZ ruchome-tło; ≥5+5 min/boot; ≥3 booty).

**Wariancja RAPORTOWANA na metrykach NIENASYCONYCH** (nie przyciętych progiem): **czas-do-ENTRY [s]**,
**coverage_seen [frakcja]**, **liczba komponentów MTI/klatkę**, **rozmiar/persystencja komponentu**. NIE na
`admit@θ` (nasycone) ani na binarnym locku.

**Siatka (proponowana, do ratyfikacji):**
- zasięgi: **{5, 7, 9} m** (11 m odrzucony — B2: sygnał zapadły; MTI zależy od ruchu WZGLĘDNEGO, nie conf);
- dwell/zasięg: **≥30 s** (≥30 klatek detektora @1 Hz / ~450 klatek MTI @15 Hz) × **≥3 booty**;
- profil ruchu: **OBSERVE** (kwadrat V=2.5 m/s, jak §B1/A1) — ego-motion konieczne dla sygnału MTI;
- ε_FP: **≥5 min pusta + ≥5 min ruchome-tło / boot × ≥3 booty**;
- **świat charakteryzacji:** `default.sdf` (low-texture) → wynik z GRANICĄ ROSZCZENIA (R2b); **teksturowany
  świat WYMAGANY przed roszczeniem operacyjnym/dema** (R2a).

---

## STOP-RULES

- **SR-M1** — brak wiarygodnego parowania klatka↔attitude (unit-test instrumentu FAIL, lub offset O
  niestabilny, lub time-jump≠0) ⇒ **STOP**. Bez zsynchronizowanej derotacji MTI bezprzedmiotowe.
- **SR-M2** — **zero budowy MTI w tej sesji** (spełnione: recon read-only).
- **SR-M3** — `θ_conf`, `DEADMAN_TICKS`, kryteria `PRE_R02C`, ANEKS-4, config r03, frozen R0.1/R0.2/R0.3,
  certy P1/P5 — **NIETYKALNE**.
- **SR-M4** — żadnych dźwigni spoza zakresu (**gimbal/0b** [ODRZUCone A1], **rozdzielczość sensora**, **FOV**)
  — zaparkowane, wracają tylko decyzją Olgi.
- **SR-M5** — ANEKS-H: bieg naruszający habitat jest **nieważny**, nie „prawie ważny".

---

## DECYZJE DO RATYFIKACJI (Olga) — TWARDY STOP

1. **Parowanie czasowe:** `vehicle_attitude` (XRCE, 100 Hz) → sim-upłynięty przez offset O; nearest-neighbor
   do `header.stamp`, **tolerancja 5 ms**; assert stabilności O + time-jump=0. (MAVSDK odrzucony — zły zegar.)
2. **Algorytm + filtry:** derotacja homografią rotacyjną `K·R(Δq)·K⁻¹` (translacja niekompensowana — nazwana
   słabość) → diff → morfologia → komponenty spójne → filtr rozmiar/persystencja; **AND-gate ze strukturą**.
   Własne FP: paralaksa gruntu (dominująca), cień, śmigła, krawędź, residuum-yaw.
3. **Definicja FP:** fałszywe ENTRY (lock) na nie-celu; sceny pusta + ruchome-tło; ≥5+5 min/boot; próg 0.
4. **Świat charakteryzacji:** `default.sdf` z GRANICĄ ROSZCZENIA + WYMÓG teksturowanego świata przed dema.
5. **Siatka zasięgów:** {5,7,9} m, dwell ≥30 s ×≥3 booty, profil OBSERVE; wariancja na metrykach nienasyconych.
6. **Kryterium (R5)** — do zamrożenia PRZED buildem.
7. **SR-M1 unit-test instrumentu** = pierwszy krok buildu (przed liczbą na realnych klatkach).

Recon domknięty (R1–R5), read-only. **Build MTI = osobny prompt PO ratyfikacji.** Push = Olga.
