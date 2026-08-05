# RAPORT BRAMKI R0.1 — scenariusze S1–S4 + certy P1/P4/P5 (sesja 2) — 2026-08-05

Zakres sesji 2 (§9): kamera-load w tle (A4) + scenariusze S1–S4 + natywny GF (A3) + certy P1/P4/P5.
Dyscyplina: **każdy scenariusz na świeżym boocie** (zaostrzenie jawne, wzorzec R0.0); każdy = trace jsonl
+ licznik `mavsdk_motion_cmds` (A1) + artefakty + dmesg-check; commit po scenariuszu.
Stack per scenariusz: PX4 v1.16.2 `gz_x500_mono_cam` + kamera-load (A4: 640×480@15, visualize=false)
+ uXRCE-DDS Agent + MAVSDK, GUI D3D12. Natywny GF (A3): GF_MAX_HOR=37/VER=25/ACTION=Hold; COM_OBL_RC_ACT=5.

## WERDYKT: **S1–S4 = 4/4 PASS**; certy **P1 PROVED, P4 PASS, P5 PASS**. **0 padów** we wszystkich scenariuszach.

## Scenariusze (kryteria zamrożone §7)

| Scen. | Wynik | Kluczowe metryki | Księgowość |
|---|:---:|---|---|
| **S1** nominal N=3 | **PASS** | laps 3/3, wp ≤1.5m, tel_gap **0.046s**<0.5, setpoint **0.053s**<0.5, **A1=0**, **GF=0**, max_radial 27.82<32 | **SUKCES** |
| **S2** wymuszony HOLD | **PASS** | loiter drift **1.37m**≤2, **offboard utrzymany podczas HOLD** (nie urywa strumienia, §4), resume domknął misję, n_hold=1, A1=0, GF=0 | **SUKCES** (HOLD≠porażka) |
| **S3** wyjście za płot | **PASS** | **REFUSE(GEOFENCE)**, setpoint nieprzepuszczony, max_radial **7.12**≤32, **GF=0** (osłona uprzedziła), A1=0 | **ODMOWA** (odmowa≠porażka) |
| **S4** warstwa-0 (urwanie strumienia) | **PASS** | reakcja natywna **1.234s→HOLD** (∈[1.0,1.5]; COM_OF_LOSS_T=1.0), dron ≤R_E (28.78), A1=0, zalogowane jako scenariusz **nie pad** | kontrolowana reakcja warstwy-0 |

**A1 (niezmiennik płaszczyzn):** we WSZYSTKICH scenariuszach `mavsdk_motion_cmds = 0` — MAVSDK tylko
param/arm/RTL/land; setpointy wyłącznie XRCE przez osłonę. Dowód: trace `gate_S{1..4}.jsonl`.
**A3 (defense-in-depth):** natywny GF uzbrojony NA ZEWNĄTRZ obwiedni; **0 odpaleń w S1–S3** (osłona
uprzedza); S4 jako jedyny — celowa reakcja warstwy natywnej (tu COM_OBL_RC_ACT=Hold, nie GF).

## Certy (§8)

| Cert | Werdykt | Metoda | Dowodzi |
|---|:---:|---|---|
| **P1** | **PROVED** | z3 1-indukcja (`r01/proofs/verify.py`) | ALLOW⇒¬geo∧¬term; geo⇒REFUSE(GEOFENCE); REFUSE⇒reason∈zbiór; terminal monotoniczny (latch) — base+inv_step+P1a..d wszystkie UNSAT |
| **P4** | **PASS** | gramatyka(5in/8out)+HMAC+property 2000 (`p4_verify.py`) | brak trybu bez admisji; tryb≡admitowany; poza gramatyką⇒COMMAND_INVALID; łańcuch weryfikowalny, sabotaż wykryty |
| **P5** | **PASS** | konformancja per-tick (`conformance.py`) | **tau ≡ shield.step 0 rozbieżności, pokrycie 6/6**; WIĄŻE P1 z KODEM egzekutora (dowód nie o fikcji) |

z3 5.0.0 (jak LiquidSight), certy JSON z `model_sha256` w `r01/proofs/certs/`.

## Higiena / stabilność
- **0 padów** we wszystkich 4 scenariuszach (CaptureCrash 0→0, oops 0). Sygnatura pada A5 (`dxg-22` koincydentne ze śmiercią) nie wystąpiła.
- Świeży boot + teardown per scenariusz; brak sierocych procesów po sesji.

## Rozbieżności (jawnie)
1. **Kamera Hz (A4) anomalnie niska pod obciążeniem** — avg ~1.4 Hz (S1) mimo config 640×480@15. Silne dławienie renderu kamery pod pełnym obciążeniem lot+MAVSDK+gate (CPU/GPU-bound). **A4 = metryka raportowana, NIE bramkująca** → nie wpływa na wynik bramki. Do zbadania (sesja 3: przyczyna dławienia / czy 15 Hz osiągalne bez lotu).
2. **ABORT jako 4. reason** osłony (operator) poza 3 z PRE §8 {GEOFENCE, COMMAND_INVALID, STALE_CMD} — dodane jawnie, uwzględnione w P1c/P5.
3. **Telemetria osłony przez MAVSDK** wymagała wymuszenia rate 30 Hz + pomiaru luki w fazie patrolu (pierwszy bieg S1: luka 1.078s w setupie); po poprawce 0.046s. Alternatywa (XRCE `/fmu/out/vehicle_local_position` 100 Hz) odnotowana jako opcja robustności.

## Pozostaje (sesja 3 wg §9)
- **P2-analog**: pomiar `a_brake` (profil hamowania PX4) → twierdzenie warunkowe geofence (bariera z3 NRA) z jawnymi założeniami; walidacja nierówności zawierania A2 zmierzonymi liczbami.
- **RAPORT_R01.md** — domknięcie fazy R0.1.

## Artefakty
- `results/R01/gate/gate_S{1..4}.jsonl` (trace per tick) + `S{1..4}_result.json` (metryki §7).
- `r01/proofs/certs/{P1,P4,P5}.json`. Kod: `r01/` (shield/language/authz/memory/config/exec_lib/gate_run/proofs).
- Skrypty: `run_scenario.sh`, `apply_camera_a4.sh`.
