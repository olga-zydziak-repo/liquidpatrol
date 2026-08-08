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
@20 Hz, N<COM_OF_LOSS_T)** ⇒ streamer **MILKNIE** ⇒ natywny failsafe warstwy-0 w `COM_OF_LOSS_T`.
Zbrojony po bring_up (climb nie odświeża setpointu). Cel **podwójny**:
- **własność** „martwa osłona ⇒ bezpieczne przejęcie warstwy-0" jest teraz **WYMUSZONA kodem**;
- **timing** wraca do okna: deadman-silence (~0.3 s) + COM_OF_LOSS_T (~1.0 s) ≈ **1.3 s ∈ 0.9–1.5 s**.

**Dowód własności (deterministyczny, bez SITL):** `r02/test_deadman.py` — realna metoda `_streamer`
na atrapie: osłona ŻYWA ⇒ 21 publikacji ciągłych, **brak** fałszywego tripu; osłona MARTWA ⇒ stream
cichnie w **0.25 s**, `deadman_tripped=True`, **zero** publikacji po progu. **PASS.**

**Re-certyfikacja (zmiana w egzekutorze):**
- Założenie **żywotności osłony** zapisane **WPROST** w P1 (`verify.py`) i P2 (`geofence.py`) jako
  warunek **egzekwowany kodem** (treść dowodowa bez zmian).
- **P1/P2/P2_vmax3p1** zregenerowane — z3 **PROVED** (7/6 zobowiązań unsat).
- **P5 konformancja od nowa** — **0 rozbieżności** tau≡shield (400 los + 10 celowanych), pokrycie 7/7,
  cert **bajt-identyczny** → dead-man w egzekutorze **NIE** zmienił automatu osłony.
- **certs_selfcheck: PASS 5/5.**

**Pozostaje: live G5 timing (oba warianty) — ZABLOKOWANE zasobem zewnętrznym.** GPU trzymane 99%
przez **niezwiązaną sesję fabryka** (`train_epoch1.py`, pid 68380). G5 mierzy timing failsafe do
rozdzielczości 0.6 s okna — pod 100% GPU-contention gz-render dałby pomiar kontencji, nie
dead-mana+COM_OF_LOSS_T. **Nie kontuję** (dyscyplina — jak wcześniejszy „latający sweep zablokowany
brakiem yaw"). Uruchomię `SCENARIO=G5 G5_CUT=zombie` i `G5_CUT=stream` **po zwolnieniu GPU**;
oczekiwany `nav_reaction_s` ≈ 1.3 s (w oknie), `deadman_tripped=True`, `stream_kept_publishing`
plateau po tripie. Instrument i fix **gotowe i zacommitowane** (9f41171) — brakuje tylko pojedynczego
pomiaru na żywym symie.

---

## Werdykt zbiorczy R0.2

| Front | Stan |
|---|---|
| Certy formalne (P1/P2/P4/P5, selfcheck 5/5, +założenie żywotności) | **PASS** |
| Logika bramki G1–G4 (harness na prawdziwym kodzie) | **PASS 4/4** |
| Teza architektury GT-fed (G2/G3/G4 + nieregularność 5 seedów) | **PASS** |
| G5 — dead-man (własność + re-cert + dowód determ.) | **PASS**; live timing **pending GPU** |
| Tor żywy (live-fed) — percepcja | **OTWARTY** (przyczyna: kadrowanie §II; tor C wyceniony) |

**STOP.** Push robi Olga. Tor C (PRE detection uplift) startuje po tym raporcie.
