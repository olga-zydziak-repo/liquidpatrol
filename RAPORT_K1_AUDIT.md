# RAPORT_K1_AUDIT — audyt biegu „AUTO.LAND ucieka 42 m pod utratą GNSS"

Data: 2026-08-22. Autor: CC. Tryb: PROMPT_K1_AUDIT (diagnostyczny, read-only).
Bazuje na commicie `6836b70` (część A: normalizacja ramek, spłata Z2). Zero biegów dowodowych.
Reguła 0.4: każda liczba ma źródło; liczby z pamięci oznaczone „(pamięć — sprawdzone)" po weryfikacji.

---

## §1. Inwentarz PRZED interpretacją (reguła D0)

### 1a. Źródło liczby „42 m" — to ASERCJA, nie zachowany ślad

`grep` całego drzewa po „42 + land/flyaway/ucieka" daje **dokładnie dwa** trafienia dla figury 42 m:

1. **`results/R03/recon/B1bis/instrument/FINDING_clock_and_regime.md:97`** (§4, znalezisko 1, data 2026-08-09):
   > „AUTO.LAND (`d.action.land`) UCIEKA pod DR = 42 m (pętla POZYCYJNA station-keeping goni dryfującą
   > estymatę). Zasada: pod degradacją estymatora tylko akcje OTWARTO-PĘTLOWE wzgl. degradowanej wielkości."
2. **`results/R03/recon/B1bis/b1bis_fly.py:118`** (komentarz uzasadniający wybór projektowy):
   > „# NIE d.action.land() (AUTO.LAND = position-hold → flyaway 42 m pod DR). Profil DWUFAZOWY: …"

**Obie to WYPOWIEDZI o biegu, nie sam bieg.** Liczba 42 nie występuje w żadnym zachowanym trace jako
policzona wartość trajektorii, ani w żadnym logu pomiarowym, ani w `DIAG/`. Kod `b1bis_fly.py`
(zachowana wersja) **nigdy nie wywołuje `d.action.land()`** — celowo, właśnie dlatego, że wersja
wcześniejsza tak robiła i uciekała. **Wariant `action.land`, który dał 42 m, NIE jest zachowany**
(brak kodu, brak trace, brak ulog). Figura 42 m jest zatem asercją pochodną z okresu 08-09,
bez zachowanego dowodu pierwotnego.

### 1b. Co JEST zachowane (i czego brak)

| artefakt | data | pola | ma trajektorię? | ma nav_state? | znaczenie |
|---|---|---|---|---|---|
| `B1bis/flights/f{1..5}_*.jsonl` | 08-09 | mono,sim,t,x,y,z | tak (max radial **38.1 m** f5_corner) | **nie** | loty które UNIKAŁY `action.land` (ścieżka `refuse_land`, zejście prędkościowe) |
| `B1bis/episode/*.jsonl` | 08-09/10 | mono,sim,t,x,y,z | tak (max radial **31.1 m** f4) | **nie** | epizod dwufazowy §3quater |
| `B1_drift/b1_flight{1,2}.jsonl` | 08-09 | t,x,y,eph,mono,xy_valid,dead_reckoning | tak | **nie** (ma xy_valid) | dryf EKF, nie ucieczka land |
| `R2_denial_ekf_ground.jsonl` | (recon) | nav_state,arming_state,dead_reckoning,xy_valid,v_xy_valid,eph,failsafe,local_position_invalid[_relaxed],global_position_invalid,fix_type | **NIE** (brak x/y) | **tak** (=4) | denial NA ZIEMI/rozbrojony — kaskada flag, bez lotu |

- **Maks. radialny w JAKIMKOLWIEK zachowanym śladzie = 38.1 m** (`f5_corner`, lot z zejściem
  prędkościowym, NIE `action.land`) — czyli nie jest to bieg 42 m.
- Jedyny zachowany artefakt z `nav_state` (`R2_denial_ekf_ground.jsonl`) jest **naziemny/rozbrojony**
  (`arming_state=1`, brak współrzędnych x/y) → dokumentuje kaskadę flag EKF pod denialiem, ale
  **nie może pokazać ucieczki poziomej w locie**.

### 1c. ulog — brak dla biegu 42 m

Zachowane katalogi ulog: `PX4-Autopilot/build/px4_sitl_default/rootfs/log/2026-08-{15,16,17,18,19,20,21}/`.
Kampania B1-bis (źródło asercji 42 m) jest z **2026-08-09/10** — **przed** najwcześniejszym zachowanym
katalogiem ulog (08-15). **Żaden ulog z bootu 42 m nie przetrwał.**

**Wniosek D0:** bieg 42 m nie ma zachowanego ani trace (z nav_state), ani ulog. To ustawia warunek §B5.

---

## §2. Rekonstrukcja osi czasu — co MOŻNA zrekonstruować

Trajektorii 42 m zrekonstruować się NIE da (brak śladu). Rekonstruowalna jest **kaskada flag EKF pod
`EKF2_GPS_CTRL=0`** z jedynego bogatego artefaktu `R2_denial_ekf_ground.jsonl` (oś: `mono`, przyrząd
lokalny; t0 = pierwsza próbka). To oś NAZIEMNA/rozbrojona — pokazuje reakcję estymatora, nie lot.

| dt [s] | zdarzenie (cytat pola) |
|---|---|
| 0.08 | stan zdrowy: `dead_reckoning=False`, `xy_valid=True`, `v_xy_valid=True`, `eph=0.152` |
| **7.68** | `dead_reckoning=False→True`; `eph 0.152→14.15` — **fuzja GNSS ustała, EKF wchodzi w dead-reckoning** |
| **11.68** | `xy_valid=True→False`, `v_xy_valid=True→False` (~4 s po DR); `eph` spada do 0.0133 (raport wewn., niewiarygodny — por. pamięć „eph niewiarygodne pod denialiem") |
| 46.68 | restore: `dead_reckoning→False`, `xy_valid→True`, `eph=1.8` (rekonwergencja) |
| całość | `nav_state=4` (AUTO_LOITER, standard PX4), `arming_state=1`, `failsafe=False` — bez zmian |

**Zmierzone (cytowalne) opóźnienia kaskady:** injekcja→`dead_reckoning` ≈ 7.6 s; →`xy_valid=False`
dalsze ≈ 4.0 s. **Brak** w tym śladzie: komendy LAND, acku, sekwencji nav_state DESCEND, ruchu poziomego.

---

## §3. Werdykt

**WERDYKT: NIEROZSTRZYGNIĘTE (SR-K6).** Brak jakiegokolwiek cytatu z logu trajektorii biegu 42 m
(brak trace z nav_state, brak ulog). Zgodnie z SR-K6 („werdykt bez cytatu z logu = nierozstrzygnięte")
mechanizmu ucieczki 42 m nie da się rozstrzygnąć z zachowanych artefaktów.

Dwa konkurencyjne, mechanistycznie spójne odczyty — obu artefakty NIE rozstrzygają:

- **Odczyt FINDING (zachowany, autor 08-09):** AUTO.LAND = pętla POZYCYJNA station-keeping goniąca
  DRYFUJĄCĄ estymatę → prawdziwa pozycja ucieka, bo kontroler trzyma się skorumpowanego setpointu.
  (zamknięto-pętlowy wzgl. zdegradowanej wielkości).
- **Predykcja prerejestrowana CC (b):** timeout odpalił, 42 m narosło w DESCEND (blind land coasting) —
  otwarto-pętlowy dryf podczas ślepego zejścia, bez korekcji poziomej.

Różnica rozstrzygalna WYŁĄCZNIE w ulog (czy AUTO.LAND wystawia poziome setpointy prędkości/pozycji —
odczyt FINDING — czy zeruje je, a dryfuje pozycja prawdziwa — odczyt b). **Ulog nie istnieje → nie
rozstrzygam.** Nie dopasowuję danych do predykcji (0.5): odnotowuję, że predykcja CC (b) i zachowana
asercja FINDING to RÓŻNE mechanizmy, i że artefakty nie faworyzują żadnego.

Jedyny człon rozstrzygnięty z cytatem (patrz §4b): `EKF2_GPS_CTRL=0` faktycznie wprowadza EKF w
dead-reckoning i unieważnia `xy_valid` — czyli warunek WEJŚCIOWY ucieczki (zdegradowana estymata
pozycji) jest potwierdzony; sam MECHANIZM ucieczki — nie.

---

## §4. Punkty B4

### 4a. Zakres COM_POS_FS_EPH / COM_POS_LOW_ACT — tylko AUTO_MISSION/AUTO_LOITER

Cytat źródła PX4 `src/modules/commander/failsafe/failsafe.cpp:532-536`:
```
// trigger Low Position Accuracy Failsafe (only in auto mission and auto loiter)
if (state.user_intended_mode == NAVIGATION_STATE_AUTO_MISSION ||
    state.user_intended_mode == NAVIGATION_STATE_AUTO_LOITER) {
    CHECK_FAILSAFE(status_flags, local_position_accuracy_low, fromPosLowActParam(_param_com_pos_low_act.get()));
}
```
**Potwierdzone:** failsafe niskiej dokładności pozycji (`COM_POS_LOW_ACT`, flaga `local_position_accuracy_low`;
próg EPH przez `COM_POS_FS_EPH`) jest zakresowany **wyłącznie** do AUTO_MISSION i AUTO_LOITER —
**NIE** do OFFBOARD ani do AUTO_LAND. Implikacja dla audytu: jeśli bieg 42 m był już w AUTO.LAND
(albo w OFFBOARD), ten konkretny failsafe **nie interweniuje** — nie może „zatrzymać" ucieczki.
Dodatkowo `:538-546`: `navigator_failure` → `Action::Land` tylko w AUTO_TAKEOFF/AUTO_RTL, inaczej
`Action::Hold`.

### 4b. Czy `EKF2_GPS_CTRL=0` ≡ utrata danych GNSS dla flag EKF? — TAK

Cytat `R2_denial_ekf_ground.jsonl` (§2): pod `EKF2_GPS_CTRL=0` `dead_reckoning` przechodzi False→True
(dt=7.68), a `xy_valid`/`v_xy_valid` True→False (dt=11.68). **Potwierdzone:** wymuszenie `EKF2_GPS_CTRL=0`
wprowadza estymator w ten sam stan dead-reckoning / nieważnej pozycji poziomej, co utrata danych GNSS —
więc jako iniekcja awarii dla ŚCIEŻKI FLAG jest wierne. (Zastrzeżenie: `eph` raportowane pod denialiem
jest niewiarygodne — spada do 0.013 zamiast rosnąć — więc próg na `eph` per se nie jest tu miarodajny;
liczy się flaga `dead_reckoning`/`xy_valid`.)

---

## §5. Rekomendacja roszczenia + status §B5

### 5a. Status figury „42 m" w roszczeniu K1

Figura **„42 m ucieczki AUTO.LAND"** jest obecnie **asercją pochodną bez zachowanego dowodu pierwotnego**
(brak trace 42 m, brak ulog; źródło = nota FINDING + komentarz kodu z 08-09). **Rekomendacja:** do czasu
świeżego, oprzyrządowanego pomiaru NIE cytować „42 m" jako zmierzonej liczby w roszczeniu kontrastowym
K1. Można uczciwie powiedzieć: „natywny AUTO.LAND pod utratą GNSS ucieka poziomo (rząd dziesiątek metrów;
w zachowanych śladach zejścia prędkościowego, unikających `action.land`, radial sięga 38.1 m), podczas
gdy osłona REFUSE→zejście domyka touchdown w R_E" — z jawnym oznaczeniem, że dokładna figura 42 m nie ma
zachowanego dowodu.

### 5b. §B5 — warunek SPEŁNIONY, ale SR-K5 blokuje bieg PORÓWNYWALNY

- **Warunek §B5 spełniony:** dla biegu 42 m nie ma ulog ANI śladu z nav_state+xy_valid → §B5 dopuszcza
  jeden bieg diagnostyczny.
- **ALE SR-K5 nie do spełnienia jako reprodukcja:** konfiguracja biegu 42 m (wariant `action.land`) NIE
  jest zachowana (brak kodu/paramów/altitude/velocity-w-chwili-land/czasu-DR). Każdy bieg diagnostyczny
  byłby REKONSTRUKCJĄ o nieznanych deltach względem oryginału → SR-K5 („jakakolwiek zmiana param/profilu
  vs bieg 42 m → nieporównywalne") czyni „reprodukcję 42 m" niemożliwą do zagwarantowania.

**Decyzja CC (bez firing biegu w tej turze):** NIE odpalam biegu diagnostycznego jako „reprodukcji 42 m"
(byłby nieporównywalny per SR-K5, a figura 42 m jako baseline nie przetrwała). Zamiast tego rekomenduję —
do RATYFIKACJI Olgi jako osobny krok — **świeżą, oprzyrządowaną (ulog ON) CHARAKTERYZACJĘ** natywnego
AUTO.LAND pod denialiem, jawnie oznaczoną jako NOWY pomiar (nie odtworzenie 42 m), z:
- pełnym ulog (nav_state, xy_valid, failsafe_flags, vehicle_command+ack, estimator_status_flags),
- jednym zamrożonym profilem (alt/velocity/settle/DENIAL_S) zapisanym PRZED biegiem jako baseline K1,
- pomiarem: czy AUTO.LAND wystawia poziome setpointy (odczyt FINDING) vs zeruje je przy dryfie pozycji
  prawdziwej (odczyt b) — to rozstrzyga §3.

To odblokowuje uczciwy kontrast K1 (osłona vs natywny failsafe) na ŚWIEŻYM baseline zamiast na
niezachowanej liczbie.

---

## Podsumowanie (jedno zdanie)

Bieg „42 m" nie ma zachowanego dowodu pierwotnego (asercja z 08-09, brak trace/ulog); kaskada flag EKF
pod denialiem jest potwierdzona (dead_reckoning@7.68 s, xy_valid=False@11.68 s), zakres COM_POS_LOW_ACT
= tylko AUTO_MISSION/LOITER (cytat PX4 :532); mechanizm ucieczki NIEROZSTRZYGNIĘTY (SR-K6) — rekomendacja:
świeża oprzyrządowana charakteryzacja jako baseline K1, do ratyfikacji.
