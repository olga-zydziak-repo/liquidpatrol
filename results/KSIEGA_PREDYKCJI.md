# KSIĘGA PREDYKCJI — skonsolidowane rozliczenia CC

**Sporządził:** CC · 11.09.2026 (audyt v2, sesja doc-only). **Reguła:** każda pozycja poniżej pochodzi
z rozliczenia zapisanego w pliku repo; zero liczb z pamięci; przy każdej — źródło w formacie `ścieżka:linia`.
Nogi, których księgi ✓/✗ nie da się odtworzyć z plików raportów, trafiają do sekcji „NIESKONSOLIDOWANE"
z listą przeszukanych miejsc — bez zgadywania.

Zakres obowiązkowy: INFRA-3, ławka (pozycja 2), sieć (pozycje 3+4), K2 (pozycja 6).

---

## INFRA-3 — rozcięcie kontroler/osłona

Rozliczenie predykcji przy werdykcie A2 PASS. Werdykt oparty o decydenta boot4 (ważny + porównywalny)
na czystej maszynie, po odrzuceniu „PASS mimo nieważności" i revert serii ze skażonej maszyny
(`results/INFRA3/RAPORT_INFRA3.md:88-90`).

- **P2 — ✓** (potwierdzona „pod skażeniem"): `results/INFRA3/RAPORT_INFRA3.md:93`.
- **P3 — ✓** (habitat env INVALID w boot3, zamanifestowana zgodnie z predykcją):
  `results/INFRA3/RAPORT_INFRA3.md:93` oraz `results/INFRA3/RAPORT_INFRA3.md:95-96`.
- **P5 — ✓** (boot4 ważny i w progach za pierwszym razem): `results/INFRA3/RAPORT_INFRA3.md:93`.
- **P4 — kierunkowo (partial, nie czyste ✓/✗):** dz najciaśniejszy margines 0.131–0.481 przy 0.5
  (`results/INFRA3/RAPORT_INFRA3.md:94`; wcześniejszy zapis marginesów 0.481/0.426/0.438
  `results/INFRA3/RAPORT_INFRA3.md:96`).
- Dodatkowo predykcja luki wrappera potwierdzona przy diagnozie: „`acts/*` bez watchdoga/mag/I2a;
  `run_k1_boot.sh` bez hasha/spawnu" (`results/INFRA3/RAPORT_INFRA3.md:25`).

**Suma INFRA-3 (czyste): 3 ✓ / 0 ✗** (P4 pozostaje kierunkowa/partial; nie wliczana do sumy czystej).

---

## ŁAWKA (pozycja 2) — orbity, blok 1 + shakeout/build + kampania

Ława prowadzi dwie księgi w dwóch plikach: build+shakeout (ANEKS_BENCH-1a §3) oraz kampania (RAPORT_BENCH §6),
z jawną sumą łączną w raporcie końcowym.

Kampania (`results/BENCH/RAPORT_BENCH.md:73`):
- **P-BE1 — ✓** (0.9167 ≥ 0.85).
- **P-BE2 — ✓** (0 REFUSE).
- **P-BE3 — ✗** (obalona: 1. klasa porażek to nie `frac`, lecz proximity wejścia egzekutora dla c05/c07/c09;
  `results/BENCH/RAPORT_BENCH.md:55` i `:73`).
- **P-BE4 — ✓** (D9 odrzuca 4.2% ≤ 15%).
- **P-BE5 — ✗** (bramka resetu trzymała; nic nie ucięło epizodów poza dsw-requeue).
- Podsuma kampanii: **3 ✓ / 2 ✗** (`results/BENCH/RAPORT_BENCH.md:74`).

Build+shakeout (`results/BENCH/ANEKS_BENCH-1a.md:35-37`):
- **P-BB1 — ✓** · **P-BB2 — ✓** · **P-BB3 — ✓** · **P-BB4 — ✓** · **P-BB5 — ✗** (problemem start intruza,
  nie bramka resetu) · **„1 linia wrappera" — ✗** (wyszły 2 linie; drugi raz zaniżony glue — poprawka
  kalibracyjna CC: rozmiar glue podawać jako przedział).
- Podsuma build+shakeout: **4 ✓ / 2 ✗** (`results/BENCH/ANEKS_BENCH-1a.md:37`).

**Suma ławki łącznie (recon/build + kampania): 7 ✓ / 4 ✗** (`results/BENCH/RAPORT_BENCH.md:74`) —
raport odnotowuje, że to poniżej progu „predykcje CC jako prior; dane rządzą".

---

## SIEĆ (pozycje 3+4) — NCP-20 vs tiny-MLP

Rozliczenie lotów w `results/NET/FLY/RAPORT_NET.md:52-63`. Napięcie P-N3 ↔ P-N8 rozstrzygnięte przez loty
na korzyść P-N8 (`results/NET/FLY/RAPORT_NET.md:63`).

- **P-N3 — ✗** (NCP↔MLP niezgodne miały być ≤3 netto; wyszło netto +37): `results/NET/FLY/RAPORT_NET.md:56`.
- **P-N4 — ✓** (NCP ≥40/48; 45/48): `results/NET/FLY/RAPORT_NET.md:57`.
- **P-N5-lot — ✓ (NCP)** (porażki na komórkach proximity c07_s02/c09_s02/c09_s03 — dokładnie granica
  nauczyciela): `results/NET/FLY/RAPORT_NET.md:58`.
- **P-N6 — ✓** (REFUSE 0–2; wyszło 0): `results/NET/FLY/RAPORT_NET.md:59`.
- **P-N7 [post-diag] — ✓** (MLP <40/48; 8/48): `results/NET/FLY/RAPORT_NET.md:60`.
- **P-N8 [post-diag] — ✓** (NCP↔MLP niezgodne ≥5 netto na korzyść NCP; +37): `results/NET/FLY/RAPORT_NET.md:61`.
- Księga pełna nogi (poz.3+4): P-N1 ✓ (S2) / P-N2 ✓* / P-N3 ✗ / P-N4 ✓ / P-N5 ✓ / P-N6 ✓ / P-N7 ✓ /
  P-N8 ✓ / P-N5-offline ✗ (`results/NET/FLY/RAPORT_NET.md:63`).

**Suma sieci (z linii 63): 7 ✓ / 2 ✗** (P-N2 zapisane jako „✓*" — z gwiazdką w źródle, liczone jako ✓).

---

## K2 (pozycja 6) — sieć + denial GNSS pod osłoną

Rozliczenie predykcji recon PRE_K2 / ANEKS_K2-1 w `results/K2/RAPORT_K2.md:33-37`.

- **P-K2-2 — ✓** (t_refuse w paśmie na wszystkich ważnych; 12/12 w [0.05,0.15]):
  `results/K2/RAPORT_K2.md:34`.
- **P-K2-4 — ✓** (0 breach; 0/12): `results/K2/RAPORT_K2.md:36`.
- **P-K2-3 — ✗ (nietrafiona w kierunku bezpiecznym):** mediana x_exc 1.809 m poniżej przewidzianego
  pasma 2.0–3.5 m — osłona wychyla mniej, niż zakładał recon: `results/K2/RAPORT_K2.md:35`.
- **P-K2-1 — ✗ (niezrealizowana):** przewidywany defekt przy pierwszym wykonaniu REFUSE+D5 nie wystąpił;
  diag i 12 epizodów czyste za pierwszym strzałem: `results/K2/RAPORT_K2.md:37`.
- **P-K2-5 — ✓** (0 fałszywych REFUSE w nominale przy uzbrojonym monitorze POS, p≈0.8; TRAFIONE):
  `results/K2/RAPORT_K4b.md:17` (pominięte przy pierwszej konsolidacji — dopisane ANEKS_FV-2 §4).

**Suma K2: 3 ✓ / 2 ✗** — obie ✗ są „bezpieczne": jedna to zejście poniżej przewidzianego wychylenia
(P-K2-3), druga to niewystąpienie przewidzianego defektu (P-K2-1).

---

## SUMA ZAKRESU OBOWIĄZKOWEGO

Liczone wyłącznie z rozliczeń w plikach, czyste ✓/✗ (partiale kierunkowe wyłączone):

- INFRA-3: **3 ✓ / 0 ✗** (+1 kierunkowa: P4).
- Ławka: **7 ✓ / 4 ✗**.
- Sieć: **7 ✓ / 2 ✗**.
- K2: **3 ✓ / 2 ✗** (P-K2-5 dopisane, ANEKS_FV-2 §4).

**RAZEM (zakres obowiązkowy): 20 ✓ / 8 ✗** (+1 kierunkowa INFRA-3 P4, poza sumą).
Uwaga interpretacyjna z plików: ławka odnotowuje wynik 7/4 jako „poniżej progu predykcje-jako-prior;
dane rządzą" (`results/BENCH/RAPORT_BENCH.md:74`); obie ✗ K2 są w kierunku bezpiecznym
(`results/K2/RAPORT_K2.md:35,37`).

---

## NIESKONSOLIDOWANE (poza zakresem obowiązkowym)

Dla nóg wcześniejszych nie znaleziono w plikach raportów księgi predykcji w formie rozliczalnej ✓/✗;
zgodnie z regułą — bez zgadywania. Przeszukane miejsca (grep `predyk|prerejestr|ksieg|P-[KDR][0-9]`,
case-insensitive):

- **K1 (pozycja 1):** `results/K1/RAPORT_K1.md` — 0 trafień księgi ✓/✗; `results/K1/RAPORT_K1_B1_STOP.md`
  — 0 trafień. Brak plików `ANEKS_K1*.md` w drzewie `results/` (rozliczenia K1 żyły w sesjach CC / memory,
  nie w commitowanych raportach jako ledger). Nie konsoliduję.
- **DEMO-B / DEMO_V2 (pozycja 5):** `results/DEMO_V2/RAPORT_DEMO_V2.md` — demo jawnie oznaczone
  „DEMO ≠ POMIAR; żadna liczba nie wchodzi do żadnej księgi" (`results/DEMO_V2/RAPORT_DEMO_V2.md:3,28`).
  Z definicji poza księgą predykcji.
- **R0.x / R02 (recon percepcji):** `results/R02/RAPORT_R02.md`, `results/R02/RAPORT_R02C.md` — brak
  ledgera ✓/✗ predykcji (kryteria zamrożone w PRE, księgowość trójwynikowa: `results/R02/RAPORT_R02.md:5`,
  ale bez rozliczonej listy P-* w pliku). Nie konsoliduję.

---

## NOGA FV (poz.1b) — weryfikacja formalna jądra osłony

Rozliczenie predykcji PRE_FV §9 + ANEKS_FV-1 §6 przy RAPORT_FV (`results/FV/RAPORT_FV.md:§5`).
Sesje S1 (lustro+różnicówka+O1), S2 (M-krok+O2), S3 (O3+O4). Werdykt bramki nogi = **PASS**
(O1∧O2 dowiedzione ∧ różnicówka czysta ∧ M-krok 27/27; `results/FV/RAPORT_FV.md:§1`).

- **P-FV-1 — ✓** (O1 dowiedzione w ≤1 sesji dowodowej od startu S1; O1 PROVED w S1, P6_d5 dde0a7e):
  `results/FV/RAPORT_FV.md:§5`.
- **P-FV-2 — ✗** (niezrealizowana: różnicówka miała znaleźć ≥1 rozbieżność wymagającą poprawki LUSTRA;
  0 rozbieżności w S1 i M5, lustro 1:1 za pierwszym biegiem): `results/FV/RAPORT_FV.md:§5`.
- **P-FV-3 — ✓** (O4(a)+(b) domknięte w ≤1 sesji; L1+L2 w S3): `results/FV/RAPORT_FV.md:§5`.
- **P-FV-4 — ✓** (wszystkie mutanty wykryte bez grid2; 27/27, 0 iteracji; ANEKS_FV-1 §6):
  `results/FV/RAPORT_FV.md:§5` oraz `results/FV/RAPORT_FV_S2.md:15-16`.

**Suma FV (czyste ✓/✗): 3 ✓ / 1 ✗** (P-FV-1,3,4 ✓; P-FV-2 ✗).

---

## OTWARTE (prerejestrowane 11.09.2026, CC v2)
- ~~P-CC2-1~~ **ROZLICZONE — ✓:** przewidywany wynik „częściowy albo śmierć na pokryciu narzędzi" (p≈0.7)
  ZISZCZONY jako CZĘŚCIOWY — predykcja trafiona. Księga jest binarna: kategoria „✓-częściowy" nie
  istnieje ⇒ zapis **✓**. Uzasadnienie: część (ii) „własności samej sieci CfC narzędziem off-the-shelf"
  zakończona desk-note „częściowy" (`results/FV/NOTA_UNROLL.md:§5`); wnętrze CfC niedowiedzione. Kanał
  komendy kontrolera dowiedziony (K1, `results/FV/RAPORT_FV.md:§3` po erracie ANEKS_FV-1c). Przeniesione
  z OTWARTE do rozliczonych.
- **P-CC2-3 (prereg 13.09.2026 CC, przed lekturą raportu) — ✓:** „L2 w RAPORT_FV instancjonuje O3 na
  v_cmd zamiast vel — wymaga korekty" (p≈0.6). ROZSTRZYGNIĘTE KODEM PINOWANYM: `_geofence_violation`/
  `_braking_dist` liczą po vel mierzonym (r01/shield.py:97-112; gate_run_r03.py:232/268,
  bench_flight.py:342/363), v_cmd dopiero po ALLOW — A-TRACK niedowiedziony i empirycznie łamany
  (K1/ANEKS_K1-8). Errata doc-only CO5 (ANEKS_FV-1c §3), `results/FV/RAPORT_FV.md:§O4/§7`.
- P-CC2-2: follow-up SPRIND dostaje merytoryczną odpowiedź w ≤3 tygodnie od wysyłki — p≈0.3.
  **ZOSTAJE OTWARTE.**
Rozliczenie: P-CC2-1 i P-CC2-3 przy RAPORT_FV (powyżej); P-CC2-2 przy warstwie 0 / odpowiedzi SPRIND.

## NOGA W (wiatr, poz.2b) — ROZLICZONE przy RAPORT_W (ANEKS_W-2 §4, 29.09.2026)
Prerejestrowane 19.09.2026 (PRE_W §13, ANEKS_W-0 §3):
- **P-W-1 ✗:** „0 REFUSE jakiegokolwiek rodzaju na całej siatce kryterialnej" (p≈0.75) —
  PADA: REFUSE(GEOFENCE) L3/net_s02, PRAWDZIWY (`results/W/RAPORT_W.md:§2`). Chybienie
  przyniosło główny wynik nogi; dokładnie po to REFUSE⇒STOP było zamrożone.
- **P-W-2 ✗:** „próba arm z ziemi przy 4.5 m/s = FAIL" (p≈0.7) — PADA: 4.5 armuje
  (W-A boot4, arm_ok=True; RAPORT_W_A).
- **P-W-3 — POZA SUMĄ (nietestowalna):** „W-A hover 3 m/s: dr=false, eph_max<1" (p≈0.75) —
  hover @3.0 nie zaistniał (no-climb = artefakt modułu infra1, `results/W/RAPORT_W.md:§4`);
  warunek antecedensu pusty.
- **P-W-4 — POZA SUMĄ (nietestowalna):** „parowanie NCP↔executor @3 m/s: ≤2 różnice netto"
  (p≈0.55) — siatka L3 przerwana OBOWIĄZKOWYM STOP po 2 parach; 2 pary to za mało na zdanie
  o ≤2 różnicach netto (dolatywanie po znalezisku = selekcja).
- **P-W-5 ✓:** przechył monotoniczny z poziomem i separuje 0 od 3 m/s (p≈0.8) — mediany
  ~3° → ~9° → ~10–13°, parytet ramion (`results/W/RAPORT_W.md:§3`).

**Suma nogi W: 1 ✓ / 2 ✗ (+2 poza sumą z przyczynami).** Kalibracja CC: obie ✗ to
przewidywania o zachowaniu środowiska/systemu pod wiatrem — reguła 9 potwierdzona kolejny raz.

## NOGA LIQ (kontrola architektury, ex-K3) — ROZLICZONE przy RAPORT_LIQ (ANEKS_LIQ-2 §5, 03.10.2026)
Prerejestrowane 29.09.2026 (PRE_LIQ §8); progi drabiny i kryterium śmierci zamrożone przed
pierwszą epoką treningu kontroli; errata progu sondy PRZED pomiarem (ANEKS_LIQ-1 §3).
- **P-LIQ-1 ✓:** GRU przechodzi bramkę offline (p≈0.9) — PASS 24/24
  (`results/LIQ/RAPORT_LIQ_S1.md` §3).
- **P-LIQ-2 ✗:** MLP-k20 przechodzi bramkę offline (p≈0.7) — PADA: 1/24 (dyspersja ziaren
  init 0–1/24) przy NAJLEPSZYM val-MSE z trójki (`results/LIQ/RAPORT_LIQ_S1.md` §3).
- **P-LIQ-3 ✗ — predykcja modalna CC pada:** werdykt W2∪W3 = śmierć etykiety (p≈0.6) —
  zaszedł wariant klasy W1 (W1′, Δ(GRU)=+16 przy progu W1′ +6), któremu dawałem 0.2
  (`results/LIQ/RAPORT_LIQ.md` §1).
- **P-LIQ-4 ✗:** sonda STOCK: pełzanie NIEOBECNE 2/2 (p≈0.65; próg po erracie ≤14.0) —
  wyszło NIEROZSTRZYGAJĄCE: s02 z_max 14.26 w przerwie 14.0–15.0
  (`results/LIQ/RAPORT_LIQ.md` §4).
- **P-LIQ-5 ✓:** NCP świeże ≥ 43/48 (p≈0.75) — dokładnie 43/48, na progu
  (`results/LIQ/RAPORT_LIQ.md` §2).

**Suma nogi LIQ: 2 ✓ / 3 ✗.** Kalibracja CC (wpis do księgi błędów): wszystkie trzy ✗ mają
TEN SAM kierunek — niedoszacowanie wyników komponentu uczonego/liquid; łącznie z nogą W
(P-W-1, P-W-2) to pięć chybień w jedną stronę przy zerze w drugą. Reguła 9 (predykcje CC
nie są priorami) potwierdzona i zaostrzona: w ocenach jakościowych stosuję korektę na
udokumentowany kierunek błędu.

## NOGA 2A (percepcja w pętli) — ROZLICZONE przy RAPORT_2A (ANEKS_2A-4 §4, 06.10.2026)
Prerejestrowane 03.10.2026 (PRE_2A §P, ratyf. przed S1):
- **P-2A-1 ✗:** „bramka A przechodzi w ≤2 bootach (pokrycie + dsw)" (p≈0.75) — PADA na
  ukrytej usterce yaw (radiany w stopniowe pole MAVSDK): pokrycie rzeczywiste 0.11–0.61
  vs próg 0.90; naprawa N1 + powtórka = 4 booty łącznie (`results/2A/RAPORT_2A_S2.md` §3,
  `RAPORT_2A_S2b.md` §4).
- **P-2A-2 ✗:** „bramka B czasowa (kadencja+latencja) PASS" (p≈0.7) — PADA literą
  kadencji (7.58 Hz < 8 po N2); latencja PASS (0.052 s). Errata ANEKS_2A-2 §2 wyjaśnia
  mechanizm (świeżość = jakość∧czas po bramkowaniu REFRESH; surowy tor czasowy zdrowy
  14.7 Hz/15 ms/52 ms) — wyjaśnienie NIE unieważnia predykcji: litera padła.
- **P-2A-3 ✗:** „błąd FEED-V p95 ≤ 3.0 m" (p≈0.55) — PADA z atrybucją: 40.9 m (S2b),
  mechanizm = top-1 detektora poza celem w ~88–97% klatek orbity na tle naziemnym;
  projekcja niewinna (pinhole na celu 0.65–0.80 m) (`results/2A/RAPORT_2A_S2b.md` §5).
- **P-2A-4 — POZA SUMĄ (nietestowalna):** werdykt kampanii C po Δ (p≈0.5/0.25/0.25) —
  kampania parowana NIE poleciała (wyjątek ekonomiczny ANEKS_2A-2 §2 po uczciwym FAIL-u
  błędu); antecedens pusty.
- **P-2A-5 — POZA SUMĄ (nietestowalna):** „≥1 REFUSE jakiejkolwiek gałęzi pod FEED-V
  w kampanii" (p≈0.25) — kampania nie poleciała; nota: w C-sondzie 2 bootów REFUSE=0
  (pogoń za fantomem szatkowana higieną toru percepcji zanim doszła do pasma geofence'u,
  `results/2A/RAPORT_2A_S4.md` §3-4).

**Suma nogi 2A: 0 ✓ / 3 ✗ (+2 poza sumą z przyczynami).** Kalibracja CC (wpis do księgi
błędów): wszystkie trzy ✗ to PRZESZACOWANIE gotowości integracyjnej nowego toru —
kierunek PRZECIWNY do serii z W/LIQ (tam: niedoszacowanie wyników komponentu uczonego).
Nowa reguła kalibracyjna: w PRE nóg integracyjnych (pierwszy przelot nowego toru przez
LIVE) predykcje bramek technicznych dostają jawną korektę W DÓŁ; predykcje wyników
naukowych — korektę W GÓRĘ (reguła 9 bez zmian: żadne nie są priorami).

## NOGA DET (detektor-v2) — ROZLICZONE przy RAPORT_DET (ANEKS_DET-4 §6, 08.10.2026)
Prerejestrowane 06.10.2026 (`PRE_DET.md:221-227`) — pierwsze PRE z jawnie zastosowaną
korektą kierunkową z ANEKS_2A-4 (bramki integracyjne ↓, komponent uczony ↑):
- **P-DET-1 ✓:** dolot 12/12 VALID w jednej sesji bez puli (p≈0.55, integracyjna ↓
  z 0.70) — 12/12 za pierwszym podejściem, pula 0/2 nietknięta
  (`results/DET/RAPORT_DET_S1.md` §0/§3).
- **P-DET-2 ✓:** v8n BEZ eskalacji osiąga T1 ≥80 % na TEST (p≈0.80, uczona ↑ z 0.65)
  — T1 100.0/99.8 %, eskalacja v8s nieuruchomiona (`results/DET/RAPORT_DET_S2.md` §3–§4).
- **P-DET-3 ✓:** model finalny przechodzi T2 ≤3.0 m na TEST (p≈0.75, uczona ↑ z 0.60)
  — p95 pooled 1.365 m, zapas 2.2× (`results/DET/RAPORT_DET_S2.md` §4).
- **P-DET-4 ✓:** smoke obie bramki runtime za 1. podejściem (p≈0.50, integracyjna ↓
  z 0.70) — 14.71 Hz ≥8 i E2E p95 0.084 s ≤0.25, 1 boot, naprawczych 0/2
  (`results/DET/RAPORT_DET_S3.md` §2).
- **P-DET-5 ✗:** Δ≤4 w kampanii C (p≈0.55) — wyszło **Δ=34** (pass(B)=47, pass(V2)=13
  na 48 parach; `results/DET/RAPORT_DET_S4.md` §4).
- pod-predykcja (≥1 REFUSE jakiejkolwiek gałęzi pod V2 w kampanii, p≈0.20): NIE zaszła
  — zaszła strona 0.80 (REFUSE=0 we wszystkich 96 epizodach obu ramion, liczniki per
  gałąź puste; `results/DET/RAPORT_DET_S4.md` §7).

**Suma nogi DET: 4 ✓ / 1 ✗.** Kalibracja CC (dwie noty, ANEKS_DET-4 §6): (1) prawo
dwukierunkowe z ANEKS_2A-4 potwierdzone WEWNĄTRZ jednej nogi — komponent uczony znów
przebił oczekiwania (detektor po akwizycji DOKŁADNIEJSZY od wyroczni: err_fresh
0.418/0.648 vs 0.676/1.280 m), a gotowość SYSTEMOWA znów przeszacowana (P-DET-5:
Δ=34 zamiast ≤4, w całości akwizycyjny); (2) doprecyzowanie reguły: „gotowość
systemowa" obejmuje geometrię sensoryczną (pole widzenia, choreografia akwizycji),
nie tylko integrację software'ową.

## NOGA AKW (akwizycja — skan yaw) — ROZLICZONE przy RAPORT_AKW (ANEKS_AKW-3 §5, 11.10.2026)
Prerejestrowane 09.10.2026 (`PRE_AKW.md:125-132`):
- **P-AKW-1 ✗:** smoke A+B+C PASS za pierwszym bootem (p 0.50, integracyjna ↓) —
  smoke padł na pierwszym profilu: A 2/3 → powtórka 0/3 (klif ω·dt;
  `results/AKW/RAPORT_AKW_S1.md` §3).
- **P-AKW-2 ✓:** zero potwierdzonych fałszywych ENTRY tła w smoke i kampanii (p 0.70)
  — FP tła 0 w całej nodze; w kampanii wszystkie ENTRY w oknach F1_cel, **F3=0**
  (pozaoknowe = znana klasa F2 lock-przed-epizodem na stagingu;
  `results/AKW/RAPORT_AKW_S3.md` §4).
- **P-AKW-3 ✗** (wynik nogi): Δ_new ≤ 4 (p 0.60) — wyszło **Δ_new=12** (pass(B)=46,
  pass(V2+skan)=34 na 48 parach) ⇒ ŚMIERĆ-AKW progiem zamrożonym; rezyduum w całości
  w celu szybkim v=1.0 (Δ=9/12), luka geometryczna domknięta (bearingi 3/3/3/3,
  +24/−3 vs DET; `results/AKW/RAPORT_AKW.md` §3).
- **P-AKW-4 ✓:** pass(B)_new ≥ 46/48 (p 0.80) — dokładnie 46/48 (obie porażki B
  = v=1.0, padły też w V2; dryf vs DET ≤1 pary).
- **P-AKW-5 ✓:** REFUSE = 0 w całej nodze (p 0.85) — REFUSE 0 we wszystkich 29
  bootach, gałęzie puste; breach 0.

**Suma nogi AKW: 3 ✓ / 2 ✗.** Kalibracja CC (ANEKS_AKW-3 §5): **TRZECI kolejny
przestrzał wyniku systemowego (2A → DET-5 → AKW-3)**, tym razem dokładnie
w interakcji NAZWANEJ-A-NIEZMIERZONEJ (recon R5.8: „intruz ruchomy × skan — desk
nie rozstrzyga"). Doprecyzowanie reguły kalibracyjnej: predykcja wyniku systemowego
z nazwaną-a-niezmierzoną interakcją dostaje korektę w dół GŁĘBSZĄ niż standardowa
(nie ≈0.6, raczej ≈0.4–0.5), dopóki interakcja nie ma pomiaru choćby sondą.

## NOGA FANTOM (czysty start — kwarantanna K1) — ROZLICZONE przy RAPORT_FANTOM (ANEKS_FANTOM-2 §4, 16.10.2026)
Prerejestrowane 12.10.2026 (`PRE_FANTOM.md` §6); dźwignia była ZMIERZONA deskiem
(recon 6/6) — korekta głęboka jawnie NIEzastosowana per ANEKS_AKW-3 §5:
- **P-F-1 ✓:** smoke za pierwszym podejściem (p 0.65) — PASS A′/B/C, obie podklasy
  skonwertowane, zapas nieużyty (`results/FANTOM/RAPORT_FANTOM_S1.md` §4).
- **P-F-2 ✗:** konwersja ≥5/6 N6 w kampanii (p 0.60) — wyszło **3/6**; wszystkie 3
  porażki z wczesną akwizycją 5.0–6.6 s i przegranym pościgiem (mechanizm startu
  domknięty, pościg nie; `results/FANTOM/RAPORT_FANTOM.md` §1).
- **P-F-3 ✓:** Δ_new2 ∈ [5,8] (p 0.55) — dokładnie **7** (strefa opisowa, zdanie ≤4
  nie padło — pościg został, jak przewidziano).
- **P-F-4 ✗ literą:** pass(B) ≥ 45 (p 0.75) — wyszło 38, ale przy n_common=40
  (mianownik skurczony środowiskowo: 8 par straconych narzędziowo); MECHANIZM
  predykcji potwierdzony wskaźnikiem 95.0% vs 95.8% AKW i nieszkodliwością
  C-exitów kwarantanny na wyroczni.
- **P-F-5 ✓:** breach 0 / REFUSE 0 w całej nodze (p 0.85) — 0/0 ×28 bootów.
- **P-F-6 n.r.:** c09_s01 przechodzi mimo kwarantanny (p 0.60) — para NIEWAŻNA
  środowiskowo (poza n_common); opisowo: nieważny przebieg D6 ✓ przy 5.2 s.

**Suma nogi FANTOM: 3 ✓ / 2 ✗ / 1 nierozstrzygnięta.** Kalibracja CC (ANEKS_FANTOM-2
§4, dwa wpisy): (a) **dowód pościgu przenosi się tylko w obrębie tego samego reżimu
opóźnienia akwizycji** — DET-PASS c08 przy akwizycji ~0 s nie dowodzi pościgu po
akwizycji 5 s (stąd przestrzał P-F-2 mimo zmierzonej dźwigni startu);
(b) **predykcje o ramionach formułować jako WSKAŹNIKI albo warunkowo na n_common**,
nigdy jako liczności bezwzględne — mianownik może skurczyć się narzędziowo (P-F-4).

## NOGA PERCEPCJA-II ścieżka (i) OPS-KADENCJA — ROZLICZONE przy CO-PERC2 (ANEKS_PERC2-2 §3, 26.10.2026)
Prerejestrowane 25.10.2026 (`PRE_PERC2.md` §4; ratyfikacja 25.10, sha PRE
24369ed9…1d9e21); dźwignia kadencja→admisja ZMIERZONA deskiem (model DP +
kotwica c08_s01) — bez korekty głębokiej; remedium stanu hosta było
nazwane-niezmierzone ⇒ cięcie głębokie na P-P2-1 (0.60) per reguła ANEKS_AKW-3 §5:
- **P-P2-1 ✓:** istnieje remedium ops dające k=1 stabilnie (p 0.60) — profil
  FastDDS SHM 16 MB + bufory UDP 4 MB (`results/PERC2/FREEZE_PERC2_OPS.md`;
  S1 3/≤4 bootów, sonda PASS 40/90/35 s). Nota: mechanizm INNY niż teza —
  klatki gubił TRANSPORT DDS, nie GPU (`results/PERC2/RAPORT_PERC2_S1.md` §3);
  cięcie głębokie na nazwanym-niezmierzonym remedium było zasadne.
- **P-P2-2 ✓:** @k=1 admisja okien czołowych T6 w ≥5/6 (p 0.70) — wyszło
  **6/6** (runy 4–1084; `results/PERC2/RAPORT_PERC2_S2.md` §2).
- **P-P2-3 ✓ z kwalifikatorem:** oba c08 (s03, s04) przechodzą D6 @k=1 (p 0.60)
  — TAK rachunkiem erratum (GT manifest, świadek obok; d_min 5.613/6.733,
  t_acq 0.10–0.31 s); litera pokładowa dała F przez artefakt tranzientu
  teleportu (1.251/0.557) — flip odtworzony niezależnie przez CC z surowych
  plików (ANEKS_PERC2-2 §1; reguła ERRATUM-DMIN).
- **P-P2-4 ✓:** breach 0 / REFUSE 0 w całej nodze (p 0.85) — 0/0 (S1 bez
  uzbrojeń; S2: 2 booty uzbrojone, 8/8 epizodów ważnych).
- **P-P2-5 ✓:** sonda jako predyktor (p 0.65) — 2/2 bootów po PASS sondy
  trzymało k=1 w locie (dt_p50 0.064–0.068, frac>0.10 = 0.0 we wszystkich
  8 epizodach; zero spadków po PASS).

**Suma nogi PERCEPCJA-II (i): 5 ✓ / 0 ✗.** Kalibracja CC (ANEKS_PERC2-2 §3,
dwa wpisy): (a) **dźwignię prerejestrować ODDZIELNIE od atrybucji mechanizmu**
— tu dźwignia (k=1 środkami ops) przeżyła falsyfikację własnej tezy
mechanizmowej (GPU→transport DDS) i to jest wzór, nie wyjątek;
(b) **progi narzędziowe projektować jako pary tendencja-centralna ∧ ogon** —
druga część progu sondy (frakcja delt >0.10 s) złapała tryb „dziurawy strumień
z dobrą medianą" (T1: p50 0.068, frac 0.47), którego mediana sama nigdy by
nie zobaczyła.

## NOGA WABIK ścieżka (iii) wabik-w-świecie — ROZLICZONE przy CO-WABIK (ANEKS_WABIK-2 §3, 27.10.2026)
Prerejestrowane 26.10.2026 (`PRE_WABIK.md` §4; ratyfikacja 26.10, sha PRE
f2cbf63b…cf3c79); cięcie głębokie zastosowane tam, gdzie mechanizm
nazwany-niezmierzony (P-WB-2 tracker przy 2 obiektach; P-WB-3 TP — w danych
programu nie było ani jednego wabika):
- **P-WB-1 ✗:** smoke czysty (p 0.70) — kotwica sędziego ZŁAMANA w konfiguracji
  A (c08_s01+W-LOITER: D6 FAIL [b_frac] 0.758/0.766, d_min 5.17/5.14 vs
  historyczne PASS 6.854; `results/WABIK/RAPORT_WABIK_S1.md`).
- **P-WB-2 ✗:** tracker utrzymuje intruza przy rozdzieleniu azymutalnym
  (p 0.55) — przeskoki na wabika 25.5 %/24.3 % ticków, wszystkie w fazach
  werdyktowych; „rozdzielenie azymutalne" unieważnia FAZA ORBITY (stożek
  omiata 360°); konfiguracja czysta istnieje przy separacji > zasięg (B: 0 %).
- **P-WB-3 ✗:** TP ≥5/6 w ≤15 s (p 0.65) — FALSYFIKACJA zdaniem zamrożonym:
  ≤1/6 (flagi-kiedykolwiek 4/6 — warstwa cech działa, pada reguła czasowa;
  trzy mechanizmy zmierzone: piki v_rad rwą 12-s streaki, ZBLIŻ strukturalnie
  ~8 s < 12 s, stale-klatki brzegu; `results/WABIK/RAPORT_WABIK_S2.md` §3).
- **P-WB-4 ✓:** FP 0/3 (p 0.75) — zero flag na c08_s03 / c10_s02 / M-ŁUK
  (podłoga dh_min 0.04–3.40 blokuje każdego poważnego).
- **P-WB-5 ✓:** M-POD-ORBITĄ separacja ≥4 m i track 2/2 (p 0.60) — track na
  celu 1.000 (666/666 ticków, świadek obok), d_min 7.064/6.577, D6 2/2 PASS.
- **P-WB-6 ✓:** breach 0 / REFUSE 0 w całej nodze (p 0.85) — 0/0 × 5 bootów
  (13 epizodów uzbrojonych, 13/13 VALID).

**Suma nogi WABIK (iii): 3 ✓ / 3 ✗.** Kalibracja CC (ANEKS_WABIK-2 §3, dwa
wpisy): (a) **konfiguracje przestrzenne projektować per FAZA lotu
(scan/track/orbit), nie per epizod** — „inny sektor" nic nie znaczy, gdy
orbita obraca stożek przez 360° (błąd projektowy CC nazwany w ANEKS-1;
przewidywalny przy biurku z geometrii skanu); (b) **wymagania ciągłościowe
przeliczać przez zmierzoną stopę zakłóceń estymaty PRZED zamrożeniem** —
stopa pików v_rad była mierzalna na NULL przy biurku, a sprzężenie T_FLAG=12 s
z limitem zdania zamrożonego (≤15 s) zostawiło zero marginesu na szum;
reguła progowa na strumieniu szumnym wymaga tolerancji przerw z konstrukcji,
nie z nadziei (dowód kruchości: dwie implementacje tej samej litery różnią
się czasem flagi o ±50 %).

## NOGA WABIK-II / REGUŁA CZASOWA — ROZLICZONE przy CO-WABIK2 (ANEKS_WABIK2-1 §3, 27.10.2026)
Prerejestrowane 27.10.2026 (`PRE_WABIK2.md` §4; ratyfikacja 27.10, sha PRE
2a1bd2a8…ee7a); noga zamknięta ścieżką śmierci S1 — zero lotów wydanych:
- **P-W2-1 ✗:** selekcja offline znajduje wariant spełniający pełne kryterium
  §2.2 (p 0.75) — zbiór dopuszczonych PUSTY na 26 wariantach (krawędź Pareto:
  TP≥5/6 ⇒ NULL-final=15>13; NULL≤13 ⇒ TP≤1/6;
  `results/WABIK2/RAPORT_WABIK2_S1.md`, `s1_tabela.json`).
- **P-W2-2, P-W2-3, P-W2-4: n.r.** — S2 nie poleciała (wzór rozliczeń FANTOM:
  predykcje sesji, która nie zaszła, bez rozliczenia).

**Suma nogi WABIK-II: 0 ✓ / 1 ✗ / 3 n.r.** Kalibracja CC (ANEKS_WABIK2-1 §3):
**człony kryterium koniunkcyjnego wyceniać ŁĄCZNIE, nie marginalnie** —
mechanizmy naprawy trafiły w TP (5/6, flagi w 8.38 s — szybciej niż reguła (i)
kiedykolwiek), ale właściwym przedmiotem predykcji było sprzężenie TP∧NULL,
a ono na tej przestrzeni nie zachodzi nigdy.

## NOGA XAI-SIECI — ROZLICZONE przy CO-XAI (ANEKS_XAI-1 §3, 27.10.2026)
Prerejestrowane 27.10.2026 (`PRE_XAI.md` §3; ratyfikacja 27.10, sha PRE
95555eb3…0166); noga zamknięta sukcesem za 0 bootów (ścieżka deskowa):
- **P-XA-1 ✓:** T1+T2 PROVED, różnicówka 0 kontrprzykładów (p 0.85) —
  T1 0/74 708 (max 2.985176, margines 0.0148), T2 0 (max 0.964907);
  dowody sympy + sondy przesłanek (`results/XAI/RAPORT_XAI_S1.md` §3).
- **P-XA-2 ✗:** T4 znak globalny na ≥80% pudełka (p 0.55) — podwójnie NIE:
  certyfikowane 0.0% (metoda POPRAWNA — zawieranie 40/40) i znak FAKTYCZNIE
  niestały (21.1% korpusu ujemnych; siatka 47.8%). **Lekcje kalibracyjne:**
  (a) twierdzenia o ZNAKU prawa sterowania polityki z fazą orbitalną
  formalizować per FAZA od początku — orbitowanie wymaga sterowania
  stycznego, globalny znak jest strukturalnie fałszywy; (b) arytmetyki
  przedziałowej przez ≥3 warstwy tanh nie preregować na pudełkach rzędu
  p1–p99 całego korpusu — dowozi wyłącznie na małych pudełkach lokalnych.
- **P-XA-3 ✗:** T3 własność przechodząca różnicówkę i dowód warunkowy
  (p 0.60) — kandydatka (lokalna kontrakcja kroku) obalona na KAŻDYM
  z 74 235 ticków założenia (max ‖J‖₂ 2.5766). **Lekcja kalibracyjna:**
  własności stabilności preregować PARĄ rozstrzygalnych hipotez (kontrakcja
  kroku = echo vs stabilność okresu = generator), nie pojedynczą kandydatką
  — wtedy różnicówka rozstrzyga, zamiast tylko obalać; następca (Floquet)
  od razu nazwany.
- **P-XA-4 ✓:** każdy dowód FAIL na ≥1 mutancie (p 0.80) — T1 pada na
  M2_skala/M4_glowa, T2 na M5_bramka; potwierdzone przez CC niezależnie,
  pełnokorpusowo dla M2/M4 (ANEKS_XAI-1 §1.4).

**Suma nogi XAI: 2 ✓ / 2 ✗.** Obie porażki to predykcje postawione
z konstrukcji blisko monety (0.55 / 0.60) — kalibracja bez wstydu
(ANEKS_XAI-1 §3).

### Dopisek 28.10.2026 — ERRATUM_XAI-1 §4 (append-only)

- **P-XA-2: ✗ → n.r.** (zmierzona wielkość ≠ prerejestrowana: narzędzia
  liczyły ∂v_n/∂rel_d po Wb[2,:], bo x₂ = rel_d z litery `bench/features.py`,
  nie „rel_y"/sin_brg — ERRATUM_XAI-1 §2). Lekcja (a) przy P-XA-2 wycofana —
  oparta na złej wielkości. Lekcja (b) zostaje tylko w części negatywnej:
  pudełko całego korpusu × 20-wymiarowe pudełko stanu przy 20k komórek nie
  certyfikuje nic; teza, że metoda dowozi na małych pudełkach, jest hipotezą
  do sprawdzenia.
- **P-XA-3:** nawias lekcji („kontrakcja kroku = echo vs stabilność okresu =
  generator") nieścisły — kontrakcja kroku to warunek wystarczający
  zapominania, nie hipoteza pary; właściwa para H-echo / H-gen
  (ERRATUM_XAI-1 §1). Mechanizm echo-vs-generator: **NIEROZSTRZYGNIĘTE**.
- **Suma nogi XAI po erracie: 2 ✓ / 1 ✗ / 1 n.r.**
- Nowe wpisy kalibracyjne CC: (1) obalony warunek wystarczający nie potwierdza
  hipotezy przeciwnej; (2) twierdzenia o sieci formułować na wielkościach
  jednoznacznych — pochodna po wejściu (indeks i nazwa z features.py) albo po
  wielkości fizycznej z jawnym „co trzymamy stałe"; (3) weryfikacja CC
  sprawdza mapowanie indeks → cecha literą kodu, zanim przelicza liczby —
  zgodność „co do bitu" na złej cesze nic nie znaczy.

## NOGA XAI-II — ROZLICZONE przy CO-XAI2 (ANEKS_XAI2-1 §3, 28.10.2026)
Prerejestrowane 28.10.2026 (`PRE_XAI2.md` §4; ratyfikacja 28.10, sha PRE
0649deea…0acb); noga zamknięta za 0 bootów:
- **P-XA2-1 (0.60) ✓** — H-ECHO.
- **P-XA2-2 (0.55) ✓** — T4a 0/1631.
- **P-XA2-3 (0.60) n.r.** — n = 8 < 30 (klauzula predykcji). Bez klauzuli
  byłoby ✗: wszystkie 8 obserwacji przeczą.
- **P-XA2-4 (0.50) ✓** — T4a certyfikowane na 100% ε-rur (jedyne T4 po
  różnicówce).

**Suma nogi XAI-II: 3 ✓ / 0 ✗ / 1 n.r.**

Lekcje kalibracyjne: (1) próg minimalnego n chroni przed potwierdzeniem na
małej próbce, nie przed falsyfikacją — w przyszłych PRE kontrprzykład
falsyfikuje niezależnie od n, a próg n dotyczy tylko statusu PROVED;
(2) pokrycie dziedziny (ile ticków w ogóle w niej leży) mierzyć przed
zamrożeniem progu — to nie jest podglądanie wyniku, a d ≤ 4 m dało się
wykluczyć przed PRE; (3) etykiety kierunków z kodu sprawdzać geometrią, zanim
trafią do opisu dla ludzi.

## NOGA WIATR-KAMERA — ROZLICZONE przy CO-WK (ANEKS_WK-1 §3, 29.10.2026)
Prerejestrowane 29.10.2026 (`PRE_WK.md` §4; ratyfikacja 29.10, sha PRE 281750e7…abebd);
noga zamknięta werdyktem V-C za 3/≤9 bootów:
- **P-WK-1 (0.85) ✓** — dym PASS za pierwszym podejściem.
- **P-WK-2 (0.55) ✗** — WK0 2/8 < 6/8.
- **P-WK-3 (0.40) n.r.** — etap B nie poleciał.
- **P-WK-4 (0.90) ✓** — breach 0.
- **P-WK-5 (0.60) ✗** — zero sejwów GEOFENCE; pełzanie nie wystąpiło.

**Suma nogi WK: 2 ✓ / 2 ✗ / 1 n.r.**

Lekcje kalibracyjne: (1) parametry fizyczne nowego habitatu mierzyć wobec zewnętrznego
odniesienia PRZED zamrożeniem — opór k ≈ 1.05 /s był do policzenia z istniejących logów W,
a CC opisał habitat jako „bliżej fizyki", nie mierząc go; (2) predykcje przenoszone z danych
innej epoki harnessu nazywają tę epokę jako czynnik zakłócający — R3 reconu to zrobił, R2 nie.

## NOGA WK-II (opór realny) — ROZLICZONE przy CO-WK2 (ANEKS_WK2-1 §3, 29.10.2026)
Prerejestrowane 29.10.2026 (`PRE_WK2.md` §4; ratyfikacja 29.10, sha PRE f83973c6…c505);
noga zamknięta werdyktem V-A2 za 6/≤18 bootów:
- **P-WK2-1 (0.60) ✓** — G0 8/8.
- **P-WK2-2 (0.45) ✓** — G3 8/8.
- **P-WK2-3 (0.55) ✓** — mediana sweep G0/stock 0.858 ≥ 0.85 (margines 0.008 — trafienie na
  krawędzi, zapisane jako takie).
- **P-WK2-4 (0.90) ✓** — breach 0.

**Suma nogi WK-II: 4 ✓ / 0 ✗.**

Lekcje kalibracyjne: (1) etykietę narzędzia w PRE („driver bez zmian, parametr X") sprawdzać literą
tego narzędzia przed zamrożeniem — druga wpadka tej klasy po route→orbit; (2) prognoza nieliniowości
(opór ~ skala²) chybiła o 41% i uratowała ją tolerancja kalibracji — zapisywać tolerancje przy każdej
interpolacji z dwóch punktów.

## NOGA WK-III (porywy) — ROZLICZONE przy CO-WK3 (ANEKS_WK3-1 §3, 30.10.2026)
Prerejestrowane 30.10.2026 (`PRE_WK3.md`; ratyfikacja 30.10, sha PRE 3758b86f…f76e4);
noga zamknięta werdyktem V-A3 za 4/≤8 bootów:
- **P-WK3-1 (0.70) ✓** — P1 8/8.
- **P-WK3-2 (0.45) ✓** — P2 7/8.
- **P-WK3-3 (0.60) n.r. (adjudykacja CC)** — litera trafiona (P2: 5/8
  epizodów z celem poza kadrem ≥ 5%), ale ten sam miernik przy stałym wietrze
  WK-II daje 4–5/8, a 85% wypadnięć to bok w fazie skanu, niezależny od
  porywów. Predykcja miała mierzyć mechanizm przechyłu, a miernik go nie
  wyodrębnia — nie zaliczam trafienia na źle postawionym mierniku.
- **P-WK3-4 (0.90) ✓** — breach 0.

**Suma nogi WK-III: 3 ✓ / 0 ✗ / 1 n.r.**

Lekcje kalibracyjne: (1) predykcja o mechanizmie musi mieć miernik z bazą kontrolną
wpisaną w PRE (tu: „dół ≥ x% ponad poziom przy stałym wietrze"), inaczej trafia w szum;
(2) (z ANEKS_WK3-1 §1.5, błąd CC w weryfikacji, złapany przed werdyktem) statystyki przechyłu
i kadru liczyć wyłącznie w oknach epizodów — między epizodami dron wykonuje manewry
nienależące do misji.

## ŚCIEŻKA WABIK-III (tor i geometria zbliżenia) — ZAMKNIĘTA DESKIEM przy CO-WABIK3R (ANEKS_WABIK3-1, 30.10.2026)
Bez PRE i bez predykcji numerowanych (recon 0 bootów → zamknięcie deskowe). Jedna
ocena CC do rozliczenia: po odtworzeniu R2 CC wycenił przeżycie kandydata na
świeżych wariantach na „pół na pół" — zanim policzył koszt na uderzających.
Bench już zawierał 37 kontrprzykładów. **✗ jako kalibracja**: ocena wydana przed
policzeniem kosztu na właściwej klasie.

Lekcje kalibracyjne: (1) **kryterium odziedziczone z poprzedniej nogi sprawdzać
przeciw pytaniu bieżącej nogi, zanim się na nim selekcjonuje** — NULL_final był
dobrą miarą dla WABIK-II („czy etykieta zostaje"), a złą dla WABIK-III („czy
etykieta wyprzedza uderzenie bez szkody"); koszt liczyć na klasie, której etykieta
szkodzi (uderzający), jako „kiedykolwiek", nie „na końcu"; (2) „FP 0/N" z próby
N=3 nie jest własnością reguły, gdy bench ma 65 egzemplarzy tej klasy — zawsze
liczyć na pełnej populacji, nie na epizodach z etykietą FP; (3) maska względem
poruszającego się obserwatora mierzy ruch obserwatora (tu: fazę wejścia drona na
orbitę) — zanim ref=dron wejdzie do kryterium, trzeba pokazać, że gaśnie przy
celu wchodzącym pod dronem na orbicie (tu: nie gaśnie, 20/37).

## NOGA WK-IV (turbulencja i sufit wiatru) — ZAMKNIĘTA DECYZJĄ przed lotami sieci (ANEKS_WK4-0, 31.10.2026)
Prerejestrowane 31.10.2026 (`PRE_WK4.md`, sha a530ebb5…1891); S1 nie odbyła się
poza częścią B0 w gołym gz.
- **P-WK4-5 (0.60) ✗** — przyczyna zacięć NIE leżała po stronie publikatora ani
  transportu: wariant bez publikatora miał te same „zacięcia" w zegarze
  ściennym, a wg CLOCK_MONOTONIC zacięć nie było wcale; źródło = skoki
  CLOCK_REALTIME gościa WSL2 (timesyncd). CC szukał przyczyny w nowej
  infrastrukturze, bo była nowa — a miernik był stary i mierzył zegar.
- **P-WK4-1…4, 6, 7: n.r.** (wzór FANTOM / WABIK-II: predykcje sesji, która nie
  zaszła, bez rozliczenia).
- **Rozliczalne już dziś — ✗ kalibracyjne CC:** w PROMPT_WK4_S0 §R2 CC napisał,
  że Dryden przy 2 m/s będzie „łagodniejszy w σ od P2, a szerszy w paśmie";
  recon pokazał łagodniejszy (σ_x 0.33 vs 1.06) i WOLNIEJSZY (90 % mocy poniżej
  0.06 Hz vs 0.25–0.34 Hz). Przy adwekcji V = Ū = 2 m/s skale Drydena
  (L_u ≈ 67 m) dają czasy korelacji rzędu dziesiątek sekund — rachunek, który
  CC mógł zrobić przed napisaniem zdania.

**Suma nogi WK-IV: 0 ✓ / 1 ✗ / 6 n.r. (+1 ✗ kalibracyjne poza numeracją).**

Lekcje kalibracyjne: (1) gdy miernik ważności pada po zmianie infrastruktury,
pierwszy A/B to miernik przeciw drugiemu zegarowi, nie infrastruktura przeciw
sobie — podejrzany „nowy element" był tu fałszywym tropem o pewności 0.60;
(2) widmo turbulencji porównywać z profilem odniesienia liczbą (σ i f90) PRZED
tezą o „szerszym paśmie" — intuicja „turbulencja = szybsza" jest fałszywa przy
małej prędkości adwekcji; (3) recon, który dostał próbnik czasu symulacji vs
ściennego, znalazł problem przed lotami sieci — zasada zostaje: każda nowa
infrastruktura świata dostaje taki próbnik w reconie.

## POZYCJA PERCEPCJA-II (iii) daleki wzrok — ZAMKNIĘTA DESKIEM przy CO-DET3-0 (ANEKS_DET3-0, 31.10.2026)
Recon bez PRE i bez predykcji numerowanych. Jedna ocena CC do rozliczenia jako
kalibracja: w raporcie programu i w rozmowie 31.10 CC opisał daleki wzrok jako
„jedyną pozycję, która rusza zmierzony sufit" — recon pokazał, że na obecnej
siatce nie rusza go wcale (intruz startuje z 15 m; detektor widzi cel w 97.7 %
klatek rampy, zanim misja go przyjmie). **✗ kalibracyjne**: ocena wydana bez
sprawdzenia, gdzie startuje intruz względem granicy korpusu.

Lekcja kalibracyjna: zanim pozycja dostanie etykietę „rusza sufit", sprawdzić
literą manifestu, czy mechanizm pozycji w ogóle występuje w zakresie, w którym
sufit jest mierzony (tu: range0 15 m vs korpus do 14.9 m) — recon deskowy
zrobił to w pierwszym pytaniu i dlatego kosztował 0 bootów.

## NOGA SKAN-II — ZAMKNIĘTA przy CO-SKAN2 (ANEKS_SKAN2-1, 2.11.2026), werdykt V-A
- P-SK2-1 (0.55) c11 ≥ 2/3 D6 PASS ze świadkiem — ✓ (3/3).
- P-SK2-2 (0.70) c11 w pierwszym przejściu t_acq ≤ 8.0 s — ✓ (6.83–7.31).
- P-SK2-3 (0.65) ≥ 1 chybione pierwsze przejście w 8 epizodach — ✗ (0/8).
- P-SK2-4 (0.80) c08 4/4 t_acq ≤ 1.0 s — ✗ (c08_s04 2.09 s; stan tracka w t0).
- P-SK2-5 (0.85) 0 ENTRY FP — ✓.
- P-SK2-6 (0.90) breach 0 — ✓.
- ✗ kalibracyjne CC (1): hipoteza PROMPT_SKAN2_S0 celowała w czas wpatrywania;
  przy 14.7 Hz admisja zachodzi w rampie (recon: 22/36 ENTRY; lot: 5/5).
- ✗ kalibracyjne CC (2): §0.4 PROMPT_SKAN2_S1 zakładał, że `wsl --shutdown`
  usuwa skoki zegara; nie usuwa (usuwa zatrzymanie timesyncd). Bramka napisana
  bez sprawdzenia, kto w torze lotu czyta zegar ścienny (nikt).
- ✗ kalibracyjne CC (3): PRE_SKAN2 V-A pisze „c08" bez sufiksu, a P-SK2-4
  „c08 (4 epizody)"; niejednoznaczność rozstrzygnięta literą Q2 dopiero po
  locie, na korzyść hipotezy. Wykonawca nazwał interpretację przed lotami.

**Suma nogi SKAN-II: 4 ✓ / 2 ✗ / 0 n.r. (+3 ✗ kalibracyjne poza numeracją).**

Lekcje kalibracyjne: (1) przy zmianie kadencji przeliczyć nie tylko stałe,
ale przesłanki, z których je wyprowadzono — sufit TRANSIT był poprawnym
rachunkiem na przesłance z innego reżimu; (2) P-SK2-3 i P-SK2-1 = 0.55 były
zbyt ostrożne: model B-kal przewidział t_acq c11 6.6–7.6 s, lot dał 6.83–7.31;
gdy model skalibrowany na danych trafia w przedział, następna predykcja może
mu ufać bardziej; (3) zbiory w kryteriach PRE nazywać identyfikatorami
epizodów, nie prefiksem komórki.

## KONT recon + errata K2 (ANEKS_KONT-0, 5.11.2026)
Recon bez PRE i bez predykcji numerowanych. Rozliczenia kalibracyjne CC:
- ✗ kalibracyjne (1): hipoteza „sekundy, nie minuty" wpisana do
  PROMPT_KONT_S0 jako skutek dryfu; budżet obcina ściana natywna PX4.
  Trafienie z niewłaściwego powodu liczę jako chybienie.
- ✗ kalibracyjne (2): PROMPT_KONT_S0 cytował ograniczenie renderu
  obalone w ENGINE-RECON (a610810).
- ✗ kalibracyjne (3): CC ratyfikował kanon K2 („zejście współdzielone do
  przyziemienia", t_td 9.8 s) bez sprawdzenia stanu pojazdu (nav_state);
  lista zdarzeń trace była jedynym przyrządem. Klasa „zadany ≠ faktyczny",
  czwarta instancja w programie.
- ✗ kalibracyjne (4): przy pisaniu kanonu K2 CC nie sprawdził, czy
  przesłanka P2-ε (r_est ≤ R_route′) jest niezmiennikiem lotów sieci.
  Nie była (44/48).

Lekcje: (1) każde zdarzenie „wykonano X" w trace sprawdzać z ulogu stanu
pojazdu, zanim trafi do kanonu; (2) przesłanka twierdzenia cytowanego dla
lotów sieci musi być zmierzona na tych lotach albo egzekwowana przez osłonę;
(3) .ulg poza gitem sprawił, że kluczowy pomiar (chwila ściany 4.0 s) jest
w repo niesprawdzalny dla recenzenta — do backlogu: wyciąg z ulogów
(nav_state, xy_valid, failsafe) commitowany jako jsonl przy każdym boocie
denialowym.

## KONT S1 (ANEKS_KONT-1, 6.11.2026)
- P-KONT-1 (0.50) maska + identyczność klatek — ✓ (T=K=0, 8/8; kontrola N 93–99).
- P-KONT-2 (0.65) aiding ≥ 70 s bez nav 14→12 — ✓ (72.01 s; nav 14 do przyziemienia).
Uwaga CC (bez zmiany predykcji): po S1 P-KONT-3 (T* ≥ 30 s) oceniam niżej,
~0.3, zależnie od diagnozy skali przepływu (R-3).

## KONT S2 (ANEKS_KONT-2, 6.11.2026)
- Droga B ratyfikowana przez Olgę: rozliczenia P-KONT-3/4/5/6 przy STOP-KONT2f.
- ✗ kalibracyjne CC (seria): R-3 „skala przepływu" (obalona S2.0);
  kandydat „samozatrucie BSON" (obalony S2b); „sygnatura resetu pozycji"
  (liczniki 0 — poprawna nazwa: szybki odjazd przy zerwanej zgodności
  pozycja–prędkość); hipoteza timestamp_sample 0 (D4a, bez poparcia);
  ✗ rachunkowe: kolejka 1c §4 liczyła 7 lotów zamiast 8.
- Wady wykonawcy nazwane: próba na sucho ręczna zamiast skryptem
  (1d §2.3, koszt 8 min); klucz `verdict` zamiast `werdykt` w kampanii;
  korekta S2b §2: `ekf2 missing data` nie jest wyróżnikiem awarii
  (jest nim urwany sensor_combined).
- Infrastruktura: launcher s2d (gz przed PX4) usuwa 14/14 FAIL
  drugiego bootu; ryzyko s2d: start EKF z biasem na limicie 0.15
  w 2/3 bootów, raz yaw 20.5° na starcie — asercja yaw w driverach
  od drogi B / S4.

## KONT S2 zamknięte Y-a (ANEKS_KONT-3, 6.11.2026): T* = 22 s, Δ_D5 =
1.524 m, R_nom = 27.51 m, koszt bariery 0/48; mechanizm = skok yaw D5
- P-KONT-3 (0.55, T* ≥ 30 s) — ✗ (22 s). P-KONT-4 (0.45, koszt 0) — ✓
  (0/48 przy R_nom 27.51).
- ✗ kalibracyjne CC (seria S2): R-3 „skala przepływu" (obalona S2.0);
  „samozatrucie BSON" (obalone S2b); „sygnatura resetu pozycji"
  (liczniki 0); hipoteza timestamp_sample 0 (obalona D4a); §3B 2B
  „równoczesność jedynym wspólnym czynnikiem" (fałsz — skok yaw);
  rachunkowe: kolejka 1c §4 7≠8 lotów, zdanie Z „≤2.4 m" zamiast
  „≤2.5 m". Diagnoza właściwego czynnika: wykonawca (NOTA-2B), nie CC.
- Wady wykonawcy nazwane: d4c bez rozkładu osi rate (S2e wskazał
  hamowanie); dry-run launchera ręczny zamiast skryptem (8 min);
  klucz verdict/werdykt; nakładka d4_y na błysku cs_in_air (po lotach,
  stan skorygowany); freeze przed rozstrzygnięciem reguły.
- Infrastruktura do S4: launcher s2y obowiązkowy (gz przed PX4);
  bias na limicie 0.15 w 3/6 bootów s2d i restart watchdoga na ziemi
  2/6 — mechanizm niezmierzony, bias przy odcięciu w normie 8/8;
  próbnik zegara + timesyncd stop bez zmian.
- Lekcja: akcja bezpieczna ma więcej stopni swobody niż jej opis —
  yaw = 0 siedział w D5 od R0.3a i był łagodny pod GNSS i zliczeniem;
  nowy estymator zmienia koszt starych akcji. Przy każdej zmianie
  źródła pozycji audytować WSZYSTKIE składowe komend akcji osłony,
  nie tylko tę mierzoną.

## KONT S3 (ANEKS_KONT-4, 7.11.2026): certy KONT PROVED/PASS,
replikacja CC zgodna (z3 5.1.0/5.3.3, różnice tylko z3_lib)
- ✗ CC: PROMPT_KONT_S3 §2 cytował kolejność frozen odwrotnie
  (R-G > R-POS); ANEKS_KONT-3b §1.2 postawił R-G-NOM ponad ABORT/HOLD
  — oba wyłapane przez wykonawcę przed/po kodzie, naprawione literą
  (3b §1.1, 4 §2.2). Lista plików §0.3 za wąska (2 pliki).
- ✗ CC: niespójność brzegowa zamrożenia (R_nom 27.51 vs bariera(0)
  27.303) — skorygowana do 27.30 w 3b §1.7.
- Wady wykonawcy nazwane: pierwotny sat P7 ze zbyt luźnej dziedziny
  (naprawa z dowodem niezmiennika); błąd przyrządu mutantów (19/20 po
  poprawce, 21/21 z mutantem brzegowym).
- Zastany czerwony test r02/test_deadman.py (atrapa bez _sp_yaw,
  od fa5dc242 20.08) — backlog; kryteria PASS modulo ten zastany.

## KONT S4 — wada przyrządu (ANEKS_KONT-4e, decyzja CC 8.11.2026)
- Wada przyrządu: próbnik zegara `results/SKAN2/tools/skan2_zegar.py`
  DOPISUJE do pliku (`open(path, "a")`), więc ponowne użycie nazwy
  bootu skleja próbki dwóch sesji; `--check` liczy wtedy granicę bootów
  VM jako skok (13598.8 s) i stare skoki jako nowe. Skutek: fałszywy
  STOP-KONT4-ZEGAR przed nom_b2_r2 (`fca17539`), 0 bootów; same nowe
  próbki 0 skoków, dryf 0.0 s. Przyrząd nieedytowany (wyniki trzech
  nóg); remedium u źródła: kolejka pomija nazwy, dla których istnieje
  jakikolwiek plik w s4. Wada wykonawcy: pliki zauważone, trybu zapisu
  nie sprawdziłam.

## KONT S4 i zamknięcie nogi (ANEKS_KONT-5, 8.11.2026)
- Drabina S4: FAIL przez (b) w c11_s01 (ε/ε_b 1.113, 548/1411 ticków,
  od 14.9 s) — obwiednia nauczyciela (n=8) za ciasna dla sieci w 1/12;
  pozostałe 11/12 ratio ≤ 0.999. (a)(c)(d)(e) 12/12; ramię (−) 20/24
  czyste (nom_b2 brak — wada kolejki f: lista z `pozostało` przerwanej
  kolejki zamiast siatka−ważne).
- P-KONT-5 (0.60, S4 PASS) — ✗. P-KONT-6 (0.90, breach 0) — ✓
  (45 bootów, 0 naruszeń w całej nodze).
- Wady wykonawcy (seria S4): ROOT w kopii drivera (1 boot); kontrola
  yaw po starcie intruder_motion (sieroty); kolejka bez kontroli V2′
  i V2′ liczona niekanonicznie; próbnik zegara dopisuje zamiast
  nadpisać (fałszywy STOP); lista pozycji z `pozostało` (utrata
  nom_b2). Każda nazwana w swoim STOP-ie, żadna nie skaziła liczb.
- Stanowisko: przyczyną spowolnień był tryb zasilania Windows
  (cichy → wydajny: 0.86–0.89 → 0.97–0.98) — znalazła Olga; launcher
  s2y (gz przed PX4) leczy 14/14 FAIL drugiego bootu, ale psuje
  inicjalizację estymatora w ~połowie bootów (bias/yaw) — mitygacja:
  wymuszony reinit EKF2 w preflight + kontrola kierunku ≤ 10°
  (skuteczna 15/15); watchdog biasu nie wykrywa złego yaw (mierzy
  nie tę obserwowablę).
- Lekcja nogi: obwiednia błędu zdjęta z nauczyciela nie jest
  obwiednią sieci — założenie o rozkładzie błędu musi być mierzone
  na tym samym sterowniku, którego dotyczy dowód (kuzyn „zadany ≠
  faktyczny", piąta instancja w programie).

## KOTW recon 1 (ANEKS_KOTW-1, 8.11.2026): kotwica centralna
CLOSED-BY-RECON (0 bootów)
- Piła nie domyka się przy żadnej z 27 kombinacji; najgorsza przerwa
  orbity 37.1 s (CC: 38.6 s niezależnie) ⇒ ε_b(37) 4.567 + Δ 1.524 =
  6.091 > 5.79 przy idealnej poprawce. Mechanizm: orbita patrzy na
  zewnątrz, start ma kamerę poziomą nad kotwicą.
- ✗ projektowe CC: pozycja kotwicy (0,0) wpisana w prompt bez rachunku
  geometrii spojrzenia; recon sfalsyfikował ją za 0 bootów (ósme
  zamknięcie kierunku przy biurku w programie).
- Znaleziska przechodnie: EV-aiding PX4 1.16.2 (timeout 1 s)
  niezdatny do poprawek co ~20 s ⇒ wariant B (osłona) jedyny;
  fałszywa admisja na obiekcie statycznym nie jest wykluczona literą
  percepcji (paralaksa w MTI, brak bramki pozycji w odświeżeniu
  tracku) — ryzyko nazwane dla każdej przyszłej kotwicy.

## KOTW recon 2 i zamknięcie nogi (ANEKS_KOTW-2, 8.11.2026): obwód
0/576 ⇒ KOTW CLOSED W CAŁOŚCI (0 bootów)
- Obwód naprawia czas (najgorsza przerwa orbity 37→9.4 s, start ~0 s,
  widoczność 87%), ale nie dokładność: poprawka z 23–44 m to 2.5 m
  optymistycznie przy budżecie 0.54 m w komórce najgorszej orbity;
  para kotwic 5/48 (geometria przecięcia mnoży błąd elewacyjny).
  Granica: pozioma kamera nie daje naraz krótkiej przerwy i bliskiego
  zasięgu. Dziewiąte zamknięcie przy biurku; cała noga za 0 bootów.
- Bias yaw −3° z S4 rozdzielony: prawdziwy błąd estymatora
  (−0.6…−5.1°, δψ 5.8°), nie artefakt dopasowania czasu.
- R4′: przejęcie tracku w paśmie [5, 18] m geometrycznie niemożliwe
  z obwodu; koincydencja ≤ 5° na 18–45 m do 8.3% próbek ⇒ bramka
  pozycji przewidywanej warunkiem PRE każdej przyszłej kotwicy.
- ✗ kalibracyjne CC ×2 (rozmowa, nie prereg): szanse domknięcia piły
  dawane na 0.5–0.6 i 0.6 — wynik 0/27 i 0/576; za optymistycznie
  o geometrii spojrzenia, drugi raz w tej samej nodze.
- Wykonawca: obie sesje deskowe czyste (bramki, zakresy, prereg
  wykonany co do litery). Znalezisko CC bez wpływu na liczby: remis
  dominanty fazy w kotw2_obwod.py łamany porządkiem zbioru
  (zależnym od środowiska) — 96 etykiet, werdykt 576/576 niezmienny.

## NADIR — otwarcie nogi (PRE_NADIR, 9.11.2026)
- Recon NADIR (0 bootów): 264/540 kombinacji dopuszczalnych; s10 "0",
  ID W1, tryb 12: 48/48 komórek, wąskie gardło c08_s02 zapas 0.11 m
  (ZMIERZ, tryb 1) / 0.60 m (tryb 12); pokrycie pełną postawą ≥1
  znacznik 100% misji, τ_max ≤ 0.96 s. CC niezależnie: pokrycie 100%,
  r_h p50 3.7 m, c08_s02 zapas 0.116 — zgodne.
- ✗ mechanizmowe CC (rozmowa, 9.11): założenie „poprawka tylko
  w osłonie wystarcza, sieć nie widzi znaczników" obalone w R3 —
  setpointy pozycyjne żyją w ramie EKF, misja bez ramy B+ kończyłaby
  się ~21 s. Znalazł wykonawca; stąd B+ w PRE.
- P-NADIR-1 (0.70): S1 przechodzi w całości (detekcja ID ≥ 95%,
  zero fałszywych admisji, tempo ≥ 0.93).
- P-NADIR-2 (0.75): warunek ważności B przechodzi w S2.
- P-NADIR-3 (0.55): S4 PASS pełną literą (a)–(f).
- P-NADIR-4 (0.90): breach 0 w całej nodze.
- Uwaga kalibracyjna: po dwóch zawyżonych szansach w KOTW powyższe
  dawane ostrożnie; różnica mechaniczna — geometria NADIR położona
  pod kamerą i zmierzona na GT, nie zgadywana.

## NADIR S1 — STOP tempa i naprawa (ANEKS_NADIR-1, 9.11.2026)
- Bramka tempa przerwała pierwszy boot epizodowy przed uzbrojeniem
  (0.854 < 0.93); A/B gołego gz rozdzielił hipotezy: drugi render +
  detekcja kosztują 11–13% przy ~9.6 Hz (CC przeliczył z surowych
  próbek). Zero lotów spalonych; sonda wykryła koszt przed serią.
- ✗ projektowe CC ×2: (i) prompty reconu i S1 nie kazały sprawdzić
  kolizji węzłów siatki z bryłami świata — 7/37 pod skrzynkami
  i budynkiem wyszło dopiero w sondzie; (ii) montaż kamery w origin
  base_link przypięty w PRE bez rachunku zasłony kadłuba — 16.9%
  stożka wyszło w b1. Obie naprawy aneksem przed lotami.
- Wykonawca: R1 identyczność 10/10 domknięta porządnie; decyzja
  visibility_flags (przepływ nie widzi znaczników — litera ε_b)
  przyjęta jako dobra; wady drobne nazwane (runner stdout, pierwsza
  maska, errata OpenCV) — żadna nie zużyła bootu ani nie skaziła
  liczb.

## NADIR S2 — charakteryzacja piły (ANEKS_NADIR-2, 9.11.2026)
- 4 cięcia GNSS pod osłoną 2d: 0 przekroczeń ε_b w 440 oknach bez
  GNSS (max 0.94 miarą 3D; CC niezależnie 0.84 w 2D); sieć na p_corr:
  ENTRY i orbita do REFUSE(T*) 4/4, kontynuacja 21.96–21.97 s; skoki
  p_corr ~5× szum GNSS i sieć je znosi; u_max 2.02–2.24 przy
  m 2.99–10.33. P-NADIR-2 (0.75) ✓.
- FREEZE: ε_fix_freeze per koszyk 0.305/0.293/0.227/0.582 m
  (1.5 × max użytej poprawki, oba reżimy); litera przyjęcia + r_h<8 m.
- Bias kursu estymatora stały w epizodzie, różny między bootami
  (−1.5…−4.6°), nie dryfuje po cięciu (trend ≤0.27°/s); para znaczników
  (87% poprawek) zdejmuje go z namiaru — potwierdzenie mechanizmu
  z reconu KOTW R2 na żywym torze.
- Trzecia instancja „zadany ≠ faktyczny" w rodzinie c11: obwiednia
  nauczyciela 2d przekroczona o 6% długohoryzontowo (ten sam EKF, bez
  nakładki); NADIR nieczuły — konsumuje ε_b tylko w prefiksie okien.
- ✗ projektowe CC: PROMPT_NADIR_S2 §R żądał „2 cięcia na boot" wbrew
  literze drivera KONT (cięcie kończy boot zejściem) — wychwycone
  przez wykonawcę przed spaleniem boota; decyzja: 1 cięcie/boot.
  ✗ metodyczne CC (weryfikacja S1F): miara odległości tracku od
  znacznika liczona poziomo zamiast 3D — 2 fałszywe trafienia,
  skorygowane w tej samej turze, litera wykonawcy słuszna.
- Wykonawca: przyczyną braku summary rejestratora była własna
  procedura sprzątania launchera z S1 (znaleziona i naprawiona,
  a91bb94e); jedno kryterium walidacji suchej postawione źle
  i poprawione przed lotami (nazwane w raporcie); strażnik kolizji
  zablokował start od słowa w linii poleceń (0 bootów). Dwa booty
  przerwane bramką tempa przed uzbrojeniem (0.910/0.925) — remedium
  operatora (restart WSL) skuteczne, wzór 4e.

## NADIR S4 — stanowisko (ANEKS_NADIR-3, 10.11.2026)
- S4: 5 bootów zużytych, 1 ważny (nominał); 4 przerwane bramką tempa
  przed uzbrojeniem (0.928 / 0.734 / 0.740 / 0.781). W nodze 7 z 16
  bootów spłonęło przed uzbrojeniem — zero informacji o tezie.
- Znalezisko CC z danych: tempo ↔ czas wnioskowania detektora
  r = 0.994 (15 bootów), ArUco na CPU +20% ⇒ wspólny, skokowy czynnik
  prędkości maszyny ~0.75–0.81. Pozycja c01_s01 wykluczona (leciała
  w nominale przy 0.956; „3/3" to artefakt kolejki ponowień). Termika
  wykluczona dla wieczoru (9 min płasko; przełączenie w bezczynnej
  przerwie 13–19 min po ostatnim sygnale operatora).
- ✗ CC ×2: (i) zatwierdzona kontrola „goły gz" (wzór 4e/f) nie jest
  związana obliczeniowo — ślepa na spowolnienie maszyny; (ii) grant
  „+2" przyjęty bez przeliczenia 11 + 16 = 27.
- Wykonawca: zbieżność z pozycją nazwana jako nierozstrzygnięta
  zamiast ogłoszona mechanizmem — dobra praktyka; luz nogi policzony
  2 zamiast 3 (nazwane w STOP-STANOWISKO).
- Lekcje: kontrola stanowiska musi być związana obliczeniowo; bramka
  zdrowia należy przed bootem, nie w nim; „ta sama pozycja" przy
  kolejce z ponowieniami nie niesie informacji o pozycji.

## NADIR S4 — diagnoza stanowiska (ANEKS_NADIR-4, 10.11.2026)
- Matryca M0–M3/M5 (0 bootów): okno w tle, profil turbo i 30 min
  bezczynności nie zmieniają tempa; częstotliwość CPU stała, brak
  procesu hosta. H2 (bezczynność / rdzenie E), hipoteza nr 1 CC —
  ✗ kalibracyjne CC.
- Znalezisko wykonawcy: dzisiejsze sondy zaniżał zegar — timesyncd
  wznowiony przez kolejkę przy STOP-ie daje skoki +1.35 s co ~33 s
  (ok. 4% tempa); po korekcie przyrząd A 0.937 / 0.920 ≈ odniesienie
  0.928 (CC przeliczył niezależnie, zgodność do 0.001). Wada
  wykonawcy nazwana: stan timesyncd zapisywany w każdej sondzie,
  niesprawdzony przed matrycą.
- Znalezisko CC: pod obciążeniem stosu karta graficzna pracuje na
  277 MHz w stanach P5/P8 przy ~21 W, z aktywnym programowym limitem
  mocy; tempo koreluje z udziałem P8 (r = −0.59, n = 22), a trzy
  najwolniejsze przebiegi nie mają żadnej próbki w stanie wyższym.
  Sygnatura
  „zdrowy start, zjazd po 10–20 s" wspólna z porannym wolnym bootem.
  Hipoteza wiodąca dla skoków −20…−25%, niepotwierdzona na dużym
  skoku.
- ✗ projektowe CC: ANEKS_NADIR-3 zlecił nową sondę zamiast użyć
  przyrządu, z którego pochodziło odniesienie — powstał przyrząd B
  o innym zachowaniu; bramka wraca na przyrząd A.
- Lekcje: pomiar tempa tylko przy zatrzymanym timesyncd (asercja
  w narzędziu); odniesienie i bramka muszą pochodzić z tego samego
  przyrządu; tempo programu liczone jest zegarem gościa, który chodzi
  ~3–4% wolniej od czasu rzeczywistego.
- Zmiana PRE (sygnał „ratyfikuję N3", ANEKS_NADIR-3 §4.4): limit nogi
  30 → 35, limit S4 19 → 24.

## NADIR S4 i zamknięcie nogi (ANEKS_NADIR-5, 11.11.2026)
- Drabina S4: FAIL przez (g) w 5/12 cięć — przyrost błędu EKF
  w oknie między poprawkami ponad ε_b(⌊τ⌋) w 36 z 6581 okien bez
  GNSS (0.55%, max 2.09; c08_s01, c08_s02, c10_s01, c10_s02,
  c11_s02). (a) 12/12 po orzeczeniu CC (od wstrzyknięcia
  110.004–110.052 s; analizator liczył od stempla zdarzenia,
  4–12 ms później). (b)–(f) 0 naruszeń, nominały 16/16. CC odtworzył
  (g) definicją analizatora co do okna (28/28 epizodów), resztę
  własnym kodem; (d) przyjęte z ULG wykonawcy.
- Zdolność zmierzona: 12/12 cięć × 110 s (5 × T*) bez GNSS na
  pozycji poprawianej znacznikami — track 100%, REFUSE 0, breach 0,
  margines do R_E min 7.47 m, koszt bariery 0; błąd pozycji
  poprawionej płaski w czasie (p95 0.2–0.4 m, max 0.67–0.73 m) przy
  błędzie własnym EKF do 8.5 m.
- P-NADIR-1 (0.70) — ✗ (śmierć S1 po literze tempa, ANEKS_NADIR-1;
  po naprawie S1F czyste). P-NADIR-3 (0.55, S4 PASS) — ✗: litera
  (a)–(f) z PRE spełniona, bramka z (g) dodanym przed lotami FAIL.
  P-NADIR-4 (0.90, breach 0) — ✓ (31 bootów). Noga: 2/4 przy sumie
  szans 2.90 — szanse CC nadal zawyżone. ✓ P-NADIR-2 z S2 było
  wynikiem próby 440 okien; na 6581 oknach warunek nie trzyma.
- Przesłanka A-nadir (CC) nie trzyma w obu połowach. (i) Przyrost:
  32 okna to zrywy błędu EKF 1.6–2.5 m/s przy hamowaniu (31/32 przy
  malejącej prędkości, |a| mediana 1.9 m/s²; tylko sześć
  najszybszych komórek), 4 okna to dziury przyjęcia 0.4–1.0 s (oba
  maksima). (ii) Błąd poprawki: bez GNSS 62/6582 ponad
  ε_fix_freeze (max 2.21), nominały 314/6565 — wszystkie jednym
  znacznikiem; para 0 z 11 250 (max 0.225 m). Błąd jednego
  znacznika ≈ r_h · sin|bias kursu| (r = 0.71). Suma per tick:
  2–40 z 27 253 ticków ponad sumę składników (o 0.11 m
  w najgorszym).
- ✗ projektowe CC ×4: (1) obwiednia nauczyciela 2d użyta wobec sieci
  w prefiksie okien i przyjęta po S2 przy max 0.94 na 440 oknach —
  zapas 6% na próbie za małej na ogon ~1%; teza z ANEKS_NADIR-2
  §3.2 („NADIR nieczuły") obalona; kolejna instancja „zadany ≠
  faktyczny" i powtórka lekcji KONT-5. (2) FREEZE „1.5 × max"
  z czterech cięć nie rozróżnia trybu poprawki i wyszedł
  niemonotoniczny (koszyk 4–6 m najniższy) — przyjęty bez pytania.
  (3) Litera S4 strzegła jednej połowy przesłanki certu. (4) Litera
  przyjęcia (18 px, r_h < 8 m, krawędź) zostawia klatki bez
  obserwacji, a ⌊τ⌋ nie widzi ich przez pierwszą sekundę — wbrew
  zdaniu z ANEKS_NADIR-2 §2.
- ✗ metodyczne CC (weryfikacja S4): okna grupowane po `seq` (licznik
  rekordów, nie poprawek); hipoteza artefaktu wyrównania czasu
  (obalona: przy zerowym przesunięciu 17 okien, max 1.88); hipoteza
  narastania z czasem (obalona: 5/10/8/7/6 na 22 s). Skorygowane
  w tej samej turze.
- Korekta w przód zdania z ANEKS_NADIR-2: bias kursu po cięciu nie
  jest stały — mediana 12 lotów −3.4° → +1.2° w 110 s, tempo maleje
  (0.94 / 0.62 / 0.46° na kolejne 22 s); dalej niezmierzone.
- Wykonawca: kampania 16/16 bez STOP-u stanowiska; analizator (g)
  poprawny; (a) i własna wada nastawy nazwane uczciwie; „mechanizm
  niezmierzony" zamiast zgadywania. Wady: nastawa T_CONT równa
  progowi i odniesienie od stempla zdarzenia; ostatnie okno epizodu
  niedomykane (4 fałszywe „✗ (g)" w nominałach, kolumna
  informacyjna); obserwabla błędu poprawki policzona, lecz
  niewyniesiona do raportu płaskiego mimo wartości niezerowych
  w 27/28 epizodów.
- Stanowisko (10.11, DIAGNOZA_STANOWISKA_2 i decyzje CC bez aneksu):
  zegar gościa pod obciążeniem równy zegarowi Windows (1.00000) —
  zdanie „gość ~3–4% wolniej" z ANEKS_NADIR-4 cofnięte, ✗ CC;
  ustawienie karty „maksymalna wydajność" odrzucone regułą; drugi
  użytkownik karty po stronie Windows obniża tempo (PredatorSense
  ~33% ⇒ 0.85, Chrome ~18% ⇒ 0.88–0.90; r = −0.94, n = 11) — reguła
  stanowiska: podczas kolejki żadnych aplikacji okienkowych poza
  terminalem. Skutek: 16 bootów 0.9355–0.9744, bramka zdrowia
  18 pomiarów / 3 NO-GO / 0 STOP-ów. Duży skok −20…−25% nigdy
  niezarejestrowany z telemetrią — przyczyna nieustalona.
- Lekcje nogi: przesłanka dowodu ma być mierzona na wielkości, którą
  dowód konsumuje (tu |p_corr − GT| per tick), na sterowniku
  docelowym i na próbie rzędu ekspozycji bramki; każda połowa
  przesłanki dostaje kryterium w literze; obwiednia niemonotoniczna
  tam, gdzie fizyka jest monotoniczna, to sygnał za małej próby;
  litera przyjęcia obserwacji wymaga rachunku pokrycia.
