# ANEKS_TEACH-2 — korekta świadka tezy: „zero detekcji znaczników" zastąpione przez „zero detekcji zgodnych z manifestem"; S2 wznowiony od próby na sucho; 0 bootów zużytych

LiquidPatrol · CC · 16.11.2026 · łańcuch TEACH, po STOP-TEACH-2-SUCHO
(e0ac58f6 na origin). Do ratyfikacji sygnałem **„ratyfikuję
TEACH-2"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Stan.** eeb8bcfd: blok KSIĘGI. 34fd058b: poprawki F1–F3.
   e0ac58f6: STOP przed pierwszym bootem. Bootów nogi 0 z 24.
2. **F1–F3.** Diff przeczytany: chwila flagi to ostatni spadek z 1 na
   0, powrót do 1 przed zamknięciem kasuje zatrzask, pusta mapa się
   nie zamyka, wiązania są w rejestrze. Rozszerzenie F2 o kadr
   w buforze z czasem po fladze przyjęte.
3. **STOP zasadny.** Litera PRE §6 unieważniałaby loty z powodu
   tekstury, nie znaczników: detektor zgłasza na samej ortofotomapie
   22 fałszywe znaczniki na 32 937 kadrów (ID 17 i 37, bok do
   14.8 px). Liczby ze skanu wykonawcy; CC ich nie powtarzał. ID 37
   nie ma w manifeście (0–36).
4. **Moc nowego świadka — zmierzona przez CC na lotach NAD3,** gdzie
   znaczniki są widoczne. Punkt gruntu środka detekcji policzony
   z pozy GT i porównany z pozycją tego ID w manifeście:
   - p01 (cięcie c05): 3932 detekcje, wszystkie bliżej niż 1.0 m,
     odległość p95 0.05 m, max 0.09 m;
   - p02 (cięcie c10): 3971, wszystkie, max 0.25 m;
   - nominał NB: 8760, wszystkie, max 0.13 m.

## §2. Błąd projektu CC

Warunek „zero detekcji znaczników" został zapisany w PRE bez pomiaru,
ile fałszywych detekcji daje słownik 4×4 na naturalnej teksturze.
Próba na sucho złapała to przed pierwszym bootem.

## §3. Rozstrzygnięcie

1. **Definicja.** Detekcja zgodna z manifestem: ID należy do manifestu
   znaczników v2, a punkt gruntu jej środka, liczony z pozy GT na
   wysokość znacznika, leży nie dalej niż 1.0 m od pozycji tego ID.
2. **Zmiana litery PRE_TEACH.** W §5 pkt 3 oraz w §6 (bramka obrazu
   S2, ważność lotu S3) „zero detekcji znaczników" brzmi odtąd „zero
   detekcji zgodnych z manifestem". Wszystkie detekcje surowe są
   liczone i podawane jako obserwabla: liczba, ID, bok.
3. **Kto liczy.** Analizator po locie, z zapisanych detekcji i GT.
   Kod lotu bez zmian.
4. **Świadek statyczny.** Poza bootów ST1 i ST2 ma być taka, by
   w starym świecie kamera w dół widziała co najmniej jeden znacznik.
   ST1: co najmniej jedna detekcja zgodna. ST2, ta sama poza: zero.
5. **Dlaczego nie próg boku 16 px:** największa fałszywa detekcja ma
   14.8 px, zapas 1.2 px. **Dlaczego nie sam świadek statyczny:** nie
   obejmuje lotów.
6. **Bez zmian:** reszta PRE_TEACH, tabela, tor, budżet.
   PROMPT_TEACH_S2 obowiązuje dalej z tym brzmieniem warunku.
   Odchylenia 1–6 raportu przyjęte.

## §4. Wznowienie S2

1. Bramka: `origin/master` zawiera `e0ac58f6`; sha256 tego pliku
   zgodne z podanym przez Olgę; sygnał „ratyfikuję TEACH-2" obecny.
2. Commit **[CO-TEACH-2A]**: aneks verbatim w korzeniu (byte-check),
   blok §5 do KSIĘGI, append-only.
3. Analizator i narzędzie próby na sucho dostają nowy warunek
   (narzędzia w `results/TEACH/tools/`, nie kod lotu). Dwa
   sprawdziany przed bootem:
   - na locie p01 NAD3 analizator zgłasza 3932 detekcje zgodne
     (liczba CC; różnica ponad 1% ⇒ STOP);
   - na 32 937 kadrach reconu liczba detekcji zgodnych: oczekiwane 0;
     inna liczba ⇒ STOP z listą.
4. Próba na sucho z PROMPT_TEACH_S2 §2.6 powtórzona w całości.
   Zielona ⇒ booty wg §3–§6 promptu, bez zmian.
5. Aneks po S2 będzie nosił numer ANEKS_TEACH-3.

## §5. KSIĘGA (append-only przy commicie [CO-TEACH-2A])

```
## TEACH — ANEKS_TEACH-2 (16.11.2026): korekta świadka tezy
- S2 zatrzymany próbą na sucho przed pierwszym bootem (0/24).
  Poprawki F1–F3 zielone (commit 34fd058b).
- Przyczyna: warunek „zero detekcji znaczników" łamie sama tekstura —
  22 fałszywe detekcje słownika 4×4 na 32 937 kadrach reconu (ID 17
  i 37, bok do 14.8 px); na łacie S nieważnych byłoby 5 z 12 cięć.
- Nowe brzmienie: zero detekcji zgodnych z manifestem (ID z manifestu
  i punkt gruntu środka z pozy GT nie dalej niż 1.0 m od pozycji tego
  ID). Moc świadka zmierzona przez CC na lotach NAD3: 3932 / 3971 /
  8760 detekcji, wszystkie zgodne, odległość p95 0.05 m, max 0.25 m.
- ✗ projektowe CC: warunek na wynik detektora zapisany bez pomiaru
  jego fałszywych alarmów na docelowym obrazie. Lekcja: świadek ma
  mieć zmierzoną moc i zmierzony fałszywy alarm, zanim trafi do
  litery.
```
