# ANEKS_WABIK-2 — werdykt nogi WABIK (iii): falsyfikacja reguły czasowej przy działającej warstwie cech + KSIĘGA + CO (zamknięcie)

CC · 27.10.2026 · łańcuch WABIK (commity na origin: bf776d20 + ea49de02 +
2729e988 + 0e218dbf STOP-WABIK2). Aneks samowykonalny w zakresie §4 (sesja CO,
jeden commit, zero bootów). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-WABIK2

Przyjęte po weryfikacji CC z repo WYKONANIEM: ARCH-1 bajt-w-bajcie; zakres
141 nowych plików + 1 M (driver wabik_s1_boot.sh — wyłącznie parametryzacja
katalogu WABIK_S_DIR, wstecznie identyczna, zadeklarowana — przyjęte;
narzędzie własne nogi, niezamrożone); **klasyfikator przeliczony WŁASNĄ,
niezależną implementacją litery FREEZE na surowych feedach wszystkich 11
epizodów:** struktura wyników identyczna (LOITER 2/2 flaga-kiedykolwiek,
ZBLIŻ 0/2, FP 0/3 z podłogami 0.04–3.40 m), **dominacja resetów od pików
v_rad potwierdzona wprost** (w00a: 14/20 resetów to izolowane piki; w00b:
9/14); czasy-do-flagi między dwiema implementacjami TEJ SAMEJ litery różnią
się o ±50% (np. w00a 17.6 vs 26.6 s) — **to niezależny dowód diagnozy:
reguła czasowa jest krucha na estymator, nie tylko na szum**. Sędzia
przeliczony (GT manifestu, świadek obok): c08_s03 PASS 5.99 ✓; c10_s02 FAIL
[c_sweep 621.7] = znana wariancja graniczna omiatania tej komórki (klasa
near-missów z POŚCIG-u; frac 0.978 i d_min w normie — poza klasyfikatorem) ✓;
m00 (M-ŁUK) PASS; m01_s01/s02 PASS, sweep 988/915 ✓. Reżim OPS 3/3, budżet
3/≤8 (noga 7/≤11), 11/11 VALID, breach 0 / REFUSE 0. Manifest S2: kopie
c08_s03/c10_s02 dowiedzione diffem (tylko episode_id); FREEZE_WABIK nietknięty.

## §2. WERDYKT NOGI (zdania zamrożone PRE §3)

- **T-W-TP: FALSYFIKACJA PROGÓW — zaszła** (etykieta w ≤15 s w ≤1/6 przy
  progu falsyfikacji ≤2/6) ⇒ literą PRE: „progi z NULL nie przenoszą się na
  TP — wracamy do cech".
- **T-W-FP: twardy wskaźnik SPEŁNIONY — 0/3 flag** na celach poważnych.
- **T-W-ORB: pytanie R4-niezmierzone DOMKNIĘTE POZYTYWNIE** — track na celu
  1.000 pod zmianą kursu, D6 2/2 PASS; semantyka etykiety-stanu zadziałała
  wzorcowo (flaga na fazie wabikowej toru → ODWOŁANIE po zejściu <5 m).

**Rozkład uczciwy:** warstwa CECH działa (LOITER/STYCZNY flagowane
kiedykolwiek, zero FP — podłoga 5 m blokuje każdego poważnego), pada
WYŁĄCZNIE **reguła czasowa**, z trzema zmierzonymi mechanizmami: (1) piki
szumu v_rad toru percepcyjnego rwą 12-sekundowe streaki (pojedyncze klatki
zerują licznik ciągłości); (2) rodzina ZBLIŻ-ODSKOK strukturalnie poniżej
progu (fazy ~8 s < T_FLAG 12 s — przewidziane przed bootem, potwierdzone);
(3) zegar od pierwszej klatki zawyżany przez stale-klatki brzegu okna.

**Zdanie kanoniczne (do cytowań):** „Rozpoznanie behawioralne wabika ma
działającą warstwę cech (flagi na rodzinach krążących, zero fałszywych
alarmów na poważnych) i sfalsyfikowaną regułę czasową: wymóg 12 s
nieprzerwanej zgodności pada na pikach szumu estymaty toru — dwie
implementacje tej samej zamrożonej litery różnią się czasem flagi o ±50% —
a naprawa (reguła odporna na przerwy) iteruje się offline na zalogowanych
feedach za zero bootów."

## §3. KSIĘGA — rozliczenie P-WB-1…6 (wpisy przy CO, append-only)

- **P-WB-1 (0.70): NIE** — kotwica sędziego złamana w konfiguracji A smoke.
- **P-WB-2 (0.55): NIE** — przeskoki 25% w fazach werdyktowych.
- **P-WB-3 (0.65): NIE** — falsyfikacja zdaniem zamrożonym (≤1/6).
- **P-WB-4 (0.75): TAK** — FP 0/3.
- **P-WB-5 (0.60): TAK** — ORB 2/2, track 1.000, separacja ≥4 m.
- **P-WB-6 (0.85): TAK** — breach 0 / REFUSE 0 w całej nodze (7 bootów).

**Bilans 3/6.** Wpisy kalibracyjne: (a) z ANEKS-1 — konfiguracje przestrzenne
projektować per FAZA lotu, nie per epizod; (b) NOWY: **wymagania ciągłościowe
przeliczać przez zmierzoną stopę zakłóceń estymaty PRZED zamrożeniem** —
stopa pików v_rad była mierzalna na NULL przy biurku, a sprzężenie
T_FLAG=12 z limitem zdania zamrożonego (≤15 s) zostawiło zero marginesu na
szum; reguła progowa na strumieniu szumnym wymaga tolerancji przerw
z konstrukcji, nie z nadziei.

## §4. Zlecenie CO-WABIK — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP.
Pliki (lista zamknięta): korzeń **`ANEKS_WABIK-2.md`** (ARCH-1, verbatim,
pierwszy w commicie); **EDYCJA `KIERUNKI_PO_PLANIE.md`** (dopisek stanu
katalogu, append-only): noga **WABIK ścieżka (iii) → CLOSED** z werdyktem
trójdzielnym §2 i zdaniem kanonicznym, odsyłacze do RAPORT_WABIK_S1/S2
i FREEZE_WABIK; dopisane pozycje: **WABIK-II / REGUŁA CZASOWA** (następca —
aktywa: feedy 11 epizodów S2 w repo, trzy kierunki naprawy z §2, ścieżka:
iteracja reguły OFFLINE na zalogowanych feedach za 0 bootów → FREEZE nowej
reguły → potwierdzenie w locie na ŚWIEŻYCH wariantach parametrów trajektorii
(anty-overfit — lekcja CH90), wycena ≤4 booty; trigger: decyzja Olgi);
**MULTI-TARGET / TOŻSAMOŚĆ TRACKA** (wg ANEKS-1 §2 — aktywa S1, trigger
verbatim); **IMITACJE / MIKRO-SYGNATURA** (krok 1 deskowy: rachunek
widzialności mikro-ruchu w px przy 9 px@15 m i 14.7 Hz; trigger: po
WABIK-II); dopisek przy pozycji 1b(ii) weryfikacja sieci: rozszerzenie
o **XAI/replay aktywacji** (S0 deskowe — kopia modułu + wagi 0337d5ea +
replay feedów wszystkich kampanii, 0 bootów). **Wpisy KSIĘGI** P-WB-1…6
+ dwie lekcje §3 (append-only, wzór CO-PERC2). ŻADNYCH edycji raportów,
RECON-ów ani kodu. Raport płaski: diff-stat, pełna treść dopisków, porcelain.
**Push = Olga („wypchnięte" — CC czyta z repo).** STOP.

## §5. Status

Noga WABIK ścieżka (iii): **CLOSED — 5/≤11 bootów** (S1: 2 — s1_smoke,
s1_rozdzielony; S2: 3 — bA, bB, bC; katalogi bootów w repo potwierdzają 5).
Nota errata-w-przód: raport płaski STOP-WABIK2 pisze „noga 7/≤11" —
rozbieżność arytmetyczna do odnotowania w raporcie CO (litera raportu S2
nietykalna); stan faktyczny = 5. KSIĘGA 3/6 z dwiema lekcjami,
breach 0 / REFUSE 0. Program
zyskał: wabik w świecie bez dotykania zamrożonych, działającą warstwę cech
z twardym zerem FP, domknięty pomiar manewru pod orbitą (R4), zmierzoną
granicę single-target i tanią, dobrze wycenioną drogę naprawy reguły
czasowej. Pierwsza noga programu zamknięta falsyfikacją głównego wskaźnika —
KSIĘGA ma pełnokrwiste NIE na dźwigni, z mechanizmem i ceną naprawy; to jest
dokładnie ten rodzaj porażki, na który reżim był projektowany.
