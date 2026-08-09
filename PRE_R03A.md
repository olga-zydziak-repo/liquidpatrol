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

**`ε_budget` Z REGUŁY (D4, zapisujemy REGUŁĘ):** `ε_budget = slack − rezerwa_tick`, gdzie
`rezerwa_tick = v_max·tick = 3.0·0.05 = 0.15 m` (droga w 1 tick osłony przed reakcją) →
`0.866 − 0.15 = 0.716 → ε_budget = 0.7 m`. Rezerwa zawierania po budżecie = `slack − ε_budget = 0.166 m`.

**Formy (D2):** (i) **statyczna** (admisja runtime): ALLOW ⇐ `ε_pos_est ≤ ε_budget`, tj. na deadline
`age_pos ≤ θ_pos`; (ii) **dynamiczna** (dowodzona): `r + d_stop + ε_pos ≤ R_E`. **MOST P2-ε:**
`(i) ∧ (r ≤ R_route) ⇒ (ii)` (przy `r=R_route` worst-case, `ε_pos ≤ ε_budget ≤ slack` ⇒ zawieranie).

**`ε_pos_est = drift_rate · age_pos`** (D1: age_pos czasowe; eph poza admisją). **Deadline
`θ_pos = ε_budget / drift_rate_assumed`.** Admisja: **REFUSE(POS_DEGRADED) gdy `age_pos > θ_pos`**.

**Założenie A-drift (jawne w twierdzeniu P2-ε, jak żywotność osłony):** *„zawieranie WARUNKOWE: dryf
rzeczywisty ≤ `drift_rate_assumed`".* `drift_rate_assumed` z **protokołu B1** (charakteryzacja POD RUCHEM,
status [A4], PRZED zamrożeniem progów — §5/B1). **ZAKAZ wstrzykiwania sztucznego dryfu** (zmiana habitatu
— tylko osobną decyzją Olgi); `drift_rate` mierzony z clean-loss EKF vs GT.

**Arytmetyka Land (A3):** akcja Land dolicza człon `t_land · drift_rate_assumed` — musi zajść:
`t_land · drift_rate_assumed ≤ rezerwa 0.166 m` **ALBO** doliczyć do budżetu (θ_pos pomniejszony).
`t_land` = czas zniżania z ALT_M=10 m — **zmierzyć sondą** (etykieta przyrządu). Nie domyka → **STOP
SR-B1** (nie strojenie).

**Zakres dowodu:** **P2-ε OSOBNY cert** (wzorzec `P2_vmax3p1.json`), kanoniczny `P2.json` NIETKNIĘTY.
z3 NRA: `(i) ∧ (r ≤ R_route) ⇒ (ii)` (UNSAT-ami) + ostrość budżetu (kontrprzykład przy `ε > ε_budget + δ`).

---

## §4. Zmiana automatu + akcja bezpieczna + histereza + re-cert (R4 — papier)

**`REFUSE(POS_DEGRADED)` = 5. REASON, NIE nowy liść** (precedens: ABORT jako 4. reason, `shield.py:32-33`,
R-A; P1c rozszerza zbiór reasonów). P1 7-liściowy NIETKNIĘTY strukturalnie. **Priorytet: prekondycja
geofence** (zdegradowana pozycja podważa barierę `p+v²/2a≤R_E` liczoną na niepewnym p) → poniżej latch,
NA/PONAD R-G. Uzasadnienie: nie wolno ufać barierze na dryfującym p.

**Akcja bezpieczna po REFUSE(POS) = Land (D5):** RTL **wykluczony** (wymaga global position;
`global_position_invalid=True` zmierzone R2). Land = zejście pionowe, nie wymaga pozycji poziomej;
komenda trybu z **listy zamkniętej** węzła osłony (rozszerzenie o Land), zapisana w trace.

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
- **S4** denial przy granicy (najgorsza geometria: narożnik trasy, r≈R_route).

**KRYTERIUM ZAMROŻONE — na MECHANIZM (A1):**
- **(+)** 100% biegów S2/S4 (≥3 świeże booty): **`REFUSE(POS_DEGRADED)` w deadline `θ_pos ± tol`**
  ORAZ **akcja Land domknięta** (touchdown wewnątrz `R_E`) ORAZ **0 naruszeń R_E** ORAZ **0 natywnych
  AKCJI przed akcją osłony** (A2, z notą pustości). `ε_pos_rzecz` (sędzia GT) raportowane **INFORMACYJNIE**
  z notą wierności SITL (NIE w kryterium — clean-loss w quasi-idealnym IMU może dać dryf ≈ 0).
- **(−)** **0 fałszywych `REFUSE(POS)`** w S1 (**N = 5 min × 3 booty**, D7).

**`tol` WYPROWADZONA i ZAMROŻONA** (suma kwantyzacji, składniki policzone): `tol = tick_osłony (0.05 s)
+ okres_źródła_flagi (dead_reckoning @100 Hz = 0.01 s; failsafe_flags @1.85 Hz = 0.54 s — użyć źródła
admisji) + niepewność_stempla_wstrzyknięcia (≤ 1 tick sondy)`. **Admisja czyta `dead_reckoning` @100 Hz**
⇒ `tol ≈ 0.05 + 0.01 + 0.05 = 0.11 s` [POLICZYĆ dokładnie w B2, zamrozić przed bramką].

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

**Stop-rules BUILD:** **SR-B1** arytmetyka Land nie domyka budżetu (A3) → STOP z liczbami. **SR-B2** P5
rozbieżność → STOP (automatu nie łata się pod test). **SR-B3** flapowanie flagi dead-reckoning w nominalu
→ STOP przed resztą bramki, raport z histogramem (bez samowolnego strojenia def. fixu/histerezy). **SR-B4**
wyników bramki nie stroi się po fakcie; FAIL=FAIL z raportem. **SR-B5** params PX4 przywrócone po sesji;
frozen R0.1/R0.2 nietykane; drzewo czyste na koniec.

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

---

## STOP/GO — RATYFIKOWANE (Olga, 2026-08-09)

PRE_R03A **RATYFIKOWANE z riderami R03A-A1..A4 + decyzjami D1–D8** (§0bis, naniesione w §1–§5).
Build wg `PROMPT_R03A_BUILD`: Krok0 aneks (ten commit) → B1 drift_rate (freeze PRZED bramką) → B2
implementacja+testy → B3 P2-ε → B4 re-cert → B5 bramka S1–S4 → B6 RAPORT_R03A. Kolejność freeze→pomiar
dowodzona łańcuchem commitów. Dowody reconu: `results/R03/recon/`. Push = Olga na końcu.
