# RAPORT_2A — noga 2A „percepcja w pętli": raport zbiorczy i zamknięcie (CO-2A)

CC · 06.10.2026 · wykonanie ANEKS_2A-4 §6. Łańcuch nogi: PRE_2A (ratyf. 03.10) →
S1 build (RAPORT_2A_S1) → S2 shadow (RAPORT_2A_S2) → ANEKS_2A-1 (N1/N2) → S2b powtórka
(RAPORT_2A_S2b) → ANEKS_2A-2 (errata B(i), C-sonda) → S3 (RAPORT_2A_S3, bloker C1) →
ANEKS_2A-3 (N3-C, żywość) → S4 sonda (RAPORT_2A_S4) → ANEKS_2A-4 (ten raport).
Booty lotne VALID: **7 z ≤31** (A1/A2 · A1b/A2b · C1 · C1r/C2). Breach 0 i REFUSE 0
we wszystkich siedmiu.

## §1. WERDYKT NOGI (ANEKS_2A-4 §2 verbatim)

Pytanie pierwotne („ile kosztuje zejście z wyroczni na percepcję", kampania parowana)
**NIE zostało zmierzone** — kampanię uchylił wyjątek ekonomiczny po uczciwym FAIL-u błędu
(ANEKS_2A-2). Zmierzone zostały trzy rzeczy, każda z twardym mechanizmem:

1. **Tor percepcji jest sprawny WSZĘDZIE poza detektorem.** Czas: klatki 14.7 Hz
   (shadow) / 6.7–7.2 Hz in-process (kontencja egzekutora — wpis do katalogu), inferencja
   ~7–15 ms, latencja end-to-end p95 0.044–0.052 s. Geometria: pokrycie orbity 1.0000 ×2
   po naprawie yaw (sanity nosa 4.1–4.7°). Projekcja: pinhole 0.65–1.06 m na celu
   w kadrze, konwersja ramek dowiedziona danymi (quat vs attitude p50 <1°). Ogniwo
   limitujące: **pretrained detektor open-vocabulary na tle naziemnym** — top-1 poza
   celem w ~88–97% klatek orbity (pix p50 ~280–300); na tle nieba trafiał (S2) — kruchość
   separatora, powtórka lekcji r02.
2. **Mapa bezpieczeństwa trzech trybów degradacji percepcji** (istnienie i mechanizm,
   nie stopy; n=1–2 biegi per tryb; breach 0 i REFUSE 0 we WSZYSTKICH 7 bootach nogi):
   - **martwa** (C1): feed niemy od t0 ⇒ hover-hold na home cały epizod, r_max 0.2 m,
     intruz GT przeszedł 1.64 m obok — fail-silent → fail-safe Z KONSTRUKCJI (semantyka
     track_valid);
   - **wygłodzona** (C1r): w zawisie brama admisyjna nie wpuszcza klatteru (central∧mti
     4/256, nigdy k=3) ⇒ dron statyczny, r_max 0.09 m; bez ego-motion MTI nie łapie tła;
   - **kłamiąca** (C2, pomiar właściwy): ENTRY na fantom t_rel 2.4, track kłamał do
     53.0 m (146 ticków z celem POZA R_E=32), NCP gonił z |cmd|≈3 m/s i wspiął się
     z 7.15 do 17.55 m — a r_est_max = **12.22 m, margines 19.78 m, zero interwencji**.
     Mechanizm zawierania NIE-osłonowy: brama REFRESH głodzi track (fresh 101/504),
     age>1.0 s tnie konsumenta na hover-hold (798/1435), θ_age dobija fantom (42.2 s) —
     pogoń POSZATKOWANA zanim dojdzie do geofence'u. Osłona pozostała cicha jako
     niezaangażowana ostatnia linia. Nota opisowa: wspinaczka do 17.55 m przy V_E=20
     spójna ze znanym pełzaniem ramienia net; komenda nie przekroczyła V_E.
3. **Usterka jednostek yaw** (radiany w stopniowe pole MAVSDK, obecna od zawsze) —
   wykryta trybem cienia za 2 booty, naprawiona na granicy jednostek; werdykty
   NET/K2/W/LIQ niezależne (sędzia pozycyjny, zweryfikowane grepem przez CC).

**Noga 2A: CLOSED — „detektor limituje; reszta toru dowiedziona sprawna; bezpieczeństwo
pod degradacją percepcji zmierzone w trzech trybach".**

## §2. Tor percepcji — liczby i dowody (S1/S2/S2b)

Przyrząd (FREEZE_2A): FEED-V = kamera mono STOCK 99.7°/640×480/15 Hz → YOLO-World
yolov8s-worldv2 (frozen 9b2c17ab, zero treningu) → admisja struktura∧MTI k=3 →
pinhole f_px=270 / W_real=2.5 m → kontrakt R1 identyczny z FeedB; rejestr feedów D6;
zero GT w torze.

- **Czas (dowiedziony sprawny):** klatki 14.71 Hz, YOLO 7–15 ms, latencja E2E p95
  0.044 s (S2 A1) / 0.052 s (S2b) — `RAPORT_2A_S2.md` / `RAPORT_2A_S2b.md`. Litera progu
  kadencji (≥8 Hz „świeżych") padła w S2b (7.58 Hz) z przyczyn JAKOŚCIOWYCH po N2 —
  errata ANEKS_2A-2 §2: świeżość mierzy od N2 koniunkcję jakości∧czasu; surowy tor
  czasowy zdrowy. Śmierć czasowa kierunku NIE ogłoszona.
- **Geometria (dowiedziona sprawna):** po N1 (rad→deg na granicy MAVSDK,
  bench_flight 05137098) pokrycie orbity RZECZYWISTE 1.0000 ×2, sanity nosa mediana
  4.66°/4.11° z kontrolą negatywną 75.16° na danych sprzed N1 — `RAPORT_2A_S2b.md` §4.
  Approach FAIL ×2 (0.898/0.648) = slew nosa na starcie epizodu, wpis opisowy.
- **Projekcja (oczyszczona):** pinhole na celu w kadrze 0.65–0.80 m (S2b) / 1.06–1.82 m
  (S2); exact-quat daje identyczny błąd (projekcja niewinna); quat pokładowy vs attitude
  PX4 p50 0.76–0.92° — `RAPORT_2A_S2.md` §2, `RAPORT_2A_S2b.md` §3.
- **Ogniwo limitujące = DETEKTOR (atrybucja twarda, dowody rozłączne):** cel w kadrze
  100% orbity i duży (80–105 px), a top-1 NIE na intruzie w ~97% (A1b) / ~88–97% (A2b)
  klatek; pix p50 298/281; tło = klatter naziemny, na tle nieba trafiał (S2); błąd toru
  p95 40.9 m (S2b) / 50.9 m (S2) z mechanizmem śledzenia-poza-celem, NIE projekcji —
  `RAPORT_2A_S2b.md` §5. MTI pod rotacją ~20°/s koincyduje z tłem (ENTRY A1b na tło
  29.5 m mimo k=3∧MTI).
- **Kadencja in-process 6.7–7.2 Hz** (S4, FEED=V w procesie ławki) vs 14.7 Hz shadow —
  kontencja jednowątkowego egzekutora feedu (pos ~100 Hz + att ~100 Hz + obraz 15 Hz);
  opisowe, do katalogu przy detektor-v2 — `RAPORT_2A_S4.md` §5.

## §3. Mapa bezpieczeństwa trzech trybów degradacji percepcji (S3/S4)

Konfiguracja sondy: FEED=V aktywnie karmi CONTROLLER=net (NCP 0337d5ea), pełne
uzbrojenie, scenariusze c11_s01/c08_s03, ważność V2′ + żywość instrumentu
(ANEKS_2A-3 §4: ALIVE = ≥1 fresh LUB ≥10 klatek w 30 s epizodu).

| tryb | boot | mechanizm | wynik bezpieczeństwa |
|---|---|---|---|
| **martwa** | C1 (`probeC/C1_c11_s01`, RAPORT_2A_S3) | kolizja egzekutora: feed 0 klatek od t0 (defekt budowy S1, naprawiony N3-C) | track_valid 0/791 ⇒ hover-hold; breach 0, REFUSE 0; r_max 0.2 m; intruz GT 1.64 m obok — fail-silent→fail-safe z konstrukcji |
| **wygłodzona** | C1r (`probeC/C1r_c11_s01`, RAPORT_2A_S4) | feed ŻYWY (306 klatek, 256 boxów tła), ale admisja D2 trzyma: klatter krawędziowy 181/256, mti_ok 10/256, central∧mti 4/256, nigdy k=3 | 0 ENTRY ⇒ dron statyczny; breach 0, REFUSE 0; r_max 0.09 m |
| **kłamiąca** | C2 (`probeC/C2_c08_s03`, RAPORT_2A_S4) | ENTRY t_rel 2.4 na fantom; track do 53.0 m (146 ticków poza R_E=32; err vs GT p50 9.9 / max 48.6 m); NCP approach \|cmd\|≈3 m/s, wspinaczka −7.15→−17.55 m | breach 0, REFUSE 0; **r_est_max 12.22 m, margines do R_E 19.78 m**; pogoń szatkowana bramą REFRESH (fresh 101/504) + cięciem age>1.0 (hold 798/1435) + θ_age (FEED_EXPIRE 42.2 s); osłona niezaangażowana |

Zastrzeżenie mocy: istnienie i mechanizm, nie stopy (n=1–2 na tryb); tryb kłamiący
zaistniał w jednej geometrii (c08_s03); REFUSE(GEOFENCE) na pogoni — możliwy, niezmierzony
(pogoń nie doszła do pasma).

## §4. Usterka yaw i nota dla nóg przeszłych

`net_controller.py:115` emituje yaw=atan2 w RADIANACH; `bench_flight.py` (przed N1)
wkładał to w STOPNIOWE pole `VelocityNedYaw` ⇒ nos stał ~0° przez pięć nóg lotnych.
Wykrycie: S2 (2 booty cienia, 100% wypadnięć celu z kadru przez azymut, desk R5 obalony
w locie); naprawa N1 = `math.degrees()` wyłącznie na granicy MAVSDK (trzecia edycja
bench_flight, D6-rozszerzenie, ratyf. ANEKS_2A-1); dowód: sanity yaw 4.66°/4.11° +
pokrycie 1.0000 ×2. **Nota dla er przeszłych:** usterka była nośna wyłącznie dla kamery —
velocity NED od yaw niezależne, sędziowie nóg NET/K2/W/LIQ są pozycyjni
(`results/NET/RAPORT_NET_S2.md`, `results/W/RAPORT_W.md`, kanony K2/LIQ), więc werdykty
stoją; zweryfikowane grepem przez CC (ANEKS_2A-4 §2 p.3).

## §5. KANON OBOWIĄZUJĄCY — ANEKS_2A-4 (verbatim §3)

**WOLNO** (każde zdanie niesie: SITL, rendering syntetyczny, kamera mono 99.7°/640×480,
detektor pretrained BEZ treningu na domenie, geometria c-siatki, liczności jak wyżej):
- zdania 1–3 z werdyktu (§1 tego raportu) verbatim, z liczbami;
- „pierwsza integracja percepcji w pętli ujawniła i zamknęła pomiarem ukrytą usterkę
  harnessu (jednostki yaw) — koszt wykrycia: 2 booty trybu cienia";
- „kampania kosztu percepcji nie została wykonana (wyjątek ekonomiczny po FAIL-u błędu
  percepcji)" — wprost, bez łagodzenia.

**NIE WOLNO:**
- „system bezpieczny pod złą percepcją" jako stopa lub ogólność — wolno: istnienie
  i mechanizm z n=1 biegu trybu kłamiącego;
- przypisywać bezpieczeństwa C2 OSŁONIE — nie interweniowała; bezpieczeństwo dała
  higiena toru percepcji (bramkowanie+starzenie+hover-hold); osłona = niezaangażowana
  ostatnia linia. Symetrycznie: nie wolno twierdzić, że osłona „by złapała" — nie było
  pomiaru;
- „percepcja nie działa" / „YOLO zły" w ogólności; cytowania 40–51 m bez noty
  o mechanizmie (śledzenie-poza-kadrem / top-1-poza-celem);
- czegokolwiek o KOSZCIE percepcji (Δ) — niezmierzony; „dron lata na kamerze" — nie lata,
  dopóki detektor-v2 nie przejdzie bramki B.

## §6. Rozliczenie predykcji (ANEKS_2A-4 §4; pełny zapis w KSIEGA_PREDYKCJI sekcja NOGA 2A)

P-2A-1 ✗ · P-2A-2 ✗ · P-2A-3 ✗ · P-2A-4/5 poza sumą (kampania nie poleciała; nota:
w sondzie REFUSE=0). **Suma: 0✓/3✗ (+2 poza sumą).** Kalibracja: wszystkie trzy ✗ =
przeszacowanie gotowości integracyjnej nowego toru (kierunek PRZECIWNY do serii W/LIQ).
Nowa reguła kalibracyjna dla PRE nóg integracyjnych: bramki techniczne — korekta w dół,
wyniki naukowe — korekta w górę (reguła 9 bez zmian).

## §7. Rejestr odchyleń nogi (ANEKS_2A-4 §5)

1. Errata progu kadencji B(i) — metryka zmieniła znaczenie przez ratyfikowaną
   interwencję N2 (błąd CC; ANEKS_2A-2 §2).
2. Trzecia edycja bench_flight (N1, rad→deg) — ratyfikowane rozszerzenie D6
   (ANEKS_2A-1 §3).
3. Defekt egzekutora rclpy z budowy S1 — klasa „tryb testowany ≠ tryb lotny
   (proces/egzekutor)", do rejestru klas (RAPORT_2A_S3 §2b, naprawa N3-C).
4. Dwa błędy driverów: globalny PYTHONPATH→ros2cli (S3 §2a, naprawione v2);
   env-faile habitatu 05.10 (GZ_IP=127.0.0.1, diagnostyka 0-lotna diag0-2).
5. Kontencja in-process 6.7–7.2 Hz — opisowa, do katalogu przy detektor-v2.
6. C1 przeklasyfikowany na ważny pomiar „dead feed" (ANEKS_2A-3 §2).
7. Warunek żywości feedu dodany przed powtórką sondy (klasa V2′ — ważność przyrządu,
   prerejestrowany w ANEKS_2A-3 §4 przed pomiarem).

## §8. Roadmapa: detektor-v2 (pozycja katalogu, NIE otwierana tym raportem)

**Trigger:** przed jakąkolwiek nogą zamykającą pętlę kamery („dron lata na kamerze").
**Zakres:** zamiana/doszkolenie detektora (jedyne ogniwo z FAIL-em atrybucji) — świadomie
poza 2A (PRE D4: zero treningu).
**Aktywa gotowe (z 2A, zero dodatkowej budowy):**
- dane treningowe za darmo: klatki bootów + GT + projekcja (pinhole frozen) ⇒
  self-labeling boxów intruza;
- sędzia percepcji (percep_judge 363c37b7) + dekompozycja kąt/zasięg;
- bramki B (kadencja/latencja/błąd z progami PRE_2A) i C (kampania parowana 12×2,
  zamrożona, NIELATANA) — po przejściu B kampania C startuje bez projektowania;
- nota kontencji: przy FEED=V in-process rozważyć decymację pos/att albo osobny proces
  feedu (lekcja S4 §5).

Porcelain przy CO-2A: tylko {ANEKS_2A-4.md, results/2A/RAPORT_2A.md,
results/KSIEGA_PREDYKCJI.md} — jeden commit, zero bootów. Push = Olga. STOP.
