# PRE_R03A — R0.3a GPS-DENIED: osłona konsumuje zdrowie własnej pozycji (recon → PRE → STOP)

Data: 2026-08-09. Reżim: recon read-only zakończony → pre-rejestracja. PX4 **v1.16.2** (`version.txt`).
Zasada: kryteria dwustronne ZAMROŻONE przed pomiarem; każda liczba czasowa z etykietą przyrządu
(`nav`/`mav`/`monotonic_local`/`ros2-topic-hz`/`px4-msg-us`); rozbieżności jawne; księgowość trójwynikowa.
**Intruz NIEPOTRZEBNY** (noga nieblokowana bugiem renderu tor C). GT symulatora WYŁĄCZNIE jako sędzia.

---

## §0. Teza + zakres

Osłona konsumuje **zdrowie własnej pozycji** semantyką age/próg/sufit (jak dla celu R0.2): `age_pos`
(czas od ostatniego wiarygodnego fixu absolutnego) + estymata niepewności wchodzą do admisji.
Twierdzenie zawierania rozszerzone o dryf: **`r + d_stop + ε_pos ≤ R_E`** — REFUSE zanim dryf zje margines.
Zero komponentów uczonych. GT (`ε_pos_rzecz = |pos_EKF − pos_GT|`) jawnie etykietowany, **nigdy w decyzji**.

**POZA ZAKRESEM (jawnie):** VIO/SLAM, intruz/percepcja, zmiany frozen R0.1/R0.2 (v_max/R_E/a_brake/kanoniczne certy).

---

## §0bis. RATYFIKACJA (2026-08-09) — decyzje D1–D8 + ridery R03A-A1..A4 (WIĄŻĄCE, nadrzędne nad §pierwotnym)

- **D1 — admisja CZASOWA:** `age_pos` od utraty wiarygodnego fixu absolutnego / wejścia w dead-reckoning
  (def. „wiarygodnego fixu" — §1). **`eph` NIGDY w admisji** — pasywna telemetria, jak conf poza kanałem (D1/A1 R0.2).
- **D2 — formy:** dowód formy dynamicznej **(ii)** przez most P2-ε: `(i) ∧ (r ≤ R_route) ⇒ (ii)`; admisja runtime = statyczna **(i)** na deadline `θ_pos`.
- **D3 — `REFUSE(POS_DEGRADED)` = 5. reason** klasy REFUSE (precedens ABORT), bez nowego liścia.
- **D4 — `ε_budget = 0.7 m` Z REGUŁY:** `slack 0.866 − rezerwa_tick (v_max·tick = 3.0·0.05 = 0.15) = 0.716 → 0.7`.
- **D5 — akcja po REFUSE(POS) = Land** (komenda trybu z listy zamkniętej węzła osłony, w trace); RTL wykluczony (brak global pos, R2).
- **D6 — histereza `M = 5 s`** ciągłego zdrowego fixu do re-ALLOW.
- **D7 — nominal S1 = 5 min × 3 świeże booty.**
- **D8 — denial = `EKF2_GPS_CTRL` 7→0** (restore 0→7). **Scope: usunięcie aidingu (clean loss), NIE jamming/spoofing** —
  roszczenia skalowane do tego. Stempel wstrzyknięcia przyrządem; odwracalność per bieg.

**Ridery R03A-A1..A4** naniesione w §1–§5 (A1 sygnał+twierdzenie+drift; A2 flaga-vs-akcja warstwy-0;
A3 ε_budget+M+most+arytmetyka Land; A4 scope denialu+stempel+eph pasywnie).

---

## §0ter. RATYFIKACJA (2026-08-09, po SR-B1) — rewizja A-drift→A-plateau: D9–D13 + R-1/R-2 (WIĄŻĄCE, nadrzędne nad §0bis w zakresie modelu błędu)

**Kontekst:** B1 (drift) OBALIŁ założenie A-drift pomiarem (ANEKS-2, §5ter): dryf = STEP do plateau
~0.9–1.5 m (NIE liniowy), max_drift lot 1 = 1.49 m > slack 0.866 m; model `ε_pos=drift_rate·age_pos`
i deadline `θ_pos` obalone. SR-B1 wyzwolone zasadnie. Olga ratyfikuje rewizję W CAŁOŚCI — obalenie
A-drift wpisane jawnie jako WYNIK nogi (pomiar poprawił twierdzenie), nie ukryte.

- **D9 — model błędu:** A-drift OBALONE (B1). Nowe założenie **A-plateau**: `ε_pos ≤ ε_cap` (błąd
  ograniczony, kształt step-do-plateau), status **[A4]**, z pomiaru in-habitat. **Czas przestaje być
  zmienną ochronną** — żaden deadline nie wygrywa wyścigu ze stepem ~0.7 m w ~0.37 s (lot 1).
- **D10 — reguła cap (zamrożona TERAZ, przed B1-bis):** `ε_cap = 1.5 × max(max_drift po WSZYSTKICH
  ważnych lotach B1 ∪ B1-bis)`, zaokrąglone **w górę** do najbliższego nadrzędnego z siatki ćwiartek
  (…, 2, 9/4, 5/2, 11/4, 3, …). Wartość ROBOCZA z dzisiejszych lotów: `1.5×1.49 = 2.235 → 9/4 = 2.25`
  (finalna liczba zamrożona w ANEKS-4 po B1-bis; TU zapisujemy REGUŁĘ, nie liczbę).
- **D11 — domknięcie GEOMETRIĄ, nie czasem:** `R_route' = R_E − d_stop − ε_cap`; połowa boku kwadratu
  `half-side' = R_route'/√2`. Koperta NIETYKANA: `R_E`/`V_E`/geofence bez zmian — **kurczymy własną
  trasę, nie rozciągamy świata**. Robocze: `32 − 2.85 − 2.25 = 26.90 → half-side' = 26.90/√2 = 19.02 m`.
  Nowa trasa wchodzi jako stała w **config r03** z cytatem reguły D11; `r01/config.py` (frozen, zapis
  historyczny) **NIETKNIĘTY**.
- **D12 — admisja EVENT-BASED:** `REFUSE(POS_DEGRADED)` na **zwalidowanej fladze** utraty aidingu
  (definicja z R1: `dead_reckoning`/`failsafe_flags`) z debounce **2 ticki (0.10 s @ 20 Hz)**; `age_pos`
  zostaje jako telemetria i nośnik histerezy `M = 5 s`. **Rola szybkiego REFUSE:** ogranicza epizod
  dead-reckoningu do reżimu, w którym A-plateau JEST ZMIERZONE — nie „wyprzedza dryf".
- **D13 — kryterium (+) bramki (5 warunków):** (a) REFUSE ≤ debounce + 1 tick od zwalidowanej flagi
  (tol z kwantyzacji, składniki wyprowadzone §5); (b) Land domknięty: touchdown wewnątrz `R_E`
  (sędzia GT); (c) `ε_pos_rzecz ≤ ε_cap` przez **CAŁY epizod** per bieg — to WALIDACJA A-plateau w
  bramce, przekroczenie = FAIL uczciwy, zero strojenia; (d) 0 naruszeń `R_E` (GT); (e) rozdział
  FLAGA/AKCJA natywna wg A2 + 0 natywnych AKCJI przed akcją osłony (z notą możliwej pustości).
  **S4 = cięcie przy narożniku na v_max.** Kryterium (−) bez zmian: **0 fałszywych REFUSE(POS)** w S1
  (5 min × 3 booty).

**Ridery wiążące:**
- **R-1:** w B1-bis pasywnie **liczniki resetów estymatora** (kandydaci: `xy_reset_counter`/
  `z_reset_counter` w `vehicle_local_position` — nazwy ZWERYFIKOWANE w msgs zainstalowanej wersji,
  nie z pamięci). Nota mechanizmu stepu (reset vs transient) jako HIPOTEZA w raporcie — nie diagnoza.
- **R-2:** lekcja przyrządowa **ENU/NED** do PRE (§7): GT gz=ENU vs EKF=NED, bez swapa fałszywe ~5 m —
  korelacja z zamianą osi OBOWIĄZKOWA w sędzim GT. Instrument sędziego dostaje **unit-test na
  syntetyce** (znany błąd → znany wynik, oba układy osi) — **PASS wymagany ZANIM** policzy cokolwiek
  w B1-bis. Przyczyna odrzucenia lotu 3 z B1 dopisana do prowieniencji (§5quater).

---

## §1. Źródła telemetrii (R1 — inwentarz + żywe potwierdzenie XRCE)

Żywe echo (stack SITL, etykieta Hz = `ros2-topic-hz`); pełny inwentarz: `results/R03/recon/R1_topics_inventory.md`.

| topik XRCE | pole | Hz | jednostka/semantyka |
|---|---|---|---|
| `/fmu/out/vehicle_local_position` | **`eph`** | **99.99** | m — std błędu pozycji poziomej (`VehicleLocalPosition.msg:72`) |
| — | **`dead_reckoning`** | 99.99 | bool — brak fixu absolutnego (`.msg:77`) |
| — | `xy_valid`,`v_xy_valid` | 99.99 | bool — ważność |
| `/fmu/out/failsafe_flags` | `local_position_invalid`, `global_position_invalid`, `local_position_accuracy_low` | **1.85** | mapa warstwy-0 (`FailsafeFlags.msg:28/31/51`) |
| `/fmu/out/vehicle_gps_position` (SensorGps) | `fix_type`, `jamming_state`, `spoofing_state` | — | stan GPS (bonus) |

**Definicja „wiarygodnego fixu absolutnego" (D1, wpisana wprost):** `¬dead_reckoning` (fix absolutny
fuzjonowany) — `dead_reckoning=true` ⇔ utrata wiarygodnego fixu ⇔ start `age_pos`. Reset `age_pos`:
`M=5 s` ciągłego `¬dead_reckoning` (histereza D6).

**Minimalny zestaw (D1):** (a) **age_pos = czas od `dead_reckoning=true`** — JEDYNY sygnał admisji;
(b) `ε_pos_est = drift_rate·age_pos` (model dryfu). **`eph` NIGDY w admisji** — pasywna telemetria
(symetria z conf poza kanałem D1/A1 R0.2: eph = zmierzone-ale-niezaufane; do logu/telemetrii, nie decyzji).
Uzasadnienie wykluczenia eph z admisji: §7.1 (niewiarygodne w bezruchu — spike→osiada).

**Rozbieżności (jawne):** (1) `estimator_status` (pełny, `pos_horiz_accuracy[m]`) **NIE publikowany** przez
XRCE — tylko `estimator_status_flags`; `eph` z VLP to jedyny ε_pos[m] przez XRCE. (2) `SensorGps.msg` (src)
nie pokazał jamming/spoofing, ale **żywy topic MA** te pola — żywe echo autorytatywne.

---

## §2. Mechanizm denialu + mapa natywnej warstwy-0 (R2 — sonda live, read-only)

**Mechanizm (SR-1 SPEŁNIONE):** **`EKF2_GPS_CTRL = 0`** (bitmask, default 7, `params_gnss.yaml`; brak
`reboot_required` → runtime) — deterministyczny, ODWRACALNY, tylko GPS (nie dotyka innych sensorów).
Sonda naziemna (disarmed): przy przełączeniu 7→0 (mono `monotonic_local`):
- `dead_reckoning` → **True NATYCHMIAST** (Δ+0.1 s); `failsafe_flags.local_position_invalid` +
  `global_position_invalid` → **True natychmiast**; `xy_valid` → False po **~4 s**; recovery przy 0→7.
- **`eph`: spike 14 m → osiada ~0.012 m** (filtr bez ruchu/GPS „myśli", że zna pozycję). Dowód:
  `results/R03/recon/R2_denial_ekf_ground.jsonl`, `R2_denial_ekf.log`.

**ROZBIEŻNOŚĆ mechanizmu:** `failure gps off` (kanoniczny) przez MAVSDK-`Failure.inject` **TIMEOUT**
(brak ACK) oraz przez pymavlink (`udpout:18570`) **sys=0** (komenda nie dotarła) — w TYM secie nie
zadziałał; `EKF2_GPS_CTRL` to działająca alternatywa. (`full.log`, `inject.log`.) `SYS_FAILURE_EN` istnieje
(`system_params.c:303`, default 0), ale ścieżka iniekcji nie dała efektu.

**Scope denialu (D8/A4):** `EKF2_GPS_CTRL` 7→0 = **usunięcie aidingu GPS (clean loss), NIE jamming/spoofing**
— wszystkie roszczenia skalowane do clean-loss. **Stempel wstrzyknięcia** = `monotonic_local` zdarzenia
denial_on (+ `px4-msg-us` najbliższej próbki); **odwracalność potwierdzana per bieg** (0→7 + weryfikacja
`get_param_int` po biegu, SR-4/SR-B5).

**Mapa natywnej warstwy-0 — ROZDZIAŁ FLAGA vs AKCJA (A2, WIĄŻĄCY):**
- **FLAGA:** `failsafe_flags.local_position_invalid`/`global_position_invalid` (nazwa jawna), czas z
  **kwantyzacją ±0.54 s** (źródło 1.85 Hz → ½·1/1.85=0.27 s? — [DO POLICZENIA w buildzie: ½ okresu =
  0.270 s; recon podał ±0.54 s = pełny okres, etykietować którą konwencją]); flaga to NIE akcja.
- **AKCJA:** czy natywny failsafe wykonał zmianę trybu **w offboard** i kiedy (nav_state, `nav`/`px4-msg-us`).
  Próg: **`COM_POS_FS_EPH=5.0 m`** (`commander_params.c:531`; jedyny COM_POS_FS_* w v1.16.2 — DELAY/EPV/PROB/GAIN
  USUNIĘTE, rozbieżność) → `local_position_accuracy_low` → `COM_POS_LOW_ACT` (`failsafe.cpp:535`).
- **Nagłówek „luka warstwy-0" TYLKO z tym rozdziałem.** Kryterium: **0 natywnych AKCJI przed akcją osłony**
  (jak GF=0), **z notą możliwej PUSTOŚCI** (próg eph 5 m „martwy" w tym trybie — eph osiada <5 m, §7.1).
- **Akcja natywna w LOCIE — NIEZMIERZONA w reconie** (iniekcja w locie zawiodła) → pomiar w bramce (B5/S2).

**Liczby czasowe (etykieta):** wszystkie z `monotonic_local` (zdarzenia sondy) + `px4-msg-us` (timestamp msg).

---

## §3. Twierdzenie ε_pos + arytmetyka (R3 — papier, cytaty linii)

Stałe zamrożone (`r01/config.py`): `R_ROUTE=28.284` (:21), `V_MAX=3.0` (:24), `T_REACT_S=0.20` (:25,
zmierzone 0.149), `A_BRAKE=2.0` (:26, zmierzone 2.65≥2.0 — rozbieżność, dowód na 2.0 konserwatywnie),
`DELTA_MARGIN=d_stop = v·t_react + v²/2a = 0.6 + 2.25 = 2.85` (:27), `R_E=32.0` (:30).
**slack = R_E − (R_route + d_stop) = 32 − 31.134 = 0.866 m** — naturalny sufit budżetu ε_pos.

### §3-REWIZJA (D9–D11, po SR-B1) — forma PLATEAU zastępuje formę rate/deadline

**Twierdzenie zawierania (forma plateau, WIĄŻĄCA):**
`(r_est ≤ R_route') ∧ (ε_pos ≤ ε_cap) ⇒ r_true ≤ R_E`.
Sens: skoro `r_true ≤ r_est + ε_pos` (przy `ε_pos = |pos_EKF − pos_GT|`) oraz `R_route' = R_E − d_stop − ε_cap`,
to na worst-case `r_est = R_route'` (+ zapas hamowania `d_stop` w barierze) mamy
`r_true + d_stop ≤ R_route' + ε_cap + d_stop = R_E`. Zawieranie NIE zależy od czasu ani od kształtu
narastania błędu — tylko od OGRANICZENIA `ε_pos ≤ ε_cap` (A-plateau, [A4], walidowane w bramce D13c).

**Reguła ε_cap (D10) — REGUŁA, nie liczba:** `ε_cap = 1.5 × max(max_drift po WSZYSTKICH ważnych lotach
B1 ∪ B1-bis)`, zaokrąglenie **w górę** do najbliższego nadrzędnego z siatki ćwiartek (…, 2, 9/4, 5/2,
11/4, 3, …). Robocze: `1.5×1.49 = 2.235 → 9/4 = 2.25` (liczba finalna → ANEKS-4 po B1-bis).

**Reguła geometrii (D11) — REGUŁA, nie liczba:** `R_route' = R_E − d_stop − ε_cap`;
`half-side' = R_route'/√2`. `R_E`/geofence NIETYKANE. Robocze: `32 − 2.85 − 2.25 = 26.90 →
half-side' = 19.02 m`. Stała trasy → **config r03** (frozen `r01/config.py` nietknięty).

**Zakres ważności A-plateau:** epizod dead-reckoningu jest OGRANICZONY łańcuchem `flaga → debounce
(2 ticki) → REFUSE(POS_DEGRADED) → Land` (D12); `ε_cap` obowiązuje przez CAŁY epizod aż do touchdown
(walidacja D13c). Poza tym epizodem admisja stoi na zdrowym fixie (`¬dead_reckoning`).

> **[OBALONE B1 — zapis historyczny, NIE kasować (§5ter dowody)]** Poniższe formy rate/deadline
> (D2/A3: `θ_pos`, `ε_pos_est = drift_rate·age_pos`, człon Land `t_land·drift_rate`) zostały OBALONE
> pomiarem B1: dryf to STEP do plateau, nie proces liniowy; żaden deadline nie wyprzedza stepu 0.7 m
> w 0.37 s. Zastąpione formą plateau powyżej. Pozostają jako ślad rewizji.

**`ε_budget` Z REGUŁY (D4, zapisujemy REGUŁĘ):** `ε_budget = slack − rezerwa_tick`, gdzie
`rezerwa_tick = v_max·tick = 3.0·0.05 = 0.15 m` (droga w 1 tick osłony przed reakcją) →
`0.866 − 0.15 = 0.716 → ε_budget = 0.7 m`. Rezerwa zawierania po budżecie = `slack − ε_budget = 0.166 m`.

> **[OBALONE B1 — zapis historyczny, NIE kasować]**
> **Formy (D2):** (i) **statyczna** (admisja runtime): ALLOW ⇐ `ε_pos_est ≤ ε_budget`, tj. na deadline
> `age_pos ≤ θ_pos`; (ii) **dynamiczna** (dowodzona): `r + d_stop + ε_pos ≤ R_E`. **MOST P2-ε:**
> `(i) ∧ (r ≤ R_route) ⇒ (ii)` (przy `r=R_route` worst-case, `ε_pos ≤ ε_budget ≤ slack` ⇒ zawieranie).
>
> **`ε_pos_est = drift_rate · age_pos`** (D1: age_pos czasowe; eph poza admisją). **Deadline
> `θ_pos = ε_budget / drift_rate_assumed`.** Admisja: **REFUSE(POS_DEGRADED) gdy `age_pos > θ_pos`**.
>
> **Założenie A-drift (obalone):** *„zawieranie WARUNKOWE: dryf rzeczywisty ≤ `drift_rate_assumed`".*
> Obalone B1: dryf front-loaded step, nie liniowy → `drift_rate_assumed` niereprezentatywny; zastąpione
> A-plateau (D9). Zakaz wstrzykiwania sztucznego dryfu (zmiana habitatu) OBOWIĄZUJE dalej w B1-bis.

**Arytmetyka Land (A3 — UPROSZCZONA, D13.4):** człon `t_land · drift_rate` **USUNIĘTY** wraz z modelem
rate. Land jest pokryty przez `ε_cap` obowiązujący przez CAŁY epizod aż do touchdown: skoro
`ε_pos ≤ ε_cap` walidowane do momentu przyziemienia (D13c), a `R_route' = R_E − d_stop − ε_cap`, to
touchdown spełnia `r_true ≤ R_E` bez osobnego członu czasowego zniżania. Brak zależności od `t_land`.

**Zakres dowodu (forma plateau):** **P2-ε OSOBNY cert** (`proofs/certs/P2_eps.json`), kanoniczny
`P2.json` NIETKNIĘTY. z3 na dokładnych ułamkach: (a) `(r_est ≤ R_route') ∧ (ε ≤ ε_cap) ⇒ r_true ≤ R_E`
(UNSAT-ami); (b) **ostrość dwustronna** — kontrprzykład przy `ε_cap + δ` ORAZ przy `R_route' + δ`;
(c) człon Land pokryty przez cap (komentarz w modelu + zdanie tu). [OBALONE B1: wzorzec deadline
`ε > ε_budget + δ` zastąpiony ostrością dwustronną cap/geometria.]

### §3bis. RAMKA SĘDZIEGO — definicja ε_pos + T_home (ratyfikacja Olgi 2026-08-09, po weryfikacji B1)

**Kontekst (znalezisko weryfikacji B1, `results/R03/recon/B1bis/instrument/FINDING_eps_definition.md`):**
ANEKS-2 `max_drift=1.49` = ABSOLUTNE `|pos_EKF − pos_GT|` (reprodukcja co do cyfry) — wliczało **offset
ramki home↔gz-world ~0.44 m**, który NIE jest błędem estymatora (przy zdrowym GPS SITL śledzi truth do
cm). Kanał GT `gz model -p` (~2 Hz, stempel przy powrocie subprocessu) ma **~0.2 m szumu skorelowanego
z ruchem** w osi patrolu (latencja stempla; interpolacja nie naprawia).

**DEFINICJA ε_pos (JEDNA, w charakteryzacji i bramce — D13 b/c/d tym samym sędzią):**
`ε_pos = || pos_EKF − (pos_GT ⊖ T_home) ||` w **ramce home** (środek koperty `R_E` = fizyczny punkt
home). `⊖ T_home` = transformacja pozy GT (gz-world, ENU→NED przez zwalidowany swap R-2) do ramki home.

- **T_home (offset ramki):** estymowany **per boot WYŁĄCZNIE z okna zdrowego GPS ≥ 20 s przed denialiem**,
  **trzymany STAŁY przez cały epizod** DR→Land. **Skoki estymaty EKF po resecie liczą się jako błąd ε**
  (NIE re-bazujemy po resecie) — `xy_reset_counter`/`z_reset_counter` (R-1) adnotują epizody resetu.
- To NIE jest „odejmowanie bazy per próbka" — `T_home` to pojedynczy, stały wektor translacji ramki na
  epizod. Dryf/reset EKF w oknie DR wchodzi w pełni do ε_pos.

**BRAMKA INSTRUMENTU per lot (kryterium ważności):** `p95(ε_pos) w oknie zdrowym ≤ 0.10 m` (oczekiwane
~cm przy poprawnym kanale). Powyżej → **lot NIEWAŻNY** (kryterium wykluczenia W5, §5quater). Systematycznie
powyżej **po** naprawie kanału (streaming) → **SR-B7** (STOP-instrument, §6).

**KANAŁ GT (naprawa, R-2):** streaming pozy gz z **sim-time** (stempel u źródła), parowanie strumieni
**po sim-time** (lockstep SITL: `vehicle_local_position.timestamp` == gz sim-time). Zastępuje `gz model -p`.
Unit-test sędziego rozszerzony o **syntetykę RUCHOMĄ** (znane `v` + znany skew stempla → **skew wykryty**).
Raport: korelacja szumu z ruchem **przed/po** naprawie (test hipotezy skew).

**Liczba robocza capa (reguła D10 na ε_pos REL):** `1.5 × 1.15 = 1.725 → 7/4 = 1.75` (B1 lot 1);
**finalnie decyduje siatka B1-bis** (`max` po B1 ∪ B1-bis, przeliczone tą definicją).
> **[OBALONE B1-bis — patrz §3ter]** Robocze 7/4 z B1 lot 1 nieaktualne: B1-bis (kanał streaming)
> pokazał dryf f(czas×v) do 25.7 m/125 s. Cap NIE z długiego okna — patrz A-episode (§3ter).

### §3ter. A-episode — rewizja po B1-bis (ratyfikacja Olgi 2026-08-09, Wariant C zaostrzony)

**A-plateau (BEZWARUNKOWE) OBALONE pomiarem B1-bis (WYNIK nogi, do raportu §II).** Kanał streaming
(mono+skew, wszystkie loty `p95(|v|<1)≤0.10` PASS, `FINDING_clock_and_regime.md`): dryf ma kształt
step-do-plateau (OGRANICZONY per okno), ale **poziom plateau = f(czas_DR × v)** — dron dead-reckonuje
PRĘDKOŚĆ i ucieka zanim estymata się ustabilizuje:

| reżim | plateau max_drift | okno |
|---|---|---|
| hover | 0.30–0.55 m | 83 s |
| narożnik v_max | 4.4 m | 73 s |
| prosta v_max | 6.0 m | 94 s |
| **prosta v_max** | **25.7 m** | **125 s** |

`ε_cap = 1.5×25.7 = 38.6 → R_route' = 32−2.85−38.6 < 0` — **twierdzenie NIEDOMYKALNE przy nieograniczonym
v_max DR**. To FALSYFIKAT bezwarunkowego A-plateau — wpisany jawnie, nie chowany.

**NOWE ZAŁOŻENIE — A-episode:** `ε_pos ≤ ε_cap` pod **WYMUSZONYM profilem epizodu** (nie dowolne DR).
Nośne, bo fast-REFUSE (D12) ogranicza epizod DR do reżimu operacyjnego (intencja D12 dosłownie).
Do **rejestru założeń P1** wchodzą JAWNIE (jak żywotność):
- **A-episode:** zawieranie ważne pod wymuszonym profilem `flaga→debounce→REFUSE→Land→touchdown`.
- **A-flag:** utrata aidingu flagowana ≤ `t_flag` (zmierzone z prowieniencją B1-bis; R2 recon ~0.1 s).

**Profil epizodu (reguła ZAMROŻONA TERAZ, przed lotami episode):**
- Cięcie denialu w **najgorszym stanie**: (i) na prostej przy `v_max` ORAZ (ii) na narożniku.
- Segment **pre-REFUSE na `v_max` przez `t_pre = 1.0 s`** (zamrożone). **Arytmetyka uzasadnienia:**
  `t_pre ≥ 4 × (t_flag + debounce + tick) = 4 × (0.10 + 0.10 + 0.05) = 4 × 0.25 = 1.00 s`
  (`t_flag≈0.10 s` R2/zmierzone B1-bis; `debounce=2 ticki=0.10 s` D12; `tick=0.05 s` @20 Hz) —
  4× łańcucha aidingu→akcja, mocny zapas na worst-case cięcia.
- Potem **Land do touchdown** (near-hover, GPS wciąż DENIED — realny scenariusz; restore po touchdown, SR-B5).
- `ε_pos` liczone przez **CAŁY epizod** (denial→touchdown), D13c bez zmian.

**Cap (reguła D10 na A-episode):** `ε_cap = 1.5 × max(ε_pos po WAŻNYCH lotach EPISODE)`, zaokrągl.
w górę do ćwiartki. **Siatka episode: ≥ 2 stany cięcia × ≥ 2 loty** (prosta v_max, narożnik).

**Zgodność char↔bramka (kluczowe):** **S2/S4 wykonują TEN SAM wymuszony profil** (t_pre=1.0 s v_max →
Land). Self-consistency: charakteryzacja i bramka mierzą ten sam reżim (zachowana z opcji A).

**Długie okno (≥60/≥120 s)** pozostaje w raporcie jako **sonda FALSYFIKUJĄCA** (SR-B6: czy błąd
ograniczony — TAK per okno, ale bezwarunkowe plateau obalone), NIE jako podstawa capa i NIE jako PASS.

**P2-ε: forma nierówności BEZ ZMIAN** (`(r_est≤R_route')∧(ε≤ε_cap)⇒r_true+d_stop≤R_E`) — warunek
A-episode żyje w rejestrze założeń, arytmetyka certu czysta.

### §3quater. Akcja bezpieczna + profil zejścia (ratyfikacja Olgi 2026-08-09, Wariant A z poprawkami)

**Znalezisko B1-bis (loty EPISODE, dobry boot 90 s konwergencji, kanał czysty p95≤0.07):**
prosta v_max `ε_pos=2.45 m`; **narożnik (zwrot 90° v_max) `ε_pos=12.33 m`** (zejście 0.7 m/s ~14 s).
Dryf zdominowany fazą ZEJŚCIA (@5s=2.7→@10s=10.5). **Pod dead-reckoningiem dron NIE wyzeruje
prawdziwej prędkości (brak aidingu) → dryf ~proporcjonalny do CZASU epizodu → tempo/czas zejścia = DŹWIGNIA.**

**ZNALEZISKO KRYTYCZNE — AUTO.LAND UCIEKA (do nagłówka raportu §II'/III):** `d.action.land()`
(AUTO.LAND) pod DR = **flyaway 42 m** — pętla POZYCYJNA (station-keeping) goni DRYFUJĄCĄ estymatę.
**Zasada: pod degradacją estymatora dozwolone tylko akcje OTWARTO-PĘTLOWE względem degradowanej
wielkości.** 2. instancja wzorca „zawodna natywna warstwa-0" (po eph-failsafe „martwym" §2).

**D5 REWIZJA (akcja bezpieczna, aneks §4, re-cert P1+P5 OD NOWA — lista komend = element spec):**
akcja po REFUSE(POS) = **zejście STEROWANE PRĘDKOŚCIĄ z `v_xy=0` zadawanym RÓWNOCZEŚNIE**
(`VelocityNed(0,0,v_down)`). **`d.action.land`/AUTO.LAND WYKLUCZONE z listy zamkniętej komend osłony**
(uzasadnienie: runaway 42 m, pętla pozycyjna na skażonej estymacie). RTL już wykluczony (global pos, R2).

**Profil zejścia DWUFAZOWY (ZAMROŻONY TERAZ, kryterium NIEZALEŻNE):**
- Faza 1 (szybka): `v_desc_fast = MPC_Z_VEL_MAX_DN = 1.5 m/s` (limit PX4 dla trybów prędkościowych =
  granica bezpieczeństwa VRS realnego wiropłata; **v1.16.2 zweryfikowane**: `multicopter_position_control_limits_params.c:81`)
  do `h_switch ≈ 2 m AGL` (z 8 m: ~4 s).
- Faza 2 (dotknięcie): `MPC_LAND_SPEED = 0.7 m/s` (`multicopter_takeoff_land_params.c:111`) do touchdown.
- **NOTA:** SITL NIE modeluje VRS — szybsze zejście niż `MPC_Z_VEL_MAX_DN` byłoby GRANIEM symulatora.
  Profil IDENTYCZNY w charakteryzacji (episode) i w bramce S2/S4.

**Warunek habitatu — height reference (Olga p.3):** `EKF2_HGT_REF` default = **1 (GPS)** — pod denialiem
wysokość degraduje. **Wymuszamy `EKF2_HGT_REF = 0 (Baro)`** na loty episode/bramkę (habitat GPS-denied
używa baro/range dla wysokości); przywracane po sesji (SR-B5). Gdyby baro niedostępne → STOP z liczbami.

**PREDYKCJA PREREJESTROWANA (wpisana PRZED lotami, Olga p.4):**
`ε_pos(narożnik, profil dwufazowy) ∈ [2.5, 6] m`. Wynik POZA pasmem → **zbadać przyczynę PRZED
przyjęciem liczby** (nie przyjmować milcząco).

**Siatka episode (Olga p.5):** **≥ 3 loty narożnik + ≥ 2 prosta** (cap=1.5×max niestabilny na n=1;
narożnik ustawia cap → gęściej tam). Cap/geometria wg D10/D11 bez zmian; poniżej progu → SR-B1' (wynik).

---

## §4. Zmiana automatu + akcja bezpieczna + histereza + re-cert (R4 — papier)

**`REFUSE(POS_DEGRADED)` = 5. REASON, NIE nowy liść** (precedens: ABORT jako 4. reason, `shield.py:32-33`,
R-A; P1c rozszerza zbiór reasonów). P1 7-liściowy NIETKNIĘTY strukturalnie. **Priorytet: prekondycja
geofence** (zdegradowana pozycja podważa barierę `p+v²/2a≤R_E` liczoną na niepewnym p) → poniżej latch,
NA/PONAD R-G. Uzasadnienie: nie wolno ufać barierze na dryfującym p.

**Akcja bezpieczna po REFUSE(POS) [D5 ZREWIDOWANE §3quater]:** = **zejście STEROWANE PRĘDKOŚCIĄ**
`VelocityNed(0,0,v_down)` z `v_xy=0` równocześnie, profil dwufazowy (1.5→0.7 m/s, §3quater).
RTL **wykluczony** (global pos, R2). **AUTO.LAND (`d.action.land`) WYKLUCZONE z listy zamkniętej**
(flyaway 42 m pod DR — pętla pozycyjna goni skażoną estymatę; §3quater). Lista zamknięta komend osłony
= {velocity-setpoint (patrol/OBSERVE), velocity-descent (POS_DEGRADED)}; AUTO.LAND/RTL poza listą.
Zapisane w trace. [OBALONE B1-bis: „Land = komenda trybu" — AUTO.LAND niestabilny pod DR.]

**Histereza (D6): `M = 5 s`** ciągłego zdrowego fixu (`¬dead_reckoning`) do re-ALLOW. (eph poza admisją;
warunek zdrowia = `¬dead_reckoning`, nie eph.)

**Interakcja z dead-manem:** denial to awaria SENSORA — pętla decyzyjna i streamer ŻYJĄ (osłona produkuje
REFUSE(POS), streamer publikuje setpoint akcji bezpiecznej). **Brak sprzężenia z dead-manem** (nie ma
stalla setpointu). Potwierdzone koncepcyjnie; zmierzyć w buildzie (stream_max_dt bez zmian).

**Zakres re-certów:** **P1** (nowy reason POS_DEGRADED + property `POS_DEGRADED ⇒ REFUSE`) — re-run;
**P5** konformancja OD NOWA (shield.py zmieniony); **P2-ε** NOWY cert (forma ii). **P2/P4 NIETKNIĘTE:**
P2 (bariera kanoniczna) bez zmian — ε w osobnym cercie; P4 (gramatyka/HMAC) — POS_DEGRADED to warunek
admisji WEWNĘTRZNY, nie komenda operatora → gramatyka bez zmian.

---

## §5. Scenariusze S1–S4 + kryterium dwustronne (R5 — ZAMROŻONE do ratyfikacji)

- **S1** nominal (zdrowy GPS, patrol ≥N min, świeży boot ×3).
- **S2** denial w patrolu → akcja bezpieczna.
- **S3** denial + recovery → powrót do ALLOW po histerezie M.
- **S4** **cięcie przy narożniku na `v_max`** (najgorsza geometria + worst-case stanu prędkości w
  chwili cięcia: `r≈R_route'`, pełna `v_max` w kierunku narożnika).

**KRYTERIUM ZAMROŻONE — forma PLATEAU (D13, nadrzędne nad A1):**
- **(+)** 100% biegów S2/S4 (≥3 świeże booty), WSZYSTKIE 5 warunków:
  - **(a)** `REFUSE(POS_DEGRADED)` ≤ **debounce + 1 tick** od zwalidowanej flagi (tol niżej).
  - **(b)** Land domknięty: **touchdown wewnątrz `R_E`** (sędzia GT).
  - **(c)** `ε_pos_rzecz ≤ ε_cap` przez **CAŁY epizod** per bieg — WALIDACJA A-plateau w bramce.
    Przekroczenie = **FAIL uczciwy**, zero strojenia. *(Zmiana vs A1: ε_pos_rzecz WCHODZI teraz do
    kryterium jako test A-plateau — nie jest już „tylko informacyjne". Nota wierności SITL zostaje:
    clean-loss w quasi-idealnym IMU może dać ε_pos_rzecz ≪ ε_cap — to nie zwalnia z warunku, tylko
    raportowane jako margines.)*
  - **(d)** 0 naruszeń `R_E` (GT).
  - **(e)** rozdział FLAGA/AKCJA natywna wg A2 + **0 natywnych AKCJI przed akcją osłony** (z notą
    możliwej pustości — próg eph 5 m „martwy", §7.1/§2).
- **(−)** **0 fałszywych `REFUSE(POS)`** w S1 (**N = 5 min × 3 booty**, D7).

**Zakres ważności A-plateau (w bramce):** epizod DR ograniczony `flaga→debounce→REFUSE→Land`; `ε_cap`
walidowany do touchdown (D13c). Twierdzenie plateau NIE rości ważności poza tym epizodem.

**`tol` dla (a) — WYPROWADZONA i ZAMROŻONA** (event-based, kwantyzacja @20 Hz, tick = 0.05 s):
`bound = debounce (2 ticki = 0.10 s) + kwantyzacja_odczytu_flagi (1 tick = 0.05 s) = 0.15 s`.
Składnik kwantyzacji: flaga `dead_reckoning` (źródło @~100 Hz) próbkowana przez osłonę na jej ticku
20 Hz ⇒ do 1 ticka opóźnienia detekcji. Niepewność stempla wstrzyknięcia (≤ 1 tick sondy) mierzona
INFORMACYJNIE per bieg (nie poszerza bound — bound liczony od ZWALIDOWANEJ flagi, nie od iniekcji).
**Bound 0.15 s zamrożony**; dokładny odczyt składników potwierdzony w B2 (SR-B2 gdyby się rozjechał).

**Metryki NIENASYCONE (rozrzut):** czas-do-REFUSE, `ε_pos_rzecz` przy REFUSE, min margines `R_E−r`,
czas Land, age_pos przy REFUSE. NIE metryki cięte deadline'em (lekcja max_age/θ_age R0.2).

---

## §5bis. Protokół B1 — charakteryzacja `drift_rate` (ZAMROŻONY PRZED pomiarem)

3 biegi patrolowe (trasa R0.1, świeży boot każdy): denial w locie, okno dead-reckoning **≥ 60 s POD RUCHEM**.
`drift_rate_measured_p95 = p95( |Δ(pos_EKF − pos_GT)| / Δt )` w oknach. Kanały: **GT = poza gz, etykieta
`gt_judge`**; **EKF = `vehicle_local_position`, etykieta `nav-local`**; **Δt = `monotonic_local`**.

**REGUŁA WYBORU (zamrożona TERAZ, przed liczbą):**
`drift_rate_assumed = max( 2 × drift_rate_measured_p95 , ε_budget / θ_pos_max )`, `θ_pos_max = 30 s`
(podłoga testowalności — zweryfikuj że noga S2 trwa ≥ `θ_pos + 15 s`). `θ_pos = ε_budget / drift_rate_assumed`
(≤ 30 s z konstrukcji). Jeśli `drift_rate_measured ≈ 0` (SITL quasi-idealne IMU) — to WYNIK do raportu
(nota wierności), deadline stoi na A-drift; **zero „poprawiania" symulatora**. Wyniki → ANEKS-2 → commit
zamrażający (PRE) PRZED bramką (kolejność freeze→pomiar dowodzona łańcuchem commitów).

---

## §5ter. ANEKS-2 — wyniki B1 (drift) + ROZBIEŻNOŚĆ (SR-B1 wyzwolone, 2026-08-09)

Pomiar (2 loty ważne z 3; lot 3 padł na bind MAVSDK 14540 — nie zmienił params; loty patrol offboard-velocity
±1.5 m/s, denial `EKF2_GPS_CTRL 7→0` w locie ≥65 s pod ruchem). Kanały: GT=`gz model -p` (`gt_judge`),
EKF=`vehicle_local_position` (`nav-local`), Δt=`monotonic_local`. Dowody: `results/R03/recon/B1_drift/`.
**Uwaga osi (znalezisko):** GT gz=ENU, EKF=NED → korelacja z zamianą osi (EKF.x↔GT.y); bez swap fałszywe ~5 m.

| lot | max_drift (swap) | plateau | p95_rate (chwil.) | czas dryf>ε_budget 0.7 m |
|---|---|---|---|---|
| 1 | **1.49 m** | 1.48 m | 0.0087 m/s | **0.37 s** |
| 2 | 0.91 m | 0.79 m | 0.108 m/s | 4.25 s |

**ROZBIEŻNOŚĆ KRYTYCZNA (A-drift OBALONE pomiarem) → SR-B1:**
- Dryf to **STEP do plateau (~0.9–1.5 m), NIE liniowy**; osiąga plateau w ~11 s pod ciągłym ruchem.
- **max plateau 1.49 m > slack 0.866 m** → przy narożniku `R_route+d_stop+drift=28.284+2.85+1.49=32.62 > R_E 32`.
- Reguła freeze (rate-based): `drift_rate_assumed=max(2×0.108, 0.7/30)=0.216 m/s → θ_pos=3.24 s` — ale realny
  dryf przekracza ε_budget w **0.37 s (lot 1)** ⇒ przy θ_pos=3.24 s dryf ≈1.2 m przy REFUSE ⇒ **arytmetyka
  Land NIE domyka** (`step 1.49 m > rezerwa 0.166 m`). Model liniowy `ε_pos=drift_rate·age_pos` nie pasuje.
- **Niuans (nie rozstrzygnięty bez decyzji):** loty mierzyły dryf pod CIĄGŁYM ruchem 65 s (worst case);
  osłona REFUSE→Land zatrzymuje ruch → istotny dryf w oknie [0,θ_pos]. Bezpośredni „czas-do-ε_budget"
  daje θ_pos ≈ **0.37 s** (min z lotów) = REFUSE ~natychmiast na dead_reckoning. Metryka rate-based reguły
  jest plateau-dominowana (kaptuje flat rate ~0, nie front-loaded step).

**STATUS: STOP (SR-B1) — arytmetyka nie domyka; θ_pos NIE zamrożony.** Decyzja Olgi: (i) θ_pos z
bezpośredniego czasu-do-ε_budget (~0.37 s, REFUSE natychmiast) zamiast rate-reguły; LUB (ii) re-def metryki
dryfu (front-window); LUB (iii) re-pomiar z osłoną zatrzymującą ruch (dryf w krótkim oknie); LUB (iv)
limitacja habitat/geometria (clean-loss w narożniku poza obwiednią). NIE strojenie.

**ROZSTRZYGNIĘCIE (2026-08-09):** Olga wybrała ścieżkę **rewizji modelu** — A-drift→A-plateau (D9),
domknięcie GEOMETRIĄ nie czasem (D11). Rate/θ_pos porzucone; cap `ε_cap` z reguły D10; admisja
event-based (D12). Szczegóły §0ter/§3-REWIZJA. B1-bis (§5quater) rozszerza charakteryzację przed freeze.

---

## §5quater. Protokół B1-bis — rozszerzona charakteryzacja plateau (ZAMROŻONY PRZED biegami)

**Cel:** zebrać `max(max_drift)` po większej, celowanej siatce (worst-case stanów prędkości) → reguła
D10 → `ε_cap`; reguła D11 → `R_route'`/`half-side'`; test progu degeneracji SR-B1'. GT **WYŁĄCZNIE
sędzią**; instrument sędziego zwalidowany unit-testem (R-2) PRZED liczeniem.

**Siatka (≥ 6 WAŻNYCH lotów, świeży boot każdy):**
- 2× cięcie/denial **w zawisie** (v≈0 w chwili denialu),
- 2× **na prostej przy `v_max`** (denial w połowie nogi, pełna prędkość),
- 2× **przy narożniku** (worst-case stanu prędkości w chwili cięcia — zmiana kierunku).
- Okna dead-reckoning **≥ 60 s**; **jeden lot z oknem ≥ 120 s** (sonda stabilności plateau — czy nie
  narasta dalej po plateau; wejście do SR-B6).

**Metryki per lot** (etykiety przyrządów, oś-swap przez ZWALIDOWANY instrument):
`max_drift`, `plateau` (średnia po transiencie), `t_do_plateau`, **liczniki resetów** (R-1:
`xy_reset_counter`/`z_reset_counter` z `vehicle_local_position` — nazwy zweryfikować w msgs zainstalowanej
wersji przy budowie rejestratora).

**Kryteria WYKLUCZENIA lotu (zamrożone TERAZ; wyprowadzone z przyczyny odrzucenia lotu 3 B1 — §5quater-prov):**
lot ODRZUCONY (nie wchodzi do siatki `max`) jeśli którekolwiek: **(W1)** nie osiągnął fazy
`armed→takeoff→offboard→denial_on` (np. `arm() COMMAND_DENIED`, utrata offboard przed denialem);
**(W2)** okno dead-reckoning pod ruchem < 60 s; **(W3)** luka telemetrii EKF > 1.0 s (5 pominiętych
próbek @20 Hz) LUB brak próbek GT przez > 2.0 s w oknie DR; **(W4)** params PX4 nieprzywrócone po locie
(`EKF2_GPS_CTRL≠7` — SR-B5); **(W5)** bramka instrumentu (§3bis): `p95(ε_pos) w oknie zdrowym > 0.10 m`
(kanał GT niewiarygodny na tym locie). Odrzucenie logowane z przyczyną (prowieniencja), NIE po cichu.

**Kanał GT + T_home (§3bis, WIĄŻĄCE):** rejestrator B1-bis używa **streamingu pozy gz z sim-time**
(nie `gz model -p`); parowanie po sim-time; `T_home` z okna zdrowego ≥ 20 s, stały na epizod; loguje
`vehicle_local_position.timestamp` (px4/sim), `xy_reset_counter`, `z_reset_counter` (R-1).

**§5quater-prov (prowieniencja lotu 3 B1, R-2):** lot 3 B1 (`/tmp/r03b/b1_3.jsonl`, 1958 próbek)
ODRZUCONY. **Przyczyna proksymalna: `arm() COMMAND_DENIED`** (`fly_3.log`) — dron NIGDY nie uzbroił/
wystartował ⇒ brak ważnego okna DR (W1). Ostrzeżenie „bind error: Address in use" pojawia się w logach
**WSZYSTKICH** lotów (także ważnych 1,2) — to NIE jest cecha różnicująca; ANEKS-2 przypisało odrzucenie
błędnie „bind MAVSDK 14540". **Korekta wpisana tu** (lekcja: różnicować przyczynę proksymalną od
ubiquitous warning). Loty ważne: lot 1 = `b1_val.jsonl`→`b1_flight1.jsonl` (2022), lot 2 = `b1_2.jsonl`→
`b1_flight2.jsonl` (1919).

**SR-B1' — próg degeneracji trasy (ZAMROŻONY TERAZ, przed liczbami z siatki):**
`half-side'_min = 3 × d_stop = 3 × 2.85 = 8.55 m`. **Uzasadnienie (grid-independent, dwa filary):**
1. **Testowalność S4 (wiążący):** noga trasy ma długość `2·half-side'`; przy narożniku pochłania
   `d_stop` na hamowanie. Aby `v_max` było UTRZYMANE przez nietrywialny odcinek (S4 wymaga worst-case
   v_max), segment cruise `≈ 2·half-side' − 2·d_stop` musi być dodatni i znaczący. Przy
   `half-side' = 3·d_stop`: noga = `6·d_stop`, cruise ≈ `4·d_stop = 2/3 nogi` → v_max realnie
   utrzymane. Poniżej `3·d_stop` frakcja utrzymanego v_max się załamuje i **S4 przestaje być
   wiernym worst-case** (kryterium zamrożone stałoby się niemierzalne).
2. **Pokrycie pola (kontrolny):** oryginał `half-side = R_route/√2 = 20.0 m`; przy 8.55 m pokrycie
   `(2·8.55)²/(2·20)² ≈ 18%` oryginalnego pola — twardy dół.
Mapowanie na cap: `half-side' ≥ 8.55 ⇔ ε_cap ≤ R_E − d_stop − √2·8.55 = 32 − 2.85 − 12.09 = 17.06 m`.
**Jeśli reguła D10 da `ε_cap` wymuszający `half-side' < 8.55 m` → STOP (SR-B1'): twierdzenie w tym
habitacie/geometrii niedomykalne — WYNIK z liczbami, nie dowożenie pozytywu.** (Robocze po §3bis `ε_cap=7/4=1.75`
→ `R_route'=32−2.85−1.75=27.40` → `half-side'=27.40/√2=19.38 m ≫ 8.55` → margines duży; próg to
backstop na katastrofę, nie target. Finalne z B1-bis.)

**[REWIZJA po B1-bis — §3ter]:** długie okna (siatka wyżej) WYKONANE jako **sonda falsyfikująca**
(kanał streaming; A-plateau bezwarunkowe OBALONE). **Cap NIE z długiego okna.** Podstawa capa = loty
**EPISODE** (profil `t_pre=1.0 s v_max → Land→touchdown`, §3ter): ≥ 2 stany (prosta v_max, narożnik)
× ≥ 2 loty; `ε_cap = 1.5×max(ε_pos episode)`. Kanał/instrument/bramka W5 (`p95(|v|<1)≤0.10`) bez zmian.

**Kolejność:** unit-test sędziego PASS ✓ → sonda długiego okna (falsyfikacja A-plateau) ✓ → **loty
EPISODE** → ε_cap (D10 na A-episode) → D11 → SR-B1' → **ANEKS-4 (freeze, commit tylko PRE) PRZED B2**.
Freeze→pomiar dowodzony łańcuchem commitów.

---

## §5quinquies. ANEKS-4 — FREEZE liczb (B1-bis episode dwufazowy, 2026-08-10)

**Loty EPISODE (profil dwufazowy §3quater, dobry boot 90 s konwergencji EKF, kanał czysty,
`EKF2_HGT_REF=0` Baro; ε_pos liczone denial→touchdown zwalidowanym sędzią mono+skew):**

| lot | stan | ε_pos [m] | p95(v<1) | ważny | epi_dr | t_flag |
|---|---|---|---|---|---|---|
| p_c1 | narożnik 90° v_max | 4.99 | 0.075 | ✓ | 9.94 s | — |
| p_c2 | narożnik 90° v_max | 4.47 | — | ✓ | 9.97 s | — |
| p_c3 | narożnik 90° v_max | 4.75 | — | ✓ | 9.96 s | — |
| p_s1 | prosta v_max | 3.36 | — | ✓ | 9.97 s | — |
| p_s2 | prosta v_max | **6.02** | 0.087 | ✓ | 9.93 s | 0.023 s |

Dowody: `results/R03/recon/B1bis/episode/` (`metrics_episode2.jsonl`, jsonl+flylog per lot).

**Sprawdzenie predykcji prerejestrowanej (§3quater):** narożnik ∈ **[2.5, 6] m** → zmierzone 4.47–4.99
**W PAŚMIE ✓**. **Prosta p_s2 = 6.02 m > narożniki** (nieoczekiwane; wariancja błędu prędkości DR
per boot — prosta nie ma bandu, ale jako max NAPĘDZA cap). Pomiar czysty (episode-clipped = full-dr max
6.023; skew nieistotny; p95 0.087 ✓) — przyjęty, nie odrzucony.

**FREEZE — reguła D10 (na max ważnych episode):**
`max ε_pos = 6.023` (p_s2) → `ε_cap = 1.5 × 6.023 = 9.034` → zaokrągl. w górę do ćwiartki = **`ε_cap = 37/4 = 9.25 m`**.

**FREEZE — reguła D11 (geometria):**
`R_route' = R_E − d_stop − ε_cap = 32 − 2.85 − 9.25 = **19.90 m**`;
`half-side' = R_route'/√2 = 19.90/√2 = **14.07 m**`.

**SR-B1' (próg degeneracji 8.55 m):** `half-side' = 14.07 m ≫ 8.55` → **NIE wyzwolone → TWIERDZENIE
DOMYKALNE** w tej geometrii przy profilu dwufazowym. (A-plateau bezwarunkowe było niedomykalne — §3ter;
A-episode z akcją velocity-descent dwufazową **domyka**.)

**Te liczby → stała w `config r03` (B2), cert P2-ε `ε_cap=37/4` (B3).** `r01/config.py` (frozen) NIETKNIĘTY.
Robocze wcześniejsze (9/4, 7/4) **OBALONE/zastąpione** finalnym `37/4` z pomiaru episode.

---

## §6. Stop-rules

- **SR-1** brak deterministycznego, odwracalnego denialu → **SPEŁNIONE** (EKF2_GPS_CTRL=0 działa); gdyby
  odpadł — STOP z opcjami.
- **SR-2** natywne failsafe pozycyjne systematycznie ubiega osłonę → to WYNIK do zmierzenia i raportu
  (trójwynikowo), NIE powód do strojenia progów pod pozytyw. (R2 sugeruje ODWROTNIE: native eph-failsafe
  może NIE odpalać w zawisie — osłona pokrywa lukę.)
- **SR-3** wymagane sygnały niedostępne przez XRCE → częściowo dotknięte: `estimator_status` niedostępny,
  ale `eph`+`dead_reckoning`+`failsafe_flags` wystarczają. **NIE przechodzić po cichu na MAVSDK-telemetrię.**
- **SR-4** żaden param PX4 zmieniony w sondach nie zostaje → **SPEŁNIONE** (EKF2_GPS_CTRL=7, SYS_FAILURE_EN=0
  zweryfikowane po sondzie).

**Stop-rules BUILD:** **SR-B1** [WYZWOLONE 2026-08-09, ROZSTRZYGNIĘTE rewizją D9–D13 — patrz §5ter/§0ter;
zostaje w historii] arytmetyka Land/deadline nie domyka → było STOP z liczbami → rewizja A-plateau.
**SR-B1'** geometria: `half-side' < 8.55 m` (próg §5quater) → STOP z liczbami (twierdzenie niedomykalne
w tej geometrii — WYNIK). **SR-B2** P5 rozbieżność → STOP (automatu nie łata się pod test). **SR-B3**
flapowanie flagi dead-reckoning w nominalu → STOP przed resztą bramki, raport z histogramem (bez
samowolnego strojenia def. fixu/histerezy). **SR-B4** wyników bramki nie stroi się po fakcie; FAIL=FAIL
z raportem. **SR-B5** params PX4 przywrócone po sesji; frozen R0.1/R0.2 nietykane; drzewo czyste na koniec.
**SR-B6** [WERDYKT WARUNKOWY po B1-bis]: błąd **OGRANICZONY per wymuszony epizod (A-episode)** — PASS
w tym sensie; ale **wzrost ~z dystansem DR przy podtrzymanym `v_max` → bezwarunkowe A-plateau OBALONE**
(25.7 m/125 s, §3ter). Długie okno = sonda falsyfikująca (nie PASS). Gdyby błąd rósł BEZ plateau nawet
per wymuszony epizod (episode ε_pos nieograniczone) → STOP z liczbami (A-episode pada jak A-drift). **SR-B7** (instrument, §3bis) `p95(ε_pos) w oknie zdrowym > 0.10 m
SYSTEMATYCZNIE po naprawie kanału GT (streaming sim-time)` → STOP-instrument: sędzia niewiarygodny,
brak podstawy do freeze — decyzja Olgi o kanale GT/definicji przed jakimkolwiek pomiarem capa.

---

## §7. Rozbieżności jawne (zbiorczo)

1. **KRYTYCZNA — `eph` niewiarygodne w bezruchu** (spike→osiada ~0.012 m przy GPS-out stacjonarnie) →
   ε_pos NIE może stać na eph; age_pos CZASOWE (dead_reckoning+czas) + model dryfu. Zmienia realizację
   tezy (§3). `drift_rate` do zmierzenia w locie (build).
2. `failure gps off` (kanoniczny) nie zadziałał w tym secie (MAVSDK inject timeout / pymavlink sys=0) →
   mechanizm = `EKF2_GPS_CTRL=0`.
3. `COM_POS_FS_*` w v1.16.2 zredukowane do `COM_POS_FS_EPH` (rodzina DELAY/EPV/PROB/GAIN usunięta).
4. `estimator_status` (pos_horiz_accuracy) nie przez XRCE; `SensorGps.msg` src vs żywy topic (jamming/spoofing).
5. Akcja natywna w LOCIE niezmierzona (iniekcja w locie zawiodła) — build.
6. **PRZYRZĄD ENU/NED (R-2, lekcja z B1):** GT `gz model -p` = **ENU**; EKF `vehicle_local_position` =
   **NED**. Bez zamiany osi (EKF.x↔GT.y, znak z) sędzia GT liczy fałszywe ~5 m. **Korelacja z zamianą
   osi OBOWIĄZKOWA**; instrument sędziego (skrypt) dostaje **unit-test na syntetyce** (znany błąd →
   znany wynik, oba układy) — PASS wymagany ZANIM policzy cokolwiek w B1-bis. 8. instancja wzorca
   „prowieniencja przyrządu" (po conf-separator R0.2, laggy-mav R0.2, att-yaw-only R0.2C…).
7. **Przyczyna odrzucenia lotu 3 B1 skorygowana** (§5quater-prov): proksymalnie `arm() COMMAND_DENIED`,
   nie „bind 14540" (bind warning ubiquitous, nie różnicujący).

---

## STOP/GO — RATYFIKOWANE (Olga, 2026-08-09)

PRE_R03A **RATYFIKOWANE z riderami R03A-A1..A4 + decyzjami D1–D8** (§0bis, naniesione w §1–§5).
Build wg `PROMPT_R03A_BUILD`: Krok0 aneks (ten commit) → B1 drift_rate (freeze PRZED bramką) → B2
implementacja+testy → B3 P2-ε → B4 re-cert → B5 bramka S1–S4 → B6 RAPORT_R03A. Kolejność freeze→pomiar
dowodzona łańcuchem commitów. Dowody reconu: `results/R03/recon/`. Push = Olga na końcu.
