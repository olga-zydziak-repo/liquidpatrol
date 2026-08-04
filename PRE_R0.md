# PRE_R0 — dokument przed budową R0.0

Data: 2026-08-04. Poprzednik: `RECON_R0.md` (etap R, kompletny).
Elementy **[PROPOZYCJA]** wymagają Twojej ratyfikacji. Do etapu B nie wchodzę, dopóki nie dopiszesz ręką **RATYFIKOWANE**.

---

## §1 — Cel R0.0 (jedno zdanie)

Stabilnie działający stack **PX4 SITL + Gazebo + ROS2** na tej maszynie, potwierdzony jednym testem **hello-mission** (dron: uzbrojenie → start → prosta trasa kilku waypointów → lądowanie) — **bez naszego kodu, bez sieci, bez portu**. To test infrastruktury, nie systemu.

---

## §2 — [PROPOZYCJA] Wybrany stos

**Rekomendacja główna (ścieżka WSL2 + GPU):**

| Warstwa | Wybór | Uzasadnienie (z RECON) |
|---|---|---|
| OS | Ubuntu 24.04.4 (jest) | — |
| ROS 2 | **Jazzy Jalisco** (desktop) | dystrybucja LTS dla 24.04 |
| Gazebo | **Harmonic** (`gz-sim`, LTS) | para z Jazzy przez `ros_gz`; testowany z PX4. *Nie Ionic, nie Classic* |
| Autopilot | **PX4 v1.16** — najnowszy stabilny tag; jeśli 1.16 wciąż alpha/RC → `main` przypięty do znanego-dobrego commita (ryzyko odnotowane) | `ubuntu.sh` wspiera 24.04 dopiero od 1.16 |
| Most PX4↔ROS2 | **uXRCE-DDS** (`MicroXRCEAgent`) | standard PX4-ROS2 |
| Most Gazebo↔ROS2 | **`ros_gz_bridge`** | tematy sensorów/kamery (później) |
| Render | **D3D12 GPU** przez wrapper: `GALLIUM_DRIVER=d3d12`, `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA` | zmierzone: daje `D3D12 (RTX 5070 Ti)`, OpenGL 4.6. **Domyślny renderer to llvmpipe — GPU trzeba wymusić** |
| Airframe | **`gz_x500`** (bazowy quad) | hello-mission; `gz_x500_mono_cam` istnieje na później (kamera) |
| Świat | domyślny (uruchamiać `gz_x500`, nie `..._default`) | lekki |
| Sterowanie z Pythona | **MAVSDK-Python** | najprostszy dowód telemetrii offboard; baza R0.1 |

**Fallback (kolejność eskalacji, jeśli ścieżka główna zawiedzie — patrz §4):**
1. **Gazebo software/headless** — `LIBGL_ALWAYS_SOFTWARE=1` (llvmpipe zmierzony: 2635 FPS na trywialnej scenie) lub `gz sim -s` (sam serwer fizyki, bez okna). Wciąż ważny wynik R0.0.
2. **Docker** `px4io/px4-dev-simulation` — izoluje toolchain.
3. **Natywny dual-boot Ubuntu 24.04** — najcięższy, eliminuje warstwę WSL2/dxg.
4. Chmura z GPU — ostateczność.

---

## §3 — [PROPOZYCJA] Kryterium sukcesu R0.0 (bramka, zamrożona przed budową)

„Stack stoi" = **wszystkie cztery** warunki spełnione i udokumentowane w `RAPORT_R0.md`:

1. **hello-mission przechodzi 3× z rzędu** bez pada GPU (exit-144). Każdy przebieg = uzbrojenie → start → przelot ≥3 waypointów → lądowanie, bez crasha PX4/Gazebo.
2. **Render z akceleracją GPU** — dowód, że to NIE llvmpipe: renderer w logu/`glxinfo` pod tym samym środowiskiem = `D3D12 (NVIDIA … RTX 5070 Ti)`, oraz zapisany real-time factor (RTF) Gazebo z GUI. *Jeśli D3D12 okaże się niestabilny pod Gazebo (§4), zejście na software/headless jest dozwolonym, JAWNIE oznaczonym wynikiem — bramka wtedy zaliczona w trybie „software", nie „GPU".*
3. **Telemetria offboard z Pythona dociera** — skrypt MAVSDK-Python łączy się i drukuje pozycję/heartbeat drona w trakcie misji.
4. **Powtarzalność** — instalacja i uruchomienie ujęte w skryptach w repo (`install_*.sh`, `run_hello_mission.sh`), tak by przebieg dało się odtworzyć.

Metryki zapisywane (nie bramkujące, ale w raporcie): RTF, FPS/obciążenie GPU (`nvidia-smi`), zużycie RAM podczas budowy i runtime, exit-code'y.

---

## §4 — Ryzyka i reguła stopu

**Ryzyko główne:** exit-144 / `dxg ioctl -22` — pad sterownika GPU w WSL2 pod obciążeniem seriami (znane z poprzednich faz). Mikro-próba (glxgears 12 s) przeszła czysto, ale realny stress to Gazebo.

**Reguła stopu (twarda, nie improwizowana):**
- **[PROPOZYCJA] Limit prób na ścieżkę główną (WSL2+D3D12):** jeśli po **~2 sesjach lub ~4 h prób** GUI-Gazebo z D3D12 nie stoi stabilnie (powtarzalny exit-144 / crash render), **STOP → zejście na fallback §2 pkt 1 (software/headless)** i zaliczenie bramki w trybie „software", z jawną notą.
- Jeśli **nawet software/headless** nie utrzyma hello-mission → STOP i **ESKALACJA do Ciebie** z opcjami (Docker / dual-boot / chmura), nie walka na ślepo.
- Każdy pad GPU w trakcie budowy = STOP z krótką notą + opcje, commit ostatniego działającego kroku.

**Blokada operacyjna do usunięcia przed B:** działające `sudo` (etap B = dziesiątki `apt install`). **[PROPOZYCJA]:** ustawić hasło konta przez `wsl -u root passwd olga` na starcie B. (Bezhasłowe sudo/NOPASSWD tylko na Twoją wyraźną zgodę — osłabia bezpieczeństwo.)

**Ograniczenie sprzętowe odnotowane:** RAM 15 GiB → budowa PX4 z ograniczoną równoległością (`-j6…8`), by nie OOM-ować.

---

## §5 — Co przeniesie się później (tylko odnotowanie — NIE robimy teraz)

Z `liquidsight` w osobnych, przyszłych fazach przyjdą: **automat osłony ALLOW/HOLD/REFUSE + certyfikaty logiczne (Z3)**, **gramatyka + parser + admisja komend**, **semantyka kanału celu z jawnym wiekiem obserwacji**, **metodologia PRE / zamrożonych bramek**. Slot **pilota/estymatora pozostaje PUSTY** do osobnej fazy. To zdanie jest tu wyłącznie po to, by R0.0 był budowany pod przyszły port — sam portu nie wykonuje.

---

## §6 — Artefakty

- `RECON_R0.md` ✅ (jest)
- `PRE_R0.md` ✅ (ten dokument)
- po budowie: `RAPORT_R0.md` — co postawione, wyniki hello-mission (3×), stabilność, RTF/GPU/RAM, rozbieżności
- skrypty w repo: `install_ros2_jazzy.sh`, `install_px4_gazebo.sh`, `env_gpu.sh` (wrapper D3D12), `run_hello_mission.sh`, `mavsdk_telemetry_check.py`

---

## §7 — [PROPOZYCJA] Budżet

**2 sesje** na R0.0:
- Sesja 1: instalacja stacku (ROS2 Jazzy + Gazebo Harmonic + build PX4 + MAVSDK + uXRCE-DDS agent), pierwsze uruchomienie Gazebo z D3D12, weryfikacja renderera.
- Sesja 2: hello-mission 3×, telemetria MAVSDK, RAPORT_R0. Bufor na tarcia PX4-na-24.04 (#24159/#25089) i ewentualne zejście na fallback.

Jeśli ścieżka główna okaże się gładka — możliwe domknięcie w 1 sesji.

---

## STOP

Po zapisaniu tego PRE: commit + push, **STOP**. Czekam na Twoją ratyfikację (**RATYFIKOWANE** ręką w tym pliku lub w czacie) zanim wejdę w etap B. Elementy do decyzji: **§2** (stos + fallback), **§3** (bramka), **§4** (limit prób + naprawa sudo), **§7** (budżet).
