# ANEKS_NADIR-5 — zamknięcie nogi: S4 FAIL przez (g) w 5/12 cięć przy zdolności zmierzonej 12/12 × 110 s bez GNSS (breach 0, REFUSE 0); orzeczenie (a) 12/12; przesłanka A-nadir nie trzyma w obu połowach (zrywy EKF przy hamowaniu, dziury przyjęcia, poprawka jednym znacznikiem × bias kursu); NADIR CLOSED

CC · 11.11.2026 · łańcuch NADIR, po STOP-NADIR4 (7b1119cb na origin).
Zamyka nogę. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem)

1. **Litera (a), (b), (c), (e), (f) przeliczona od zera** z
   `trace.jsonl` i `rama.jsonl`, bez kodu wykonawcy. 12 cięć:
   kontynuacja od wstrzyknięcia odcięcia 110.004–110.052 s; REFUSE
   w fazach misji 0; track 1.000, pasmo 6–10 m 0.936–1.000; margines
   do R_E min 7.47 m; u_max/m max 0.812, zero ticków u > m; τ p95
   ≤ 0.212 s, max 1.004 s. 16 epizodów nominalnych: zero REFUSE, zero
   ticków poza NOMINAL, margines min 6.00 m. Zgodne z raportem.
2. **(g) odtworzone definicją analizatora** (jego `e3_series`
   i reguła okna, pętla CC; chwila flagi z wierszy `flag` trace, bo
   ULG nie ma w repo): 28/28 epizodów zgodnych z tabelą raportu co do
   liczby okien i trzeciej cyfry. Bez GNSS **36 z 6581 okien (0.55%)**
   ponad ε_b(⌊τ⌋): c08_s01 8 (max 1.978), c08_s02 3 (2.093), c10_s01
   11 (1.353), c10_s02 8 (1.246), c11_s02 6 (1.222). W oknach z GNSS
   przed cięciem 0.
3. **(d) nieprzeliczone** — liczone z `boot.ulg`, których nie ma
   w repo (.gitignore). Przyjęte z `wyniki_nadir_s4.json` (nav_state
   14 i failsafe 0 od flagi do przyziemienia, 12/12); trace zgodny:
   sekwencja zdarzeń bez failsafe'u, zejście komendą drivera.
4. **Stanowisko:** tempo 16 bootów 0.9355–0.9744, bramka zdrowia
   18 pomiarów, 3 poniżej 0.90, zero STOP-ów — z `kont_tempo.json`
   i `bramka_ksiega.jsonl`.
5. **Trzy znaleziska CC ponad raport:**
   - **Nominały, kolumna (g) — artefakt przyrządu.** Cztery „✗" to
     ostatnie okno epizodu, niedomykane końcem epizodu (τ_max
     175–268 s); pierwsze przekroczenie pada 1.0–1.5 s po
     `episode_end`. W oknach misji nominałów przekroczeń 0. Bez
     wpływu na werdykt.
   - **Druga połowa przesłanki certu nie ma kryterium w literze S4.**
     |p_fix − GT(t_fix)| wobec ε_fix_freeze(koszyk), fazy misji:
     bez GNSS **62 z 6582 poprawek ponad obwiednię (0.94%), max
     2.21×** (0.50 m przy 0.227 m), z tego 56 w koszyku 4–6 m;
     w nominałach 314 z 6565 (4.8%), max 0.89 m — tu co do sztuki
     zgodne z obserwablą wykonawcy `eps_fix_live_ponad_freeze`
     w plikach per boot.
   - **Suma, którą konsumuje dowód,** |p_corr − GT| per tick misji
     bez GNSS (27 253 ticki): p50 0.11 / p95 0.25 / max 0.67 m przy
     GT z chwili ticku; p50 0.22 / p95 0.39 / max 0.73 m
     z przesunięciem czasu przyrządu (0.10–0.12 s, jak w (g)). Ponad
     ε_fix_freeze + ε_b(⌊τ⌋): 2 ticki (o ≤ 0.04 m) albo 40 ticków
     w pięciu bootach (o 0.11 m w najgorszym) — zależnie od
     parowania; dane w repo parowania nie rozstrzygają. Błąd nie
     rośnie z czasem od cięcia: p95 0.22–0.27 m (0.35–0.43 m)
     w każdym z pięciu przedziałów po 22 s, gdy błąd własny EKF
     rośnie do p95 7.4 m i max 8.5 m.
6. **Korekty własnej metody w tej weryfikacji:** okna grupowane po
   `seq` (licznik rekordów klatek, nie poprawek) — zaniżone,
   zastąpione definicją analizatora; hipoteza „przekroczenia to
   artefakt wyrównania czasu" — obalona (przy zerowym przesunięciu
   17 okien w tych samych pięciu bootach, max 1.88); hipoteza
   „tempo dryfu rośnie z czasem od cięcia" — obalona (§3.1).

## §2. Werdykt drabiny

1. **(g): 5/12 cięć z przekroczeniem ⇒ FAIL nogi** (litera
   PROMPT_NADIR_S4 §2). Werdykt wykonawcy potwierdzony. Bez
   strojenia, bez powtórek.
2. **(a) — orzeczenie CC: spełnione 12/12.** „Kontynuacja ≥ 110 s od
   cięcia" liczy się od chwili wstrzyknięcia odcięcia (`t_inj_sim`
   w rekordzie `denial`); pole `sim` tego rekordu to stempel zapisu,
   4–12 ms późniejszy. Od wstrzyknięcia wszystkie 12 ≥ 110.004 s;
   trzy „✗" analizatora (109.992–109.996 s) wynikają z punktu
   odniesienia przyrządu. Orzeczenie zapada po obejrzeniu danych
   i jest tak zapisane; werdyktu nogi nie zmienia, bo (a) nie jest
   jego podstawą. Wada nazwana przez wykonawcę stoi: nastawa drivera
   równa progowi, bez zapasu.
3. **(b)–(f): zero naruszeń** w 28 epizodach.
4. **NADIR — CLOSED. Bramka S4: FAIL przez (g).** Czyste w całej
   literze 7/12 cięć (c01_s01, c01_s03, c02_s01, c02_s03, c05_s01,
   c05_s02, c11_s01) i 16/16 epizodów nominalnych. Budżet: S4 20/24,
   noga 31/35. Breach 0, REFUSE(POS) fałszywy 0.

## §3. Co zawiodło: przesłanka dowodu, nie lot

P9_nadir dowodzi zawierania przy założeniu A-nadir: (i) przyrost
błędu EKF w oknie między poprawkami ≤ ε_b(⌊τ⌋); (ii) |p_fix − GT| ≤
ε_fix_freeze(koszyk). Obie połowy sformułował CC i obie nie trzymają
na świeżych danych.

**3.1 Połowa (i) — 36 okien, dwa mechanizmy.**
- **Zrywy przy hamowaniu: 32 okna po 0.2 s, max 1.58×.** Układają
  się w 13 serii (10 po 2–4 kolejne okna, 3 pojedyncze). 31 z 32
  pada przy malejącej prędkości (baza 51%); przyspieszenie poziome
  w tych oknach ma medianę 1.91 m/s² (95. percentyl wszystkich okien
  tych komórek), przechył 10° (mediana bazy 3.5°). Błąd własny EKF
  przesuwa się wtedy o 0.33–0.51 m na okno, czyli 1.6–2.5 m/s.
  Wszystkie leżą w sześciu komórkach z v_p95 ≥ 3.0 m/s (5 z 6
  z przekroczeniem, szósta 0.91). W sześciu wolniejszych takie
  przyspieszenie zdarza się w 1 oknie na 3298 i przekroczeń jest 0
  (max 0.66–0.95). Przyczyna wewnątrz estymatora niezmierzona
  (wymaga ULG).
- **Dziury przyjęcia: 4 okna, w tym oba maksima (2.09 i 1.98).**
  W 20 z 6602 klatek misji żadna widoczna obserwacja nie przeszła
  litery przyjęcia (bok < 18 px, r_h ≥ 8 m, krawędź kadru); powstało
  11 okien 0.4–1.0 s. Bariera ich nie widzi, bo ε_b(⌊τ⌋) jest stałe
  przez całą pierwszą sekundę. Zdanie z ANEKS_NADIR-2 §2 („bariera
  konsumuje to uczciwie przez ε_b(⌊τ⌋)") było dla τ < 1 s błędne.
- **To nie jest granica czasu.** Przekroczenia rozkładają się równo:
  5 / 10 / 8 / 7 / 6 w kolejnych przedziałach po 22 s od cięcia. To
  ogon rzędu 1% okien w szybkich komórkach, którego próba S2
  (440 okien, max 0.94) nie mogła pokazać.

**3.2 Połowa (ii) — wszystkie przekroczenia z poprawek jednym
znacznikiem.** 16 bootów, 15 275 przyjętych poprawek: para
znaczników 11 250 — max 0.225 m, zero ponad obwiednię w każdym
koszyku i reżimie; jeden znacznik 4025 — 415 ponad (bez GNSS 62
z 1397, z GNSS przed cięciem 39 z 692, nominały 314 z 1936), max
0.89 m. Błąd poprawki jednym znacznikiem idzie za r_h · sin|bias
kursu| (r = 0.71, nachylenie 1.09, n = 1746 przy r_h > 2 m); para
bias zdejmuje. Obwiednia „1.5 × max z czterech cięć S2" nie
rozróżniała trybów i wyszła niemonotoniczna (koszyk 4–6 m
najniższy: 0.227 m).

**3.3 Bias kursu po cięciu nie jest stały** (korekta w przód zdania
z ANEKS_NADIR-2 „nie dryfuje po cięciu", opartego na 22 s): mediana
12 lotów przechodzi z −3.4° tuż przed cięciem do +1.2° w przedziale
88–110 s; tempo maleje (0.94 / 0.62 / 0.46° na kolejne 22 s). Dalszy
przebieg niezmierzony. W bootach nominalnych bias z par
−3.7…−5.75°.

**3.4 Arytmetyka na wartościach faktycznych** (fakt, nie dowód):
największy zmierzony błąd pozycji poprawionej plus Δ_D5 to najwyżej
0.75 · m w najwęższej komórce (c08_s02, m = 2.99). Zawieranie
fizyczne nie było zagrożone w żadnym ticku; nie trzyma rachunek,
który miał je gwarantować z góry.

## §4. Co stoi (pomiar)

- **Zdolność:** sieć pod odcięciem GNSS prowadzi zadanie 110 s
  (5 × T*) w 12/12 cięć na pozycji poprawianej znacznikami
  naziemnymi (kamera w dół, 5 Hz): track 100%, w paśmie 6–10 m
  ≥ 93% czasu, zero REFUSE, zero naruszeń R_E przy marginesie min
  7.47 m, koszt bariery 0; offboard do końca i zero natywnego
  failsafe wg ULG wykonawcy.
- **Mechanizm „bez limitu" w zakresie zmierzonym:** błąd pozycji
  poprawionej jest płaski w czasie (max 0.67–0.73 m), gdy błąd
  własny EKF rośnie do 8.5 m. Lot dłuższy niż 110 s nie był
  mierzony.
- **Ramię nominalne:** 16/16 epizodów bez fałszywego wejścia i bez
  REFUSE przy `NADIR_MODE=1`.
- **Certy** P9/P1/P5/P7_nadir (replikowane przez CC po S3) pozostają
  poprawne jako twierdzenia warunkowe; dla lotów S4 warunek nie jest
  spełniony, więc loty są zmierzone, nie dowiedzione.

## §5. KSIĘGA (append-only przy commicie §CO)

```
## NADIR S4 i zamknięcie nogi (ANEKS_NADIR-5, 11.11.2026)
- Drabina S4: FAIL przez (g) w 5/12 cięć — przyrost błędu EKF
  w oknie między poprawkami ponad ε_b(⌊τ⌋) w 36 z 6581 okien bez
  GNSS (0.55%, max 2.09; c08_s01, c08_s02, c10_s01, c10_s02,
  c11_s02). (a) 12/12 po orzeczeniu CC (od wstrzyknięcia
  110.004–110.052 s; analizator liczył od stempla zdarzenia,
  4–12 ms później). (b)–(f) 0 naruszeń, nominały 16/16. CC odtworzył
  (g) definicją analizatora co do okna (28/28 epizodów), resztę
  własnym kodem; (d) przyjęte z ULG wykonawcy.
- Zdolność zmierzona: 12/12 cięć × 110 s (5 × T*) bez GNSS na
  pozycji poprawianej znacznikami — track 100%, REFUSE 0, breach 0,
  margines do R_E min 7.47 m, koszt bariery 0; błąd pozycji
  poprawionej płaski w czasie (p95 0.2–0.4 m, max 0.67–0.73 m) przy
  błędzie własnym EKF do 8.5 m.
- P-NADIR-1 (0.70) — ✗ (śmierć S1 po literze tempa, ANEKS_NADIR-1;
  po naprawie S1F czyste). P-NADIR-3 (0.55, S4 PASS) — ✗: litera
  (a)–(f) z PRE spełniona, bramka z (g) dodanym przed lotami FAIL.
  P-NADIR-4 (0.90, breach 0) — ✓ (31 bootów). Noga: 2/4 przy sumie
  szans 2.90 — szanse CC nadal zawyżone. ✓ P-NADIR-2 z S2 było
  wynikiem próby 440 okien; na 6581 oknach warunek nie trzyma.
- Przesłanka A-nadir (CC) nie trzyma w obu połowach. (i) Przyrost:
  32 okna to zrywy błędu EKF 1.6–2.5 m/s przy hamowaniu (31/32 przy
  malejącej prędkości, |a| mediana 1.9 m/s²; tylko sześć
  najszybszych komórek), 4 okna to dziury przyjęcia 0.4–1.0 s (oba
  maksima). (ii) Błąd poprawki: bez GNSS 62/6582 ponad
  ε_fix_freeze (max 2.21), nominały 314/6565 — wszystkie jednym
  znacznikiem; para 0 z 11 250 (max 0.225 m). Błąd jednego
  znacznika ≈ r_h · sin|bias kursu| (r = 0.71). Suma per tick:
  2–40 z 27 253 ticków ponad sumę składników (o 0.11 m
  w najgorszym).
- ✗ projektowe CC ×4: (1) obwiednia nauczyciela 2d użyta wobec sieci
  w prefiksie okien i przyjęta po S2 przy max 0.94 na 440 oknach —
  zapas 6% na próbie za małej na ogon ~1%; teza z ANEKS_NADIR-2
  §3.2 („NADIR nieczuły") obalona; kolejna instancja „zadany ≠
  faktyczny" i powtórka lekcji KONT-5. (2) FREEZE „1.5 × max"
  z czterech cięć nie rozróżnia trybu poprawki i wyszedł
  niemonotoniczny (koszyk 4–6 m najniższy) — przyjęty bez pytania.
  (3) Litera S4 strzegła jednej połowy przesłanki certu. (4) Litera
  przyjęcia (18 px, r_h < 8 m, krawędź) zostawia klatki bez
  obserwacji, a ⌊τ⌋ nie widzi ich przez pierwszą sekundę — wbrew
  zdaniu z ANEKS_NADIR-2 §2.
- ✗ metodyczne CC (weryfikacja S4): okna grupowane po `seq` (licznik
  rekordów, nie poprawek); hipoteza artefaktu wyrównania czasu
  (obalona: przy zerowym przesunięciu 17 okien, max 1.88); hipoteza
  narastania z czasem (obalona: 5/10/8/7/6 na 22 s). Skorygowane
  w tej samej turze.
- Korekta w przód zdania z ANEKS_NADIR-2: bias kursu po cięciu nie
  jest stały — mediana 12 lotów −3.4° → +1.2° w 110 s, tempo maleje
  (0.94 / 0.62 / 0.46° na kolejne 22 s); dalej niezmierzone.
- Wykonawca: kampania 16/16 bez STOP-u stanowiska; analizator (g)
  poprawny; (a) i własna wada nastawy nazwane uczciwie; „mechanizm
  niezmierzony" zamiast zgadywania. Wady: nastawa T_CONT równa
  progowi i odniesienie od stempla zdarzenia; ostatnie okno epizodu
  niedomykane (4 fałszywe „✗ (g)" w nominałach, kolumna
  informacyjna); obserwabla błędu poprawki policzona, lecz
  niewyniesiona do raportu płaskiego mimo wartości niezerowych
  w 27/28 epizodów.
- Stanowisko (10.11, DIAGNOZA_STANOWISKA_2 i decyzje CC bez aneksu):
  zegar gościa pod obciążeniem równy zegarowi Windows (1.00000) —
  zdanie „gość ~3–4% wolniej" z ANEKS_NADIR-4 cofnięte, ✗ CC;
  ustawienie karty „maksymalna wydajność" odrzucone regułą; drugi
  użytkownik karty po stronie Windows obniża tempo (PredatorSense
  ~33% ⇒ 0.85, Chrome ~18% ⇒ 0.88–0.90; r = −0.94, n = 11) — reguła
  stanowiska: podczas kolejki żadnych aplikacji okienkowych poza
  terminalem. Skutek: 16 bootów 0.9355–0.9744, bramka zdrowia
  18 pomiarów / 3 NO-GO / 0 STOP-ów. Duży skok −20…−25% nigdy
  niezarejestrowany z telemetrią — przyczyna nieustalona.
- Lekcje nogi: przesłanka dowodu ma być mierzona na wielkości, którą
  dowód konsumuje (tu |p_corr − GT| per tick), na sterowniku
  docelowym i na próbie rzędu ekspozycji bramki; każda połowa
  przesłanki dostaje kryterium w literze; obwiednia niemonotoniczna
  tam, gdzie fizyka jest monotoniczna, to sygnał za małej próby;
  litera przyjęcia obserwacji wymaga rachunku pokrycia.
```

## §6. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 11.11.2026 (CO-N5, ANEKS_NADIR-5)
- **NADIR (kamera w dół + siatka znaczników naziemnych: lot po
  utracie GNSS bez limitu czasu) — CLOSED, bramka S4 FAIL przez (g).**
  Zdolność zmierzona end-to-end w SITL: sieć pod odcięciem GNSS
  prowadzi zadanie 110 s (5 × T*) w 12/12 cięć na pozycji
  poprawianej znacznikami 5 Hz (track 100%, zero REFUSE, offboard do
  końca, zero naruszeń R_E przy marginesie min 7.47 m, zero
  fałszywych wejść w 16 epizodach nominalnych); błąd pozycji
  poprawionej nie rośnie z czasem (max 0.67–0.73 m przy błędzie
  własnym EKF do 8.5 m). Dowód zawierania P9_nadir (+P1/P5/P7_nadir,
  replikacja CC) nie obowiązuje dla tych lotów: przesłanka A-nadir
  nie trzyma w obu połowach (przyrost w oknie 36/6581, błąd poprawki
  jednym znacznikiem 62/6582) — loty zmierzone, nie dowiedzione. Lot
  dłuższy niż 110 s niezmierzony. Budżet 31/35.
- Mechanizmy nazwane: zrywy błędu EKF przy hamowaniu w szybkich
  komórkach; dziury litery przyjęcia niewidoczne dla ⌊τ⌋; poprawka
  jednym znacznikiem niesie bias kursu (para go zdejmuje:
  0 przekroczeń na 11 250); bias kursu po cięciu przesuwa się
  (−3.4° → +1.2° w 110 s).
- Kierunek ewentualnego powrotu (nowa pozycja, NIEOTWARTA):
  przesłanka na sumie |p_corr − GT| per tick z danych S4
  (27 253 ticki), z zapasem i rozdzielczością τ poniżej sekundy;
  poprawka jednym znacznikiem z bieżącym biasem z par albo para
  z partnerem ≥ 8 m; świeża bramka 12 + 4. Rachunek wstępny (nie
  przesłanka): 1.5 × 0.73 + Δ_D5 = 2.62 ≤ 2.99 w najwęższej komórce,
  zapas 0.37 m. Recon przy biurku na danych S4 (0 bootów; ULG
  u wykonawcy na zrywy przy hamowaniu), szac. całość 18–22 booty.
- Katalog: 2d zamknięta budżetem czasu (T* = 22 s), KOTW granicą
  geometrii, NADIR bramką dowodu przy zmierzonej zdolności 5 × T*.
  Breach 0 / REFUSE(POS) fałszywych 0 programowo bez zmian
  (31 bootów nogi, łącznie ~220 bootów programu).
```

## §CO

Bramka: origin/master == **7b1119cb**. Jeden commit [CO-N5]: korzeń
`ANEKS_NADIR-5.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §5 append-only + `KIERUNKI_PO_PLANIE.md` §6 append-only. Zero
bootów, zero zmian kodu i raportów — errata tylko w przód,
`STOP_NADIR4.md` zostaje jak jest. Pliki `boot.ulg` z 16 bootów S4
zostają na dysku wykonawcy (potrzebne do ewentualnego reconu zrywów
przy hamowaniu) — nie kasować. Push = Olga. Po „wypchnięte" CC
zamyka z repo (byte-check) i aktualizuje raport programu.
