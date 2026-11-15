# ANEKS_NAD3-3 — S2 zamknięte: geometria i smoke PASS; zgoda na bramkę S3 (12 cięć, 2 nominały, 3 rezerwy)

LiquidPatrol · CC · 15.11.2026 · łańcuch NAD3, po STOP-NAD3-2
(15eed5cd na origin). Do ratyfikacji sygnałem **„ratyfikuję NAD3-3"**.
Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

Tabela P1 wpisana z liczb PRE §4, nie z pliku FREEZE; e′ liczone
z wierszy ramy jako |p_corr − GT|.

1. **B3 (cięcie c05, bez degradacji).** 2447 ticków utraty, ocenione
   2402, przekroczeń przesłanki 0, max e/U 0.105. Nieocenione 45 —
   wszystkie po zatrzasku τ\* w zejściu, w misji 0. Bariera z mojego
   wzoru zgodna z zapisem w każdym ticku. Zapas bariery w misji min
   8.82 m. r_max GT 15.529 m.
2. **B4 (cięcie c05, P1, bias na zewnątrz).** 2433 ticki utraty,
   ocenione 2326, przekroczeń 0, max e′/U′ 0.421; e′ p50 / p95 / max
   1.17 / 1.50 / 1.84 m. Nieocenione 107, w misji 0. Zapas bariery min
   5.41 m. r_max GT 15.479 m.
3. **Degradacja na żywo.** Między cięciem a zejściem producent
   wyliczył 553 poprawki, dostarczono 110, odstęp 1.000 s bez wyjątku.
   Wektor błędu: długość 1.0000 m, składowa radialna +1.0000 m
   w każdej poprawce. τ w misji max 1.024 s.
4. **Odmowy.** W misji żadnej: 2219 i 2216 ticków KONT przed zejściem
   planowym, wszystkie ALLOW. Zatrzask τ\* zapadł 9.0 s i 5.4 s po
   komendzie zejścia (tick 3074 i 2997), przy `r_est` 11.5 i 12.0 m
   wobec bariery 22.1 m.
5. **`r_est` = |p_corr|** we wszystkich tickach utraty obu lotów
   (z dokładnością zapisu).

Liczby raportu wykonawcy potwierdzone; różnica w max e/U (0.103 wobec
0.105) wynika z chwili odczytu GT.

## §2. Odczyt

Tor działa od końca do końca: decymacja, wstrzyknięty błąd, tabela
punktu, osłona i replay zachowują się w locie tak, jak w S1 przy
biurku. Błąd 1 m przy 1 Hz zużywa 42% dopuszczalnego U′.

Geometria wyszła ciaśniejsza, niż zakładał PRE. Komórka c05 lata do
16 m, c10 do 18.9 m. Skutek dla drabiny punktów przy biasie na
zewnątrz, z samej reguły bariery:

- P2 (bariera najniższa 20.80 m): c05 daje `r_est` do ok. 17.8 m,
  c10 do ok. 20.6 m — odmowy nie należy oczekiwać w c05, w c10 jest
  na krawędzi;
- P3 (bariera najniższa 19.30 m): c05 do ok. 18.8 m, c10 do ok.
  21.6 m — odmowa oczekiwana tylko w c10.

Komórki są zamrożone w PRE §4 i zostają. Dane S2 nie zmieniają tabel,
punktów ani predykcji; P-NAD3-5 stoi, jak ją zapisano, i rozliczy się
literą.

## §3. Rozstrzygnięcia

1. **S2 zamknięte.** Bramka promienia PASS (5 epizodów z misją, max
   18.870 m; dwa cięcia c05 w pełnym oknie 15.5 m). Smoke PASS (B3,
   B4). Rezerwa z ANEKS_NAD3-2 §3.5 nieużyta i nie przechodzi do S3.
2. **Zgoda na bramkę S3.** Litera, werdykt i obserwable: PRE §6 bez
   zmian.
3. **Kolejność lotów (wiążąca):**
   - cztery cięcia P1: c05 na zewnątrz, c10 na zewnątrz, c05 do
     środka, c10 do środka;
   - nominał NA;
   - cztery cięcia P2 w tej samej kolejności;
   - nominał NB;
   - cztery cięcia P3 w tej samej kolejności.
4. **Nominały S3 (bez c03, ANEKS_NAD3-2 §3.6):** tabela P1, GNSS
   obecny, bez cięcia.
   - NA: epizody 0, 1, 5, 10, degradacja na zewnątrz;
   - NB: epizody 1, 2, 5, 10, degradacja do środka.
   Epizod nominalny bez akwizycji jest dla (B5) pusty: nazwany,
   policzony, niepowtarzany.
5. **Rezerwa — 3 booty** na boot nieważny stanowiskowo i na cięcie bez
   wejścia (ANEKS_NAD3-2 §3.7). Czwarta potrzeba ⇒ STOP.
6. **Zatrzymania przed końcem:**
   - naruszenie B1–B5 w dowolnym locie ⇒ werdykt V-C, STOP
     natychmiast;
   - replay poprawek albo osłony poniżej 100% ⇒ STOP, lot nie nadaje
     się do sądzenia;
   - po bloku P1: mniej niż 3 z 4 cięć dostępnych według (D1) ⇒ STOP
     przed P2 i aneks.
7. **Budżet:** noga 4 zużyte; S3 ≤ 17 (12 + 2 + 3).
8. **Numeracja.** Aneks zamykający nogę będzie ANEKS_NAD3-4.

## §4. KSIĘGA (append-only przy commicie [CO-NAD3-3])

```
## NADIR-III — ANEKS_NAD3-3 (15.11.2026): S2 zamknięte, zgoda na S3
- S2: 4/4 booty. Geometria PASS na 5 epizodach z misją (max
  18.870 m); cięcia c05 w pełnym oknie 15.53 i 15.48 m.
- B3 (bez degradacji): 0 przekroczeń, max e/U 0.10. B4 (P1, 1 m na
  zewnątrz, 1 Hz): 0 przekroczeń, max e′/U′ 0.42, e′ p50 1.17 m;
  poprawki co 1.000 s, τ max 1.024 s; replay 100% w obu. CC
  odtworzył liczby własnym kodem z tabelą wpisaną z PRE §4.
- REFUSE w misji 0; zatrzask τ* dopiero w zejściu planowym (jak NAD2).
- Obserwacja do P-NAD3-4, bez rozliczenia: r_max B3 wobec B4 różni
  się o 0.05 m, ale to para o różnym E, nie o przeciwnym znaku.
- Geometria ciaśniejsza niż w PRE (c05 do 16 m, c10 do 18.9 m):
  z reguły bariery odmowa przy biasie na zewnątrz jest oczekiwana
  tylko w c10. Predykcje P-NAD3-5 i P-NAD3-6 stoją bez zmian.
```
