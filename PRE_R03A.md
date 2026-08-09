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

## §1. Źródła telemetrii (R1 — inwentarz + żywe potwierdzenie XRCE)

Żywe echo (stack SITL, etykieta Hz = `ros2-topic-hz`); pełny inwentarz: `results/R03/recon/R1_topics_inventory.md`.

| topik XRCE | pole | Hz | jednostka/semantyka |
|---|---|---|---|
| `/fmu/out/vehicle_local_position` | **`eph`** | **99.99** | m — std błędu pozycji poziomej (`VehicleLocalPosition.msg:72`) |
| — | **`dead_reckoning`** | 99.99 | bool — brak fixu absolutnego (`.msg:77`) |
| — | `xy_valid`,`v_xy_valid` | 99.99 | bool — ważność |
| `/fmu/out/failsafe_flags` | `local_position_invalid`, `global_position_invalid`, `local_position_accuracy_low` | **1.85** | mapa warstwy-0 (`FailsafeFlags.msg:28/31/51`) |
| `/fmu/out/vehicle_gps_position` (SensorGps) | `fix_type`, `jamming_state`, `spoofing_state` | — | stan GPS (bonus) |

**Minimalny zestaw (wybór z uzasadnieniem):** (a) **age_pos = czas od `dead_reckoning=true`** (NIE eph —
patrz §7 rozbieżność krytyczna); (b) **ε_pos_est** wyprowadzony z age_pos przez model dryfu (bo eph
niewiarygodne w bezruchu), z `eph` jako sygnał POMOCNICZY/górny gdy wiarygodny.

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

**Mapa natywnej warstwy-0:** jedyny param rodziny w v1.16.2 = **`COM_POS_FS_EPH = 5.0 m`**
(`commander_params.c:531`; DELAY/EPV/PROB/GAIN USUNIĘTE — rozbieżność vs starsze PX4). Failsafe:
`local_position_accuracy_low` → `COM_POS_LOW_ACT` (`failsafe.cpp:535`). **Konsekwencja krytyczna:** skoro
`eph` osiada NISKO gdy nieruchomo/zawis, **natywny failsafe eph>5 m może NIE odpalić** — luka, którą
osłona (age_pos czasowe) pokrywa. Analogia GF: warstwa-0 NA ZEWNĄTRZ, kryterium 0 odpaleń w nominale.
**Akcja natywna w LOCIE — NIEZMIERZONA** (iniekcja w locie zawiodła, patrz rozbieżność) → pomiar w buildzie.

**Liczby czasowe (etykieta):** wszystkie z `monotonic_local` (zdarzenia sondy) + `px4-msg-us` (timestamp msg).

---

## §3. Twierdzenie ε_pos + arytmetyka (R3 — papier, cytaty linii)

Stałe zamrożone (`r01/config.py`): `R_ROUTE=28.284` (:21), `V_MAX=3.0` (:24), `T_REACT_S=0.20` (:25,
zmierzone 0.149), `A_BRAKE=2.0` (:26, zmierzone 2.65≥2.0 — rozbieżność, dowód na 2.0 konserwatywnie),
`DELTA_MARGIN=d_stop = v·t_react + v²/2a = 0.6 + 2.25 = 2.85` (:27), `R_E=32.0` (:30).
**slack = R_E − (R_route + d_stop) = 32 − 31.134 = 0.866 m** — naturalny sufit budżetu ε_pos.

**Dwie formy:** (i) **statyczna:** ALLOW ⇐ `ε_pos_est ≤ ε_budget` (stała ≤ slack); (ii) **dynamiczna:**
`r_bież + d_stop + ε_pos_est ≤ R_E` (w locie — dopuszcza większe ε_pos blisko Home).

**REWIZJA z R2 (krytyczna):** `ε_pos_est` **NIE = eph** (eph niedoszacowuje dryf w bezruchu). Robustnie:
**`ε_pos_est = drift_rate · age_pos`** (age_pos = czas w `dead_reckoning`; `drift_rate` [m/s] MIERZONY
w locie GPS-out przeciw GT — build). Admisja realizuje się jako **próg CZASOWY**: REFUSE gdy
`age_pos > age_pos_max = ε_budget / drift_rate`. `eph` sygnał pomocniczy (górny), gdy `¬dead_reckoning`.

**Zakres dowodu:** **P2-ε jako OSOBNY cert** (wzorzec `P2_vmax3p1.json`), kanoniczny `P2.json` NIETKNIĘTY.
z3: bariera rozszerzona `p + v²/2a + ε_pos ≤ R_E` — dodanie członu `ε_pos ≥ 0` (liniowe) → **forma (ii)
w NRA WYKONALNA**. Dowodzimy (ii); admisja = konserwatywne (i) przy `r=R_route` (⇒ `ε_pos ≤ slack`).
**DO RATYFIKACJI:** forma (i) vs (ii); `ε_budget` (propozycja 0.7 m: slack 0.866 − 0.7 = 0.166 m rezerwy
zawierania, i 0.7 ≫ nominalny eph 0.15 → brak fałszywego REFUSE; alternatywa 0.8 zostawia 0.066 m — cieńsza).

---

## §4. Zmiana automatu + akcja bezpieczna + histereza + re-cert (R4 — papier)

**`REFUSE(POS_DEGRADED)` = 5. REASON, NIE nowy liść** (precedens: ABORT jako 4. reason, `shield.py:32-33`,
R-A; P1c rozszerza zbiór reasonów). P1 7-liściowy NIETKNIĘTY strukturalnie. **Priorytet: prekondycja
geofence** (zdegradowana pozycja podważa barierę `p+v²/2a≤R_E` liczoną na niepewnym p) → poniżej latch,
NA/PONAD R-G. Uzasadnienie: nie wolno ufać barierze na dryfującym p.

**Akcja bezpieczna po REFUSE(POS):** RTL **niedostępny** (wymaga global position; `global_position_invalid=True`
zmierzone w R2) → lista zamknięta: **Hold** (na ostatniej estymacie, ryzyko dryfu) lub **Land** (zejście
pionowe, nie wymaga pozycji poziomej). **Rekomendacja: Land** (robustne wobec dryfu). DO RATYFIKACJI.

**Histereza:** re-ALLOW dopiero po **M s** zdrowego fixu (`¬dead_reckoning ∧ eph≤ε_recover`, `ε_recover<ε_budget`).
M DO RATYFIKACJI (propozycja z R2: recovery eph wraca <1 s, ale margines anty-flapping → M≈3–5 s).

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

**KRYTERIUM (ZAMROŻONE, Olga ratyfikuje):**
- **(+)** 100% biegów S2/S4 (≥3 świeże booty każdy): akcja bezpieczna **ZANIM** `ε_pos_rzecz` (sędzia GT)
  przekroczy `ε_budget` ORAZ **0 naruszeń R_E** ORAZ **0 odpaleń natywnego failsafe pozycyjnego**
  (osłona uprzedza warstwę-0);
- **(−)** **0 fałszywych `REFUSE(POS)`** w S1 (N min × 3 booty).
- **N (nominal):** eph nominalny STABILNY ~0.15 m (R1) → N = 3 min (zapas nad transjentami bootu).

**Metryki NIENASYCONE (raportować rozrzut):** czas do REFUSE, `ε_pos_rzecz` przy REFUSE, min margines
`R_E − r`, age_pos przy REFUSE. NIE metryki cięte sufitem (lekcja max_age/θ_age R0.2).

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

## STOP — decyzje do ratyfikacji (Olga)

Recon R1–R5 domknięty; PRE zamrożony. **Koniec sesji, żadnej budowy.** Do ratyfikacji przed buildem:
1. **Sygnał admisji: age_pos CZASOWE (dead_reckoning+czas)** vs eph — rekomendacja: czasowe (§7.1).
2. Forma twierdzenia **(i) statyczna** vs (ii) dynamiczna — rekomendacja: dowód (ii), admisja (i).
3. Reason vs liść — rekomendacja: **reason POS_DEGRADED** (precedens ABORT).
4. **ε_budget** — rekomendacja 0.7 m (rezerwa 0.166 m).
5. **Akcja po REFUSE(POS)** — rekomendacja **Land** (RTL niedostępny bez global pos).
6. **Histereza M** — rekomendacja 3–5 s.
7. **N minut** nominalu — rekomendacja 3 min.
8. **Mechanizm denialu** — rekomendacja `EKF2_GPS_CTRL=0` (kanoniczny `failure gps off` zawiódł).

Push = Olga. Dowody: `results/R03/recon/`. Build startuje po ratyfikacji (osobny cykl).
