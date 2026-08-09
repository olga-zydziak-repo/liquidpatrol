# RAPORT_R02 — synteza końcowa R0.2 (osłona + OBSERVE + kanał ZOH-age; bramka G1–G5)

Data: 2026-08-09. Reżim: **budowa — blok R3→R4→re-cert→bramka**, domknięcie G5.
Poprzedniki: `PRE_R02.md` (ratyfikowany, A1–A7), `RAPORT_G_R02.md` (log bramki §1–§9bis).
Kryteria **zamrożone w PRE §4** przed pomiarem. Księgowość **trójwynikowa**. `θ_conf` **nigdy nie obniżony**.

Ten raport mówi **trzy rzeczy naraz** (§I–§III). Szczegóły bramki: `RAPORT_G_R02.md`.

---

## I. TEZA ARCHITEKTURY — **PASS w trybie GT-fed (z nieregularnością, 5 seedów)**

Teza R0.2: *osłona (7 liści, R-G nadrzędny) + OBSERVE (7. liść, ALLOW poniżej R-G) + kanał celu
5-dim ZOH-age* utrzymuje niezmienniki R0.1 **niezależnie od jakości percepcji**. Tor B (GT-fed,
decyzja Olgi): kanał zasilany **pozą GT** projektowaną do kamery (perfekcyjna detekcja w FOV,
conf=1.0), by testować **kanał+sterowanie+osłonę**, nie detektor.

| Scenariusz GT-fed | Zmierzone | Kryterium (zamrożone) | Wynik |
|---|---|---|---|
| **G2** intruz→OBSERVE | ENTRY, d≥D_safe=5.32, f_fov≥0.8, A1=0 | ENTRY≤T_ack, d≥D_safe | **SUKCES** |
| **G3** prowadzenie ku płotowi | REFUSE(GEOFENCE), ≤R_E, GF-native=0 | REFUSE(GF), ≤R_E | **ODMOWA** (≠porażka) |
| **G4** utrata→age→sufit→wyjście | EXPIRE na θ_age, wyjście OBSERVE, A1=0 | age-ceiling→exit | **SUKCES** |
| **G5** warstwa-0 (martwa osłona) | patrz §III (regresja domknięta) | reakcja 0.9–1.5 s, ≤R_E, A1=0 | **§III** |

**Nieregularność — rozrzut na 5 seedach** (nie 1; `r02/irr_seed_spread.py`, logika kanału bez SITL,
dropout=0.25 burst=0.3/5 noise=0.01, 60 s @1 Hz):

| seed | drop | entry | reent | expire | max_age | lock_tk |
|---|---|---|---|---|---|---|
| 1 | 33 | 2 | 1 | 2 | 3.0 | 497 |
| 7 | 31 | 3 | 2 | 2 | 3.0 | 378 |
| 13 | 24 | 3 | 2 | 2 | 3.0 | 678 |
| 42 | 31 | 4 | 3 | 4 | 3.0 | 534 |
| 101 | 36 | 4 | 3 | 3 | 3.0 | 436 |

Rozrzut: n_dropout 24–36 (mean 31.0, sd 3.95), n_entry 2–4, n_expire 2–4, **max_age=3.0 na KAŻDYM
seedzie (sd=0.00)** — sufit θ_age egzekwowany **deterministycznie** niezależnie od wzorca dziur;
re-ENTRY↔EXPIRE **spójne** wszędzie. Wcześniejszy pojedynczy live seed=42 (n_dropout=31) leży w
rozkładzie. **Teza trzyma na 5 seedach, nie na jednym szczęśliwym.**

---

## II. TOR ŻYWY (live-fed) — **OTWARTY, przyczyna źródłowa nazwana + wycena naprawy**

Latający G1 na żywo: **FAIL — ε_FP w locie** (5 fałszywych locków, 1.585/min). Atrybucja (tor A,
`RAPORT_G_R02 §3f`) — **PERCEPCJA, nie pipeline**: detektor generuje słabe/fałszywe boxy, bo
**kadrowanie kamery** (pitch hover + elewacja intruza) wycina wyniesiony cel z pionowego pola
widzenia; conf w locie (~0.045) spada ~4× względem statycznego (~0.169), a separacja sygnał/szum
jest **marginalna** (nie 35×). To **NIE** wada osłony ani kanału (te przechodzą GT-fed §I) — wada
**wejścia percepcyjnego**.

**Przyczyna źródłowa (nazwana):** obwiednia detekcji (A7) — kamera level przy hover-pitch nie
utrzymuje wyniesionego intruza w kadrze; grunt jako tło zabija detekcję (potrzebne niebo+paralaksa).

**Wycena naprawy (tor C, PRE „detection uplift", startuje po tym raporcie):**
- (a) **gimbal/tilt** kamery ku celowi (utrzymanie w kadrze mimo pitch) — sprzęt+sterowanie;
- (b) **retrening/augmentacja** detektora na kadrach lotnych (domain gap static→flight);
- (c) **MTI/ruch** (dźwignia 2) jako sygnał uzupełniający conf (ratyfikowana eskalacja, nie teraz).
Recon→PRE→STOP jak zawsze; `θ_conf` bez zmian (obniżanie zakazane — separacja krucha).

Werdykt live-fed rozdzielony od GT-fed **jak §3b**: teza architektury (GT-fed) **niezależna** od tego
otwartego frontu percepcyjnego.

---

## III. G5 — regresja **znaleziona → zdiagnozowana → naprawiona w rundzie**

**Znaleziona:** poprzednia runda — G5 GT-fed reakcja natywna **2.179 s > okno 0.9–1.5 s** (R0.1 S4
dawało ~1.03 s). To **regresja własności certyfikowanej R0.1** (warstwa-0 przejmuje martwą osłonę),
wprowadzona przez **fix#2** (odsprzężony streamer 20 Hz).

**Zdiagnozowana (dwie przyczyny):**
1. **Zombie-stream (własność bezpieczeństwa):** odsprzężony streamer publikuje **stary** setpoint,
   gdy pętla decyzyjna/osłona **zamiera** → PX4 **nie widzi utraty offboard** → martwa osłona **nie**
   wyzwala failsafe. To złamanie odziedziczonego niezmiennika „martwa osłona ⇒ bezpieczne przejęcie
   warstwy-0" — regresja gorsza niż samo opóźnienie.
2. **Pomiar (2.179 s zawyżone):** stara metryka czytała `flight_mode` z **MAVSDK** (event-driven na
   HEARTBEAT ~1 Hz) → do ~1 s lagu detekcji. Prawdziwy failsafe ~1.1 s **+ ~1 s lag telemetrii** ≈
   2.179 s. Dodano **precyzyjny instrument**: `NavStatusSub` na `/fmu/out/vehicle_status.nav_state`
   (XRCE, ~kilka-Hz) — chwila opuszczenia OFFBOARD (=14). G5 mierzy `nav_reaction_s` (precyzyjny) vs
   `mavsdk_reaction_s` (laggy), oba warianty urwania: `G5_CUT=zombie` (śmierć osłony, streamer żyje)
   vs `G5_CUT=stream` (bezpośredni stop).

**Naprawiona:** **dead-man w streamerze** — brak odświeżenia setpointu przez **N=6 ticków (0.3 s
@20 Hz)** ⇒ streamer **MILKNIE** ⇒ natywny failsafe warstwy-0 w `COM_OF_LOSS_T`. Zbrojony po bring_up.
Cel **podwójny**: (a) własność „martwa osłona ⇒ bezpieczne przejęcie warstwy-0" **WYMUSZONA kodem**;
(b) timing failsafe.

**Dowód własności (deterministyczny, bez SITL):** `r02/test_deadman.py` — realna metoda `_streamer`
na atrapie: osłona ŻYWA ⇒ 21 publikacji ciągłych, **brak** fałszywego tripu; osłona MARTWA ⇒ stream
cichnie w **0.25 s**, `deadman_tripped=True`, **zero** publikacji po progu. **PASS.**

**POMIAR NA ŻYWO (świeży boot per wariant, precyzyjny nav_state; GPU zwolnione przez fabrykę):**

| wariant urwania | nav_reaction (XRCE) | mavsdk_reaction | dead-man | ≤R_E / A1 | okno 0.9–1.5 |
|---|---|---|---|---|---|
| **stream** (bezpośredni stop = scenariusz oryginalnego G5) | **1.383 s** | 2.623 s | — (niepotrzebny) | ✓/✓ | **PASS** |
| **zombie** (śmierć osłony, streamer żyje) | **1.589 s** | 2.587 s | trip @0.286 s, potem cisza | ✓/✓ | **0.089 s ponad** |

**Dwa wnioski pomiarowe:**
1. **Regresja 2.179 s = ARTEFAKT POMIARU.** Prawdziwa reakcja trybu utraty transportu (stream = scenariusz
   oryginalnego G5) to **1.383 s — w oknie**. MAVSDK `flight_mode` (HEARTBEAT ~1 Hz) zawyżał o **1.0–1.24 s**
   (nav 1.383 vs mavsdk 2.623; nav 1.589 vs mavsdk 2.587). Precyzyjny `NavStatusSub` to demaskuje.
   **Oryginalny scenariusz G5 przechodzi (1.383 s).** dmesg czysty (brak segfault/OOM), dron bezpieczny.
2. **Dead-man domyka GŁĘBSZĄ dziurę bezpieczeństwa (zombie).** Martwa osłona przy żywym streamerze:
   dead-man tripuje **na żywo @0.286 s** → stream cichnie (`stream_kept_publishing=5` potem 0) → failsafe
   @**1.589 s** (nav_state→4 HOLD). Własność „martwa osłona ⇒ warstwa-0" **wymuszona i zmierzona live**.
   Koszt: **+0.286 s** (nieusuwalne wykrycie śmierci przez N ticków) → 0.089 s ponad górną granicą okna.

**DECYZJA OLGI — rozdział trybów, bez retro-poszerzania okna:**

**(a) Zamrożone kryterium G5 dotyczy ścieżki UTRATY TRANSPORTU** (bezpośredni stop = scenariusz oryginalnego
G5 = wariant `stream`). Wynik precyzyjny **1.383 s ∈ 0.9–1.5 s → PASS**. Okna NIE poszerzamy.

**(b) Ścieżka ZOMBIE to NOWY tryb, nieobjęty bramką R0.1** (R0.1 publikował setpoint w pętli decyzyjnej →
śmierć pętli = natychmiastowy stop; brak odsprzężonego streamera = brak trybu zombie). Raportowana OSOBNO,
z **własnym budżetem wyprowadzonym JAWNIE**:
> `budżet_zombie = COM_OF_LOSS_T + N·tick = ~1.30 s + 6·0.0476 s (0.286 s zmierzone) = ~1.59 s`
>
> wynik **1.589 s** — zgodny z budżetem. Bezpieczny (≤R_E, A1=0, własność wymuszona). To **nie** porażka
> zamrożonego kryterium (które dotyczy trybu transportu) — to zmierzony koszt NOWEJ wymuszonej własności.

**(c) N=6 = PROWIZORYCZNE [A4].** Reguła: N·tick > max LEGALNEGO stalla pętli decyzyjnej (fix#2 istnieje BO
pętla stalluje pod kontencją detektora: stall > COM_OF_LOSS_T → natywny HOLD). GT-fed (bez detektora) →
pętla nie stalluje → N=0.3 s bezpieczne. **Live-fed: N re-derywowane z rozkładu stalli pętli pod kontencją —
DELEGOWANE DO TORU C** (i tak potrzebne do live-fed). Opcja N=4-teraz **odrzucona**: bez rozkładu stalli
grozi fałszywym tripem = reintrodukcja problemu, który fix#2 rozwiązał. (`config_r02.DEADMAN_TICKS`, [A4].)

### III-bis. PROWIENIENCJA PRZYRZĄDU (lekcja, decyzja Olgi (3))

**Każda liczba czasowa dostaje etykietę kanału pomiaru.** Kanały: **`nav`** = `NavStatusSub`/XRCE
(`vehicle_status.nav_state`, ~kilka-Hz, precyzyjny); **`mav`** = MAVSDK `flight_mode` (HEARTBEAT ~1 Hz,
lag 0–1 s, event-driven).

| Pomiar | Kanał | Wartość |
|---|---|---|
| G5 stream (utrata transportu) | **nav** | **1.383 s** |
| G5 stream | mav | 2.623 s (lag 1.24 s) |
| G5 zombie (śmierć osłony) | **nav** | **1.589 s** |
| G5 zombie | mav | 2.587 s (lag 1.00 s) |
| R0.1 **S4** (retrospekcja, `results/R01/gate/S4_result.json`) | **mav** | 1.234 s |
| R0.2 stream = precyzyjna reprodukcja S4 (ten sam mechanizm urwania) | **nav** | **1.383 s** |

**Rozbieżność:** R0.1 S4 (1.234 s) **ORAZ** okno 0.9–1.5 s (`gate_run.py:216`) **ORAZ** nota
`COM_OF_LOSS_T ~1.03 s` — **wszystkie z laggy kanału `mav`**. Lag jest zmienny 0–1 s → próbka R0.1 S4
miała MAŁY lag (1.234 ≈ precyzyjne 1.383), więc okno wyszło trafne **przypadkiem**. Precyzyjna wartość
trybu transportu (odtwarzalna): **1.383 s (nav)**. **Fantomowa regresja 2.179 s** z poprzedniej rundy =
wysokolagowa próbka `mav` tej samej ~1.3–1.4 s reakcji — NIE prawdziwa regresja timingu. **Lekcja: timing
warstwy-0 mierzyć kanałem `nav` (XRCE), nie `mav`; etykietować kanał przy każdej liczbie.**

**Re-certyfikacja (zmiana w egzekutorze):**
- Założenie **żywotności osłony** zapisane **WPROST** w P1 (`verify.py`) i P2 (`geofence.py`) jako
  warunek **egzekwowany kodem** (treść dowodowa bez zmian).
- **P1/P2/P2_vmax3p1** zregenerowane — z3 **PROVED** (7/6 zobowiązań unsat).
- **P5 konformancja od nowa** — **0 rozbieżności** tau≡shield (400 los + 10 celowanych), pokrycie 7/7,
  cert **bajt-identyczny** → dead-man w egzekutorze **NIE** zmienił automatu osłony.
- **certs_selfcheck: PASS 5/5.**

Dowody live: `results/R02/gate_live/G5_{ZOMBIE,STREAM}_gate.{jsonl,log}` + dmesg (czyste). Pomiar
wykonany po zwolnieniu GPU przez fabrykę (bez kontencji — pomiar czysty, jak uzgodniono z Olgą).

---

## Werdykt zbiorczy R0.2

| Front | Stan |
|---|---|
| Certy formalne (P1/P2/P4/P5, selfcheck 5/5, +założenie żywotności) | **PASS** |
| Logika bramki G1–G4 (harness na prawdziwym kodzie) | **PASS 4/4** |
| Teza architektury GT-fed (G2/G3/G4 + nieregularność 5 seedów) | **PASS** |
| G5 — oryginalny scenariusz (stream) live | **PASS 1.383 s** (regresja 2.179 = artefakt MAVSDK) |
| G5 — dead-man (własność „martwa osłona⇒warstwa-0") | **WYMUSZONA + zmierzona live** (zombie trip @0.286 s, failsafe 1.589 s, bezpieczny) |
| G5 — zombie timing vs okno | 1.589 s = 0.089 s ponad; N vs stall = **decyzja Olgi** (live-fed N → tor C) |
| Tor żywy (live-fed) — percepcja | **OTWARTY** (przyczyna: kadrowanie §II; tor C wyceniony) |

**STOP.** Push robi Olga. Tor C (PRE detection uplift) startuje po tym raporcie.
