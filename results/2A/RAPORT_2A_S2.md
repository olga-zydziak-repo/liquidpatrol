# RAPORT_2A_S2 — etap A: 2 booty SHADOW + etap B: sędzia percepcji offline

CC · 05.10.2026 · łańcuch 2A · PROMPT_2A_S2 (numerowany) · po STOP-2A1 (c6790ba na origin).
Reguła nadrzędna dotrzymana: FEED-V (shadow) konsumował wyłącznie klatki + stan pokładowy
(EKF `/fmu/out/vehicle_local_position`, attitude `/fmu/out/vehicle_attitude`); GT wyłącznie
u sędziów offline. Lot w obu bootach na FEED=B (default, kontroler nie widział percepcji).

## §0. Bramka wejścia (wykonana)

origin/master = c6790ba, `origin/master..HEAD` puste, porcelain pełny CZYSTY (zero obcych M).
Piny 5/5 (`check_shield_frozen=True`) · certy 9/9 (`certs_selfcheck` PASS) · sha 8/8:
bench_judge `8ec0fcfb` ✓ · features `9adc1505` ✓ · ncp `0337d5ea` ✓ · yolo `9b2c17ab` ✓ ·
feed_vision `0ce7569c` ✓ · rejestr `2629bc40` ✓ · bench_flight `2972a48a` ✓ · percep_judge
`363c37b7` ✓. Kod frozen NIETKNIĘTY w całej sesji; wszystkie nowe pliki w `results/2A/**`.

## §1. ODCHYLENIE HABITATU 05.10 (przed pierwszym VALID): 3× env-fail + diagnoza + mitygacja env

**Zjawisko:** 3 kolejne booty (A1_c08_s03, `_r2`, `_r3`) = `HEALTH TIMEOUT` PRZED uzbrojeniem
(bench_flight:198): px4 do końca „Accel/Gyro Sensor 0 missing / barometer missing / ekf2 missing
data", `infra2_ekf_watchdog` n_poll_fail=28/28, przy ŻYWYM gz (rtf_stream: sim idzie, RTF ~1.0;
intruz spawnuje, usługi REQ/REP działają). SHADOW w żadnym z nich nie wystartował (start dopiero
po `armed`) ⇒ to NIE jest tryb B5 (obciążenie LIVE w oknie settle/arm) ani INFRA-2 (zatrzask
biasu) — sygnatura nowa: **pub/sub gz→px4 głodzony od t0**.

**Diagnoza (3 stacki ręczne, zero lotów, `results/2A/stageA/diag*` + `diag_proofs.md`):**
diag0: topiki sensorów SĄ, model spawnuje; px4 „zdrowy" FAŁSZYWIE (bez GCS nie drukuje ocen).
diag1: `gz topic -e` na IMU → dane płyną; `px4-ekf2 status` → **EKF update: 0 events**,
`sensor_gyro timestamp: 0`; połączenia TCP px4↔gz ESTAB (eth0). diag2: **`GZ_IP=127.0.0.1`
→ EKF update: 1473 events, attitude/local/global = 1** — fix dowiedziony wykonaniem.
Kontekst hosta: reboot ~1 h przed sesją; docker `vks_postgres` Up od reboota, 16× mostów br-*
+ veth UP — gz-transport advertyzował przez zoo interfejsów i strumień do px4 głodniał.

**Mitygacja (środowiskowa, odwracalna):** `export GZ_IP=127.0.0.1` w driverze etapu
(`results/2A/tools/stageA_boot.sh`) dla całego drzewa bootu; echo per boot w `.gz_ip_proof`.
Zero zmian frozen kodu/świata/modelu/parametrów PX4; kontener Olgi nietknięty. Po fixie:
**armed 2/2** (0/3 przed), oba booty VALID. Klasyfikacja 3 failów: **env-fail = nie-próby**
(wzór B5 §0 / REGATE SR-R5); artefakty zachowane w repo. Do ANEKS_2A-1: czy GZ_IP przenosić
do run_boot.sh (edycja frozen = decyzja Olgi) — bez tego każda przyszła sesja z aktywnym
dockerem może nie wstać.

**Drugie odchylenie proceduralne:** klatki jpg wykluczone z gita przez **`.git/info/exclude`**
(wpis `results/2A/stageA/*/frames/`), bo §0.3 zabrania dotykać `.gitignore` (poza results/2A).
Lokalne i jawne; przeniesienie do `.gitignore` = 1-liniowa decyzja Olgi.

## §2. Etap A — booty (oba VALID, REFUSE=0, breach=0)

| | **A1 = `stageA/A1_c08_s03_r4`** | **A2 = `stageA/A2_c11_s01`** |
|---|---|---|
| scenariusz / EP | c08_s03 (najgorszy desk f60), ep 32 | c11_s01 (nominalny), ep 11 |
| kontroler | net/NCP (weights_sha `0337d5ea…` w manifeście) | j.w. |
| kind / V2′ / D6 | 2a / **VALID** / success | 2a / **VALID** / success |
| dsw (Δsim/Δwall) | **0.9907** | **0.9951** |
| refuse / breach / d_min | 0 / nie / 5.07 m | 0 / nie / 6.02 m |
| t_entry / epizod | 0.15 s / 111.0–181.1 s | 1.94 s / 108.2–180.2 s |
| shadow: klatki YOLO | 1283 (gap p50 0.068 s ≈ **14.7 Hz**) | 539 (gap p50 0.132 s ≈ **7.6 Hz**, p95 0.464 — dropy mostu) |
| shadow: boxy / fresh | 973 / 958 | 413 / 45 (wszystkie PO epizodzie) |
| push_frame wall | p50 14.8 / p95 21.1 ms | p50 15.8 / p95 46.8 ms |
| jpg 2 Hz (lokalnie) | 165, sha zbioru `d683a1fd…` (manifest) | 146, sha `419f5e43…` (manifest) |

Dowody shadow per boot: topic kamery w `topics.txt` (gz + ros2 po bridge'u:
`/world/world_demo_A3/model/x500_mono_cam_0/link/camera_link/sensor/imager/image`), sha yolo
w logu shadow (`weights_sha=9b2c17ab… SR-2 PASS`, `shadow_stdout.log` + meta-wiersz
`shadow_feed.jsonl`), źródła stanu wypisane wprost (meta: `pos_ekf=/fmu/out/vehicle_local_position`,
`att=/fmu/out/vehicle_attitude`), `feed_sha=ffccf86b… == FREEZE_2A`. Shadow startował PO `armed`
(lekcja B5 — launcher czeka na `"ev": "armed"` w trace); kontrolera nie karmił (jedyne wyjście
procesu = pliki w OUTDIR; FEED env nieustawiony ⇒ gałąź FeedB verbatim w bench_flight).

## §3. Bramka A (progi PRE §3)

**(i) Pokrycie kadru RZECZYWISTE (GT drona z trace [quat D5] + GT intruza, pinhole FREEZE_2A,
fazy z demo): FAIL ×2.**

| faza | próg | A1 | A2 |
|---|---|---|---|
| approach | ≥0.90 | **0.609** (56/92) | **0.113** (15/133) |
| orbit | ≥0.90 | **0.403** (857/2127) | **0.385** (812/2109) |

**Mechanizm (zmierzony, nie hipoteza):** 100% ticków poza kadrem wypada przez AZYMUT
(A1: 1297/1297, A2: 1398/1398; |az| p50 ~70°), elewacja ZAWSZE w zapasie (|el| p95 20.9°/30.0°
przy połówce vFOV 39.8° — tu desk R5 się potwierdza). Przyczyna: **yaw drona stoi w miejscu**
(A1: 0.3°±3 po całym locie; A2: −0.8° p5/p95 −2.2/+2.5) mimo komendy „twarz ku intruzowi" —
kontroler liczy yaw = atan2 w **RADIANACH** (±π, `net_controller.py:115`, `orbit_executor.py:75`),
a ławka wkłada tę wartość w pole **yaw stopniowe** MAVSDK `VelocityNedYaw` (`bench_flight.py:398`)
⇒ komenda ±3.14° ≈ nos na północy. Kadr trafia w cela tylko gdy LOS≈N — stąd A1 (bearing 0°=N)
0.40, A2 (bearing 270°=W) 0.11 w approach. **Założenie desku R5 („yaw-follow robi sam dron",
f90=1.000) obalone w locie** — dokładnie luka „pitch/yaw nielogowany", którą D5 miał zamknąć,
i powtórka lekcji r02 („kadrowanie w locie", §3f) z ustaloną tym razem przyczyną źródłową.
Naprawa = edycja frozen (bench_flight/kontrolery) ⇒ poza mandatem S2; decyzja w ANEKS_2A-1.
PRE nie przewiduje retry dla (i) (retry det-5Hz dotyczy tylko (ii)) — nie wykonano.

**(ii) V2′ dsw ≥ 0.90 z pełnym stackiem percepcji: PASS ×2 bez retry** — A1 0.9907, A2 0.9951.
Opisowo vs pasmo kampanii LIQ (0.9544–1.0): **oba W PAŚMIE** — koszt always_on + mostu + YOLO
15 Hz na GPU niewidoczny w dsw bootu (odpowiedź na pytanie R6/R3: kamera renderuje zawsze,
FILM=0, a kontencja ujawnia się nie w RTF, lecz w kadencji klatek SHADOW: A2 efektywnie 7.6 Hz
przy YOLO p95 46.8 ms — dropy BEST_EFFORT na moście, nie stalle świata).

**(iii) Quat w trace obecny i sensowny: PASS ×2** — obecność 2918/2918 i 2966/2966 wierszy gt,
norma 0.999999–1.000001, ciągłość max 6.4°/wiersz @≤50 Hz, oraz test niezależny: R(ned←frd)
zrekonstruowane z kwaternionu GZ vs attitude PX4 (shadow `own_q`) — kąt rozbieżności
p50 0.76°/0.92°, p95 1.94°/2.05° (n=1160/478). Konwersja ramek (FREEZE_2A) dowiedziona danymi.

**Werdykt bramki A: (ii) PASS ∧ (iii) PASS ∧ (i) FAIL ×2** — FAIL z mechanizmem leżącym
w torze KOMEND ławki (jednostki yaw), nie w percepcji i nie w geometrii kamery.

## §4. Etap B — sędzia percepcji offline (`percep_judge` 363c37b7; FP: `stageB_extras`)

Punkty odniesienia: FeedB kalibracja S1 (r1_ncp): 0.741/0.673/1.258 m · kąt 3.11°/6.96° ·
9.62 Hz. FeedB z TYCH SAMYCH bootów (lot szedł na FeedB): A1 0.745/0.707/1.360 m · A2
0.716/0.677/1.273 m · 9.62 Hz — przyrząd spójny z S1.

| metryka | próg B | **A1 shadow** | **A2 shadow** | **łącznie (pooled)** | FeedB (S1) |
|---|---|---|---|---|---|
| kadencja świeżych p50 [Hz] | ≥8 | **14.71 PASS** | **n/d — 0 świeżych w oknie GT** | 14.71 | 9.62 |
| latencja capture→update p95 [s] | ≤0.25 | **0.044 PASS** (p50 0.036, n=810) | n/d (brak próbek) | 0.044 | ~0.2 (konstrukcyjna) |
| błąd NED p95 [m] | ≤3.0 | **50.891 FAIL** (mean 19.15, p50 13.25, n=993) | n/d (n=0) | 50.891 | 1.258 |
| dekompozycja: kąt p50/p95 [°] | — | 87.2 / 162.8 | n/d | 87.2 / 162.8 | 3.11 / 6.96 |
| dekompozycja: zasięg p50 [m] (bias) | — | 3.72 (+7.74) | n/d | 3.72 | 0.33 (+0.03) |
| FP-admisje: świeże o err>5 m | — | **768/810 (95%)** | **0/0 w oknie GT** | 768/810 | — |
| track_valid frakcja (locked w logu) | — | 1267/1283 | 90/539 (dopiero od 184.8 s, po epizodzie) | — | — |

**Klasyfikacja progowa (wypisana; wnioski kanoniczne → ANEKS_2A-1):**
B(i) kadencja: **PASS na A1 · FAIL-przez-brak-próbek na A2 · PASS pooled**;
B(ii) latencja: **PASS** (0.044 s, 5.7× zapasu);
B(iii) błąd p95: **FAIL**, w tym **p95 > 6.0 m ⇒ wyjątek ekonomiczny PRE §3 (C → sonda 2 bootów)**.

**Noty mechanizmu (do cytowania ŁĄCZNIE z dekompozycją, PRE §4):**
1. A1: po poprawnym ENTRY (struktura∧MTI, 2.7 s od startu epizodu, err 1.82 m) kanał trzyma lock,
   a REFRESH jest admission-only (AM2.0) — gdy cel wypada z kadru (60% ticków, yaw), top-1 tła
   odświeża track ⇒ kąt p50 87° i err p95 51 m. **Na tickach z celem w kadrze pinhole działa:**
   sanity best_fresh err **1.06 m** @ d≈10 m (box na intruzie, mti=True).
2. A2: brama ENTRY k=3∧MTI **obroniła się przed tłem przez cały epizod** (0 fałszywych wejść
   w oknie GT przy 413 boxach tła) — track nie powstał, bo cel prawie nie bywał w kadrze
   (pokrycie approach 0.11). ENTRY dopiero w resecie (184.8 s, poza GT).
3. FAIL-e B są DOWNSTREAM znaleziska yaw (kadrowanie komend, §3), nie zdolności czasowej toru
   (B(ii) 0.044 s, YOLO p50 ~15 ms) ani pinhole. Czy to wyzwala zdanie ŚMIERCI KIERUNKU
   („percepcja limituje czasowo") — decyzja aneksu: prereg zakładał kadrowanie ≥0.90, które
   padło z przyczyny zewnętrznej wobec toru percepcji.

Sanity-klatki (6 w repo, wzór U1R, `stageA/*/sanity/*.png`): A1 best/worst/entry
(1.06 m / 142.6 m FP przy widocznym intruzie / ENTRY 1.82 m), A2 entry (po epizodzie)
+ 2× odrzut D2 (top-1 tła NIE-admitowany, locked=False).

## §5. Budżet, artefakty, narzędzia

Booty lotne VALID: **2** (A1_r4, A2). Env-faile pre-arm: 3 (nie-próby, habitat §1). Diagi
stackowe bez modułu lotu: 3. Retry det-5Hz: nie użyty. Budżet PRE (≤31): po etapie A zużyte 2
lotne + 3 env-fail do ewidencji aneksu. Cooldowny ≥300 s (driver), wyłączność (pgrep + REPO-2
guard), manifesty 1. klasy kind=2a z sekcją `shadow` (sha zbioru klatek + sha shadow_feed).
`shadow_feed.jsonl` COMMITOWANE (390 kB + 156 kB); jpg lokalnie (3.3/3.0 MB, sha w manifestach).

Narzędzia S2 (nowe, wszystkie w `results/2A/tools/`, sha8): stageA_boot.sh `a040d3fd` (driver:
guardy+cooldown+shadow po armed+GZ_IP) · shadow_feed_live.py `2e64873c` (FeedVisionLive jako cień;
`t_update_sim` doklejany przez proxy pliku loga — kompozycja, zero edycji frozen; jpg 2 Hz;
`--det-hz` dla wariantu retry) · coverage_real.py `53453371` (bramki A i/iii; konwersje wyłącznie
przez common/frames + r02/mti) · stageB_extras.py `03c60c6d` (FP>5 m) · stageB_pooled.py
`b95208f3` (etap B łącznie) · sanity_frames.py `b51aca51`. Sędzia percep_judge NIETKNIĘTY
(`363c37b7` ✓).

## §6. STOP-2A2

Zgodnie z §4 PROMPT_2A_S2: commit artefaktów (booty + shadow-logi + sanity + raport; bez *.ulg
[gitignore], bez frames/ [exclude §1]), porcelain po commicie CZYSTY, **push = Olga**.
Dalej: **ANEKS_2A-1** (werdykt bramek A/B; go/no-go etapu C — na stole: znalezisko yaw_deg,
wyjątek ekonomiczny C-sonda z B(iii), los GZ_IP w run_boot). STOP.
