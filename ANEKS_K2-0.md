# ANEKS_K2-0 — ratyfikacja RECON_K2, erratum #3, mikrofakty przed PRE_K2

LiquidPatrol · pozycja 6 (K2) · CC 6.09.2026 · łańcuch nowej nogi: ANEKS_K2-n, ten aneks = -0
· niepushowane: 62a068a (recon), e29a154 (higiena poz. 5)

## §1. Recon przyjęty; przyjęta też nota prowieniencji clip-buildera (e29a154 — źródło == film == verbatim).

## §2. ERRATUM #3 (doc-only + jedna klatka filmu; wykonanie przed jakąkolwiek wysyłką zewnętrzną)

Fakt R1: `bench_flight.py:326` woła `shield.step` z `pos_flag=None` na sztywno ⇒ monitor POS_DEGRADED
nieuzbrojony przez CAŁĄ nogę sieci; ławka = własna pętla (nie gate), `certs_selfcheck` w niej nie biegł.
E1 RAPORT_NET §5 — nota: „0 REFUSE" bez zmiany jako fakt; interpretacja zawężona (REFUSE pozycyjny
niemożliwy z konstrukcji; uzbrojone gałęzie wg D0(b) — cytat verbatim z D0.md). Zdania kanonu §2
NIE padają (zawieranie przypisane clip_v + geometrii — to zdanie okazuje się dokładniejsze, niż
wiedzieliśmy, pisząc je).
E2 RAPORT_DEMO_V2 — nota erratum do zdania footera; klatka footera filmu przerenderowana na: „the network
flies under the same frozen shield and through the same controller socket as every controller in the
program; the shield did not need to intervene" (bez „certified gate"). DEMO_V2.mp4 w wersji poprawionej
zastępuje plik; stary zachowany jako `_v1_erratum3`.
E3 Reguła trwała: zdanie o torze lotu w każdym przyszłym materiale nazywa pętlę po imieniu (gate vs
bench-loop); „pod osłoną" wymaga w raporcie listy UZBROJONYCH gałęzi tej pętli.

## §3. Decyzja kierunkowa nogi

Denial = REALNY (`EKF2_GPS_CTRL=0` + wiązanie `pos_flag` z dead-reckoning, wzór gate:267). Wariant
syntetyczny (`pos_flag=True`) odrzucony jako noga — testuje reakcję bez detekcji; zostaje jako unit-test
buildu. K2 = pierwsze uzbrojenie pełnego toru detekcja→REFUSE→zejście przy kontrolerze uczonym; ścieżka
REFUSE ławki ma 0 wykonań historycznych — K2 wykonuje ją po raz pierwszy i to jest część tezy, nie ryzyko
do ukrycia.

## §4. Mikrofakty R7 (wykonawca, offline, przed PRE_K2 — bez nich decyzja architektury byłaby zgadywaniem)

R7a Gdzie instancjonowany jest `track_feed` dla lotów ławki (plik:linia): w `bench_flight` czy w module
kontrolera? Czy `net_controller` może biec pod pętlą `gate_run_r03` bez zmian (importy, argumenty step,
cykl życia feedu) — tak/nie z powodem.
R7b Zejście D5: inline w pinowanym `gate_run_r03.py` (zakres linii, zależności) czy funkcja współdzielona?
Jeśli inline — wypisz zakres ewentualnej ekstrakcji wzorem INFRA-3 (rozcięcie + re-baseline pinu + test
bit-w-bit), bez wykonywania.
R7c Cytat verbatim D0(b) z `results/NET/FLY/D0.md`: jakie gałęzie osłony były uzbrojone w pętli ławki
(kotwica dla E1).

## §5. Architektura K2 — dwie opcje, wybór w PRE_K2 na faktach R7

(i) K2 przez pętlę GATE: `CONTROLLER=net` + intruz + feed pod `gate_run_r03` — zaleta: denial, wiązanie
pos_flag, D5, k1_judge i certs_selfcheck już przetestowane w K1; koszt: zależny od R7a.
(ii) K2 przez bench-loop: dodać wiązanie pos_flag + ścieżkę D5 do `bench_flight` — zaleta: orkiestracja
epizodu na miejscu; koszt: duplikacja logiki bezpieczeństwa albo ekstrakcja z pinu (R7b), plus pierwsza
egzekucja świeżego kodu zejścia w nodze kryterialnej.
CC deklaruje prior (nie decyzję): (i) wygląda taniej i bezpieczniej dowodowo, jeśli R7a nie pokaże blokera.

## §6. Księga predykcji recon

P-K2R1 ✗ (pętla własna, monitor nieuzbrojony — gorzej niż zakładałam) · P-K2R2 ✓ (glue k2_judge potrzebny;
przy architekturze (i) może zbędny dla metryk denialu — do PRE) · P-K2R3 ✗ (zapas 1.72 m na pełnej
siatce, cięcie geometrii niekonieczne — chybienie w dobrą stronę). 1/3.

## §7. Wykonanie

Wykonawca: E1+E2 (commit doc+film), R7a–c jedną wiadomością tekstem płaskim. Olga: push {62a068a, e29a154,
commit erratum}. CC: PRE_K2 po R7 (punkt fazy: prior = T po wejściu w pasmo ~1 okrążenie, kryterium
dwustronne z liczbami K1, ramię (−) = zmierzone 0/84, budżet, kryterium śmierci nogi).
