# ANEKS_KONT-3b — rozstrzygnięcia przed kodem S3: kolejność reguł z kodu, R-G-NOM bez zatrzasku, t_KONT od pierwszego ticka flagi, stary monitor POS zostaje uzbrojony (odrzucenie rekomendacji 4), korekta R_nom → 27.30 m

CC · 7.11.2026 · łańcuch KONT, po pytaniach wykonawcy (stan 94ff9851,
0 bootów, zero nowych plików — bramka zadziałała). Wklejany jako jedyny
dokument; po commicie §CO wykonawca zaczyna kod S3 według PROMPT_KONT_S3
z poniższymi rozstrzygnięciami. Sygnały bez numeru odrzucasz.

## §1. Rozstrzygnięcia

1. **Kolejność reguł: zostaje frozen — latch > R-POS > R-G.** Zapis
   w PROMPT_KONT_S3 §2 „dominacja R-G > R-POS jak frozen" był błędem CC
   (cytowałem frozen odwrotnie; uzasadnienie kolejności w shield.py:154
   jest merytoryczne — bariera geofence na niepewnym p jest
   niewiarygodna). P1_kont dowodzi kolejność z kodu. ✗ CC do KSIĘGI.
2. **Bariera nominalna = nowy liść R-G-NOM, bez zatrzasku.** REFUSE(GEOFENCE,
   rule="R-G-NOM"), stan bez zmian, applied = cel bez składowej radialnej
   na zewnątrz; warstwa komend trybu KONT rzutuje v_ned analogicznie
   (tor wykonawczy wysyła prędkość — bench_flight.py:397, potwierdzone).
   Umiejscowienie w priorytecie: poniżej R-G, powyżej abort (R-G-NOM
   jest prewencyjny, nie terminalny). **Doprecyzowanie S4(f):**
   „0 fałszywych REFUSE w nominale" liczy REFUSE(POS) i wejścia w KONT.
   Aktywacje R-G-NOM w nominale raportowane osobno; na siatce oczekiwane
   0 (r_max 26.16 < R_nom); ≥ 1 nie jest automatycznym FAIL-em, ale
   wymaga wyjaśnienia mechanizmu w raporcie i rozstrzygnięcia CC przy CO.
3. **t_KONT liczy się od pierwszego ticka z flagą** (wejście w stan po
   debounce z cofnięciem zegara o debounce). Indeks koszyka w barierze
   i w P9_kont = ⌊wiek flagi⌋. Opóźnienie odcięcie→flaga (0.004–0.016 s,
   8/8) pokrywa A-flag. Rekomendacja przyjęta — bez tego ostatni koszyk
   gwarancji byłby liczony na danych sprzed własnego zera.
4. **Stary monitor POS zostaje uzbrojony — rekomendacja ODRZUCONA.**
   `pos_flag` (dead_reckoning) podłączony we wszystkich trybach, stara
   ścieżka REFUSE(POS) działa także w KONT. Powód: to jedyna obrona na
   utratę przepływu w KONT (flow pada ⇒ dr=True ⇒ REFUSE(POS)→D5yaw);
   ryzyko nazwane przez wykonawcę w pkt. 4 staje się pokryte, a nie
   zaakceptowane. Koszt zerowy w zmierzonym reżimie: dr = 0 w powietrzu
   w 8/8 lotów S2. Zapis §1 promptu „dead_reckoning logowane pasywnie"
   dotyczył wyłącznie wyzwalacza WEJŚCIA w KONT (nim jest cs_gnss_pos),
   nie rozbrojenia monitora — doprecyzowane niniejszym. P7_kont
   enumeruje oba monitory i licznik t_KONT.
5. **Rekonstrukcja wejść fikstur: przyjęta** w kształcie z pytania
   (S2: cel = pozycja + v·T_LOOKAHEAD, prędkość/pozycja z ekf, flaga
   z wyciągu; FV: v = 0, cel = pozycja, pos_flag = dr). Kod
   rekonstrukcji commitowany; w raporcie nazwana wprost; zakres T0 =
   równoważność na wejściach zrekonstruowanych, dla fikstury FV
   dodatkowo porównanie z decyzjami zapisanymi w trace.
6. **Układ plików: decyzja wykonawcy przyjęta** (cztery certy KONT
   i lustro w `p9_kont_verify.py`; selfcheck i mutanty w
   `results/KONT/s3/tools/`). Lista §0.3 promptu była za wąska — ✗
   drobne CC.
7. **Korekta zamrożenia (kierunek konserwatywny): R_nom = 27.30 m**
   (bariera koszyka 0: 32 − 2.85 − 0.323 − 1.524 = 27.303, w dół do
   setnych). Znosi okno (27.303, 27.51], w którym utrata GNSS dawałaby
   REFUSE w pierwszym ticku KONT — bariera nominalna ma gwarantować
   wejście w kontynuację, nie tylko zawieranie. Koszt bez zmian: 0/48
   (r_max siatki 26.16). ANEKS_KONT-3 §2 obowiązuje z tą jedną liczbą
   zmienioną; niespójność brzegowa we własnym zamrożeniu = ✗ CC do
   KSIĘGI.

## §2. Informacyjne — przyjęte do raportu S3/S4

- Asercja arytmetyczna T* = 22 s obok P9_kont (osobny test reguły
  m_p50, koszyk 22 nie jest kontrprzykładem twierdzenia) — tak.
- Skrócona kontynuacja barierą przy szerokich orbitach (c02_s01_r4:
  przecięcie ~10.5–10.8 s) jest zgodna z PRE §4(c) — kryterium S4 mówi
  „min(T*, chwila legalnego wyjścia barierą)"; do raportu S4 wejdzie
  czas kontynuacji per epizod z przyczyną zakończenia.
- Cytaty braku yaw w obligacjach — do raportu S3 (grep CC i wykonawcy
  zgodne: 0 trafień).

## §CO

Bramka: origin/master == **94ff9851**. Commit 1: korzeń
`ANEKS_KONT-3b.md` verbatim (byte-check sha256 z wiadomości CC):
`KONT [ANEKS-3b]: rozstrzygnięcia S3 1–7, R_nom 27.30`. Potem kod S3
według PROMPT_KONT_S3 + niniejszych rozstrzygnięć, raport STOP-KONT3.
Push = Olga.
