# ANEKS_WABIK2-1 — zamknięcie nogi WABIK-II ścieżką śmierci S1 (zero lotów) + KSIĘGA + CO

CC · 27.10.2026 · łańcuch WABIK2 (commity na origin: 580eeb8e ARCH-1 +
b260de4b STOP-WABIK2-1). Aneks samowykonalny w zakresie §4 (sesja CO, jeden
commit, zero bootów). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-WABIK2-1

Przyjęte po weryfikacji CC z repo WYKONANIEM: ARCH-1 bajt-w-bajcie (sha PRE
w korzeniu = dokument ratyfikowany); zakres czysty (4 nowe pliki;
FREEZE_WABIK2 i manifest świeżych wariantów SŁUSZNIE nie powstały — ścieżka
śmierci nie ma czego mrozić); **kotwica implementacyjna potwierdzona**
(wariant bazowy = wyniki wabik_sig v1 co do setnej: 17.62/20.99/15.51/24.88 s,
NULL_final 13/115); **selekcja przeliczona mechanicznie własnym kodem na
pełnej tabeli: 0 rozbieżności na 26 wariantach, zbiór dopuszczonych PUSTY**
literą kryterium PRE §2.2; krawędź Pareto z mojego przeliczenia OSTRZEJSZA
niż w raporcie płaskim: TP≥5/6 ⇒ NULL_final = 15 (dokładnie), a
**NULL≤13 ⇒ TP ≤1/6** (raport pisał ≤4/6 — górne ograniczenie prawdziwe,
litera tabeli twardsza); FP=0/3 i ORB=2/2 tworzą po 26 wariantach zbiór
jednoelementowy {(0,2)} — podłoga klatkowa potwierdzona dwudziestosześciokrotnie.
Budżet 0/≤4. Zero edycji istniejących; wabik_sig v1 i progi FREEZE_WABIK
nietknięte.

## §2. WERDYKT NOGI: ŚMIERĆ S1 literą PRE §2.4

**„Reguła czasowa nieosiągalna przy tym szumie toru bez zmiany cech"** —
zamknięta przestrzeń 26 wariantów A/B/C wyczerpana, żaden nie spełnia
koniunkcji kryterium. Trade-off jest zmierzony, nie domniemany: warianty
ratujące TP (B×C: 5/6 z flagami w 8.38 s — szybciej niż reguła (i)
kiedykolwiek) płacą dokładnie dwoma epizodami wędrowców v=0.5 na populacji
normalnej (c07_s01, c05_s04 — próg frakcji jest dla wędrowca łatwiejszy niż
próg ciągłości); jedyny wariant czystszy od bazy na NULL (C solo: 11/115)
nie ratuje TP (1/6).

**Zdanie kanoniczne (do cytowań):** „Czysta agregacja czasowa nie domyka
rozpoznania wabika przy tym szumie toru: na 26 wariantach zamkniętej
przestrzeni TP≥5/6 i czystość populacji normalnej nigdy nie zachodzą naraz
(krawędź Pareto: NULL≤13 ⇒ TP≤1/6) — wąskie gardło leży piętro niżej,
w jakości predykatu klatkowego (piki v_rad estymaty toru); zero FP i poprawne
odwołania trzymają we wszystkich 26 wariantach."

**Nota (bez poluzowania czegokolwiek):** dwa epizody, o które pada
dopuszczenie, należą do klasy antycypowanej w PRE (i) §1 jako granica
nierozróżnialności — PRZYSZŁA prerejestracja warstwy cech może zdefiniować
kryterium NULL z tą klasą rozdzieloną jawnie; TA noga stoi literą, która
była zamrożona. Wartości trwałe: **s1_tabela.json = gotowy bench
akceptacyjny** (nowa warstwa cech musi dać wariant spełniający stare
kryterium offline, zanim cokolwiek poleci), kotwica implementacyjna jako
wzór, podłoga potwierdzona 26×.

## §3. KSIĘGA — rozliczenie (wpisy przy CO, append-only)

- **P-W2-1 (0.75): NIE** — selekcja offline nie znalazła wariantu. Lekcja
  kalibracyjna: **człony kryterium koniunkcyjnego wyceniać ŁĄCZNIE, nie
  marginalnie** — mechanizmy naprawy trafiły w TP (5/6, szybko), ale
  sprzężenie TP∧NULL było właściwym przedmiotem predykcji.
- **P-W2-2, P-W2-3, P-W2-4: n.r.** — S2 nie poleciała (wzór rozliczeń
  FANTOM: predykcje sesji, która nie zaszła, bez rozliczenia).

## §4. Zlecenie CO-WABIK2 — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP.
Pliki (lista zamknięta): korzeń **`ANEKS_WABIK2-1.md`** (ARCH-1, verbatim,
pierwszy w commicie); **EDYCJA `KIERUNKI_PO_PLANIE.md`** (dopisek append-only):
**WABIK-II / REGUŁA CZASOWA → CLOSED-BY-DESK-DEATH (0 bootów)** ze zdaniem
kanonicznym §2 i odsyłaczami (RAPORT_WABIK2_S1, s1_tabela.json); pozycja
następcza SCALONA (jedna, nie dwie): **„TOR-CECHY (wygładzenie v_rad przed
predykatem / estymator toru)" — zbieżna z MULTI-TARGET/TOŻSAMOŚĆ TRACKA**
(oba wątki potrzebują porządniejszego toru; aktywa: s1_tabela jako bench
akceptacyjny offline, mapa przeskoków z WABIK (i) S1, nota wędrowców §2;
trigger: decyzja Olgi); pozycje IMITACJE i ODPOWIEDŹ-EKONOMIA bez zmian.
**Wpisy KSIĘGI** §3 (P-W2-1 NIE z lekcją koniunkcji; P-W2-2…4 n.r.;
append-only, wzór CO-WABIK). ŻADNYCH edycji raportów, RECON-ów ani kodu.
Raport płaski: diff-stat, pełna treść dopisków, porcelain. **Push = Olga
(„wypchnięte" — CC czyta z repo).** STOP.

## §5. Status

Noga WABIK-II: **CLOSED — 0/≤4 bootów**; pierwsza noga programu zamknięta
w całości przy biurku PO pełnej prerejestracji (dotychczasowe zamknięcia
deskowe były reconowe — ta przeszła przez ratyfikowany PRE i umarła dokładnie
tam, gdzie PRE kazał jej umrzeć, zanim wydała choć jeden lot). Wątek wabikowy
po dwóch nogach, bilans uczciwy: cechy separują, zero FP potwierdzone 26×,
flagi w 8.4 s są osiągalne — ale gwarancja czasu i czystości naraz czeka na
warstwę toru (pozycja TOR-CECHY ∪ MULTI-TARGET). Breach 0 / REFUSE 0
programowo bez zmian — w tej nodze nic nie latało. Program w trybie katalogu.
