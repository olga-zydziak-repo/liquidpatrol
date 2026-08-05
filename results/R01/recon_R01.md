# RECON R0.1 — pomiary i mapa (ETAP R) — 2026-08-05

Faza R0.1: egzekutor offboard lata patrol perymetru pod osłoną runtime ALLOW/HOLD/REFUSE(reason), księgowość trójwynikowa. Slot uczonego pilota pusty (R0.2). Recon = tylko odczyt + pomiary nieinwazyjne. Higiena: cały recon **0 padów** (CaptureCrash=0), kille teardownu benign.

Stack pomiarowy: PX4 SITL v1.16.2 + gz Harmonic 8.14.0 (D3D12) + uXRCE-DDS Agent v2.4.3 + ros_gz_bridge, ROS2 Jazzy, WSL2/RTX 5070 Ti.

---

## R0 — mapa portu (LiquidSight → LiquidPatrol)

Źródło: `~/projects/liquidsight` (Python + z3-solver==5.0.0.0, rdzeń bez zależności numerycznych). **Portujemy STRUKTURĘ/LOGIKĘ, nie liczby**, uczony pilot pominięty.

| Element | Plik źródłowy | Port | Uwaga |
|---|---|:---:|---|
| Automat osłony `Shield` (ALLOW/HOLD/REFUSE, states, `step()`/`_decide()`, priorytet reguł) | `s3c1/shield.py` | STRUKTURA | reasons i progi = nowe dla PX4 |
| `outcome()` trójwynik SUKCES/ODMOWA/PORAZKA + asercja rozłączności `(ODMOWA)⇔terminal-REFUSE` | `s3c1/shield.py:139` | STRUKTURA | sedno „odmowa≠porażka" |
| Gramatyka zamknięta + parser deterministyczny | `demo_proof/language.py` | STRUKTURA | leksykon = nowy (komendy patrolu) |
| Admisja + HMAC-SHA256 + łańcuch PCDL | `demo_proof/authz.py` | STRUKTURA | DEMO_KEY→realny klucz |
| Pamięć korekt (aliasy przed-parserem, podpisane) | `demo_proof/memory.py` | STRUKTURA | — |
| Integracja harness↔osłona (HOLD podmienia setpoint, REFUSE przerywa nogę) | `mission_runner.py:146` | WZORZEC | wprost na węzeł osłony PX4 |
| P1 (własności automatu, z3 1-indukcja) | `proofs/verify.py` | KSZTAŁT | re-weryfikacja na nowym automacie |
| P2 (geofence, bariera+próg, z3 NRA) | `proofs/geofence.py` | KSZTAŁT | przepisać na dynamikę PX4 |
| P4 (gramatyka/HMAC, property-based) | `proofs/p4_verify.py` | KSZTAŁT | nowy zestaw komend |
| P5 (konformancja kod↔model, z3 concrete-eval) | `proofs/conformance.py` | KSZTAŁT | **obowiązkowo od nowa** |
| P3 (robustność liquid, IBP) | `proofs/net_ibp.py` | **NIE PORT** | uczony pilot — R0.2 |

Rozbieżność do świadomego rozstrzygnięcia przy porcie: `geo_lim` zaszyty **dwukrotnie** (Shield + authz) — scentralizować w jednym configu, by admisja i osłona się nie rozjechały.

---

## R1 — płaszczyzna sterowania (ZMIERZONE)

Punkt wpięcia osłony = węzeł między planerem patrolu a publikacją setpointów. Dla XRCE: `/fmu/in/trajectory_setpoint` + `/fmu/in/offboard_control_mode`. Dla MAVSDK: MAVLink `SET_POSITION_TARGET_LOCAL_NED` → mavlink_receiver → te same uORB.

**Mechanika (z kodu, PX4 v1.16.2):**
- Recency offboard liczona od `offboard_control_mode.timestamp` vs `COM_OF_LOSS_T` (default **1.0 s**) — `offboardCheck.cpp:44`. Trzeba streamować OBA topici z okresem < COM_OF_LOSS_T.
- Failsafe po utracie: `COM_OBL_RC_ACT` (default **0=Position**; 0-7=Position/Altitude/Stabilized/Return/Land/Hold/Terminate/Disarm) — `commander_params.c:351`, `failsafe.cpp:280`.
- XRCE wchodzi wprost do uORB (agent DDS); MAVLink dokłada warstwę mavlink_receiver (translacja type_mask→ocm). XRCE = mniej warstw / niższa latencja.

**Pomiary (probe `xrce_offboard_probe.py`, XRCE @ 50 Hz, 4 biegi):**
| Metryka | Wynik |
|---|---|
| Jitter pętli setpointów @50Hz | mean **20.7 ms**, std **0.21 ms**, p95 21.1, max 23.2, min 20.4 (n≈377) — sub-ms jitter, 50 Hz trywialnie utrzymywalne |
| Latencja aktywacji trybu offboard (cmd→`flag_control_offboard_enabled`) | **42–125 ms** |
| Detekcja utraty strumienia (`offboard_control_signal_lost`) | **1.03–1.08 s** po odcięciu = dokładnie `COM_OF_LOSS_T` (1.0 s), spójne 3× |
| nav_state w offboard | 14 (OFFBOARD) potwierdzony |

**KLUCZOWE znalezisko:** arm czysto-XRCE/ROS2 pojazdu **ODRZUCONY** — `Preflight Fail: No connection to the ground control station` (`commander`: „Arming denied: Resolve system health failures first"). PX4 wymaga heartbeatu GCS (MAVLink) do uzbrojenia; MAVSDK w R0.0 dostarczał go → arm działał. **Konsekwencja dla decyzji:** setpointy najlepiej XRCE (zmierzony świetny jitter, mniej warstw), ale **arming/zarządzanie trybem wymaga źródła heartbeatu MAVLink (MAVSDK) LUB poluzowania arming-checka** (`COM_ARM_WO_GCS`/pokrewny). Walidacja akcji failsafe **w locie** odłożona do BUILD (blokował tylko arming, teraz zdiagnozowany).

**Rekomendacja (do PRE):** hybryda — **XRCE dla wysokoczęstego strumienia setpointów pod osłoną** + **MAVSDK (heartbeat) dla arm/mode/RTL**; osłona wpięta w strumień XRCE. Alternatywa: pełny MAVSDK offboard (prościej, jedna warstwa uwierzytelniania, wyższa latencja ingress). Decyzja pomiarowo uzasadniona w PRE §płaszczyzna.

---

## R2 — natywny geofence PX4 (z kodu) — ostatnia warstwa POD osłoną

- Parametry `GF_*` (`geofence_params.c`): `GF_ACTION` (default **2=Hold**; 0-5=None/Warning/Hold/Return/Terminate/Land), `GF_MAX_HOR_DIST`/`GF_MAX_VER_DIST` (default **0=wyłączone** — trzeba jawnie ustawić!), `GF_SOURCE` (0=GPOS), `GF_PREDICT` (0, eksperymentalny). **`GF_COUNT` NIE istnieje** w v1.16.2.
- `geofence_breach_check()` biegnie **bezwarunkowo** w navigatorze PRZED `switch(nav_state)` (`navigator_main.cpp:762,913`) → niezależnie od trybu, w tym offboard. Commander egzekwuje przez `failsafe.cpp:548` z `cannotBeDeferred()` → natychmiast.
- **Defense-in-depth potwierdzone:** geofence jest niezależną warstwą względem failsafe utraty strumienia. Dla R0.1: ustawić `GF_MAX_HOR_DIST`/`GF_MAX_VER_DIST` na obwiednię perymetru + margines, `GF_ACTION`=Hold/Return — natywna siatka bezpieczeństwa PONIŻEJ naszej osłony (której geofence-logika = port P2-analog).

---

## R3 — dryf kamery (ZMIERZONE) — saturacja, nie wyciek

- Konfiguracja: 1280×960 @ **30 Hz** sensor, `always_on=1`, `visualize=true` (`mono_cam/model.sdf`).
- Pomiar 60 s: avg **13.2 Hz**, **min/s = 4 Hz** (wariancja 4–16 Hz/s). Wcześniejsze „15.8→11.8" = dwie krótkie próbki w tym paśmie, **nie monotoniczny dryf**.
- Przyczyna: render kamery 1280×960@30 pod D3D12 **rywalizuje z GUI o GPU** i nie nadąża za 30 Hz → dostarcza ~13 Hz z dużym jitterem.
- **Stabilny strumień (do [PROPOZYCJA]):** obniżyć koszt renderu tak, by cel był utrzymywalny: (a) niższa rozdzielczość (np. 640×480 ≈ 4× taniej), (b) `update_rate`→utrzymywalny (np. 10–15 Hz), (c) `visualize=false`. W R0.1 kamera = obciążenie w tle → wybrać stałą, powtarzalną konfigurację z kryterium dwustronnym (np. min/s ≥ 0.8×cel).

---

## R4 — świat patrolu (przegląd)

- Światy PX4/gz: `default` (ground+sun, najtańszy), `walls` (100×100 + wysokie bloki = przeszkody, nie czysty perymetr), `forest` (12K, ciężki — dużo drzew). Reszta = stuby 4K.
- Perymetr patrolu = **pętla waypointów + obwiednia geofence**; scena wizualna wtórna. **Najtaniej:** `default` + opcjonalne lekkie znaczniki perymetru (słupki/boxy) LUB własny minimalny świat z prostokątnym płotem. Koszt renderu zdominowany przez kamerę (R3), nie geometrię sceny.

---

## R5 — zasoby pełnego stacka (ZMIERZONE) — komfort przy 15 GB

Pełny stack (gz_x500_mono_cam + serwer + GUI D3D12 + kamera + agent + węzeł Python):
| Proces | Peak RSS | CPU |
|---|---:|---:|
| gz serwer (ruby, fizyka+render kamery) | ~833 MB | ~144 % |
| gz GUI (ruby) | ~676 MB | ~76 % |
| px4 | ~21 MB | ~13 % |
| MicroXRCEAgent | ~25 MB | ~2 % |
| węzeł Python (probe≈osłona) | ~82 MB | ~1 % |

- System pod pełnym obciążeniem: **min. 13.5 GB wolne** z 15.7 GB, ~2.5 rdzenia zajęte z 24.
- Dominuje render kamery (gz serwer). **Węzeł osłony (Python, ~80–150 MB) pomijalny.** Margines do 15 GB duży — osłona + planer + admisja zmieszczą się z zapasem.

---

## Rozbieżności względem promptu (jawnie)
1. `COM_OBL_ACT` (prompt) **nie istnieje** w v1.16.2 — jest tylko `COM_OBL_RC_ACT` (default 0=Position).
2. `GF_COUNT` (prompt) **nie istnieje** w v1.16.2 — 5 parametrów GF_ (ACTION/SOURCE/MAX_HOR/MAX_VER/PREDICT).
3. Dryf kamery „15.8→11.8" przeformułowany: to **wariancja saturacji** (avg ~13 Hz, min/s 4), nie monotoniczny dryf.
4. Nowe znalezisko (poza promptem): arm czysto-XRCE blokowany brakiem heartbeatu GCS — wpływa na wybór płaszczyzny sterowania.

## Artefakty
- `results/R01/xrce_offboard_probe.py` — probe pomiarowy R1.
- `results/R01/r1_xrce_probe.json` — surowe wyniki R1.
- `results/R01/r5_resources.log` — próbki RSS/CPU/free R5.
