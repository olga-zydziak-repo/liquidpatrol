# RAPORT_DET_S4 — KAMPANIA C: 12 rund × {FEED-B, FEED-V2} × NCP → STOP-DET4

LiquidPatrol · CC-wykonawca · 07.10.2026 · ANEKS_DET-3 §3 (ARCH-1 commit d914eaa0).
Raport = liczby i mechanizm z telemetrii; werdykt Δ i kanon nogi należą do ANEKS_DET-4.

## §0. Bramka wejścia (wykonaniem, przed czymkolwiek)

origin/master = `b7a5cab1` ✓ · `origin/master..HEAD` puste ✓ · porcelain pełny pusty ✓.
FROZEN wykonaniem: det_v2.pt `775ead15…` ✓ · feed_sha_v2 `8015bd12…` (policzone
`harness.det_v2.feed_sha_v2()` z procesu) ✓ · rejestr `ee1481f9` ✓ · feed_vision
`acc81df7` ✓ · bench_flight `05137098` ✓ · ncp.npz `0337d5ea` ✓ · piny 5/5
(SHIELD FROZEN True) ✓ · certy 9/9 (certs_selfcheck PASS) ✓.
ARCH-1: `ANEKS_DET-3.md` verbatim w korzeniu, pierwszy commit `d914eaa0`
(sha256 kopii `953f4df4819618…`). Konfiguracja: commit `37eeb370` (4 nowe narzędzia
w `results/DET/tools/`, zero edycji frozen). Host przed kampanią: load1 0.23,
29 GB RAM wolne, GPU 0 %.

## §1. Konfiguracja (PRE_2A §3-C VERBATIM, podmiana FEED-V→FEED-V2)

Siatka 48 i przydział rund JAK LIQ: runda r = episode_id 4(r−1)…4r−1 porządku
manifestu F2 (`results/BENCH/scenario_manifest.json`, blok 1); r1 c00–c03×s01 · … ·
r12 c08–c11×s04. Rotacja ramion naprzemienna: nieparzyste B→V2, parzyste V2→B.
Oba ramiona: CONTROLLER=net NET_ARM=ncp (wagi `0337d5ea`), WORLD=world_demo_A3,
INTRUDER=1, FILM=0, KIND=det, pełne uzbrojenie ławki. Ramię B: env ścieżki LIQ
(FEED default B; manifest feed_sha `da9ef2f4` = FeedB). Ramię V2: env smoke S3
VERBATIM (FEED=V2 przez rejestr; percepcja w osobnym procesie `percep_proc.py`
startowana po `"ev": "armed"` wraz z bridge; manifest feed_sha `8015bd12`).
Reżim bootów: driver etapowy `detS4_boot.sh`, GZ_IP=127.0.0.1, wyłączność pgrep,
cooldown ≥300 s, SUSTAINED CLEAN 3×30 s (proc_gate), REPO-2. Manifesty 1. klasy:
weights_sha `0337d5ea` wstrzyknięte post-boot (guard SR-2 przeszedł w locie),
feed_sha per ramię z procesu ławki, booty V2 dodatkowo sha logów percep/klienta.
Sędzia: bench_judge `8ec0fcfb` FROZEN przez `campaign_analyze.judge_boot`
(D9 = V2′ jak LIQ/ławka); ważność V2 dodatkowo żywość feedu VERBATIM ANEKS_2A-3 §4
per epizod. Narzędzie parowania: `detS4_pairs.py` (pierwsza ważna próba per ramię,
pary wspólnie ważne).

**Nota konstrukcyjna (zero zmian kodu, udokumentowana przed lotami, commit 37eeb370):**
klient FROZEN `feed_vision_proc.py` otwiera log E2E w trybie „w" PER EPIZOD, więc
w boocie 4-epizodowym `client_e2e.jsonl` niesie ostatni epizod; driver przechwytuje
pełny strumień czysto odczytowo (`tail -F` → `client_e2e_full.jsonl`, sha w manifeście).
Re-bind gniazda UDS per epizod działa na frozen bajtach, bo percep wysyła
`sendto(path)` per datagram (ścieżka rozwiązywana przy wysyłce) — zweryfikowane
z kodu przed lotami i potwierdzone wykonaniem (świeże próbki we wszystkich epizodach
z akwizycją, w tym 4. epizodzie bootu).

## §2. Przebieg: 24 booty, zero nieważnych, zero powtórek

Booty nogi nr 14–37 (24 kampanijne), wszystkie rc=0, finalize=0; **zapas 0/3
nietknięty**; przerwań nie było (12 rund ciurkiem, 09:22–14:54). Ważność:
**48/48 epizodów B ważnych (V2′)** i **48/48 epizodów V2 ważnych (V2′ ∧ żywość)**
⇒ **n_common = 48/48** (próg STOP n_common<40 odległy). Żywość: minimum
113 klatek przetworzonych w pierwszych 30 s epizodu (próg ≥10 — zapas >11×);
dsw min 0.9058 (≥0.90), timejump 0 wszędzie. V2′ per boot: 24/24 VALID.

## §3. Tabela 48 par (sędzia D6; d_min opisowy; split PRE_DET: TEST c06+c09, VAL c02+c04)

| scenariusz | split | B D6 | V2 D6 | d_min B | d_min V2 | | scenariusz | split | B D6 | V2 D6 | d_min B | d_min V2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c00_s01 | TRAIN | ✓ | ✓ | 7.95 | 8.04 | | c06_s01 | TEST | ✓ | ✗ | 6.57 | 3.75 |
| c00_s02 | TRAIN | ✓ | ✓ | 7.90 | 8.28 | | c06_s02 | TEST | ✓ | ✗ | 6.75 | 8.85 |
| c00_s03 | TRAIN | ✓ | ✓ | 7.73 | 8.27 | | c06_s03 | TEST | ✓ | ✗ | 7.47 | 7.32 |
| c00_s04 | TRAIN | ✓ | ✓ | 8.30 | 8.17 | | c06_s04 | TEST | ✓ | ✗ | 7.49 | 2.89 |
| c01_s01 | TRAIN | ✓ | ✗ | 7.81 | 14.97 | | c07_s01 | TRAIN | ✓ | ✗ | 7.42 | 6.37 |
| c01_s02 | TRAIN | ✓ | ✗ | 7.44 | 15.08 | | c07_s02 | TRAIN | ✓ | ✗ | 7.57 | 7.52 |
| c01_s03 | TRAIN | ✓ | ✗ | 7.90 | 10.86 | | c07_s03 | TRAIN | ✓ | ✗ | 7.54 | 1.51 |
| c01_s04 | TRAIN | ✓ | ✗ | 8.36 | 15.11 | | c07_s04 | TRAIN | ✓ | ✓ | 7.65 | 4.97 |
| c02_s01 | VAL | ✓ | ✗ | 7.38 | 12.38 | | c08_s01 | TRAIN | ✓ | ✓ | 6.65 | 6.54 |
| c02_s02 | VAL | ✓ | ✗ | 7.52 | 13.74 | | c08_s02 | TRAIN | ✓ | ✓ | 7.24 | 6.88 |
| c02_s03 | VAL | ✓ | ✗ | 7.90 | 10.95 | | c08_s03 | TRAIN | ✓ | ✓ | 5.40 | 5.46 |
| c02_s04 | VAL | ✓ | ✗ | 8.38 | 10.90 | | c08_s04 | TRAIN | ✓ | ✓ | 7.19 | 6.63 |
| c03_s01 | TRAIN | ✓ | ✗ | 7.73 | 14.76 | | c09_s01 | TEST | ✓ | ✗ | 6.55 | 2.07 |
| c03_s02 | TRAIN | ✓ | ✗ | 7.95 | 14.90 | | c09_s02 | TEST | ✓ | ✗ | 6.32 | 1.48 |
| c03_s03 | TRAIN | ✓ | ✗ | 7.80 | 15.02 | | c09_s03 | TEST | **✗** | ✗ | 1.17 | 0.41 |
| c03_s04 | TRAIN | ✓ | ✗ | 8.46 | 10.82 | | c09_s04 | TEST | ✓ | ✗ | 6.23 | 0.54 |
| c04_s01 | VAL | ✓ | ✓ | 6.80 | 7.01 | | c10_s01 | TRAIN | ✓ | ✗ | 6.38 | 0.52 |
| c04_s02 | VAL | ✓ | ✓ | 6.99 | 7.42 | | c10_s02 | TRAIN | ✓ | ✗ | 6.85 | 1.85 |
| c04_s03 | VAL | ✓ | ✓ | 7.25 | 7.74 | | c10_s03 | TRAIN | ✓ | ✗ | 5.16 | 0.34 |
| c04_s04 | VAL | ✓ | ✓ | 7.26 | 7.25 | | c10_s04 | TRAIN | ✓ | ✗ | 5.46 | 0.73 |
| c05_s01 | TRAIN | ✓ | ✗ | 6.63 | 8.25 | | c11_s01 | TRAIN | ✓ | ✗ | 6.89 | 1.66 |
| c05_s02 | TRAIN | ✓ | ✗ | 6.60 | 0.34 | | c11_s02 | TRAIN | ✓ | ✗ | 5.51 | 1.53 |
| c05_s03 | TRAIN | ✓ | ✗ | 7.27 | 8.24 | | c11_s03 | TRAIN | ✓ | ✗ | 7.53 | 0.45 |
| c05_s04 | TRAIN | ✓ | ✗ | 6.94 | 6.58 | | c11_s04 | TRAIN | ✓ | ✗ | 7.65 | 1.27 |

Jedyna porażka B: c09_s03 (d_min 1.17 m przy WYROCZNI — scenariusz intrinsycznie
trudny: trajektoria v=1.0 tnie orbitę; V2 też FAIL ⇒ para nie wnosi do Δ).

## §4. Liczniki Δ (progi VERBATIM PRE_2A §4; werdykt = ANEKS_DET-4)

**pass(B) = 47/48 · pass(V2) = 13/48 · Δ = 34** na 48 parach wspólnie ważnych.
Δ=34 ≥ 10 ⇒ strefa zdania „percepcja limituje wykonanie: −34/48 par; mechanizm
z telemetrii" (§5). Kwalifikatory każdego cytowania (VERBATIM ANEKS_DET-3 §3.7):
SITL, rendering syntetyczny, mono-zasięg ze znanym rozmiarem, detektor doszkolony
na klatkach tego symulatora i tej sceny (komórki held-out w bramce T; 46/48 par
sceno-świeżych), geometria c-siatki, NCP. ZAKAZ ekstrapolacji na realne
sensory/warunki (PRE_2A §4).

Predykcje (rozliczenie formalne w KSIĘDZE przy ANEKS_DET-4): P-DET-5 (Δ≤4, p 0.55)
— nietrafiona; pod-predykcja (≥1 REFUSE pod V2, p 0.20) — nietrafiona w kierunku
własnego przechyłu (REFUSE=0).

## §5. Mechanizm z telemetrii: AKWIZYCJA, nie jakość tracku

**Wszystkie 35 porażek V2 to brak akwizycji celu przed/na czas** — ani jedna nie
jest błędem pozycji utrzymywanego tracku:

- **29/35 ŚLEPE** (fresh <10 w całym epizodzie, kontroler w hover-hold, frakcja
  track_valid ≈0): komórki bearing 90/180/270° przy v∈{0, 0.5} systematycznie
  (c01/c02/c03 ×4, c05/c06/c07 bez jednej, częściowo c09–c11). Statyczny lub wolny
  intruz poza stożkiem sztywnej kamery (FOV 99.7°, montaż przód, yaw≈0 w zawisie)
  nigdy nie wchodzi w kadr — akwizycja z zawisu jest geometrycznie niemożliwa.
  Boxy w tych epizodach: 0 (detektor przetwarza klatki, w kadrze nie ma celu).
- **6/35 AKWIZYCJA ZA PÓŹNO / UTRATA**: intruz v≥0.5 wwędrował w stożek w trakcie
  epizodu (fresh 282–1068), t_entry 14.1–20.0 s lub przelot w ślepej fazie przed
  akwizycją (d_min 0.34–1.5 m): c09_s02/s03, c10_s01/s03/s04, c05_s04 (akwizycja
  wczesna t_entry 0.68, potem utrata). Frac_band nie wystarcza do D6.
- **Komórki bearing 0° (c00/c04/c08): V2 12/12 PASS** — wszystkie v_intr, wszystkie
  ziarna. Po akwizycji jakość tracku det_v2 w pętli zamkniętej jest LEPSZA niż
  wyrocznia FeedB: err_fresh mediana per epizod p50 0.418 / p95 0.648 m (22 epizody
  z próbkami) vs FeedB p50 0.676 / p95 1.280 m (48 epizodów). Jedyny pass spoza
  bearing 0°: c07_s04 (t_entry 26.9 s, zdążył z frac_band).

Dekompozycja B obowiązkowa przy cytowaniu (PRE_2A §4): koszt NIE siedzi w ogniwie
kierunek/zasięg/dropout tracku — siedzi w polu widzenia toru akwizycji (kamera
sztywna + zawis bez skanowania). FEED_EXPIRE łącznie 8 w 48 epizodach V2 (dropouty
marginalne). Echo lekcji r02 „kadrowanie kamery" w wersji zamknięto-pętlowej:
w 2A etap A pokrycie kadru mierzono NA LOCIE wyroczni (dron już latał orbitę);
w pętli zamkniętej system musi NAJPIERW zobaczyć cel, żeby w ogóle polecieć.

## §6. Telemetria zbiorcza (OPISOWA) + prerejestracje §2 ANEKS_DET-3

| miara | FEED-B | FEED-V2 |
|---|---|---|
| err_fresh per epizod: mediana p50 / mediana p95 / max | 0.676 / 1.280 / 27.5* | 0.418 / 0.648 / 14.2* |
| err_consumed (demo): mediana p50 / mediana p95 | 0.676 / 1.280 | 0.513 / 1.406* |
| err w paśmie d<6 m (prereg §2): mediana p50 / mediana p95 / max | 0.808 / 1.264 / 13.97* | 0.373 / 3.544 / 7.19 |
| epizody z próbkami w paśmie d<6 m | 5 | 8 |
| FEED_EXPIRE łącznie | 0 | 8 |
| z_max (alt) / r_max | 13.78 / 26.24 | 14.05 / 26.03 |
| d_min (opisowy, min po ramieniu) | 1.172 (c09_s03) | 0.339 (c10_s03) |

\* maxima w obu ramionach niosą artefakt granicy epizodu (track trzyma pozę sprzed
teleportu startowego ≤1 s wieku; w V2 dodatkowo do re-ENTRY) — nazwany w narzędziu
przed lotami; mediany p50/p95 na niego niewrażliwe.

**Ogon zbliżeniowy (prereg §2): w porażkach V2 NIE uczestniczy.** Porażki to brak
akwizycji (§5), nie błąd zasięgu w bliskim polu. Ogon jest widoczny opisowo tam,
gdzie track żyje przy d<6 m: p95 pasma 3.54 m vs p95 całości 0.648 m (echo smoke;
pasmo poniżej korpusu treningowego Z p5=6.5 m). Maksimum pasma 7.19 m.

**Kadencja przetwarzania V2 (opisowa):** bimodalna per boot — 6 bootów ~7.58 Hz,
6 bootów ~14.71 Hz p50 (sim-time; ta sama bimodalność narzędziowa co zrzut S1,
ANEKS_DET-1 odchylenie (a)). Poniżej poziomu smoke w części bootów; kryterium
ważności kampanii (V2′ ∧ żywość) tego nie bramkuje, żywość z zapasem >11×,
push_frame wall p50 ~13.6 ms (detektor nie jest limitem). E2E klatka→próbka
u klienta (z przechwytu _full): p95 0.080–0.088 s per boot — poziom smoke (0.084),
wszystkie ≤0.25.

## §7. S-BEZP (kryterialne) + REFUSE per gałąź

**breach: 0** we wszystkich 96 epizodach obu ramion (twardy STOP nie zadziałał).
**REFUSE: 0 / 0** — liczniki per gałąź PUSTE w obu ramionach; osobny licznik
fałszywych odmów pod szumem percepcji (pytanie nogi W w ostrzejszej wersji) = **0**
(w 29 epizodach ślepego zawisu i 6 późnych akwizycji osłona nie wygenerowała ani
jednej odmowy). REFUSE(POS): brak. Opisowo: 7 epizodów V2 z d_min <1 m i 6 w paśmie
1–2 m — wszystkie w trybie ślepego zawisu/późnej akwizycji; kolizja nie jest
przedmiotem osłony (geofence/POS), d_min pozostaje miarą opisową programu.

## §8. Dekompozycje opisowe (ANEKS_DET-3 §3.7)

- **46 par sceno-świeżych: pass(B)=45, pass(V2)=12, Δ=33** (werdykt niesie 48/Δ=34
  VERBATIM; dekompozycja potwierdza, że 2 pary TRAIN-scene nie robią wyniku).
- **2 pary scene-in-train (prereg §2):** c08_s03 V2 ✓ (bearing 0°), c11_s01 V2 ✗
  (bearing 270°, ślepy zawis) — o wyniku decyduje geometria akwizycji, nie
  znajomość sceny przez detektor.
- **Per komórka (Δ):** c00/c04/c08 (bearing 0°): 0/0/0 · c01/c02/c03 (v=0): 4/4/4 ·
  c05/c06: 4/4 · c07: 3 · c09: 3 (B też raz padł) · c10/c11: 4/4.
- **Per split detektora:** TRAIN 32 pary: B 32, V2 9 · VAL 8: B 8, V2 4 · TEST 8:
  B 7, V2 0. Zero passów V2 w TEST to artefakt geometrii komórek (c06 bearing 180°,
  c09 bearing 90°), nie dowód luki generalizacji — wszystkie porażki TEST to brak
  akwizycji (§5), track w c06/c09 po akwizycji miał err_fresh p95 0.61–1.49 m.

## §9. Odchylenia i noty uczciwości

1. Kadencja bimodalna 7.58/14.71 Hz per boot (§6) — narzędziowa, jak S1; nie frozen,
   nie bramkująca; odnotowana per boot w artefaktach.
2. `client_e2e.jsonl` per boot niesie ostatni epizod (właściwość klienta FROZEN,
   mode "w" per epizod); pełny strumień w `client_e2e_full.jsonl` (przechwyt driver,
   sha w manifeście). Zero zmian kodu.
3. Artefakt granicy epizodu w maximach err (§6, przypis \*) — nazwany przed lotami
   w narzędziu (commit 37eeb370).
4. t_entry=null w trace dla 5 passów V2 = lock przed epizodem (artefakt falsy-zero
   znany ze smoke; w §5 policzone jako akwizycja wczesna).
5. c05_s02: t_entry 0.97 s pochodzi ze stale-locku granicy epizodu (fresh=1);
   epizod sklasyfikowany jako ślepy (29) po frakcji fresh, nie po t_entry.

## §10. Budżet, artefakty, porcelain

Booty nogi: 13 (S1–S3) + 24 (S4) = **37 z ≤45; limit po S4 ≤40 — SPEŁNIONY**
(zapas 3 nietknięty). Sesja lotna: jedna (09:22–14:54, 12 rund bez przerwania).
Artefakty: `results/DET/camp/` — 24 booty (trace, demo, gt_intruder, rtf, ulog,
manifesty; booty V2 dodatkowo percep_feed.jsonl+summary, client_e2e+_full,
bridge/percep logi), `detS4_summary.json` per boot, `detS4_pairs.json` +
`pairs_after_r*.txt` + `pairs_final.txt`, `campaign_state.json`
(launches 24, spares 0), `detS4_monitor.log`. Porcelain po commicie STOP-DET4: pusty.

Dalej (poza tym raportem): **ANEKS_DET-4** — werdykt Δ, kanon nogi, KSIĘGA
(P-DET-1…5), CO-DET (zamknięcie). STOP.
