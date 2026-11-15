# ANEKS_NAD3-2 — c03 w N2 to brak akwizycji celu stojącego, nie geometria; bramka promienia przechodzi na 5 epizodach z misją; S2 leci dalej (B3, B4); c03 poza nominałami S3

LiquidPatrol · CC · 15.11.2026 · łańcuch NAD3, po
STOP-NAD3-2-GEOM-NOMINAL (ad7614e0 na origin). Do ratyfikacji
sygnałem **„ratyfikuję NAD3-2"**. Sygnały bez numeru albo nazwy
odrzucasz.

## §1. Weryfikacja CC (z repo, wykonaniem)

1. **Naprawa manifestu.** v2 ma 120 epizodów, pozycja = numer, suma
   2f3b4a94; sześć używanych wpisów identycznych z plikiem z S1,
   którego suma się nie zmieniła. Zmienione pliki to dokładnie lista
   z ANEKS_NAD3-1 §3.3. W N2 log intruza ma etykiety (2, c02),
   (3, c03), (5, c05), (10, c10).
2. **Promień, własnym kodem:** N2 daje 18.271 / 0.485 / 15.997 /
   18.870 m, zgodnie z raportem do 0.001 m. Analizator: bezpieczeństwo
   czyste w 4/4.
3. **c03, własnym kodem.** W 40 s epizodu 606 klatek: detektor
   powyżej 0.3 w 179 (max 0.846), potwierdzenie ruchu w 18, klatek
   przyjętych przez bramkę 0, blokady brak.
4. **Porównanie z bramką NAD2 (intruz na 15 m, `nom_b1`).** c03 był
   tam najtrudniejszą z czterech komórek stojących: pierwsza blokada
   16.0 s po starcie epizodu, w pozostałych trzech 0.0 / 0.0 / 5.9 s;
   potwierdzenie ruchu przed wejściem w 18 z 253 klatek. Przy 10 m:
   18 z 606.
5. **Komórki cięcia mają akwizycję.** W N2 c05 blokuje po 10.4 s,
   c10 po 4.2 s; klatek przyjętych przed wejściem 27 i 29.
6. **W epizodach z akwizycją sieć trzyma zadanie:** track 0.873–0.946,
   pasmo 0.931–0.987 w pięciu epizodach.

## §2. Odczyt

Wada leży przed siecią i nie ma związku ze źródłem pozycji. Admisja
celu wymaga trzech kolejnych klatek, w których detekcja pokrywa się
z potwierdzeniem ruchu. Cel stojący, oglądany z zawisu przy obrocie
kursu, daje detektorowi ruchu niewiele do potwierdzenia. Komórka c03
była pod tym względem najsłabsza już przy 15 m; przy 10 m w 40 s nie
złożyła serii ani razu. Czy bliższy intruz to pogarsza, czy to ten sam
proces losowy z gorszym wynikiem — jedna para lotów nie rozstrzyga.
**Mechanizm jest hipotezą, nie pomiarem.**

Obawa, którą niosła bramka geometrii w PRE, była inna: że sieć nie
utrzyma zadania przy intruzie bliżej środka. Ta obawa się nie
potwierdziła.

## §3. Rozstrzygnięcia

1. **Klasyfikacja.** c03 w N2 to brak akwizycji, nie geometria. STOP
   z ANEKS_NAD3-1 §3.8 rozstrzygnięty: śmierć geometrii nie zachodzi.
2. **Bramka promienia: PASS na 5 epizodach z misją**, max 18.870 m
   (c10), zapas 0.63 m. Wynik c03 (0.49 m w zawisie) jest dla promienia
   pusty i nie liczy się jako spełnienie. Zapis poprawny to 5/5
   zmierzonych, nie 6/6.
3. **c03 się nie powtarza.** Wynik byłby losowy i nie odpowiada na
   pytanie nogi.
4. **S2 leci dalej:** B3 i B4 według PROMPT_NAD3_S2 §2–§4, manifest v2.
5. **Cięcie bez wejścia.** Jeśli w B3 albo B4 nie będzie akwizycji,
   cięcie nie nastąpi i lot nie ma ticków utraty. Taki boot liczy się
   do budżetu, lot jest nieważny dla smoke i wolno go powtórzyć **raz**.
   Powtórkę finansuje boot zapisany w PRE §6 na korektę geometrii,
   która po PASS bramki promienia nie jest potrzebna. Drugi lot bez
   wejścia ⇒ STOP.
6. **Nominały S3 bez c03.** Powód: epizod bez akwizycji stoi w zawisie
   0.5 m od środka i nie sprawdza (B5), bo nie ma czego odmówić. Listę
   komórek poda prompt S3.
7. **Ta sama reguła w S3:** cięcie bez wejścia jest nieważne dla
   bramki i powtarzane z rezerwy; liczba takich lotów wchodzi do
   raportu.
8. **Zakres zdania końcowego (dopisek do PRE §7).** Wynik nogi dotyczy
   lotów z akwizycją celu. Akwizycja celu stojącego na 10 m: trzy
   z czterech kierunków (c00, c01, c02 tak; c03 nie) — osobne
   znalezisko, poza pytaniem nogi.
9. **Stanowisko.** ChatGPT po zamknięciu okna zostawia procesy w tle
   (15 o 12:15). Przed bootami zamknąć go z zasobnika; sprawdzanie
   listy procesów przez wykonawcę zostaje.
10. **Numeracja.** Aneks po S2 (zgoda na bramkę S3) będzie
    ANEKS_NAD3-3.

## §4. Wznowienie

1. commit **[CO-NAD3-2]**: ten plik verbatim w korzeniu (byte-check),
   bloki §5 i §6 append-only;
2. B3 → B4, każdy sądzony według PROMPT_NAD3_S2 §3 przed następnym.

Budżet S2: zużyte 2 z 4, zostają 2 i jedna powtórka z §3.5. Noga:
2 z ≤ 22.

## §5. KSIĘGA (append-only przy commicie [CO-NAD3-2])

```
## NADIR-III — ANEKS_NAD3-2 (15.11.2026): geometria po N2
- Manifest v2 potwierdzony lotem. Bramka promienia: 5 epizodów
  z misją, max 18.870 m (c10) przy progu 19.5 m. P-NAD3-1 ✓ na
  promieniu, z zastrzeżeniem: c03 bez misji, wynik dla promienia pusty.
- c03 w N2: brak akwizycji celu stojącego w 40 s (detekcja w 179
  z 606 klatek, potwierdzenie ruchu w 18, przyjętych 0). W bramce NAD2
  przy 15 m ta sama komórka blokowała ostatnia, po 16.0 s.
  Bezpieczeństwo czyste w 8/8 epizodów obu nominałów.
- ✗ CC bez predykcji: żadna z siedmiu predykcji PRE nie obejmowała
  akwizycji. Ryzyko geometrii nazwane w PRE dotyczyło sieci, nie toru
  admisji.
- Lekcja: zmiana położenia celu ma dwóch odbiorców — sieć i tor
  admisji; bramka sprawdza oba osobno.
- Decyzja: c03 poza nominałami S3; cięcie bez wejścia nieważne dla
  bramki i powtarzane z rezerwy.
```

## §6. KIERUNKI_PO_PLANIE (append-only przy commicie [CO-NAD3-2])

```
## Dopisek stanu katalogu — 15.11.2026 (CO-NAD3-2)
- **Obserwacja, pozycja nieotwarta: admisja celu stojącego.** Cel
  nieruchomy oglądany z zawisu przy skanie kursem rzadko składa serię
  trzech klatek detekcja ∧ ruch. Komórka c03 (kierunek 270°): 16.0 s
  do blokady przy 15 m (NAD2), brak blokady w 40 s przy 10 m (NAD3).
  Mechanizm niezmierzony. Otwarcie tylko decyzją Olgi.
```
