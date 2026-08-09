# RAPORT_R03A — R0.3a GPS-DENIED: osłona konsumuje zdrowie własnej pozycji

Data: 2026-08-10. PX4 **v1.16.2**. Reżim: build wg `PROMPT_R03A_BUILD2`; kryteria dwustronne ZAMROŻONE
przed pomiarem; każda liczba z etykietą przyrządu; rozbieżności jawne; księgowość trójwynikowa.
**GT (gz) WYŁĄCZNIE sędzią — nigdy w decyzji.** STOP na push (push = Olga).

Łańcuch commitów (freeze→pomiar dowodzony): ANEKS-3 (`9293ab0`) → aneks-3-bis ramka T_home (`f9ad8e3`)
→ B1-bis sonda + instrument (`980fca2`) → aneks-3-ter A-episode (`8abf9b5`) → aneks-3-quater D5+profil
(`d12511b`) → B1-bis episode (`72eba50`) → **ANEKS-4 freeze** (`5a60278`) → B2 (`c5aa7b0`) → B3
(`10690bb`) → B4 (`ea6c4dd`) → B5 (`bac07ae`).

---

## (I) TWIERDZENIE (forma plateau/A-episode) — P2-ε + bramka

**Twierdzenie zawierania (P2-ε, cert `proofs/certs/P2_eps.json`, z3 PROVED):**
`(r_est ≤ R_route') ∧ (0 ≤ ε_pos ≤ ε_cap) ∧ (r_true ≤ r_est + ε_pos) ⇒ r_true + d_stop ≤ R_E`.
Zawieranie NIE zależy od czasu ani kształtu narastania błędu — tylko od OGRANICZENIA `ε_pos ≤ ε_cap`.
Ostrość DWUSTRONNA dowiedziona: kontrprzykład przy `ε_cap+δ` ORAZ `R_route'+δ` (sat); próg dokładny
bezpieczny (unsat). Człon Land `t_land·rate` USUNIĘTY (model rate OBALONY B1) — Land pokryty przez cap.

**Stałe ZAMROŻONE (ANEKS-4, reguły D10/D11 na ε_pos episode dwufazowego):**
`ε_cap = 37/4 = 9.25 m` (= 1.5×6.023, zaokrągl. w górę do ćwiartki) · `R_route' = R_E − d_stop − ε_cap
= 32 − 2.85 − 9.25 = 19.90 m` · `half-side' = 14.07 m` (> próg degeneracji SR-B1' 8.55 m) → **DOMYKALNE**.
Koperta `R_E=32` NIETYKANA (kurczymy własną trasę, nie rozciągamy świata). `r01/config.py` frozen NIETKNIĘTY.

**Bramka (D13, osłona W PĘTLI, GT sędzią):**

| scen | status | (a) REFUSE od flagi | (b) touchdown r [GT] | (c) ε_pos ≤ ε_cap | (d) 0 naruszeń R_E |
|---|---|---|---|---|---|
| **S2** denial w patrolu | **LIVE PASS** | 0.091 s ≤ 0.15 ✓ | 14.84 m ≤ 32 ✓ | 2.97 ≤ 9.25 ✓ | rmax 20.1 ≤ 32 ✓ |
| S4 narożnik v_max | pokryty kompozycyjnie¹ | — | — | (B1-bis narożn. 4.5–5.0 ≤ 9.25) | — |
| S3 denial+recovery | pokryty kompozycyjnie¹ | — | — | — | — |
| S1 nominal (−) | pokryty kompozycyjnie¹ | 0 fałszywych REFUSE (P5/B2) | — | — | — |

POS_DEGRADED w S2 = ODWRACALNY (`terminal=None`, `n_pos_enter=1`) — nie latch (D6).

¹ **Blokada środowiskowa (SR-B4, bez fikcyjnego PASS):** S4/S3/S1 nie ukończyły live w tej sesji —
SITL zdegradował po długiej sesji (arm-preflight gyro-bias/heading intermittent, gz/mavsdk boot flakiness,
czyszczenie /tmp ubijające biegi tła). Executor `r03/gate_run_r03.py` ZBUDOWANY i zwalidowany (łączy
ros2/gz/MAVSDK, zapisuje telemetrię; S2 ukończone). Reżim tych scenariuszy pokryty KOMPOZYCYJNIE:
- **S4 narożnik worst-case:** B1-bis EPISODE narożnik (ten SAM profil dwufazowy) `ε_pos = 4.47/4.75/4.99 m`
  — wszystkie ≤ ε_cap 9.25; touchdown zawarty.
- **S1 (−) 0 fałszywych REFUSE:** P5 konformancja (400+15 epizodów, 0 rozbieżności) + B2 test
  `backward_compat` (pos_flag=None ⇒ brak POS_DEGRADED) + `debounce_1t` (1 tick NIE tripuje).
- **S3 recovery:** B2 test histerezy (M ciągłego zdrowia → re-ALLOW; flicker < M bez oscylacji).

---

## (II) A-episode — siatka measured vs cap, wierność SITL, zakres ważności

**A-plateau BEZWARUNKOWE OBALONE pomiarem B1-bis (WYNIK nogi):** kanał streaming GT (sim-time),
sonda długiego okna wykazała dryf f(czas_DR × v) — dead-reckoning PRĘDKOŚCI ucieka zanim estymata się
ustabilizuje:

| reżim (długie okno) | max_drift | okno | kształt |
|---|---|---|---|
| hover | 0.30–0.55 m | 83 s | plateau |
| narożnik v_max | 4.4 m | 73 s | plateau |
| prosta v_max | 6.0 m | 94 s | plateau |
| **prosta v_max** | **25.7 m** | **125 s** | plateau (WYSOKO) |

`1.5×25.7 = 38.6 → R_route' < 0` — bezwarunkowe A-plateau **niedomykalne**. Zastąpione **A-episode**
(ε_pos ≤ ε_cap pod WYMUSZONYM profilem epizodu). Nośne bo fast-REFUSE (D12) ogranicza epizod DR.

**Siatka EPISODE (profil dwufazowy §3quater; dobry boot 90 s konwergencji EKF; kanał czysty):**

| lot | stan | ε_pos [m] (denial→touchdown) | ważny |
|---|---|---|---|
| p_c1/2/3 | narożnik 90° v_max | 4.99 / 4.47 / 4.75 | ✓✓✓ |
| p_s1/2 | prosta v_max | 3.36 / **6.02** | ✓✓ |

`max ε_pos = 6.023 (p_s2 prosta) → ε_cap = 1.5×6.023 = 9.034 → 37/4`. Predykcja prerejestrowana
narożnik ∈ [2.5, 6] m — zmierzone 4.47–4.99 **W PAŚMIE**. `t_flag` zmierzone 0.023–0.046 s (A-flag ✓).

**Zakres ważności A-episode:** ε_pos ≤ ε_cap ważne dla epizodu `flaga→debounce(0.1 s)→REFUSE→
velocity-descent dwufazowy→touchdown` (~10 s). POZA tym reżimem (długie DR podtrzymanego v_max) dryf
rośnie z dystansem — A-episode NIE rości ważności tam (to falsyfikat bezwarunkowego plateau).

**Wierność SITL (jawnie):** eph≈0.150 m (podłoga szumu GPS/EKF SITL); healthy ε_pos podczas ruchu
~0.1–0.25 m (accel-lag zawrotów + eph). SITL NIE modeluje VRS → tempo zejścia ograniczone do
`MPC_Z_VEL_MAX_DN=1.5 m/s` (kryterium niezależne, nie granie symulatora). Realne domknięcie [A4]:
IMU/HIL zmierzy prawdziwy dryf DR (SITL quasi-idealny może zaniżać) — cap z realnego habitatu.

## (II') AKCJA BEZPIECZNA — znalezisko AUTO.LAND (NAGŁÓWEK) + D5 rewizja

**ZNALEZISKO KRYTYCZNE: `d.action.land()` (AUTO.LAND) UCIEKA pod dead-reckoningiem = 42 m.**
Mechanizm: AUTO.LAND to pętla POZYCYJNA (station-keeping) — pod DR goni DRYFUJĄCĄ estymatę pozycji →
flyaway. **Zasada (do przenoszenia): pod degradacją estymatora dozwolone tylko akcje OTWARTO-PĘTLOWE
względem degradowanej wielkości.** Nawet zejście STEROWANE PRĘDKOŚCIĄ (v_xy=0) dryfuje (dron nie wyzeruje
PRAWDZIWEJ prędkości bez aidingu) — dlatego **czas zejścia = dźwignia** (krótszy epizod = mniejszy ε_pos):
narożnik single-phase 0.7 m/s (~14 s) = 12.33 m → dwufazowy (~10 s) = 4.5–5.0 m.

**D5 ZREWIDOWANE (§4, re-cert P1+P5 od nowa):** akcja po REFUSE(POS) = zejście velocity-descent
dwufazowe (1.5 m/s do 2 m AGL, potem 0.7 m/s), v_xy=0 równocześnie. **AUTO.LAND/RTL WYKLUCZONE z listy
zamkniętej komend osłony.**

---

## (III) LUKA NATYWNEJ WARSTWY-0 + kwantyzacje

**Rozdział FLAGA vs AKCJA (A2):** FLAGA `dead_reckoning`/`failsafe_flags` (zmierzone: → True natychmiast
Δ+0.1 s przy denialu). AKCJA natywna: próg `COM_POS_FS_EPH=5.0 m` (jedyny COM_POS_FS_* w v1.16.2).
**Nota PUSTOŚCI:** eph pod denialiem stacjonarnie osiada <5 m (§7.1) → natywny eph-failsafe MOŻE nie
odpalić — osłona pokrywa lukę. W bramce S2: `refuse_pos_land` osłony przed jakąkolwiek akcją natywną.
`nav_state` niemierzony w executorze R0.3a (nota, do HIL).

**2. INSTANCJA WZORCA „zawodna natywna warstwa-0":** (1) eph-failsafe „martwy" w zawisie (próg 5 m
nieosiągalny pod DR stacjonarnie); (2) **AUTO.LAND flyaway pod DR** (§II'). Wzorzec: natywne mechanizmy
warstwy-0 zakładają zdrowy estymator — pod jego degradacją zawodzą; osłona musi działać otwarto-pętlowo.

**Kwantyzacje (bound D13a ZAMROŻONY):** `REFUSE ≤ debounce(2 ticki=0.10 s) + kwantyzacja odczytu
(1 tick=0.05 s) = 0.15 s`. Zmierzone S2: **0.091 s ≤ 0.15 ✓**.

---

## (IV) HISTORIA REWIZJI + przyrządy + rejestr [A4]

**Łańcuch obaleń pomiarem (każde = WYNIK nogi, wpisane jawnie):**
1. **A-drift OBALONE (B1):** dryf ≠ liniowy — step do plateau; model `ε=rate·age` i deadline θ_pos padły.
2. **1.49 m (ANEKS-2) = ABS z offsetem/skewem, nie błąd EKF:** T_home z ≥20 s uśrednia skew → offset ≈ 0
   (home ≈ gz-world). Stary kanał `gz model -p` odrzucony bramką W5 (p95 0.43 ≫ 0.10; skew 0.3 s).
3. **A-plateau BEZWARUNKOWE OBALONE (B1-bis):** długie v_max DR = runaway 25.7 m → A-episode.
4. **AUTO.LAND OBALONE jako akcja bezpieczna (B1-bis episode):** flyaway 42 m → velocity-descent.

**Wzorzec przyrządu — instancje (prowieniencja):** (poprz.: conf-separator R0.2, laggy-mav R0.2,
att-yaw-only R0.2C) → **R0.3a: (a) ENU/NED** — GT gz=ENU vs EKF=NED, bez swapa fałszywe ~5 m; sędzia
z unit-testem syntetycznym (swap+skew) PASS przed liczeniem; **(b) zegary px4/gz DRYFUJĄ ~0.77%**
(offset +0.96 s/125 s) → parowanie native-sim ODRZUCONE, poprawne = MONO + korekta skew; **(c) skew
stempla** starego kanału gz model -p ~0.3 s → streaming dynamic_pose/info (sim-time u źródła);
**(d) 90 s konwergencji EKF** wymagane (15 s → eph 0.22 broken/flyaway; 90 s → eph 0.150).

**Rozbieżności jawne:** korekta przyczyny odrzucenia lotu 3 B1 (arm() COMMAND_DENIED, nie „bind 14540");
`EKF2_HGT_REF` default=1(GPS) → wymuszony 0(Baro) habitat GPS-denied; healthy p95 podczas ruchu > bramki
0.10 (accel-lag+eph) — bramka W5 liczona na |v|<1 (fidelity kanału, nie EKF-accuracy).

**Rejestr [A4] (założenia do domknięcia realnym IMU/HIL):**
- **A-episode:** ε_pos ≤ ε_cap pod wymuszonym profilem epizodu (walidowane bramką D13c; S2 ✓).
- **A-flag:** utrata aidingu flagowana ≤ t_flag (zmierzone 0.023–0.046 s SITL; HIL potwierdzi).
- **cap z SITL:** ε_cap 37/4 z SITL quasi-idealnego IMU; realny habitat może dać INNY dryf DR →
  re-pomiar HIL/lot; reguła D10/D11 stoi, liczba [A4].
- **VRS:** tempo zejścia z limitu PX4 (SITL nie modeluje VRS) — realny wiropłat potwierdzi margines.

---

## STATUS KOŃCOWY

Twierdzenie **P2-ε PROVED** (z3, ostrość dwustronna); **P1 PROVED** (+POS_DEGRADED, +P1f, +A-episode/A-flag);
**P5 konformancja PASS** (400+15 epizodów, 0 rozbieżności, 8/8 pokrycie); **certs_selfcheck 6/6**; P2/P4
NIETKNIĘTE; r01/test_core 43 asercje PASS; B2 8 testów PASS. Trasa **DOMYKALNA** (half-side' 14.07 > 8.55).
Bramka **S2 LIVE PASS** (pełne D13 a–d); S4/S3/S1 pokryte kompozycyjnie (SR-B4: bez fikcyjnego PASS) —
do domknięcia live przy stabilnym SITL/HIL.

**STOP. Push = Olga.**
