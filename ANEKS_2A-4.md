# ANEKS_2A-4 — werdykt nogi 2A + kanon trzech trybów percepcji + zamknięcie (CO-2A)

CC · 06.10.2026 · łańcuch 2A (po STOP-2A4, commity 583bc45→d85c678→5750fc1 na origin).
Aneks zamykający i samowykonalny (§6): sesja wykonuje CO-2A i STOP; zero bootów — loty
nogi zakończone na 7/≤31.

## §1. Przyjęcie STOP-2A4

Przyjęte po weryfikacji CC z repo: ANEKS_2A-3 w korzeniu byte-identyczny z ratyfikowanym;
N3-C w kodzie (dedykowany SingleThreadedExecutor, diff 2 hunki, sha acc81df7 = FREEZE_2A;
feed_sha niezmieniony d6a3367b z poprawną notą — parametry nietknięte); manifesty sondy
przeliczone: valid ×2, refuse 0 ×2, breach false ×2, wagi 0337d5ea, dsw 0.9588/0.9502.
Warunek żywości (ANEKS_2A-3 §4) zadziałał jako przyrząd: ALIVE ×2, ślepy boot nie mógł
się powtórzyć niezauważony. Test kolizji egzekutora na prawdziwej klasie + kontrola
negatywna — przyjęte.

## §2. WERDYKT NOGI 2A (całość; pytanie pierwotne i to, co faktycznie zmierzono)

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

## §3. KANON ROSZCZEŃ 2A — obowiązujący

**WOLNO** (każde zdanie niesie: SITL, rendering syntetyczny, kamera mono 99.7°/640×480,
detektor pretrained BEZ treningu na domenie, geometria c-siatki, liczności jak wyżej):
- zdania 1–3 z §2 verbatim, z liczbami;
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

## §4. Rozliczenie predykcji (do KSIĘGI, sekcja NOGA 2A)

**P-2A-1 ✗** (bramka A w ≤2 bootach — padła na usterce yaw). **P-2A-2 ✗** (B-czasowa
w całości — litera kadencji padła; errata ANEKS_2A-2 §2 wyjaśnia mechanizm, nie
unieważnia predykcji). **P-2A-3 ✗** (błąd ≤3 m — 40.9 z atrybucją). **P-2A-4 i P-2A-5
poza sumą** (kampania nie poleciała; nota: w sondzie REFUSE=0). **Suma nogi: 0✓/3✗
(+2 poza sumą).** Kalibracja CC, wpis do księgi: wszystkie trzy ✗ to PRZESZACOWANIE
gotowości integracyjnej nowego toru — kierunek przeciwny do serii z W/LIQ (niedoszacowanie
wyników komponentu uczonego). Nowa reguła kalibracyjna: w PRE nóg integracyjnych
(pierwszy przelot nowego toru przez LIVE) predykcje bramek technicznych dostają jawną
korektę w dół; predykcje wyników naukowych — korektę w górę (reguła 9 bez zmian: żadne
nie są priorami).

## §5. Rejestr odchyleń nogi (do RAPORT_2A §7)

Errata progu kadencji B(i) (ANEKS_2A-2 §2, klasa: metryka zmieniła znaczenie przez
ratyfikowaną interwencję — błąd CC); trzecia edycja bench_flight ratyfikowana
(ANEKS_2A-1/2A-... N1, D6-rozszerzenie); defekt egzekutora rclpy z budowy S1 (klasa:
tryb testowany ≠ tryb lotny, proces/egzekutor — do rejestru klas); dwa błędy driverów
(PYTHONPATH→ros2cli, env-faile GZ_IP 05.10 z diagnostyką 0-lotną); kontencja in-process
6.7–7.2 Hz (wpis do katalogu przy detektor-v2); C1 przeklasyfikowany na pomiar „dead
feed" (ANEKS_2A-3 §2); warunek żywości dodany przed powtórką sondy (klasa V2′).

## §6. Zlecenie CO-2A — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista
zamknięta): korzeń `ANEKS_2A-4.md` (ARCH-1, verbatim, pierwszy w commicie); NOWY
`results/2A/RAPORT_2A.md`: §1 werdykt §2 verbatim; §2 tor percepcji z liczbami
(odsyłacze S1/S2/S2b); §3 mapa trzech trybów (odsyłacze S3/S4); §4 usterka yaw + nota
dla er przeszłych (odsyłacz RAPORT_NET/RAPORT_W — werdykty pozycyjne, yaw bez wpływu);
§5 kanon §3 verbatim z nagłówkiem „KANON OBOWIĄZUJĄCY — ANEKS_2A-4"; §6 predykcje §4;
§7 odchylenia §5; §8 roadmapa: **detektor-v2** jako pozycja katalogu z triggerem
(„przed jakąkolwiek nogą zamykającą pętlę kamery"; aktywa gotowe: klatki+GT
⇒ self-labeling, sędzia percepcji, bramki B/C, nota kontencji egzekutora). EDYCJA
`results/KSIEGA_PREDYKCJI.md`: sekcja NOGA 2A wg §4 (0✓/3✗ +2 poza, obie noty
kalibracyjne). Raport płaski: diff-stat, pełna treść RAPORT_2A.md, porcelain. STOP.
Push = Olga.

## §7. Status i dalej

**Noga 2A: CLOSED** z chwilą commita CO-2A i pushu. Budżet 7/31 bootów — najtańsza noga
lotna programu, a przyniosła: naprawę ukrytej usterki harnessu, twardą atrybucję ogniwa
percepcji i pierwszą mapę bezpieczeństwa degradacji percepcji. Program wraca do trybu
katalogu. Przy następnym wyborze nogi moja rekomendacja jest jawna już teraz:
**detektor-v2** ma najkrótszą ścieżkę do „dron lata na kamerze" — dane treningowe za
darmo (GT→etykiety z projekcji), cała ewaluacja zbudowana w 2A, a po przejściu bramki B
czeka gotowa, nielatana kampania C.
