# ANEKS_NAD2-3 — po STOP-NAD2-4-INTRUZ: ruch intruza w locie długim przedłużony nowym manifestem (ten sam generator i ziarno; w razie niezgodności prefiksu — wahadło), bez skoków i bez zmian w harness; ścieżka manifestu i limit wyciągu ULG przez env

CC · 12.11.2026 · łańcuch NAD2, po STOP-NAD2-4-INTRUZ (6e74d020
lokalnie; 0 bootów, kod bez zmian). Zmienia PROMPT_NAD2_S4 §0.4 i §R
w części o ruchu intruza; PRE_NAD2 nie dotyka. Sygnały bez numeru
albo nazwy odrzucasz.

## §1. Ocena

STOP był zasadny: prompt dopuszczał „powtarzanie wzoru" i jedną
zmianę env w driverze, a tych dwóch rzeczy nie da się pogodzić.
Żadna z trzech dróg wykonawcy nie jest dobra — każda przenosi
intruza skokiem o 11.2 m, czego w bramce nie było. Intruz stojący
od 200 s zamieniłby dwie trzecie lotu w spokojną orbitę i odjął
pomiarowi to, co go obciąża. Wzór ruchu to odcinki proste ze stałą
prędkością i natychmiastową zmianą kursu (w c10_s01 także niemal
o 180°), więc da się go przedłużyć bez skoku.

## §2. Decyzja

**Ruch intruza przez cały lot z nowego pliku manifestu, w tej
kolejności prób:**

1. **Przedłużenie tym samym generatorem i ziarnem** do co najmniej
   700 s — jeśli pierwsze 200 s wychodzi identyczne z wzorem bramki.
2. **Jeśli prefiks się nie zgadza: wahadło** — wzór 200 s w przód,
   potem ten sam tor wstecz, na przemian, do co najmniej 700 s.
   Nawrót to natychmiastowa zmiana kursu o 180° przy tej samej
   prędkości, czyli zdarzenie tego typu, jakie wzór już zawiera.
3. **Jeśli żadnej z dwóch nie da się zrobić bez zmiany `harness/`:**
   lot leci z intruzem stojącym od 200 s, a raport nazywa to wprost
   („200 s ruchu, potem orbita wokół nieruchomego celu").

**Dopuszczone zmiany — lista zamknięta:**
- nowy manifest lotu długiego i skrypt, który go generuje, w
  `results/NAD2/s4/` i `results/NAD2/tools/`;
- `nad2_boot.sh` (i launcher, jeśli trzeba): ścieżka i suma manifestu
  scenariuszy z env, domyślnie wartości bramki;
- `nad2_flight.py`: nastawy czasu z env (kontynuacja, bezpiecznik
  ściany, ewentualny limit czasu epizodu), domyślnie wartości bramki;
- `nad2_ulg.py`: limit rozmiaru wyciągu z env, domyślnie 3 MB; dla
  tego lotu 10 MB.

Bez zmian zostają `harness/`, `r01/`, `r03/`, krok drivera, litera,
tabela i analizator kryteriów.

**Testy przed lotem (0 bootów), wszystkie w raporcie:**
- pierwsze 200 s nowego wzoru identyczne z wzorem bramki (siatka
  0.1 s, |Δ| ≤ 1e-6 m);
- ciągłość: największy krok pozycji między próbkami 0.1 s nie
  przekracza v · 0.1 s + 1e-6 m na całej długości — zero skoków;
- prędkość stała i równa v komórki; tor w dysku scenariusza;
- przebieg na sucho ruchu intruza na nowym manifeście przez 700 s —
  bez zatrzymania;
- bez env: ścieżka i suma manifestu, nastawy czasu i limit wyciągu
  równe wartościom bramki (diff i test wartości domyślnych).

Test nie przechodzi ⇒ następna pozycja z listy §2; nie przechodzi
żadna ⇒ pozycja 3. Reszta PROMPT_NAD2_S4 bez zmian, w tym komórka,
litera, rezerwa i predykcje L1–L4.

## §3. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-II — lot długi, ruch intruza (ANEKS_NAD2-3, 12.11.2026)
- STOP-NAD2-4-INTRUZ przed startem (0 bootów): wzór ruchu c10_s01
  trwa 200 s, potem intruz stoi; prompt dopuszczał tylko powtarzanie
  wzoru i jedną zmianę env. ✗ projektowe CC: prompt lotu długiego
  napisany bez sprawdzenia czasu trwania wzoru ruchu — warunek
  „jeśli wzór się kończy" był w tekście, ale z niewykonalnym
  remedium.
- Decyzja: nowy manifest — przedłużenie tym samym generatorem
  i ziarnem przy zgodnym prefiksie 200 s, inaczej wahadło po tym
  samym torze; bez skoków, bez zmian w harness; fallback nazwany:
  intruz stojący od 200 s.
```

## §CO

Bramka: origin/master == **6e74d020** (po pushu Olgi). Commit
[CO-NAD2-3]: korzeń `ANEKS_NAD2-3.md` verbatim (byte-check sha256
z wiadomości CC) + KSIĘGA §3 append-only. Potem budowa i testy §2
(0 bootów), wynik testów w raporcie przed lotem, i lot wg
PROMPT_NAD2_S4. `STOP_NAD2_4_INTRUZ.md` zostaje jak jest; raport
końcowy w `results/NAD2/s4/STOP_NAD2_4.md`. Push = Olga.
