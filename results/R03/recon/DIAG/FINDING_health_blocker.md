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

## RIDERY R-D1..R-D4 (ratyfikacja 2026-08-11, commit osobny)

**R-D1 — sanitize uogólniony z paramu na KLASĘ.** Biała lista wszystkich parametrów, które uprząż
KIEDYKOLWIEK zapisuje, w JEDNYM źródle prawdy: `r03/config.HARNESS_PARAM_NOMINAL`. Przegląd kodu
(2026-08-11): `gate_run_r03.py` + `results/R03/recon/B1bis/b1bis_fly.py` zapisują wyłącznie
`EKF2_GPS_CTRL` i `EKF2_HGT_REF`. **`SYS_FAILURE_EN` — sprawdzone, NIE zapisywany; nic innego.**
`r03/config.HARNESS_PARAM_PREFLIGHT` = wymagany STAN PREFLIGHT dla WAŻNEGO biegu (nie „czysty default"):
`EKF2_GPS_CTRL=7` (zdrowy GPS; default PX4=7 params_gnss.yaml) i `EKF2_HGT_REF=0` (Baro habitat §3quater;
default PX4=1 module.yaml:103 — habitat nadpisuje; S2-passing też ustawiał 0 JEDNYM setem przed health-wait).
**ZASADA: assert-on-entry, NIE restore-on-exit.** Restore z definicji ZAWODZI przy `pkill -9`, `os._exit`
i crashu — dlatego naprawa jednego paramu nie zamyka KLASY błędu. Preflight egzekutora asertuje CAŁĄ listę
do stanu preflight JEDNYM setem na param (bez churn/podwójnego resetu EKF — pierwsza wersja R-D1 asertowała
HGT_REF=1 a potem 0, co dawało dwa resety i blokowało arm „Resolve system health failures"; poprawione).
Denial ustawia GPS_CTRL=0 dopiero w LOCIE. Restore-on-exit zostaje tylko jako sprzątanie best-effort —
twardą gwarancją czystego wejścia jest asercja NASTĘPNEGO biegu.

**R-D2 — zatrucie jest SAMO-WYKRYWALNE ⇒ dane nieskażone.** Zatruty GPS blokuje uzbrojenie (health/arm
nie przechodzi), a wrapper liczy bieg DOPIERO po udanym uzbrojeniu (event `armed`). Zatem żaden bieg z
zatrutego bootu nigdy nie został policzony. **Wniosek: S2 LIVE PASS oraz dane B1-bis/cap (ε_cap=37/4) są
NIESKAŻONE** — pochodzą wyłącznie z bootów, które się uzbroiły, czyli miały zdrowy GPS. Zatrucie nie mogło
„po cichu" wejść do żadnego zaliczonego pomiaru; jest głośną awarią bring-upu, nie cichym biasem.

**R-D3 — twarda asercja w trace.** Param POISON-CRITICAL na wejściu ≠ stan preflight ⇒ egzekutor emituje
event `harness_invalid` (z powodem) i `meta.harness_valid=false`. Wrapper NIE liczy takiego biegu, choćby
się uzbroił (self-heal naprawia stan na przyszłość, ale runu z brudnego wejścia nie ufamy) → retry na czysty
boot. **POISON-CRITICAL = tylko `EKF2_GPS_CTRL`** (`config.HARNESS_PARAM_POISON_CRITICAL`): ≠7 na boocie =
GPS-denied od startu (dangerous). `EKF2_HGT_REF=0` to wartość habitatu, którą USTAWIAMY SAMI — łagodna,
oczekiwana (wycieka przy każdym ubitym biegu), więc NIE unieważnia (inaczej marnowałaby budżet 3 bootów).
Zatrucie GPS nie może się prześlizgnąć jako ważny wynik.

**R-D4 — lekcja przyrządowa (zapisana, nie zatarta).** `tone_alarm home set` NIE certyfikuje pozycji
globalnej (to zdarzenie home, nie werdykt EKF); linie `WARN Preflight Fail ...` to STRUMIEŃ transientów,
nie werdykt — liczy się STAN KOŃCOWY (`is_global_position_ok ∧ is_home_position_ok` z telemetrii health,
nie ostatnia linia WARN w px4.log). W turze poprzedzającej DIAG „home set ⇒ GPS OK" i „ostatni WARN = GCS"
były MYLNYM TROPEM. Reguła: diagnozuj po stanie końcowym mierzonym przyrządem, nie po strumieniu logu.

## Retro — „flakiness" był NAZWANYM, DETERMINISTYCZNYM mechanizmem
Ten sam mechanizm tłumaczy „degradację SITL / arm-preflight flakiness" z sesji BUILD: po PIERWSZYM ubitym
biegu denialowym każdy kolejny boot startował GPS-denied i nie mógł się uzbroić. **Awaria była
DETERMINISTYCZNA, nie losowa.** Słowo „flakiness" usunięte z opisów TEJ KLASY (`run_gate_one.sh`,
`gate_run_r03.py`, `FINDING_clock_and_regime.md`:103 — korekta inline) i zastąpione nazwanym mechanizmem.
**Awaria gz z sesji CLOSE (0 /clock nawet dla `empty.sdf`) zostaje OSOBNYM, prawdziwym znaleziskiem
środowiskowym** (WSL2/gz-stack; minęła po restarcie) — nie jest tą samą klasą.

## Weryfikacja przed powrotem do biegów
- `python3 -m py_compile r03/gate_run_r03.py` OK; `bash -n` obu wrapperów OK; `certs_selfcheck` 6/6
  (config.py nie jest hashowany — selfcheck hashuje pliki proverów).
- Środowisko zostawione czyste (brak zombie, porty 14540/8888/50051 wolne), bson uzdrowione (GPS_CTRL=7).

## WYNIK BRAMKI (2026-08-11, po ratyfikacji DIAG) — 4/4 LIVE PASS
Po riderach + fix headless (`run_stack` honoruje HEADLESS — gz GUI ciągnął >180% CPU i głodził lockstep →
time-jump → EKF reset → „Arming denied: Resolve system health failures"; headless usuwa to) bramka
przeszła: **S1 PASS** (0 fałszywych REFUSE, flag_flips=0), **S2 PASS** (ratyf.), **S3 PASS** (re-ALLOW
6.09 s ≥ M=5, 0 oscylacji), **S4 PASS** (touchdown 18.95 m, margines 11.69 m). R-D3 zadziałało w praktyce:
S1 boot1 = `harness_invalid` (GPS=0 wyciekło z teardown S4, PX4 autosave 0 podczas denialu) → self-heal →
boot2 czysty PASS. S3 z ALT=15 m (param uprzęży) — zejście z 8 m było krótsze niż recovery+lag+M, więc
touchdown wyprzedzał re-ALLOW; wyższy start daje margines do zaobserwowania kryterium D13. **Push = Olga.**
