# ANEKS_DEMO3-2 — werdykt kanoniczności captions + zamknięcie DEMO_V3 (warunkowe)

CC · 29.09.2026 · łańcuch DEMO3 (po ANEKS_DEMO3-1). Samowykonalny: sesja wykonuje §3 i STOP;
zero bootów — wszystkie poprawki są post-produkcją na istniejących klatkach.

## §1. Przyjęcia

Film 362.6 s, akty z jednego ujęcia, cztery cięcia na granicach — kształt zgodny z wizją.
Sejw ZREPRODUKOWANY NA ŻYWO w podejściu 2/2: REFUSE(GEOFENCE) @ t_rel 68.0 s vs 68.5 s
w epizodzie kryterialnym, z_max 19.42, breach false — zbieżność czasowa odnotowana jako
OBSERWACJA (powtarzalność mechanizmu pełzania), nie wpis księgowy (DEMO ≠ POMIAR). take_1
(bez repro, z_max 15.08) zachowany i zaraportowany — uczciwość wyboru ujęć pełna. Płynność:
max przerwy sim 0.26/0.43/0.82 s < 1 s — warunek ANEKS_DEMO3-1 §2 PASS. Sanity panelu 3/3.
Budżet 6/8, sesje 2/2. Odchylenia §13 przyjęte (pre-roll +8 s; sha wideo przez odsyłacz —
precedens DEMO_V2).

## §2. Werdykt captions — словo po słowie

Czyste: FOOTER (pętla nazwana, gałęzie uzbrojone wyliczone — E3 domknięte), INTRO (komplet
zastrzeżeń), ACT1 w całości, ACT2 @10-24/@54-72/@76-90/@93-105, ACT3 @10-26 (podpis „demo
re-flight" ✓), @30-48, @52-68 (**kwalifikator habitatowy jest** — pułapka ominięta), @71-90
(zdanie sejwu z guardem n=1 wierne), @92-99. Kanon K2 w outro wierny.

Trzy poprawki WYMAGANE przed skutecznością (wszystkie tekstowe):

- **C1 (zakres na karcie formalnej):** kanon W niesie klauzulę „SITL, wektor stały, komórka
  c11, feed emulowany" — intro pokrywa SITL/feed globalnie, ale karta OUTRO jest formalnym
  nośnikiem kanonów i musi nieść pełny zakres. Dopisz do bloku prowieniencji OUTRO jedną
  linię: „All results: SITL, emulated track feed (10 Hz / 0.2 s / sigma 0.5 m); wind campaign
  flown in one scenario geometry (cell c11), constant wind vector."
- **C2 (próg przeinaczony):** OUTRO/NET „passes the preregistered 0.9 threshold" jest BŁĘDNE —
  próg to 0.9·p_exec nauczyciela (= 0.825, 40/48), nie 0.9; obecne brzmienie czyta się jako
  „bar 90%". Zamień na: „passes the preregistered threshold of 0.9× its teacher's success
  rate". (Klasa: liczba kanonu skrócona do fałszu — dokładnie po to jest ta weryfikacja.)
- **C3 (atrybucja zejścia — klasa erratum #3):** ACT3 @101-109 „The shield takes over: hover,
  then controlled descent" przypisuje zejście OSŁONIE. Zweryfikuj z trace/kodu, KTO komenduje
  opadanie po REFUSE(GEOFENCE) w pętli ławki: jeśli tor D5 osłony — zdanie zostaje z dopiskiem
  „(shared descent)"; jeśli zejście końca epizodu po stronie harnessu — brzmienie: „The climb
  is refused and held; the flight ends in a controlled descent." Wynik weryfikacji (plik:linia
  ścieżki, która realnie zadziałała w take_2) do raportu. Nie zgaduj — to jest dokładnie
  rozróżnienie, które kosztowało erratum #3.

## §3. Wykonanie

1. C1/C2: re-render karty OUTRO; C3: weryfikacja + ewentualny re-render nakładki segmentu
   @101-109 aktu 3; re-encode `DEMO_V3.mp4`; poprzednia wersja zachowana jako
   `DEMO_V3_rc1.mp4` (precedens erratum #3 — nic nie znika); nowy sha do RAPORT_DEMO_V3
   + aktualizacja CAPTIONS_VERBATIM.
2. Commit (raport zaktualizowany + CAPTIONS + oba mp4 wg polityki wideo repo). Skuteczność
   tego aneksu = automatyczna z chwilą commita poprawek; osobna linia CC niepotrzebna.
   Odchylenie przy wykonaniu ⇒ pytanie przed wpisem, jak zawsze.
3. STOP. Push = Olga. **Ostatnia bramka filmu = seans Olgi** (czytelność panelu, tempo,
   moment sejwu); jej uwagi wracają do mnie — montażowe poprawki na istniejących klatkach są
   legalne bez nowego aneksu, nowe booty NIE.

## §4. Po zamknięciu

DEMO_V3 wchodzi do pakietu zewnętrznego programu (follow-up „video available" może wskazywać
ten plik; nota syntezy — akapit o sejwie ma teraz materiał wizualny). Tryb katalogu bez zmian;
następna noga = decyzja kryterium dwóch miesięcy, osobno.
