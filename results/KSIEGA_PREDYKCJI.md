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
