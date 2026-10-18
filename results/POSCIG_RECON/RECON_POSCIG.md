# RECON_POSCIG — recon pozycji POŚCIG-V1 (deficyt pościgu za celem szybkim) — STOP-POSCIGR

CC · 18.10.2026 · wykonanie PROMPT_POSCIG_S0. **Zero bootów, zero SITL, zero treningu,
zero edycji istniejących plików**; narzędzia NOWE w `results/POSCIG_RECON/tools/`
(poscig_index / poscig_recon / poscig_artefakt / poscig_sweep / poscig_r3), dane
WYŁĄCZNIE z istniejących artefaktów (FANTOM S2, AKW S3, ławka blok1+2, manifest ławki).
Czeka decyzja CC: aneks zamykający ALBO PRE_POSCIG (numerowany).

**WYNIK GŁÓWNY (uprzedzając szczegóły, bo przebudowuje pozycję):**

1. **Sufitu kinematycznego NIE MA** — idealny pościgowiec w kopercie komendy
   (|v|≤V_MAX=3.0) domyka D6 w **13/13** epizodach zbioru odniesienia startując od t0
   i w **7/13 od chwili realnej akwizycji**; 6 niewykonalnych-od-akwizycji to wyłącznie
   epizody z akwizycją 19.5–31.2 s (okno sędziego spalone na ślepo). Prowadzenie
   z wyprzedzeniem (intercept) nie zmienia ŻADNEGO werdyktu względem ogona —
   przy stosunku prędkości 3:1 prowadzenie nie jest wąskim gardłem. Zamknięcie
   rachunkiem jako „sufit scenariusza" **nie zachodzi**.
2. **ZNALEZISKO PRZYRZĄDU (werdykto-nośne, poza-prompt, dowód §R2a): tranzient
   teleportu na starcie epizodu zanieczyszcza d_min zamrożonego sędziego.** Pierwsze
   1–2 próbki `gt_intruder.jsonl` epizodu (t_rel 0.04–0.14 s) niosą pozę intruza
   SPRZED teleportu bramki startu (do 29.97 m od komendy), sędzia liczy na nich
   i na interpolacji przez skok d_min ⇒ fikcyjne `d_dmin`. Po odfiltrowaniu
   (|ned−cmd_ned|>1 m): **3/11 porażek V2 zbioru to artefakt (w tym porażka N6
   c05_s02), oba B-FAILe FANTOM S2 i oba AKW S3 to artefakt (wyrocznia realnie NIE
   pada), 6/6 porażek NAUCZYCIELA ławki to artefakt** (klasa „proximity wejścia"
   z RAPORT_KAMPANIA_BLOK1 nie istnieje w realnej geometrii; nauczyciel realnie
   120/120, w tym 40/40 na v=1.0).
3. **Mechanizm „deficyt pościgu" ROZPUSZCZA SIĘ w danych:** V2-11 = 3 artefakty
   przyrządu + 6 ślepych najazdów przy późnej akwizycji (klasa AKWIZYCJA-TRANSIT,
   nie pościg; d_min pada w fazie `hold` 11.9–16.3 s, PRZED akwizycją) + **2 realne
   porażki zachowania przy żywym tracku — oba czyste `c_sweep` i oba near-miss**
   (558.7°/630° i 551.3°/630°; frac i d_min OK). Rekomendacja: **wariant (a′)
   — aneks zamykający pozycję rozpuszczeniem mechanizmu + ERRATUM-DMIN** (0 bootów);
   szczegóły i uczciwe alternatywy w §R4/§R6.

## §0. Bramka wejścia — PASS

`git fetch` → origin/master zawiera **d31d1007 (CO-FANTOM)** ✓ · `origin/master..HEAD`
puste ✓ · porcelain pełny pusty ✓. FROZEN wykonaniem: **piny 5/5** (k1_shield_pins:
SHIELD FROZEN True; shield 1c584964 · config 4c440e42 · gate_run 5647ae20 · base
7fc45cf2 · safe_descend e3c1040b) · **certy 9/9** (certs_selfcheck PASS). Sha
przeliczone i ZGODNE z FREEZE_FANTOM/FREEZE_AKW/FREEZE_DET: fantom_scan **e435ed7e** ·
rejestr kontrolerów **87203d29** · akw_scan **b94cdeae** · bench_flight `05137098` ·
bench_judge `8ec0fcfb` · feed_vision `acc81df7` · det_v2.pt `775ead15` · ncp
`0337d5ea` · percep_proc `38a3a765` · feed_vision_proc `79633489` · feed_registry
`ee1481f9` · net_controller `e8c1b658`.
**Kolizja nazwy „POSCIG": BRAK w kodzie/env/katalogach** (grep plików .py/.sh/.yaml/.json
poza results: zero; `results/`: zero katalogów). Wzmianki wyłącznie dokumentowe
(ANEKS_REAKW-1, ANEKS_FANTOM-2, RAPORT_FANTOM*, KIERUNKI_PO_PLANIE — pozycja katalogu).
Rekomendacja: env **`POSCIG_*`**, katalog **`results/POSCIG/`**, kontroler (gdyby
powstał) `net_poscig` — rejestr additive jak net_akw/net_fantom.

## §Z. Zbiór odniesienia (zamknięty) — rozstrzygnięcie listy

- **V2-11** = 9 z FANTOM S2 (c05_s02, c08_s03, c08_s04, c09_s02, c10_s02, c10_s03,
  c11_s02, c11_s03, c11_s04) + **2 z AKW-ery: `c09_s03` i `c10_s01`** — ustalone
  z RECON_REAKW §R3 (tabela utrat): 5 porażek AKW S3 „bez utraty po akwizycji (czysty
  pościg)" = c09_s02, c09_s03, c10_s01, c10_s03, c11_s03; spoza dziewiątki FANTOM
  są dokładnie c09_s03 i c10_s01.
- **B-2** = FANTOM S2 B: c09_s03, c11_s02. (Analogiczne B-FAILe AKW S3: c09_s02,
  c11_s02 — dołączone do pomiaru artefaktu §R2a.)
- **Kontrola** = 5 par v=1.0 przechodzących na V2 w FANTOM S2 (z fantom_pairs
  i indeksu): c08_s02, c09_s03, c09_s04, c10_s01, c10_s04.

**Odchylenie jawne od litery promptu:** przesłanka „wszystkie z wczesną akwizycją
5.0–6.6 s" NIE potwierdza się pomiarem. 5.0–6.6 s to `t_entry_s` sędziego = GT-wejście
w pasmo [6,10] — w tych epizodach **pasywne** (cel transituje obok ślepego drona
w zawisie); realna akwizycja (pierwszy tick `track_valid` z trk ≤3 m od GT celu —
semantyka F1_cel; demo loguje surowy feed, więc lock fantomowy wykluczony bramą 3 m)
wynosi 4.9–10.7 s tylko w 5/11, a w 6/11 — **19.5–31.2 s**. Pełne liczby w tabeli R1;
wpływ na dekompozycję nazwany w §R2/§R4 (to zmienia obraz pozycji, stąd pomiar
zamiast przyjęcia przesłanki).

## §R1. Rachunek wykonalności z GT — serce

**Koperta i źródła:** V_MAX=3.0 m/s = clamp normy KOMENDY prędkości —
`r01/config.py:24`; sieć: głowa tanh×V_MAX + `clip_v` (`r03/controllers/
net_controller.py:97`, `r03/controllers/common.py:10-16`); egzekutor analogicznie
(`orbit_executor.py:48`); ławka podaje `vmax=V_MAX` (`bench/bench_flight.py:205,310`).
**ERRATUM_VMAX.md:** prędkość FAKTYCZNA GT przekracza setpoint w zakrętach (zmierzone
do 5.34; obwiednia V_env=6.0) — rachunek używa **3.0 (komendy)**, więc dla pytania
„czy koperta wystarcza" jest **konserwatywny**. **Sędzia (litera):**
`bench/bench_judge.py:121-127` — D6 = a∧b∧c∧d∧e: (a) t_entry≤25 s (pierwsze dh∈[6,10],
:97-101), (b) frac_band≥0.85 w oknie [t_entry, t_entry+70] (:109,123), (c) omiatanie
≥630° (:124), (d) d_min(3D)≥4 m (:96,125), (e) 0 REFUSE ∧ ¬breach; progi DEFAULTS
:21-23. **NIE modelowane (jawnie):** dynamika wewnętrzna PX4 (przyspieszenia, lag
śledzenia setpointu — obie strony), szum estymacji własnej/celu (kwantyfikacja →
§R5), wiatr (ławka bez wiatru), yaw. Punkt materialny integruje komendę idealnie
@20 Hz ⇒ wynik = GÓRNA granica zdolności.

**Metoda:** trajektoria intruza = manifest `results/BENCH/scenario_manifest.json`
poprzez `bench/scenarios.position_at` (ramka scenariusza = NED poziomo, z=−10;
`harness/intruder_motion.py:61-64`), zwalidowana per epizod vs `gt_intruder.jsonl`
(p50 niezgodności 0.036–0.08 m; maxy to tranzienty teleportu — §R2a). Idealny
pościgowiec: approach = V_MAX·wersor na cel (OGON) albo na punkt wyprzedzenia
(INTERCEPT, pełna informacja o prędkości celu, rozwiązanie kwadratowe), z hamowaniem
1.0·(d−8); orbita = pełny feed-forward prędkości celu + korekcja radialna (k=0.8,
clip 1.5) + styczna 10.5°/s z priorytetem pasma przy saturacji; ewazja radialna przy
d<5. Start: (a) od realnej akwizycji (prefix = REALNE GT drona [t0, t_acq] — okno
sędziego widzi prawdziwy ślepy początek), (b) od t0. Werdykt: `judge_episode`
(zamrożony sędzia) na pełnej serii. Dane: `r1_feasibility.json`.

| epizod (kampania) | v | t_acq [s] | real (frozen) | od akwizycji (ogon=int) | margines wejścia [s] | od t0 |
|---|---|---|---|---|---|---|
| c05_s02 (F) | 0.5 | 5.41 | FAIL d_dmin | **OK** | 17.95 | OK |
| c08_s03 (F) | 1.0 | 19.53 | FAIL b,c,d | FAIL c,d | 19.04 | OK |
| c08_s04 (F) | 1.0 | 26.18 | FAIL b,c,d | FAIL b,d | 18.91 | OK |
| c09_s02 (F) | 1.0 | 5.44 | FAIL d_dmin | **OK** | 18.86 | OK |
| c10_s02 (F) | 1.0 | 29.18 | FAIL b,c,d | FAIL b,c,d | 19.08 | OK |
| c10_s03 (F) | 1.0 | 10.69 | FAIL c_sweep | **OK** | 18.74 | OK |
| c11_s02 (F) | 1.0 | 31.16 | FAIL b,d | FAIL b,d | 18.89 | OK |
| c11_s03 (F) | 1.0 | 22.26 | FAIL b,d | FAIL b,d | 19.12 | OK |
| c11_s04 (F) | 1.0 | 25.10 | FAIL b,d | FAIL b,d | 19.10 | OK |
| c09_s03 (A) | 1.0 | 4.90 | FAIL c,d | **OK** | 19.17 | OK |
| c10_s01 (A) | 1.0 | 8.89 | FAIL c_sweep | **OK** | 18.88 | OK |
| **B** c09_s03 (F) | 1.0 | 0.10 | FAIL d_dmin | **OK** | 22.67 | OK |
| **B** c11_s02 (F) | 1.0 | 0.42 | FAIL d_dmin | **OK** | 22.35 | OK |

(F)=FANTOM S2, (A)=AKW S3; „ogon=int" — intercept nie zmienił żadnego werdyktu ani
istotnie marginesów (pełne liczby obu prowadzeń w JSON). Marginesy = 25 − t_entry
symulanta.

- **Od t0: 13/13 wykonalne** (oba prowadzenia) ⇒ **koperta komendy 3.0 m/s wystarcza
  na cel 1.0 m/s z zapasem**; w ustalonej orbicie wymagane |v| ≤ v_celu + ω·r ≈
  1.0 + 1.257 = 2.26 < 3.0. Kwantyfikacja (a)−(b): całe nie-artefaktowe rezyduum
  kupuje samo OPÓŹNIENIE AKWIZYCJI, nie pościg.
- **Od realnej akwizycji: 7/13** — niewykonalne (nawet dla ideału) wyłącznie 6
  epizodów z t_acq 19.5–31.2 s: okno sędziego otwiera się pasywnie @~5 s (cel sam
  wchodzi w pasmo), do akwizycji płonie 14–26 s okna (b_frac/c_sweep nie do odrobienia)
  i/lub d_min już spalony na ślepo (§R2). Geometria jawna: ogon vs intercept —
  identycznie; ratunkiem nie jest ani prędkość, ani prowadzenie, tylko CZAS AKWIZYCJI.
- **B-2 osobno:** po usunięciu artefaktu (§R2a) wyrocznia nie ma żadnej realnej
  porażki — teza „sufit potwierdzony najmocniej przez B" upada; dla ideału oba
  epizody trywialnie wykonalne (marginesy 22.4–22.7 s).
- **Kontrola (sanity prerejestrowany): 5/5 wygranych sklasyfikowane jako wykonalne**
  (od akwizycji i od t0, oba prowadzenia; marginesy 18.96–20.93) — model rachunku
  zdrowy.

## §R2a. ZNALEZISKO PRZYRZĄDU: tranzient teleportu w d_min sędziego (dowód)

**Mechanizm:** `gt_intruder.jsonl` loguje parę {`cmd_ned` (komenda trajektorii),
`ned` (poza ZASTOSOWANA z bufora subskrypcji pose/info w procesie intruder_motion —
`harness/intruder_motion.py:102-109`)}. Na pierwszych 1–2 próbkach epizodu bufor
bywa STALE sprzed teleportu bramki startu. Dowód na c09_s02 (FANTOM r6_V2):
(1) bramka startu w t0=188.02 widzi intruza DOKŁADNIE na pozie startowej [0,15,−10]
(event `intruder_start_gate` status OK; weryfikacja ≤TOL_START=0.20 m —
`bench_flight.py:276`, `intruder_motion.py:30`); (2) próbki gt t_rel 0.092/0.112
mają `cmd_ned`=[0,14.9,−10] (poprawna komenda), ale `ned`=[−0.2,0.39,−10] =
**ostatnia logowana poza POPRZEDNIEGO epizodu** (c08_s02 @ sim 183.29:
[−0.17,0.33,−10]); od t_rel 0.136 `ned` wraca na [0,14.91]. Dron startuje z home
(0,0) ⇒ fikcyjne d_min 1.594 m @ t_rel 0.09. Zamrożony sędzia liczy d_min na tych
próbkach i na interpolacji liniowej przez skok (`bench_judge.py:34-47,88-96`).
Klasa tranzientu znana od shakeoutu („max 21 m = tranzient teleportu granicznego",
`intruder_motion.py:27-29`) — dotąd nieskojarzona z d_min. Marker artefaktu:
|`ned`−`cmd_ned`|_xy > 1 m (intruz „nie śledzi" własnej komendy).

**Reprodukcja i filtr (sanity):** werdykt sędziego odtworzony co do 0.001 na pełnym
logowanym GT w oknie epizodu dla WSZYSTKICH badanych epizodów (zgodność z
akw_summary/raportami); filtr usuwa średnio 1–2 próbki na starcie epizodu; kontrola
5/5 bez flipa w drugą stronę. Dane: `artefakt_dmin.json`, `sweep_artefakt.json`.

**Skala (pełny sweep obu kampanii sieci + 6 porażek nauczyciela):**

| zbiór | epizody z próbkami artefaktu | flipy D6 FAIL→PASS (ważne) |
|---|---|---|
| AKW S3 V2 (48) | 28 | **4**: c06_s04, c09_s02, c09_s03, c10_s03 |
| AKW S3 B (48) | 25 | **2**: c09_s02, c11_s02 |
| FANTOM S2 V2 (48) | 32 | **2**: c05_s02, c09_s02 |
| FANTOM S2 B (44) | 25 | **2** ważne: c09_s03, c11_s02 (+1 nieważny c11_s01) |
| nauczyciel (6 porażek ławki) | 6/6 | **6/6**: c05_s01 (boot11, 2.988→7.597), c05_s08, c07_s02, c09_s02, c09_s03, c09_s06 |

**Implikacje (desk, what-if — zdania zamrożone kampanii NIETKNIĘTE, decyzja
o erratum = CC/Olga):** AKW S3: pass_B 46→48, pass_V2 34→38 ⇒ Δ_new 12→**10**;
FANTOM S2: pass_B 38→40, pass_V2 31→33 ⇒ Δ_new2 **7→7** (liczba bez zmian, skład
zmieniony); N6 FANTOM: c05_s02 FAIL→PASS ⇒ 3/6→**4/6** (nadal strefa opisowa —
litera werdyktu POZYCJI bez zmiany progowej); erratum RE-AKW/AKW: klasa „czysty
pościg" 5→3 (c09_s02, c09_s03 AKW = artefakt); D0: 6 wykluczeń korpusu =
artefaktowe (usunęły DOBRE demonstracje, w tym 3×c09 v=1.0 — korpus zubożony,
nie skażony). Wzór postępowania: ERRATUM_VMAX/ERRATUM_42M (adnotacja in-place +
plik erratum); sędzia FROZEN — filtr jako ŚWIADEK OBOK zdań zamrożonych, nigdy
podmiana wstecz.

## §R2. Co robi sieć w porażkach (telemetria; `r2_behavior.json`)

**Mody zachowania z licznikami (V2-11 + B-2):**

| mod | n | epizody | sygnatura |
|---|---|---|---|
| **A. artefakt przyrządu** (realnie PASS) | 3 V2 + 2 B | c05_s02, c09_s02, c09_s03(A); B: c09_s03, c11_s02 | d_min sędziego @ t_rel 0.04–0.11 s; realne d_min 6.35–7.76 |
| **B. ślepy najazd + spalone okno** (późna akwizycja) | 6 | c08_s03, c08_s04, c10_s02, c11_s02, c11_s03, c11_s04 | t_acq 19.5–31.2 s; d_min 0.44–3.48 w fazie `hold`, track_INVALID, t_rel 11.9–16.3 s — PRZED akwizycją; cel wchodzi pod zawis podczas skanu; R1-od-akwizycji: niewykonalne nawet dla ideału |
| **C. omiatanie za wolno przy żywym tracku** (near-miss) | 2 | c10_s03 (sweep 558.7°/630, frac 0.889 ✓, d_min 4.12 ✓), c10_s01(A) (551.3°/630; po filtrze artefaktu 594.3°) | sieć trzyma pasmo, ale tempo kątowe pod translacją celu za małe o ~6–11% |

**d(t):** w oknach pościgu (track żywy, d>10) nachylenie d(t) = −0.01…−0.24 m/s —
**zbieżne-za-wolno, nigdy rozbieżne**; żaden epizod nie pada na „cel odjechał".
**Profil prędkości:** |cmd_h| p50 1.60–2.69 m/s (53–90% V_MAX), p90 2.10–3.00
(70–100%), frakcja saturacji ≥0.9·V_MAX zwykle <0.2 ⇒ **lot poniżej koperty** —
sieć odwzorowuje prawo hamowania nauczyciela (0.6·(d−8), czyli ≤1.8 przy d≤11),
zamiast gonić pełną prędkością; nauczyciel w analogicznej sytuacji w korpusie leci
p50 2.70 (§R3). **Kierunek:** kąt komendy do LOS p50 20–57°, do kierunku intercept
20–52° — sieć NIE celuje czysto ani w bieżącą pozycję, ani z wyprzedzeniem; komenda
niesie składową styczną (orbitopodobną) już w dojściu. Rozstrzygnięcie pytania R2:
**sieć nie wykorzystuje posiadanej koperty prędkości (90–100% tylko w ogonach
rozkładu), ale to kosztuje wyłącznie w modzie C** — w modzie B nawet pełna koperta
nic nie kupuje (R1), w modzie A nie ma czego kupować.
**Gdzie pada D6:** mod B: d_dmin (na ślepo) + b_frac/c_sweep (okno spalone);
mod C: wyłącznie c_sweep. **Kontrola (ciekawostki uczciwości):** pass c09_s04 ma
slope +0.045 (cel sam wraca), pass c10_s04/c09_s03 mają p50 |cmd|≈0 przy d>10
(sieć w hover, cel wraca sam) — część wygranych v=1.0 to łut geometrii, nie
umiejętność pościgu; spójne z near-missami modu C.

## §R3. Korpus treningowy i nauczyciel (drugi świat; `r3_corpus.json`)

- **Materiał v=1.0 W KORPUSIE JEST:** komórki c08–c11 = 40/120 scenariuszy ławki;
  w zbiorze D0 (kept) 37/114 epizodów i 52 030/161 380 wierszy (32.2%; suma c08–c11
  z tabeli `results/NET/D0_dataset.md` §3). Ułamek epizodów |v_intr|≥0.8 w TRAIN:
  26/81 (7 ziaren × 4 komórki − 2 wykluczenia c09).
- **Nauczyciel DEMONSTROWAŁ pościg za celem szybkim:** w grupie v=1.0 — 2 176 wierszy
  sytuacji pościgowej (track ważny ∧ d>10; 3.9% wierszy) z |cmd| p50 2.70 / p90 2.99
  (90–100% V_MAX — saturuje, inaczej niż sieć w porażkach) oraz **340 powrotów do
  pasma** po wypadnięciu; orbita pod translacją = 98% wierszy. Dysproporcja jest
  OBJĘTOŚCIOWA (chase 3.9%), nie zerowa.
- **Wynik nauczyciela na komórkach v=1.0:** frozen-judge 37/40 (3 porażki c09_s02/
  s03/s06, klasa „proximity wejścia" — RAPORT_KAMPANIA_BLOK1); **po odfiltrowaniu
  artefaktu §R2a: 40/40** (wszystkie 6 porażek ławki, także c05/c07, to tranzient
  teleportu; c05_s01 liczony z boot11: 2.988→7.597). Frac nigdy nie był przyczyną
  porażki nauczyciela (RAPORT_KAMPANIA_BLOK1:13). **Hipoteza „sufit nadzoru —
  nauczyciel sam nie domykał v=1.0" jest OBALONA pomiarem.** Konsekwencja dla D0:
  6 wykluczeń = dobre demonstracje usunięte (erratum-materiał; korpus zubożony
  o 3 epizody c09 v=1.0, nie skażony).
- Skaza metodyczna skanu (jawna): dedup scenariuszy per pierwszy boot w porządku
  leksykalnym — przy bootach-retry możliwa zamiana pojedynczych epizodów; agregaty
  procentowe nieczułe (sprawdzone na liczności: 40/40/40 epizodów per grupa v).

## §R4. Przestrzeń dźwigni (projekt, bez budowy) — per wynik R1–R3

Wynik NIE jest ani (a) niewykonalnością (R1: 13/13 od t0), ani czystym (b) „dziura
w korpusie" (R3: materiał jest, nauczyciel domykał), ani czystym (c) deficytem
polityki (R2: realne porażki zachowania = 2 near-missy c_sweep). **Pozycja
POŚCIG-V1 w kształcie z ANEKS_REAKW-1 §4 („5+2B porażek przy żywym tracku,
jeden mechanizm: pościg") rozpuszcza się: 3+2B artefakt przyrządu + 6 akwizycja-
transit + 2 near-miss omiatania.** Dźwignie nazwane z ligą:

- **D1 — ERRATUM-DMIN (liga: przyrząd/erratum; rekomendowana, 0 bootów):** aneks
  erratum wzorem ERRATUM_VMAX (adnotacja in-place w raportach dotkniętych + plik);
  filtr |ned−cmd|>1 m jako ŚWIADEK OBOK zdań zamrożonych (sędzia 8ec0fcfb FROZEN —
  żadnej podmiany wstecz); dla PRZYSZŁYCH nóg: utwardzenie u źródła (bramka czystości
  pierwszych próbek gt_intruder albo start logowania po potwierdzeniu świeżości
  bufora) = zmiana intruder_motion/ławki ⇒ wymaga własnego FREEZE i zgody na dotyk
  przyrządu (dziś frozen) — decyzja PRE/Olga. Bez D1 każda przyszła kampania
  i ewaluacja offline dziedziczy fikcyjne d_dmin.
- **D2 — resztka omiatania (mod C; liga: polityka/trening):** dotrening = NOWE wagi
  pod NOWĄ nazwą rejestru (ncp 0337d5ea NIETKNIĘTE) na korpusie doważonym
  pościgowo/orbitalnie pod translacją; narzędzia istnieją (net/train.py numpy-CPU,
  net/rollout_eval.py offline, zbiór 120 scenariuszy). **Rachunek przeciw:** zysk
  górny = 2 pary near-miss (−71.3° i −35.7° omiatania), ryzyko regresji na 33/40
  przechodzących, koszt pełnej ścieżki ~27–29 bootów (§R6). Nieuzasadniona jako
  noga; co najwyżej sonda (§R6 iii). Liga architektury (gdyby PRE chciał głębiej):
  sieć NIE dostaje prędkości celu — cechy 8D jawnie bez trk_vel
  (`bench/features.py:4-9`); NCP musi różniczkować pozycję w stanie ukrytym;
  rozszerzenie cech = NOWY kontrakt train/flight (features FROZEN w D0) — inna,
  droższa liga, wyceniona nie-projektowana.
- **D3 — klasa ślepego najazdu/późnej akwizycji (mod B; liga: poza pościgiem):**
  to stara klasa „skan vs cel transitujący" (admisja wieloprzebiegowa, znana z AKW;
  tu z nowym kosztem: cel wchodzi <4 m pod ślepy zawis — d_dmin pada ZANIM track
  istnieje). Dźwignia pościgowa NIC tu nie kupuje (R1). Ewentualna pozycja katalogu
  **AKW-TRANSIT** z flagą [MECHANIZM ZMIERZONY] (6 epizodów, sygnatura kompletna);
  percepcja/profil II/kwarantanna FROZEN — dźwignia musiałaby być w choreografii
  skanu lub wyżej, poza zakresem tego recon.
- **Granica programowa (nazwana wprost):** skryptowy wrapper pościgowy (np. czysty
  LOS-pursuit przy track żywym) ominąłby uczony kontroler w gnieździe i wydrążył
  tezę programu (gniazdo kontrolera = sieć). Rachunek D2 vs 2 near-missy mógłby
  kusić skryptem „taniej niż trening" — koszt tezowy: werdykty W1′/LIQ przestają
  porównywać sieci, program wraca do skryptów. Odrzucenie/przyjęcie = decyzja PRE,
  nie recon.

## §R5. Ryzyka (mechanizmy, liczby)

- **R1 to górna granica:** realny tor ma szum i opóźnienie — err_fresh p50 0.29–0.35,
  p95 ~0.5 m (akw_summary obu kampanii), E2E p95 0.080–0.084 s (RAPORT_AKW_S3:98),
  ≤0.104 s (RAPORT_FANTOM_S2:49). Kurczenie marginesu: błąd pozycji celu ~0.5 m +
  v_celu·E2E ≈ 0.08 m ⇒ ekwiwalent ~0.2 s przy V_MAX — wobec marginesów wejścia
  ≥17.9 s i deficytu omiatania ~4–8 s NIE zmienia żadnej klasyfikacji R1 (rząd 2–3%
  deficytu c_sweep).
- **Dotrening → regresja na 33/40 przechodzących (po erratum):** ewaluacja tania
  offline ISTNIEJE — `net/rollout_eval.py` (kinematyka punktowa z D0 §5: accel≤2.0,
  |v|≤V_MAX, FEED-B) + manifest 120; warunek uczciwości: rollout z filtrem-świadkiem
  d_min (inaczej selekcja wag na artefakcie).
- **Porównywalność W1′/LIQ:** nowe wagi = NOWY kontroler (nowa nazwa w rejestrze,
  nowy wpis FREEZE); stare wagi/wpisy nietknięte — łańcuch Δ 34→12→7 pozostaje
  interpretowalny tylko ze starymi wagami.
- **Kwarantanna/profil II:** żadna z dźwigni D1–D3 ich nie dotyka — D1 to log/sędzia-
  świadek, D2 to wagi, D3 jest poza zakresem; fantom_scan e435ed7e i akw_scan
  b94cdeae pozostają FROZEN (potwierdzenie kontraktu: jedyny most feed→kontroler
  `bench_flight.py:359-360`).
- **NOWE ryzyko systemowe (z §R2a):** każdy przyszły werdykt liczony zamrożonym
  sędzią na surowym gt_intruder dziedziczy artefakt d_min zależny od pozycji końca
  POPRZEDNIEGO epizodu (deterministycznie reprodukowalny per układ bootu — stąd
  „B pada tak samo" przez dwie kampanie). Bez świadka-filtra artefakt będzie dalej
  produkował fikcyjne pary i fikcyjne N-ki.

## §R6. Wycena wariantów dalszej drogi

- **(i) Aneks zamykający + ERRATUM-DMIN (REKOMENDACJA): 0 bootów.** Pozycja
  POŚCIG-V1 zamknięta rozpuszczeniem mechanizmu (ten recon = dowód); erratum
  obejmuje: adnotacje RAPORT_AKW/RAPORT_FANTOM/RAPORT_KAMPANIA_BLOK1/RECON_REAKW
  (in-place, wzór ERRATUM_VMAX), tabelę flipów (gotowa: `sweep_artefakt.json`),
  reguły: świadek-filtr obok zdań zamrożonych; otwarcie pozycji katalogowej
  AKW-TRANSIT (D3) — decyzja osobna.
- **(ii) PRE_POSCIG z dotreningiem (gdyby mimo rachunku):** przygotowanie korpusu
  doważonego + trening (train.py, godziny CPU/GPU Olgi) + rollout offline 120 ep.
  z świadkiem d_min + smoke 1–2 booty + kampania verbatim 12×{B,V2} 24+3 ⇒
  **~27–29 bootów, 2 sesje lotne**; przewidywanie z tego recon: zysk ≤2 pary
  (near-missy), Δ bez zmiany klasy werdyktu — kampania potwierdziłaby desk za
  ~27 bootów (analogia REAKW §R5). Sufit nogi (propozycja): ≤30.
- **(iii) Sonda celowana (taniej, bez interpretacji progowej — słabość wprost):**
  2 pary c10 (s01, s03) × {B,V2} + 1 kontrola ⇒ ~4–6 bootów; wynik tylko
  mechanizmowy (podzbiór nielosowy, bez Δ). Ma sens WYŁĄCZNIE po D1 (inaczej mierzy
  artefakt) i tylko jeśli PRE przeformułuje pozycję na „omiatanie pod translacją".
- **Zarys FREEZE_POSCIG (gdyby ii/iii):** sha nowych wag + receptura korpusu +
  konfig treningu + rollout_eval + świadek-filtr d_min + odziedziczone FREEZE_FANTOM/
  AKW/DET verbatim. **Czego NIE wolno dotknąć:** percepcja (det_v2, FeedVision, MTI,
  progi admisji), osłona + piny, kwarantanna `fantom_scan.py` e435ed7e, profil II
  `akw_scan.py` b94cdeae, stare wagi `net/frozen/*` (ncp 0337d5ea), rejestry
  (feed ee1481f9, kontrolery — wpis WYŁĄCZNIE additive), sędzia 8ec0fcfb (świadek
  obok, nie podmiana), bench 05137098. Dźwignia wyłącznie: nowe wagi/nowy wpis
  rejestru + narzędzia treningowe + dokumenty.

## Artefakty

`tools/poscig_index.py` → `index_episodes.json` · `tools/poscig_recon.py` →
`r1_feasibility.json`, `r2_behavior.json` · `tools/poscig_artefakt.py` →
`artefakt_dmin.json` · `tools/poscig_sweep.py` → `sweep_artefakt.json` ·
`tools/poscig_r3.py` → `r3_corpus.json`.

**Rekomendacja końcowa: wariant (a′) z §R6(i)** — pozycja zamyka się reconem
(rozpuszczenie mechanizmu: 3+2B artefakt / 6 akwizycja-transit / 2 near-miss
omiatania), a natychmiastowym owocem jest ERRATUM-DMIN (werdykto-nośne w czterech
zbiorach, zero bootów). Dalej: CC pisze **aneks zamykający** (z erratum i decyzją
o pozycji AKW-TRANSIT) ALBO **PRE_POSCIG numerowany** (wtedy: dźwignia zmierzona
przed PRE = ten recon; dowód pościgu per reżim opóźnienia akwizycji — reguła
z KSIĘGI zastosowana wprost; predykcje jako wskaźniki). Sygnały bez numeru
odrzucam. **STOP-POSCIGR.**
