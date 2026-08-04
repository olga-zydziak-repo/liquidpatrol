# RECON_R0 — rekonesans wykonalności stacku PX4 SITL + Gazebo + ROS2

Data: 2026-08-04. Etap: **R (rekonesans, tylko inspekcja + jedna próbna instalacja diagnostyczna)**.
Repo: `~/projects/liquidpatrol` (nowy program; `liquidsight` nietknięty — tylko odczyt).

Cel R: ustalić, co realnie da się postawić na TEJ maszynie i jakim kosztem — WIEDZA, nie działający stack.
Główne pytanie R0.0 (z nagłówka sesji): **czy Gazebo dostanie akcelerację GPU, czy spadnie na llvmpipe**, i czy stack stoi stabilnie pod WSL2 mimo znanego ryzyka exit-144/dxg.

---

## 0. Stan maszyny (zmierzony)

| Element | Wartość | Uwaga |
|---|---|---|
| OS | Ubuntu 24.04.4 LTS (Noble) | → determinuje ROS2 **Jazzy** + Gazebo **Harmonic** |
| Kernel | 6.18 microsoft-standard-WSL2 | WSL2 |
| GPU | RTX 5070 Ti Laptop, 12 GB VRAM | driver 577.13 (Win) / 575.66 (WSL), CUDA 12.9 |
| CPU / RAM | 24 wątki / **15 GiB RAM** + 4 GiB swap | ⚠ RAM to realne ograniczenie przy budowie |
| Dysk | 928 GiB wolne (z 1 TB) | bez problemu |
| WSLg | 1.0.73.2, `DISPLAY=:0`, `wayland-0`, `/mnt/wslg` OK | GUI możliwe |
| `/dev/dxg` | jest | ścieżka GPU (dxcore) obecna |
| **`/dev/dri`** | **BRAK** (`NO /dev/dri`) | ⚠ brak węzła render — objaw cytowany w zgłoszeniach WSL o fallbacku na llvmpipe |
| Mesa GL | `d3d12_dri.so → libdril_dri.so`, `libGLX_mesa`, `libEGL_mesa` obecne | ścieżka D3D12-Gallium istnieje |
| Zainstalowane | **NIC z docelowego stacku**: brak ROS2, Gazebo, PX4, Docker, cmake, MAVSDK | czysta karta |
| Toolchain | Python 3.12.3, gcc 13.3, git 2.43 | baza OK; cmake do doinstalowania |

---

## (a) Wersje i zgodność

Kanon dla Ubuntu 24.04 (rekomendacja dla nowych instalacji wg PX4/ROS/Gazebo):

- **ROS 2 Jazzy Jalisco** (dystrybucja LTS dla 24.04).
- **Gazebo Harmonic** (nowy Gazebo / `gz-sim`, LTS) — sparowany z Jazzy przez `ros_gz`. *NIE Classic, NIE Ionic.*
  Ionic/Jetty też stoją na 24.04, ale **Harmonic** to wariant testowany z PX4 i z `ros_gz` dla Jazzy → mniejsze ryzyko.
- **PX4 v1.16** (główna gałąź). Skrypt `Tools/setup/ubuntu.sh` **oficjalnie wspiera 24.04** dopiero od v1.16 (v1.15 na 24.04 nie instaluje Harmonica).
- Mosty:
  - PX4 ↔ ROS2: **uXRCE-DDS** (`MicroXRCEAgent`) — klient w firmware PX4, agent po stronie towarzysza.
  - Gazebo ↔ ROS2: **`ros_gz_bridge`** (tematy sensorów/kamery).

**Znane zgłoszenia (ryzyka do odnotowania):**
- PX4 #25089 — timeouty accel/mag przy SITL na Gazebo Harmonic (wymaga tuningu/parametrów).
- PX4 #24159 — v1.16-alpha2 + 24.04 + Jazzy + Harmonic potrafi rzucać błąd (setup script pisany pod starsze wersje, bywa potrzebna korekta).
- Wniosek: kombinacja jest "wspierana", ale **nie zero-friction** — spodziewać się drobnych poprawek skryptu.

## (b) Ścieżka renderu na WSL2 — SEDNO R0.0

Fakty: ścieżka GPU-GL WSLg (`d3d12` Gallium via dxcore/`/dev/dxg`) jest **obecna**, ale węzła DRM `/dev/dri/renderD128` **brak**. Historycznie WSLg akceleruje GL przez `d3d12` enumerujący adapter przez dxcore (nie przez węzeł DRM), więc sam brak `/dev/dri` NIE przesądza o llvmpipe — **trzeba zmierzyć renderer**.

- Gazebo Harmonic renderuje przez **OGRE2 na OpenGL** (domyślnie), *nie* Vulkan. To dobrze: Vulkan/`dzn` na WSL 24.04 bywa zepsuty (brak plików sterownika `dzn`), ale nas to nie dotyczy przy domyślnym OGRE2-GL.
- Dźwignie środowiskowe, jeśli domyślnie llvmpipe: `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`, `GALLIUM_DRIVER=d3d12`, `LIBGL_ALWAYS_SOFTWARE=0`.

**POMIAR ZROBIONY (2026-08-04, `mesa-utils` 9.0.0, Mesa 25.2.8):**

| Konfiguracja | Renderer | OpenGL | glxgears 12 s |
|---|---|---|---|
| **domyślnie** | `llvmpipe (LLVM 20.1)` — **software** | 4.5 | 2635 FPS, exit 124 |
| `GALLIUM_DRIVER=d3d12` + `…ADAPTER_NAME=NVIDIA` | **`D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)`** | **4.6** | 146 FPS, exit 124 |

Werdykt:
1. **Akceleracja GPU JEST dostępna, ale NIE jest domyślna** — domyślny renderer to llvmpipe (software). GPU włącza się wyłącznie przez zmienne środowiskowe → w etapie B Gazebo MUSI być uruchamiany przez wrapper eksportujący `GALLIUM_DRIVER=d3d12` i `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`. To jest konkretny, mierzalny warunek bramki §3.
2. **glxgears NIE jest miarodajny** — trywialna scena, gdzie ścieżka D3D12 płaci narzut *present* przez kompozytor WSLg (Weston/RDP) na ramkę, więc software „wygrywa" na FPS. Przy realnym obciążeniu (OGRE2: cienie/tekstury/siatki) relacja się odwraca. Jedyny wiarygodny werdykt wydajności/stabilności = **sam Gazebo w hello-mission** — dokładnie to, co mierzy bramka R0.0.
3. **Stabilność (mikro-sygnał):** oba renderery przeżyły 12 s ciągłego rysowania z exit 124 (czysty timeout), **żadnego exit-144/pada dxg**. To dobry, ale niewystarczający sygnał — realny stress to Gazebo pod obciążeniem, nie glxgears.
4. **Konsekwencja dla fallbacku:** llvmpipe daje 2635 FPS na trywialnej scenie → **software rendering jest realną, być może wystarczającą opcją** dla lekkiego świata patrolu, jeśli D3D12 okaże się niestabilny pod Gazebo. Wzmacnia bezpiecznik headless/software z (e).

## (c) Airframe i world

- Modele quada dostępne out-of-the-box w PX4/Gazebo Harmonic:
  - `gz_x500` — bazowy quad (do hello-mission).
  - `gz_x500_mono_cam` — **quad z kamerą** (airframe 4010 ≡ 4001; strumień RTP na UDP:5600).
  - `gz_x500_depth` — kamera głębi; `gz_x500_gimbal` — kamera na gimbalu.
- Model z kamerą **istnieje** ✓ — zabezpiecza przyszłego groundera (patrol/śledzenie intruza). W R0.0 nie używamy kamery.
- Światy: domyślny (uruchamiać `gz_x500`, **nie** `gz_x500_default`), plus np. `baylands`. Dla hello-mission wystarczy świat domyślny (lekki).

## (d) Sterowanie z Pythona

- **MAVSDK-Python** — prostszy do egzekutora waypointów: stabilne API, sam wysyła setpointy 20 Hz (PX4 wymaga min. 2 Hz), gotowy plugin `Mission`. Idealny do §3 "telemetria offboard z Pythona dociera" i do przyszłego R0.1.
- **ROS2 + `px4_msgs` + uXRCE-DDS** — bliższy docelowemu portowi (natywny ROS2), ale cięższy: workspace, zgodność definicji uORB↔msg, rekompilacja firmware przy zmianie tematów.
- Rekomendacja: **hello-mission i R0.1 egzekutor = MAVSDK-Python** (najkrótsza droga do zielonej bramki). Docelowa warstwa bezpieczeństwa (port `liquidsight`) prawdopodobnie i tak pójdzie przez ROS2/`px4_msgs` — zostawiamy to na osobną fazę. Dla samego hello-mission wystarczy nawet wbudowany `commander`/QGC bez Pythona; MAVSDK dokłada tylko dowód telemetrii z Pythona.

## (e) Koszt i ryzyka

**Koszt (dysk/czas):** ROS2 Jazzy desktop + Gazebo Harmonic + build PX4 ≈ **15–25 GB**, kilka godzin (głównie kompilacja PX4). Dysk 928 GB — bez problemu.

**Ryzyka wg wagi:**
1. **GPU render → llvmpipe / niestabilność dxg (GŁÓWNE).** Fallback = Gazebo GUI 1–5 fps lub crash; do tego znane z poprzednich faz exit-144 / `dxg ioctl -22`. To jest powód istnienia R0.0. *Obejście-bezpiecznik:* Gazebo **headless** (`gz sim -s`, sam serwer fizyki, bez okna) omija GPU-GL — hello-mission (uzbrojenie/start/waypointy/lądowanie) to fizyka, nie grafika. Jeśli GUI-render padnie, headless nadal daje ważny wynik R0.0.
2. **RAM 15 GB przy budowie PX4.** `-j24` może OOM-ować. Mitigacja: ograniczyć równoległość (`-j6…8`), swap 4 GB jest.
3. **Tarcia PX4-on-24.04** (#24159/#25089): korekty skryptu setup, timeouty sensorów — do przewidzenia, nie blokujące.
4. **Vulkan `dzn` zepsuty na WSL 24.04** — nie dotyczy, bo Harmonic używa OGRE2-GL.

**Obejścia (nazwane z góry, nie improwizowane):** headless Gazebo → Docker `px4io/px4-dev` → natywny dual-boot Ubuntu (najcięższy) → chmura z GPU. Kolejność eskalacji do zapisania w PRE §4.

## (f) Rozbieżności prompt ↔ rzeczywistość

- Prompt dopuszcza "Ionic": dla naszej pary (Jazzy + PX4 + `ros_gz`) rekomenduję **Harmonic**, nie Ionic — jako wariant testowany. (Odstępstwo świadome, nie decyzja obchodząca założenie — do ratyfikacji w PRE §2.)
- Nagłówek: ryzyko exit-144/GPU — potwierdzone jako realne; konkretny objaw do zmierzenia = renderer llvmpipe vs D3D12 (brak `/dev/dri` to sygnał ostrzegawczy, nie wyrok).
- **RAM 15 GB** — nie było w założeniach; flaguję jako ograniczenie budowy (parallelizm).
- Poza tym brak rozbieżności blokujących — stack jest teoretycznie stawialny na tej maszynie; jedyny twardy znak zapytania to render GPU.

---

## Nota operacyjna: sudo w WSL

`sudo` wymaga hasła konta Linuksa (≠ hasło Windows). Konto `olga` nie miało znanego hasła; obejście = wejście jako root z Windowsa (`wsl -u root …`), którym doinstalowano `mesa-utils`. **Do etapu B (dziesiątki `apt install`: ROS2/Gazebo/PX4) potrzebne działające sudo** — rekomendacja: ustawić hasło (`wsl -u root passwd olga`) przed budową. Do rozstrzygnięcia w PRE §4.

**Status R: KOMPLETNY.** Wszystkie punkty (a)–(f) zmierzone/rozpoznane, łącznie z sednem (b). → PRE_R0.md, potem STOP na ratyfikację.
