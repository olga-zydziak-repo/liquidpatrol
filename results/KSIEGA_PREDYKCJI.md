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

**Suma K2: 2 ✓ / 2 ✗** — obie ✗ są „bezpieczne": jedna to zejście poniżej przewidzianego wychylenia
(P-K2-3), druga to niewystąpienie przewidzianego defektu (P-K2-1).

---

## SUMA ZAKRESU OBOWIĄZKOWEGO

Liczone wyłącznie z rozliczeń w plikach, czyste ✓/✗ (partiale kierunkowe wyłączone):

- INFRA-3: **3 ✓ / 0 ✗** (+1 kierunkowa: P4).
- Ławka: **7 ✓ / 4 ✗**.
- Sieć: **7 ✓ / 2 ✗**.
- K2: **2 ✓ / 2 ✗**.

**RAZEM (zakres obowiązkowy): 19 ✓ / 8 ✗** (+1 kierunkowa INFRA-3 P4, poza sumą).
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

## OTWARTE (prerejestrowane 11.09.2026, CC v2)
- P-CC2-1: jeśli noga FV otwarta, część (ii) w wariancie „własności samej sieci CfC narzędziem
  off-the-shelf" kończy się wynikiem częściowym albo śmiercią na pokryciu narzędzi — p≈0.7.
- P-CC2-2: follow-up SPRIND dostaje merytoryczną odpowiedź w ≤3 tygodnie od wysyłki — p≈0.3.
Rozliczenie: przy raportach nogi FV i warstwy 0.
