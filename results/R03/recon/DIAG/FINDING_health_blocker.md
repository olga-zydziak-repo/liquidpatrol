# ZNALEZISKO (DIAG) — przyczyna HEALTH TIMEOUT: zatruty EKF2_GPS_CTRL=0 w rootfs, nie gz/timeout/MAVSDK

Data: 2026-08-11 (sesja PROMPT_R03A_DIAG). **NIE bieg bramkowy.** Zero S1/S3/S4. Jeden ręczny bring-up
(diagnostyka). HEAD wyjściowy `c5c0586`.

## Objaw
Po restarcie WSL2 gz **działa** (`/clock` po ~2 s). Mimo to boot dawał HEALTH TIMEOUT:
`is_global_position_ok=False` przez cały czas, `is_home_position_ok=True`.

## Przyczyna (PROWIENIENCJA — z dowodem)
**Zatruty parametr `EKF2_GPS_CTRL=0` utrwalony w `rootfs/parameters.bson`, obecny już przy ŚWIEŻYM
boocie.** GPS-denied od startu → EKF bez pozycji globalnej → `is_global_position_ok` nigdy True.

Dowody (etykieta przyrządu: MONO = time.monotonic od momentu zmiany):
- `results/R03/recon/DIAG/probe.log` (mirror egzekutora, bez limitu 45 s):
  `[probe] przed: EKF2_GPS_CTRL=0 EKF2_HGT_REF=0` → `is_global_position_ok -> False` →
  `[MONO 180.0s] health NIE OK po 180 s`. **Żaden timeout by tego nie uratował.**
- `results/R03/recon/DIAG/confirm.log` (test przyczynowości): ustaw `EKF2_GPS_CTRL=7` na żywej instancji →
  `[MONO 2.3s] is_global_position_ok -> True` → `HEALTH OK t_health=2.3s`. **Przyczyna potwierdzona.**
- Zdrowy default (cytat źródła): `PX4-Autopilot/src/modules/ekf2/params_gnss.yaml` → `EKF2_GPS_CTRL default:7`.
- Persystencja: `rootfs/parameters.bson` (SITL zapisuje param przy zmianie, PRZEŻYWA reboot). Po `set 7`
  bson skurczył się 850→831 B (override 0 usunięty, bo 7=default) — środowisko SAMO-uzdrowione.

## Mechanizm zatrucia (dlaczego trwałe i samo-utrwalające)
1. Bieg z denialiem ustawia `EKF2_GPS_CTRL=0` (osłona: `set_param(...,0)` @denial).
2. Proces ginie PRZED restore (teardown `pkill -9` w locie / `os._exit(2/3)` / crash) → 0 zapisane w bson.
3. Każdy kolejny boot startuje GPS-denied.
4. Egzekutor czytał `gps_old = get_param("EKF2_GPS_CTRL")` = zatrute 0 i „restore" robił do 0 →
   **samo-utrwalające, nie potrafiło się uzdrowić.** (identycznie S3 recovery „restore" do 0)

Zatrucie POPRZEDZA tę sesję (obecne przy 1. czystym boocie dziś). Dokładnego biegu-sprawcy nie da się
odtworzyć z artefaktów (kandydat: epizod B1-bis lub bieg z denialiem ubity przed restore); mechanizm
udowodniony niezależnie od sprawcy.

## Rozstrzygnięcie hipotez z promptu
- **H1 (timeout uprzęży 45 s) — WTÓRNE.** Przy zdrowym GPS `t_health=2.3 s ≪ 45 s`; 45 s NIE było za
  krótkie. Zatrutego bootu nie ratuje żadna wartość. (Uwaga: stary BEZTERMINOWY `async for` WIESZAŁ się
  w nieskończoność na zatrutym boocie — ograniczenie było słuszne, tylko maskowało prawdziwą przyczynę.)
- **H2 (MAVSDK się nie łączy) — OBALONE.** MAVSDK łączy się (`partner IP: 127.0.0.1` w px4.log; probe
  „MAVSDK connected"; health() streamuje). Łącze OK.
- **`No connection to GCS` — MYLNY TROP.** To preflight UZBROJENIA, nie telemetria `health()`. Health
  stał się OK (2.3 s) bez żadnej zależności od GCS. Blokerem był wyłącznie `is_global_position_ok`.

## Poprawki instrumentu (UPRZĄŻ — nie kryteria; ANEKS-4/D13/config r03/certy NIETKNIĘTE)
1. **Preflight sanitize (główna).** `r03/gate_run_r03.py`: przed health-wait wymuś
   `EKF2_GPS_CTRL = GPS_CTRL_NOMINAL(=7)` NIEZALEŻNIE od wartości z bootu. Każdy boot startuje
   GPS-zdrowo → uprząż SAMO-uzdrawia się mimo zatrutego bson. Uzasadnienie 7: cytat params_gnss.yaml.
2. **Restore/recovery do NOMINAŁU, nie do odczytu.** Linie restore (koniec) i S3 recovery ustawiają
   `GPS_CTRL_NOMINAL`, nie `gps_old`. Znika samo-utrwalanie. `gps_boot` czytany tylko do logu (wykrywa
   zatrucie: `PREFLIGHT: EKF2_GPS_CTRL boot=0 → wymuszono 7`).
3. **Restore na ścieżkach twardego wyjścia.** `os._exit(2/3)` też zostawiają `GPS_CTRL=7`.
4. **Timeout health-wait.** Ograniczony ZOSTAJE (bez powrotu do zawieszenia). Wartość `45 s` uzasadniona
   liczbą: zmierzone `t_health=2.3 s` + ~19× margines (pokrywa reset HGT_REF 1→0). Stała nazwana
   `HEALTH_WAIT_TIMEOUT_S`.
5. **Luka logowania (wrapper).** `r03/run_gate_one.sh`: przy odrzucie bootu dopisuje do `run.log`
   przyczynę (tail preflight/health/GPS z px4.log + tail egzekutora) — widoczna bez grzebania.
   `run_stack.sh`: `LOGDIR` konwertowany na ABSOLUTNY (relatywny gubił px4.log po `cd rootfs`).
6. **Zombie-check rozszerzony.** Łapie osierocony egzekutor `r03.gate_run_r03`/sondy i trzymaczy portów
   UDP (14540 MAVSDK / 8888 agent / 50051 mavsdk_server) przez `ss -lunp` — wzorzec gz/px4 ich nie łapił.

## Wpływ na SR-C4 (rekonsyliacja, uczciwie)
gz DZIAŁA po restarcie WSL2 (`/clock` 2 s) — awaria gz z 2026-08-10 była środowiskowa i minęła.
Ale bloker health, który ZAINICJOWAŁ serię odrzutów S4, to zatruty GPS (px4.log S4/boot1 z 08-10
pokazuje ZDROWY sim: `tone_alarm home set`, `partner IP` — to nie „0 /clock"). SR-C4 spięło dwie różne
awarie; ta nota to rozdziela. Po tej naprawie i restarcie środowiska bramka jest odblokowana.

## Weryfikacja przed powrotem do biegów
- `python3 -m py_compile r03/gate_run_r03.py` OK; `bash -n` obu wrapperów OK.
- Środowisko zostawione czyste (brak zombie, porty 14540/8888/50051 wolne), bson uzdrowione (GPS_CTRL=7).
- **Push = Olga.** Po ratyfikacji: `bash r03/run_gate_one.sh S4` → `S1 5` → `S3` → `gate_judge`.
