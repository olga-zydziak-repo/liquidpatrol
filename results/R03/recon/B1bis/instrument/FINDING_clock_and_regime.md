# B1-bis — ZNALEZISKO 2: zegary px4/gz DRYFUJĄ + reżim długiego okna vs operacyjny epizod

Data: 2026-08-09. Dotyczy kanału streaming GT (b1bis) i interpretacji dryfu.

## 1. Zegary NIE są lockstep — dryfują ~0.77 %

Native stemple: `vehicle_local_position.timestamp` (px4, epoch-offset) vs gz `dynamic_pose.header.stamp`
(sim). Zmierzone: offset `px4_ts − gz_sim` dryfuje **+0.964 s / 125 s** (~7.7 ms/s). Parowanie po
stałym gross-offset (align_by_sim) daje przy v_max błąd `v·Δt` do ~2.6 m (f3 healthy p95=2.64 sim vs
0.06 mono). **Wniosek: parowanie po native-sim ODRZUCONE.** Poprawne: **MONO** (jeden zegar odbioru)
+ korekta stałego skew latencji (estymator skew). Fit liniowy offsetu ma residuum 370 ms (jitter odbioru
XRCE) — też niewystarczający. Mono+skew: f1/f2/f3 healthy p95 (|v|<1.0) = 0.032/0.040/0.097 ≤ 0.10 PASS.

Instrument poprawiony: `gt_judge.py` — mono-pairing, skew stosowany gdy obserwowalny (v>0) i pomaga;
bramka W5 liczona na próbkach `|v|<V_GATE=1.0` (izoluje fidelity kanału od `v·Δt` przy ruchu). Unit-test
(swap+skew) dalej PASS.

## 2. Dryf SILNIE zależny od dynamiki — długie okno v_max ≫ zawis

Profil dryfu (mono+skew, ε_pos = ||e − T_home||):

| lot | mode | max_drift | plateau | @2s | @5s | @10s | @20s | dr_win |
|---|---|---|---|---|---|---|---|---|
| f1 | hover | 0.30 | 0.28 | 0.03 | 0.04 | 0.09 | 0.28 | 84 s |
| f2 | hover | 0.55 | 0.54 | 0.03 | 0.12 | 0.32 | 0.54 | 84 s |
| f3 | straight v_max | **6.24** | 5.99 | 0.74 | 0.43 | 3.84 | 5.99 | 94 s |

f3: dryf rośnie do ~6 m i **PLATEAUJE** (~6 m od ~20 s do 94 s — A-plateau trzyma, ale WYSOKO).

## 3. ROZBIEŻNOŚĆ REŻIMU (do decyzji) — długie okno vs operacyjny epizod

Protokół §5quater mierzy `max_drift` po oknie **≥60 s ciągłego v_max DR**. Ale OPERACYJNY epizod
(D9/D12): flaga → debounce 2 ticki (0.1 s) → **REFUSE(POS) → Land**. Land = zejście pionowe, poziom
≈ hover (~14 s zniżania z 10 m). Więc operacyjne ε_pos ≈ dryf przez [~0.1–1 s v_max/brake] +
[~14 s near-hover] ≈ SUB-METR (rząd zawisu), NIE 6 m.

`ε_cap = 1.5×max(max_drift)`:
- z długiego okna v_max (f3=6.24; f5/f6 narożnik mogą być gorsze) → `ε_cap ≈ 9+ m` →
  `R_route' = 32 − 2.85 − 9 = 20.15` → `half-side' = 14.2 m` (> próg 8.55 SR-B1', ale mocno
  konserwatywne; narożnik może zbić poniżej progu → SR-B1').
- z operacyjnego epizodu (early-episode + Land) → `ε_cap` rzędu sub-metra → trasa prawie nietknięta.

**Fast-REFUSE (D12) istnieje PO TO, by ograniczyć epizod DR** — więc 94 s v_max DR to NIE reżim
operacyjny; długie okno to sonda PLATEAU-STABILNOŚCI (SR-B6: czy dryf jest ograniczony — TAK, plateauje),
nie podstawa capa. **Podstawa capa = dryf po epizodzie REFUSE→Land.** To interpretacja wymagająca
ratyfikacji Olgi (zmienia sens liczby capa i wynik SR-B1').

Rekomendacja do decyzji: rozdzielić DWIE metryki — (i) SR-B6 plateau-stability z długiego okna (czy
ograniczony); (ii) ε_cap z dryfu OPERACYJNEGO epizodu (mierzony lotem z profilem REFUSE→Land: krótki DR
przy v_max/narożniku + Land near-hover do touchdown). Cap = 1.5×max(ε_pos operacyjnego).

## 4. PEŁNA SIATKA (mono+skew, poprawione) — kształt PLATEAU potwierdzony

| lot | mode | max_drift | @2s | @10s | @20s | plateau (20→koniec) | dr_win | p95(|v|<1) valid |
|---|---|---|---|---|---|---|---|---|
| f1 | hover | 0.30 | 0.03 | 0.09 | 0.28 | 0.28 flat | 83 s | 0.032 ✓ |
| f2 | hover | 0.55 | 0.03 | 0.32 | 0.54 | 0.54 flat | 83 s | 0.040 ✓ |
| f3 | straight v_max | 6.24 | 0.74 | 3.84 | 6.0 | 6.0 flat (20–90 s) | 94 s | 0.097 ✓ |
| f4 | straight (125 s) | 25.82 | 3.53 | 22.8 | 25.7 | 25.7 flat (20–150 s) | 153 s | 0.100 ✓ |
| f5 | corner | 4.63 | 0.75 | 0.86 | 4.4 | 4.4 flat (20–60 s) | 73 s | 0.061 ✓ |

**KSZTAŁT: wszystkie step-do-plateau, plateau OSIĄGNIĘTE ~20 s i FLAT do końca** (f4 flat 25.7 przez
130 s). A-plateau QUALITATYWNIE POTWIERDZONE (błąd OGRANICZONY, nie random-walk). **SR-B6 NIE wyzwolone**
(brak wzrostu monotonicznego przez całe okno). Kanał GT czysty (p95 |v|<1 ≤ 0.10 wszędzie).

**ALE poziom plateau = f(czas DR × v)**: dron dead-reckonuje PRĘDKOŚĆ → ucieka zanim się ustabilizuje.
f4 (2 resety EKF, R-1) uciekł do 25.7 m.

## 5. SR-B1' — arytmetyka (literalny protokół §5quater)

`ε_cap = 1.5 × max(max_drift) = 1.5 × 25.82 = 38.73 → 39/1`.
`R_route' = R_E − d_stop − ε_cap = 32 − 2.85 − 38.73 = −9.58 m < 0` → `half-side'` UROJONE.
**SR-B1' WYZWOLONE: twierdzenie NIEDOMYKALNE w tej geometrii — jeśli cap z długiego okna v_max DR.**

## 6. Rozstrzygnięcie — reżim capa (do ratyfikacji Olgi)

Sprzeczność: §5quater (protokół) mierzy dryf po ≥60 s ciągłego v_max DR → runaway 26 m → SR-B1'.
D12 (intencja) mówi: fast-REFUSE OGRANICZA epizod DR „do reżimu, w którym A-plateau JEST ZMIERZONE".
Operacyjnie: flaga → debounce 0.1 s → REFUSE → Land (near-hover, ~14 s zniżania). ε_pos zostaje w
RAMPIE (pierwsze ~1 s v_max + Land near-hover), NIGDY nie dochodzi do runaway-plateau.

Dwa spójne odczyty:
- **(A) literalny §5quater** → ε_cap 39 m → SR-B1' STOP: „niedomykalne, WYNIK" (FAIL uczciwy).
- **(B) reżim operacyjny (intencja D12)** → cap z epizodu REFUSE→Land (krótki DR + Land do touchdown).
  Wymaga lotu z profilem epizodu (dodać MODE=episode). Wtedy cap ~rząd 1–3 m, trasa ważna.
  Długie okno pozostaje SONDĄ SR-B6 (plateau-stability: PASS — błąd ograniczony).

## 7. EPISODE (operacyjny) + AKCJA BEZPIECZNA — znaleziska (ratyf. Wariant A z poprawkami)

Loty EPISODE (dobry boot 90 s konwergencji EKF; eph→0.150; kanał czysty p95≤0.07):
| lot | stan | ε_pos (zejście 0.7 m/s ~14 s) | @2s | @5s | @10s | t_flag |
|---|---|---|---|---|---|---|
| g1 | prosta v_max | 2.45 m | 0.45 | 1.19 | 2.44 | — |
| c1 | narożnik 90° v_max | 12.33 m | 0.68 | 2.71 | 10.5 | 0.025 s |

**Znaleziska:**
1. **AUTO.LAND (`d.action.land`) UCIEKA pod DR = 42 m** (pętla POZYCYJNA station-keeping goni dryfującą
   estymatę). Zasada: pod degradacją estymatora tylko akcje OTWARTO-PĘTLOWE wzgl. degradowanej wielkości.
   2. instancja zawodnej natywnej warstwy-0 (po „martwym" eph-failsafe §2). → D5 REWIZJA: velocity-descent.
2. **Velocity-descent (v_xy=0, v_down) też dryfuje** — pod DR dron nie wyzeruje PRAWDZIWEJ prędkości
   (brak aidingu). Dryf ~proporcjonalny do CZASU epizodu → **tempo/czas zejścia = DŹWIGNIA**.
3. Konwergencja EKF: 15 s settle → eph 0.22 (broken, flyaway); **90 s → eph 0.150** (dobry). NIE load
   (24 rdzenie, ~23%). ~~Arm preflight (gyro bias/heading) czasem nie przechodzi — losowa flakiness SITL.~~
   **KOREKTA 2026-08-11 (retro DIAG):** to NIE była „losowa flakiness". Bieg B1-bis ubity przed restore
   zostawiał `EKF2_GPS_CTRL=0` utrwalone w `rootfs/parameters.bson` → następny boot GPS-denied → arm
   preflight nie przechodził DETERMINISTYCZNIE. Nazwany mechanizm: `results/R03/recon/DIAG/FINDING_health_blocker.md`.
4. `EKF2_HGT_REF` default=1 (GPS) → wysokość degraduje pod denialiem → wymuszamy 0 (Baro), §3quater.

**Profil dwufazowy (§3quater):** 1.5 m/s (MPC_Z_VEL_MAX_DN) do 2 m AGL, potem 0.7 (MPC_LAND_SPEED).
Predykcja prerejestrowana: ε_pos(narożnik, dwufazowy) ∈ [2.5, 6] m. Re-pomiar: ≥3 narożnik + ≥2 prosta.
