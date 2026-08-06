# RAPORT_R01 — domknięcie fazy R0.1 (patrol perymetru pod osłoną)

Status: **KOMPLETNY**. Faza R0.1 (port osłony LiquidSight → PX4/ROS2, bez komponentów uczonych) domknięta 2026-08-06.
Poprzedniki: `RAPORT_R0.md` (bramka R0.0 PASS), `PRE_R01.md` (ratyfikowany + aneksy A1–A4), `results/R01/recon_R01.md`.

## WERDYKT: **R0.1 ZALICZONA** — bramka S1–S4 4/4 + certy P1/P2/P4/P5, niezmiennik A1 utrzymany, 0 padów

Egzekutor offboard lata patrol perymetru pod osłoną runtime ALLOW/HOLD/REFUSE(reason) z księgowością
trójwynikową (odmowa ≠ porażka). Slot uczonego pilota **jawnie pusty** (→ R0.2). Zejście na software nie było potrzebne.

---

## 1. Co postawione

**Stack** (jak R0.0): PX4 SITL v1.16.2 + Gazebo Harmonic 8.14.0 (D3D12) + ROS 2 Jazzy + uXRCE-DDS Agent v2.4.3 + MAVSDK. WSL2/RTX 5070 Ti.

**Port z LiquidSight** (`r01/`, Python + z3 5.0.0; STRUKTURA przeniesiona, LICZBY nowe):
- `shield.py` — automat osłony (bariera geofence P2-analog + HOLD + ABORT + terminal latch + `outcome()` 3-wynik z asercją rozłączności ODMOWA⇔terminal).
- `language.py` / `authz.py` / `memory.py` — gramatyka R0.1 + admisja HMAC-SHA256 + pamięć korekt.
- `config.py` — SCENTRALIZOWANY (A2: obwiednia jedno źródło).
- `exec_lib.py` / `patrol_exec.py` / `gate_run.py` / `brake_test.py` — egzekutor hybrydowy + runner bramki.
- `proofs/` — certy P1/P2/P4/P5 (z3).

## 2. Płaszczyzna sterowania — HYBRYDA (§3 + A1)

- **MAVSDK**: telemetria NED + arm/RTL/Land + param (MPC_XY_VEL_MAX=3, GF_*, COM_OBL_RC_ACT=5) + heartbeat GCS (rozwiązuje znalezisko recon R1: arm czysto-XRCE blokowany).
- **XRCE** (rclpy publisher): OffboardControlMode + TrajectorySetpoint = **jedyna ścieżka setpointów, przez osłonę**; wejście offboard = VehicleCommand DO_SET_MODE (tryb, nie ruch).
- **[A1] Niezmiennik utrzymany we WSZYSTKICH biegach**: `mavsdk_motion_cmds = 0` — żadnej komendy ruchu po MAVSDK. Dowód: trace każdego scenariusza.

## 3. Bramka S1–S4 (kryteria zamrożone §7; świeży boot per scenariusz — zaostrzenie R0.0)

| Scen. | Wynik | Kluczowe | Księgowość |
|---|:---:|---|---|
| **S1** nominal N=3 | **PASS** | 3 okrążenia, wp≤1.5m, tel_gap 0.046s, setpoint 0.053s, A1=0, GF=0, max_r 27.82<32 | SUKCES |
| **S2** wymuszony HOLD | **PASS** | loiter 1.37m≤2, **offboard utrzymany podczas HOLD** (§4), resume domknął, A1=0 | SUKCES (HOLD≠porażka) |
| **S3** wyjście za płot | **PASS** | **REFUSE(GEOFENCE)**, setpoint nieprzepuszczony, max_r 7.12, **GF=0** (osłona uprzedziła) | **ODMOWA** (≠porażka) |
| **S4** warstwa-0 | **PASS** | urwanie strumienia → reakcja natywna 1.234s→HOLD, ≤R_E, scenariusz nie pad, A1=0 | reakcja warstwy-0 |

**A3 (defense-in-depth):** natywny GF (GF_MAX_HOR=37) na zewnątrz obwiedni R_E=32; **0 odpaleń w S1–S3** (osłona uprzedza); S4 jako jedyna celowa reakcja warstwy natywnej.

## 4. Certyfikaty (§8) — wszystkie zaliczone

| Cert | Werdykt | Metoda | Dowodzi |
|---|:---:|---|---|
| **P1** | **PROVED** | z3 1-indukcja | ALLOW⇒¬geo∧¬term; geo⇒REFUSE(GEOFENCE); REFUSE⇒reason∈zbiór; terminal monotoniczny |
| **P2-analog** | **PROVED** | bariera z3 NRA, twierdzenie warunkowe | Inv(p,v)=0≤v≤v_max ∧ p+v²/(2·a_brake)≤R_E ⇒ p≤R_E; założenia jawne |
| **P4** | **PASS** | gramatyka/HMAC/property-2000 | brak trybu bez admisji; poza gramatyką⇒COMMAND_INVALID; sabotaż wykryty |
| **P5** | **PASS** | konformancja per-tick | **tau≡shield 0 rozbieżności, 6/6 pokrycie** — WIĄŻE P1 z KODEM egzekutora |

z3 5.0.0 (jak LiquidSight), certy JSON z `model_sha256` w `r01/proofs/certs/`. **Żadna liczba nie przeniesiona** — wszystkie stałe zmierzone/ustalone dla PX4.

## 5. a_brake (S3-1) + P2-analog (S3-2) — empiryczna, zmierzona

### 5.1 Pomiar a_brake — test hamowania w ruchu przy granicy (`brake_test.py`)
Warunki biegu: lot wzdłuż +x na **v_max**, na **wysokości patrolu 10 m AGL (z = −10 m NED)**; osłona wymusza **REFUSE w pędzie** (target 50 m ≫ R_E). Zmierzone w chwili REFUSE i podczas hamowania:
- **v w chwili REFUSE = 3.084 m/s** (na clampie v_max=3), pozycja x = 14.05 m.
- **droga zatrzymania = 1.794 m** (do v < 0.15 m/s).
- **a_brake = v²/(2·d_stop) = 3.084² / (2·1.794) = 2.65 m/s² — DOLNE OSZACOWANIE** (średnia deceleracja z drogi/energii; deceleracja chwilowa szczytowa 5.80 m/s²). Wartość użyta w barierze to konserwatywne dolne oszacowanie zdolności hamowania.
- **a_brake ≥ A_min (1.447)** oraz **≥ 2.0** → prowizoryczne założenie kodu (a_brake=2.0) **empirycznie potwierdzone jako konserwatywne** (2.0 ≤ 2.65).

### 5.2 Kompozycja t_react ze zmierzonych składników
t_react złożony jawnie z pomiarów S1:
```
t_react = tel_gap(0.046 s) + tick(0.050 s) + okres_setpointu(0.053 s) = 0.149 s  ≤  budżet 0.200 s
```
Suma zmierzonych **0.149 s** mieści się pod przyjętym budżetem **0.2 s** (zapas 0.051 s). W dowodzie użyto budżetu t_react = 0.2 s (1/5).

### 5.3 Nierówność zawierania A2 — przeliczona wartościami z pomiaru
Δ = v_max·t_react + v_max²/(2·a_brake). Z wartościami zmierzonymi (a_brake=2.65):
```
Δ = 3·0.2 + 3²/(2·2.65) = 0.600 + 1.698 = 2.298 m
R_route + Δ = 28.284 + 2.298 = 30.58 m  ≤  R_E = 32 m     → DOMYKA
```
(Dla konserwatywnej wartości kodu a_brake=2.0: Δ = 0.6 + 2.25 = 2.85; R_route+Δ = 31.13 ≤ 32 — również domyka.)
**Poszerzanie obwiedni NIE potrzebne** — R_E=32 wystarcza przy zmierzonej dynamice.

### 5.4 Werdykt bariery z3 NRA (P2-analog) + założenia twierdzenia warunkowego
Cert `r01/proofs/certs/P2.json` (z3 5.0.0), a_brake=2.0 (wartość kodu), A_min=1.447:
**WERDYKT: PROVED** — wszystkie 6 zobowiązań **unsat**:
`base_start_in_route` · `step_allow` · `step_brake` · `safety_p_le_R_E` · `threshold_A_ge_amin_safe` · `threshold_A_lt_amin_unsafe`.

**Twierdzenie (warunkowe):** `Inv(p,v) = 0 ≤ v ≤ v_max ∧ p + v²/(2·a_brake) ≤ R_E  ⇒  p ≤ R_E` (dron respektujący osłonę nie opuszcza obwiedni).
**Założenia jawne:**
1. |v| ≤ v_max = 3.0 m/s (clamp `MPC_XY_VEL_MAX`, zmierzony);
2. t_react = 0.2 s złożony ze zmierzonych (tel_gap+tick+setpoint = 0.149 ≤ 0.2, §5.2);
3. a_brake ≥ 2.0 m/s² (ZMIERZONY 2.65, §5.1 — dolne oszacowanie);
4. hamowanie ciągłe (bariera p + v²/2a zachowana wzdłuż hamowania);
5. rzut na promień (najgorsza oś); **native GF (R_GF = 37 m) jako backstop A3**.

Twierdzenie dowiedzione dla wartości kodu a_brake=2.0; zwalidowane pomiarem 2.65 ≥ 2.0 (`empirical_validation` w P2.json). Model wymierny: v_max=3, t_react=1/5, R_route=2829/100 (≥ 20√2, konserwatywnie), R_E=32.

## 6. Badanie kamery (S3-3) → wejście do R0.2 (NIE bramka R0.1)

Rozdzielono przyczyny niskiego Hz kamery (A4 raportowane, niebramkujące). Sonda 3 konfiguracji:

| Config | rozmiar obrazu | gz-side (gz-transport) | ROS2-bridge |
|---|---|---:|---:|
| 640×480@15 | 900 KB | 13.9 Hz | **2.6 Hz** |
| 320×240@15 | 225 KB | 13.5 Hz | **15.1 Hz** |
| 320×240@30 | 225 KB | 19.7 Hz | **29.2 Hz** |

**Wniosek (ZAMKNIĘCIE RYZYKA):** wąskie gardło = **transport DDS/most ROS2 skalujący się z ROZMIAREM ramki**, NIE render gz (gz-side zawsze zdrowy 13–20 Hz). **Zmierzony sufit mostu: ramka ≤ ~256 KB przechodzi przy PEŁNYM rate** (225 KB → 15 Hz@15, 29 Hz@30); ≥ 900 KB dławi best_effort DDS do 2.6 Hz. Ryzyko „kamera dławi łącze" jest tym samym **domknięte i skwantyfikowane** (nie otwarte): to nie awaria renderu ani symu, lecz znany próg transportu, z jawną granicą. Wyjaśnia anomalię S1 (640×480 = 900 KB → most 2.6 Hz + contention lotu → 1.4 Hz).

**Profil kamery R0.2 mieści się POD progiem** (percepcja, nie sterowanie — slot uczony w R0.2):
- **256×256 @ 1 Hz** = 196 KB/ramkę (< 256 KB) — klatki kontekstowe.
- **64×64 @ 12 Hz** = 12 KB/ramkę (≪ 256 KB) — szybki kanał percepcji.
Oba profile są znacząco pod zmierzonym sufitem mostu → transport nie będzie wąskim gardłem R0.2.

**Opcje uszeregowane (R0.2, malejąco preferencja):**
1. **Ramka ≤ 320×240 (≤ ~256 KB) na moście** — najprostsze, zmierzone jako pełny rate; profil R0.2 już się mieści.
2. **gz-transport w węźle** (subskrypcja gz bez mostu ROS2) — 14 Hz nawet przy 640×480; omija DDS, kosztem integracji poza ekosystemem ROS.
3. **Kompresja** (image_transport / compressed) — utrzymuje duże ramki na moście kosztem CPU/dekompresji; ostatnia opcja.

## 7. Stabilność / higiena
- **0 padów** we wszystkich biegach R0.1 (S1–S4 + brake + sonda kamery): CaptureCrash=0, oops=0. Sygnatura pada A5 (`dxg-22` koincydentne ze śmiercią) nie wystąpiła.
- Świeży boot + teardown per scenariusz; brak sierocych procesów.

### Uwaga o wartościach RTF (co jest miarodajne, a co NIE)
Aby uniknąć błędnego cytowania:
- **MIARODAJNE RTF** (real-time factor symu): **R0.0 soak avg 0.99982** (29 próbek, `RAPORT_R0.md` §3/A4) oraz §3.2 R0.0 ~0.99. To rzeczywisty RTF stacku pod obciążeniem (≈ real-time). W R0.1 sim pracował tak samo (potwierdzenie pośrednie: gz-side kamery 13–20 Hz, lot lockstep bez dryfu).
- **ARTEFAKT — NIE cytować:** wartości RTF ~**0.0035** w `results/R01/gate/camera_probe.log` (sonda S3-3) to **błąd parsera** pola `real_time_factor` z `/world/default/stats` (sonda chwyciła zły token), a NIE realny RTF — sim był zdrowy (gz-side render 13.9–19.7 Hz w tych samych biegach). Te liczby są nieważne i nie należy ich przywoływać jako RTF.
- RTF pozostaje metryką **raportowaną, nie bramkującą** (A4).

## 8. Rozbieżności (rejestr)
1. **Korekta geometrii pod A2 (przy ratyfikacji):** obwiednia 25 m → **R_E=32 m** (narożnik trasy 28.3 m nie mieścił się w 25); margines wyliczony, potem zmierzony (a_brake 2.65). Twierdzenie nietknięte.
2. **ABORT jako 4. reason** osłony (operator) poza 3 z PRE §8 — dodane jawnie, ujęte w P1c/P5.
3. **Kamera Hz (A4)** anomalnie niska pod obciążeniem — zdiagnozowana (transport DDS, §6); raportowana, nie bramkująca; fix w R0.2.
4. **Telemetria osłony przez MAVSDK** wymagała rate 30 Hz + pomiaru luki w fazie patrolu (fix 1.078→0.046s); XRCE-telemetria odnotowana jako opcja robustności R0.2.
5. **`COM_OBL_ACT`/`GF_COUNT` nie istnieją** w PX4 v1.16.2 — użyto `COM_OBL_RC_ACT` (=5 Hold) i 5 param GF_ (recon R1/R2).

## 9. Zakres — co NIE zrobione (jawnie)
- **Slot uczonego pilota/estymatora PUSTY** — planer proceduralny. Percepcja (kamera jako obciążenie, nie wejście sterowania). Wchodzi w **R0.2**.
- P3 (robustność liquid/CfC) — poza R0.1.
- Kamera jako realne wejście percepcji + fix transportu — R0.2.

## 10. Konkluzja

**Faza R0.1 ZALICZONA.** Osłona LiquidSight sportowana na dynamikę PX4: automat + semantyka trójwynikowa + gramatyka/admisja/HMAC działają na żywym egzekutorze offboard. Bramka S1–S4 4/4 (nominal / HOLD / REFUSE-za-płot / warstwa-0) z zamrożonymi kryteriami; certy P1/P2/P4/P5 (P5 wiąże dowody z kodem, P2-analog z jawnymi założeniami zwalidowanymi pomiarem a_brake=2.65). Niezmiennik A1 (setpointy tylko XRCE) utrzymany wszędzie; defense-in-depth (natywny GF) uzbrojony, 0 odpaleń bo osłona uprzedza. Zero padów. Badanie kamery domknięte jako wejście do R0.2. Push do remote wykonuje Olga.
