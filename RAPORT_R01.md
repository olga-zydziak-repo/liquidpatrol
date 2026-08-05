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

## 5. a_brake + walidacja A2 (S3-1) — empiryczna, zmierzona

Test hamowania w ruchu przy granicy (`brake_test.py`): lot na v_max → REFUSE w pędzie (v=3.08 m/s) → hamowanie.
- **a_brake zmierzone = 2.65 m/s²** (droga zatrzymania 1.79 m; peak decel 5.8).
- **a_brake ≥ A_min (1.44)** i **≥ 2.0** → prowizoryczne założenie kodu (2.0) **empirycznie potwierdzone jako konserwatywne**.
- **A2 (nierówność zawierania) DOMYKA przy R_E=32**: R_route 28.28 + Δ 2.298 = 30.58 ≤ 32 → **poszerzanie obwiedni NIE potrzebne**.
- **t_react = 0.2 s** złożony ze zmierzonych: tel_gap 0.046 + tick 0.05 + setpoint 0.053 = **0.149 s ≤ budżet 0.2 s**.

P2-analog dowiedziony dla a_brake=2.0 (wartość kodu), zwalidowany pomiarem 2.65 ≥ 2.0 (`empirical_validation` w P2.json).

## 6. Badanie kamery (S3-3) → wejście do R0.2 (NIE bramka R0.1)

Rozdzielono przyczyny niskiego Hz kamery (A4 raportowane, niebramkujące). Sonda 3 konfiguracji:

| Config | rozmiar obrazu | gz-side (gz-transport) | ROS2-bridge |
|---|---|---:|---:|
| 640×480@15 | 900 KB | 13.9 Hz | **2.6 Hz** |
| 320×240@15 | 225 KB | 13.5 Hz | **15.1 Hz** |
| 320×240@30 | 225 KB | 19.7 Hz | **29.2 Hz** |

**Wniosek:** wąskie gardło = **transport DDS/most ROS2 skalujący się z ROZMIAREM obrazu**, NIE render gz (gz-side zawsze zdrowy). 900 KB dławi best_effort DDS do 2.6 Hz; 225 KB przechodzi pełną częstotliwość. Wyjaśnia anomalię S1 (640×480 bridge 2.6 Hz + contention lotu → 1.4 Hz).
**Rekomendacja R0.2:** kamera bridged ≤320×240 (≤256 KB) → pełny rate; albo **gz-transport bez mostu** (14 Hz przy 640×480); albo tuning QoS/kompresja. (RTF w sondzie = artefakt parsowania; zdrowie symu z gz-side Hz.)

## 7. Stabilność / higiena
- **0 padów** we wszystkich biegach R0.1 (S1–S4 + brake + sonda kamery): CaptureCrash=0, oops=0. Sygnatura pada A5 (`dxg-22` koincydentne ze śmiercią) nie wystąpiła.
- Świeży boot + teardown per scenariusz; brak sierocych procesów.

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
