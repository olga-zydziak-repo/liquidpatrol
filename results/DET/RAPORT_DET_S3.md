# RAPORT_DET_S3 — FEED=V2 zbudowany + smoke PASS za 1. podejściem (STOP-DET3)

CC-wykonawca · 07.10.2026 · wykonanie ANEKS_DET-2 §4 · commity sesji: 0b8570c (ARCH-1)
→ 6962c30 (build) → ten (smoke+raport).

## §0. TL;DR

**Pierwszy w programie lot z ZAMKNIĘTĄ pętlą na uczonym detektorze — i smoke przechodzi
WSZYSTKO za pierwszym podejściem (1 boot, naprawczych 0):** kadencja przetwarzania
**14.71 Hz p50 ≥ 8 (PASS)** — poziom shadow-procesu z 2A, dowód że osobny proces usuwa
kontencję in-process (6.7–7.2 Hz w S4-2A); E2E **p95 0.084 s ≤ 0.25 (PASS)**; żywość
ALIVE (247 klatek + 108 świeżych / 30 s); **S-BEZP: breach 0, REFUSE 0**; V2′ PASS
(dsw 0.9698). Opisowo (bez progów): **err tracku vs GT W LOCIE p50 0.335 / p95 0.716 /
max 4.88 m** — zamknięto-pętlowe echo T2 LEPSZE niż replay TEST (1.365), dron realnie
orbitował na percepcji (fazy: orbit 68 % / hold 27 % / approach 4 %; r_max 17.83 m,
margines do R_E 14.17 m). **Warunek 2/2 kampanii C SPEŁNIONY** — czeka ANEKS_DET-3.
P-DET-4 ✓ (formalnie przy zamknięciu; noga 4/4).

## §1. Bramka + ARCH-1 + budowa (commit 6962c30)

Bramka §4.1 PASS (origin c86ec13, ahead 0, porcelain pełny, det_v2 775ead15, feed_vision
acc81df7, bench_flight 05137098, det_replay de0feb37, rejestr sprzed edycji 2629bc40).
ARCH-1: ANEKS_DET-2.md w korzeniu (0b8570c).

**Budowa — wymóg wspólnych bajtów (ANEKS §3) dotrzymany konstrukcją:**
- `harness/det_v2.py` — wrapper wag 775ead15 (guard klasy SR-2), kontrakt D4 jak
  YoloDetector.top1, **bez progu conf** (θ\* nie wchodzi, ANEKS §2); `feed_sha_v2()` =
  jeden punkt prawdy kontraktowego sha (params rdzenia ∪ sha det_v2) =
  **`8015bd12…`** (FREEZE_DET; potwierdzony w manifeście bootu z procesu ławki).
- `harness/percep_proc.py` — proces percepcji: własny kontekst rclpy + **DEDYKOWANY
  SingleThreadedExecutor (lekcja N3-C wbudowana)**; subskrypcje obraz+pos+att; **rdzeń
  `FeedVision` (acc81df7) importowany READ-ONLY z wstrzykniętym DetV2 — zero
  reimplementacji MTI/admisji/pinhole/REFRESH/starzenia**; LogProxy t_update_sim (wzór
  S2); datagram UDS po każdej klatce (sample(t_frame) + stemple).
- `harness/feed_vision_proc.py` — cienki klient: zero rclpy/GT, nieblokujący dren
  DGRAM, kontrakt R1 VERBATIM; wiek w sim rozcięty przez IPC:
  age(sim_now) = (sim_now − t_frame) + age(t_frame) — ta sama matematyka co
  FeedVision.sample; vel ZOH (odchyłka okna ≤0.07 s, nota); log E2E przy pierwszej
  konsumpcji (miara bramki).
- `harness/feed_registry.py` — wpis **V2 ADDITIVE** (jedyna edycja istniejącego pliku;
  bazowy 2629bc40 → ee1481f9; B/V nietknięte — regresja feed 15/15 PASS).
- Narzędzia: driver `detS3_smoke.sh` (percep+bridge po armed, teardown SIGTERM→summary,
  czysty PYTHONPATH bridge'a — lekcje B5/C1), sędzia `detS3_analyze.py`.
- **Testy przed lotem 4/4 PASS** (`results/DET/tools/test_aneks_det2.py`): kontrakt dict
  (wiek/hold-last/dren), latencja UDS p95 <0.01 s, klasa kolizji egzekutora
  (wątek-lustro ławki + klient bez rclpy), cykl życia percep_proc (spawn z prawdziwym
  det_v2 → meta-datagram → SIGTERM rc=0 + summary). Nota: AF_UNIX sun_path ~108 B ⇒
  testy na krótkim mkdtemp; ścieżki lotne (~65 zn.) bez ryzyka.

## §2. Smoke — 1 boot, FEED=V2, c10_s01 (ep 10), pełne uzbrojenie

| pomiar | wynik | próg | werdykt |
|---|---|---|---|
| V2′ (dsw / stall) | 0.9698 / 0.0 | pasmo LIQ | **VALID** |
| żywość feedu (ANEKS_2A-3 §4) | 247 klatek + 108 fresh / 30 s | ≥1 fresh LUB ≥10 klatek | **ALIVE** |
| **kadencja przetwarzania (def. a)** | **14.71 Hz p50** (877 klatek) | ≥8 Hz p50 | **PASS** |
| **E2E klatka→próbka u klienta** | **p95 0.084 s** (n=626, sim-time) | ≤0.25 s | **PASS** |
| **S-BEZP: breach R_E** | 0 | =0 wymagane | **PASS** |
| S-BEZP: REFUSE | 0 (żadna gałąź; POS brak) | wpis per gałąź | czysto |

**Opisowe (bez progów):** kadencja świeżych (def. b) 14.71 Hz p50 — brama przepuszczała
niemal każdą klatkę (fresh 521/877; gate mti **519** / window 2; ENTRY 2, FEED_EXPIRE 2
— dwa krótkie cykle re-admisji); **err tracku vs GT w locie: p50 0.335 / p95 0.716 /
max 4.88 m (n=488)** — pierwsze zamknięto-pętlowe echo T2, lepsze od replayu (1.365)
i od referencji FeedB (1.258); track_valid 75.9 % ticków; dron LATAŁ na percepcji:
t_entry=0.0 s (track locked już przed epizodem — percep startuje po armed; w trace
`t_entry: null` to artefakt falsy-zero przy logowaniu, stan wewnętrzny 0.0), fazy
orbit 942 / hold 379 / approach 60 ticków, r_est_max 17.83 m (margines 14.17 m do
R_E=32), z_min −12.96 m, d_min do intruza GT 2.02 m (przelot bliski w scenariuszu
ruchomego celu v=1.0 — opisowy, bez progu).

Prowieniencja: manifest 1. klasy (net_arm=ncp 0337d5ea, **feed_sha = 8015bd12… = V2**,
sekcja feed_v2 z sha logów percep/klienta); nota numpy ławki 2.4.4 (B0SP — klient
importuje r02.mti; jak S4-2A); GZ_IP=127.0.0.1; proc_gate CLEAN; teardown czysty
(percep SIGTERM → summary; zero sierot).

## §3. Wnioski mechanizmowe (do ANEKS-u)

1. **Kontencja in-process ROZWIĄZANA architekturą:** 6.7–7.2 Hz (FEED=V in-process,
   S4-2A) → **14.71 Hz** (osobny proces) przy tych samych bajtach rdzenia i cięższym
   o nic detektorze — zgodnie z dowodem shadow; „śmierć czasowa" pozostaje nieaktualna.
2. **Separator po doszkoleniu działa też w pętli zamkniętej:** brama admisyjna, która
   w 2A głodziła track (fresh 25 % boxów), przy det_v2 przepuszcza ~100 % klatek przez
   koniunkcję struktura∧MTI — bez jednej zmiany w bajtach bramy.
3. Echo T2 w locie (0.716) < replay TEST (1.365): spójne, bo c10 ∈ TRAIN i geometria
   zamknięto-pętlowa trzyma cel centralnie; liczba kampanijna pozostaje do zmierzenia
   na 48 parach (S4).

## §4. Budżet i status

Smoke: **1 boot VALID (naprawczych 0/2, drugi smoke niepotrzebny)** ⇒ noga **13 bootów
z ≤45** (limit po S3 ≤16 — z zapasem). Porcelain przy STOP: build (commit 6962c30) +
boot smoke + raport. Push = Olga. **Warunek odpalenia kampanii C (PRE §7): T2 PASS ∧
smoke PASS — OBA SPEŁNIONE.** Dalej: **ANEKS_DET-3** (werdykt smoke; zwolnienie
KAMPANII C: 12 rund × {B, V2}, blok 1). STOP.
