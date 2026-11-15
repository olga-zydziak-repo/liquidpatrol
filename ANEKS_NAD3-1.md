# ANEKS_NAD3-1 — wada manifestu NAD3: naprawa pełną listą 120 epizodów, bez zmiany kodu; S2 wznawia od N2; bramka geometrii na 6 ważnych epizodach

LiquidPatrol · CC · 15.11.2026 · łańcuch NAD3, po
STOP-NAD3-2-MANIFEST (d4958c04 na origin). Do ratyfikacji sygnałem
**„ratyfikuję NAD3-1"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, wykonaniem)

1. **Mechanizm potwierdzony w kodzie.** Proces ruchu intruza bierze
   wpis z listy po numerze epizodu (`harness/intruder_motion.py:169`).
   Driver przy liście z env bierze wpis po pozycji
   (`nad3_flight.py:305`). W manifestach BENCH i bramki NAD2 lista ma
   120 wpisów i pozycja równa się numerowi. Manifest NAD3 z S1 ma
   6 wpisów z numerami 0, 1, 2, 3, 5, 10 i tę równość łamie.
2. **Ślad w zapisie N1.** Log intruza ma wiersze tylko dla (0, c00),
   (1, c01) i (10, c10); dla numeru 5 nie ma żadnego — epizod c05
   poleciał z torem c10. `IndexError` w `act.log:30`.
3. **Geometria N1 własnym kodem:** r_max GT 18.325 / 18.143 / 18.831 /
   12.175 m, zgodnie z raportem do 0.001 m; wszystkie ticki misji
   NOMINAL i ALLOW.
4. **Droga (A) sprawdzona wykonaniem.** Pełna lista 120 epizodów z
   parametrami NAD3 (10.0 / 11.0 / 8.5 m, 200 s) ma pozycję równą
   numerowi, a wpisy c00–c03, c05 i c10 są identyczne z plikiem z S1
   (równość słowników, 6/6). Największy promień intruza w całej
   liście: 11.000035 m (c10_s01).

## §2. Przyczyna

Wada ma dwóch autorów. Podzbiór komórek stał w literze
PROMPT_NAD3_S1 §1.4 — CC nie sprawdził, że wzorzec (manifest bramki
NAD2) jest pełną listą, i nie objął przeglądem S1 procesów czytających
manifest. Wykonawca zostawił w krótkiej liście numery kanonu, a próba
na sucho przeszła przez driver, nie przez proces intruza.

## §3. Rozstrzygnięcia

1. **Droga (A): pełny manifest.** (B) odrzucona — numery w zapisie
   lotu odeszłyby od kanonu, na którym stoją analizatory. (C)
   odrzucona — zmiana kodu toru lotu bez potrzeby.
2. **Nowy plik** `results/NAD3/s1/scenario_manifest_nad3_v2.json`,
   120 epizodów. Plik z S1 zostaje nietknięty jako zapis tego, na czym
   poleciał N1.
3. **Dozwolone zmiany** (żadna nie dotyka kodu lotu, osłony ani
   degradacji): `nad3_manifest.py` (wyjście v2), strażnik manifestu
   w `nad3_boot.sh` (ścieżka i suma), numery epizodów w
   `nad3_s2_run.py`, suma w `test_nad3_s1.py`, próba na sucho.
4. **Asercje przed wznowieniem (0 bootów).** Niepowodzenie którejkolwiek
   ⇒ STOP bez bootu.
   - pozycja = numer epizodu dla wszystkich 120 wpisów; ta sama
     asercja w kolejce przed każdym bootem;
   - wpisy c00–c03, c05, c10 w v2 identyczne z plikiem z S1;
   - testy promienia, ciągłości i czasu wiążące dla sześciu komórek
     używanych; dla pozostałych 114 raportowane, nie blokują;
   - **próba na sucho procesu intruza:** dla każdego epizodu planu
     (N2: 2, 3, 5, 10; B3 i B4: 5) wpis wybrany ścieżką drivera
     i ścieżką procesu intruza ma ten sam `scenario_id` i te same
     odcinki. Negatyw: na manifeście z S1 próba wykrywa rozjazd dla
     numerów 5 i 10;
   - pełna próba drivera z S2 powtórzona na v2.
5. **Kolejka podaje numery kanonu:** N2 = 2, 3, 5, 10; cięcia = 5.
6. **N1.** Epizody c00 i c01 są ważnymi pomiarami geometrii: start
   i tor zgodne z manifestem, wpisy identyczne w v2. Epizody c05 i c10
   z N1 są nieważne jako pomiar geometrii i zostają opisowo. Boot N1
   liczy się do budżetu. N1 się nie powtarza.
7. **Bramka geometrii — zmiana litery PRE §6, nazwana.** Sądzona na
   6 ważnych epizodach nominalnych (c00, c01 z N1; c02, c03, c05, c10
   z N2) zamiast 8. Próg 19.5 m bez zmian. Komórki c05 i c10 mają po
   jednym pomiarze nominalnym zamiast dwóch; c05 dostaje dwa pomiary
   w dłuższym oknie cięcia (B3, B4), a reguła „r_max > 19.5 m
   w cięciu ⇒ STOP" z PROMPT_NAD3_S2 §3 zostaje.
8. **Kryterium śmierci geometrii nie luzuje się.** Jeden epizod z 6
   niespełniający kryteriów nominału ⇒ STOP i aneks. Dwa lub więcej
   ⇒ śmierć geometrii.
9. **Kod wyjścia 9 drivera** ma dwa znaczenia (bramka tempa,
   niezgodność degradacji) i w tej nodze tak zostaje; kolejka
   rozróżnia je po pliku tempa i zdarzeniu degradacji.
10. **Stanowisko.** Przed wznowieniem zamknąć Chrome i ChatGPT —
    pierwsza próba bramki zdrowia N2 dała NO-GO przy tempie 0.866.
11. **Numeracja.** Aneks po S2 (geometria i zgoda na bramkę S3) będzie
    ANEKS_NAD3-2.

## §4. Wznowienie

PROMPT_NAD3_S2 obowiązuje dalej, z różnicami §3. Kolejność:

1. commit **[CO-NAD3-1]**: ten plik verbatim w korzeniu (byte-check),
   blok §5 do KSIĘGI append-only;
2. budowa v2, asercje §3.4 — jeden commit, 0 bootów;
3. N2 → bramka geometrii → B3 → B4.

Budżet S2: zużyty 1 z 4, zostają 3. Noga: 1 z ≤ 22.

## §5. KSIĘGA (append-only przy commicie [CO-NAD3-1])

```
## NADIR-III — ANEKS_NAD3-1 (15.11.2026): wada manifestu, S2 po N1
- STOP-NAD3-2-MANIFEST: manifest NAD3 z S1 (6 epizodów, numery
  0, 1, 2, 3, 5, 10) złamał niezmiennik „pozycja na liście = numer
  epizodu". Proces intruza indeksuje numerem, driver pozycją. W N1
  epizod c05 poleciał z torem c10, a przy c10 proces intruza padł.
  Bezpieczeństwo nienaruszone (B1–B5 czyste w 4/4). Ważne pomiary
  geometrii: c00 18.33 m i c01 18.14 m przy bramce 19.5 m.
- ✗ projektowe CC: podzbiór komórek w literze PROMPT_NAD3_S1 §1.4
  bez sprawdzenia, że wzorzec jest pełną listą; przegląd S1 nie objął
  procesów czytających manifest.
- ✗ wykonawcy: próba na sucho objęła driver, nie proces intruza.
- Lekcja: wejście wspólne dla kilku procesów sprawdza się na sucho
  w każdym z nich, a niezmiennik formatu jest asercją, nie zwyczajem.
- Naprawa: pełna lista 120 epizodów, kod bez zmian. Bramka geometrii
  na 6 ważnych epizodach nominalnych; P-NAD3-1 rozlicza się na 6/6.
```
