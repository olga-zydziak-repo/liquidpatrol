# PRE_TEACH — lot bez GNSS i bez znaczników na mapie z własnego lotu: mapa spięta obrazem (M4, SIFT), tabela U′ z E = 1.00 m i krawędziami do 2.15 s, osłona bez zmiany kodu; trzy tereny, 12 cięć; ≤ 24 booty

LiquidPatrol · CC · 16.11.2026 · łańcuch TEACH, po STOP-TEACHR2
(ad1e71fd na origin). Do ratyfikacji sygnałem **„ratyfikuję
PRE_TEACH"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja reconu S0B przez CC (z repo, własnym kodem)

1. **Łańcuch commitów.** eb187c68: ANEKS_TEACH-1 w korzeniu, sha256
   3a6259bf… zgodny. 6bfd3892: predykcje przed wynikiem. ad1e71fd:
   STOP.
2. **Mapa tylko sprzed cięcia.** W 39 plikach wiązań (42 660
   wierszy) nie ma wiązania o czasie późniejszym niż chwila cięcia.
3. **Georeferencja — własne rozwiązanie.** Układ równań M3 i M4
   rozwiązany osobnym kodem z zapisanych wiązań: obrót i przesunięcie
   wszystkich klatek kluczowych (732 rozwiązania na wariant) zgodne
   z wykonawcą do czwartej cyfry.
4. **Poprawki po cięciu — własne przeliczenie.** Poprawka i błąd
   policzone od nowa z numeru klatki kluczowej i wektora dopasowania
   dla 154 910 wyników: różnica do 0.0001 m.
5. **Tabela i klasyfikacja przerw.** Policzone od nowa, z własnym
   pokryciem: liczby raportu potwierdzone; wszystkie przerwy ponad
   1.15 s leżą poza mapą.
6. **Ś2 wg litery.** M4 z SIFT spełnia oba warunki na łatach S, M
   i J; M4 z AKAZE tylko na M; M3 nigdzie.
7. **Znalezisko weryfikacji.** Jedyna przerwa na 12 cięciach (p02,
   łata S, 1.4 s) nie wynika z braku mapy. Dobór kandydatów liczy
   pokrycie tak, jakby klatka kluczowa miała rozmiar bieżącego kadru.
   Pięć małych klatek ze startu, leżących jedna na drugiej, wypiera
   wtedy klatkę z wysokości przelotowej. W tym samym miejscu mapa M1
   wybrała ją i dostała 56–96 zgodnych punktów, a M4 wybrało klatki
   startowe i dostało 6–16.

## §2. Rozliczenie reconu i błędy CC

- **Predykcje S0B:** R8 ✓ (0.73 m, przerwa 1.4 s), R9 ✓, R10 ✓
  (0.85 m), R11 ✓ (0.71 m), R12 ✓ (1.05 m), R13 ✓ (p95 0.53 m),
  R14 ✓ — 7/7 przy sumie szans 4.55. Razem z S0: 8/14 przy 8.45.
- **Rachunek z póz (ANEKS_TEACH-1 §4) wobec pomiaru:** M4 na 12
  cięciach 0.91–0.94 m wobec 0.71–0.75 m; lot długi 0.81–0.88 m wobec
  0.85–0.95 m; M3 na 12 cięciach 1.15–1.39 m wobec 1.04–1.12 m.
- **Błędy CC:**
  - dobór kandydatów ślepy na wysokość klatki kluczowej (§1 pkt 7)
    jest w literze obu promptów;
  - sito odległości wiązań nie odrzuciło niczego — było zbędne;
  - predykcje jednego reconu są ze sobą związane: siedem pudeł w S0
    i siedem trafień w S0B to dwa razy ten sam mechanizm, nie
    czternaście niezależnych prób.
- **Wykonawca:** odchylenia 1–9 raportu przyjęte.

## §3. Rozstrzygnięcia CC

1. **Świat — „PRZEPŁYW-JAK-NAD3" w bramce.** Zmienia się jedna rzecz:
   źródło poprawki. Kamera przepływu zostaje nad szachownicą, więc
   tabela G z 25 lotów obowiązuje. „TEREN-DLA-WSZYSTKICH" wymaga
   nowego pomiaru G i jest pozycją po bramce (§6, S4).
2. **Lot długi — poza bramką.** W bramce wylot poza mapę kończy się
   odmową osłony („ODMOWA-POZA-MAPĄ"). „TRASA-UCZĄCA" należy do lotu
   pokazowego po werdykcie (S4).
3. **Cechy — SIFT.** AKAZE ma na 12 cięciach przerwy do 4.0 s.
4. **Sito wiązań — „SITO-ODLEGŁOŚCI"**, bez zmian.
5. **Kadr — „TEREN-I-OBIEKTY".** Modele dronów bez zmian. Boot
   statyczny mierzy, ile pikseli kadru zajmuje własny kadłub i cień.
6. **Osłona — reżim „nad3" z nową tabelą.** Plik tabeli w formacie
   NAD3: F = 0 we wszystkich polach, E = 1.00 m, dziesięć krawędzi.
   `r03/nadir_shield.py` bez zmiany bajtu. Prover jako kopia provera
   NAD3 z nową tabelą; certy NAD2 i NAD3 zostają.
7. **E = 1.00 m, τ\* = 2.15 s.** Recon dał najwyżej 0.95 m na każdej
   łacie i w każdym locie; 1.00 m to także punkt P1 zmierzony w NAD3.
   τ\* jest największą krawędzią, przy której bariera zostaje nad
   zadaniem z zapasem na błąd źródła (21.13 − 1.00 ≥ 20 m). Przy
   wyborze między zapasem E a dłuższym τ\* pierwszeństwo ma E:
   przesłanka to litera bezpieczeństwa, τ\* to tylko dostępność.
8. **Dobór kandydatów — jeden wariant K′, rozstrzygany przy biurku.**
   Pokrycie liczone z własnych rozmiarów obu kadrów (klatka kluczowa
   z wysokości, na której powstała). K′ wchodzi do lotów tylko wtedy,
   gdy na kadrach reconu nie pogarsza niczego (§6, S1). To zmiana po
   wyniku, więc ma regułę zapisaną z góry i nie ma drugiego wariantu.
9. **Trzy tereny w bramce.** Parking, osiedle i łąka po cztery
   cięcia. Render nie rozróżnił terenów; obraz z gz może.

## §4. FREEZE

- **Zadanie:** r_zad = 20.0 m, manifest NAD3 v2, komórki c05 i c10,
  ziarno s01.
- **Źródło:** mapa M4, cechy SIFT, tor odniesienia
  `results/TEACH_RECON2/tools/teach2.py` z ad1e71fd (sha256
  07925633…). Wybór klatek kluczowych, wiązania, rozwiązanie
  (Gauss–Newton, 6 iteracji, wagi 1 / 5 / 0.05, skala 1) i reguła
  przyjęcia `a12_geo0_g1.5` jak w reconie.
- **Częstość:** każda klatka kamery w dół (5 Hz), bez decymacji.
- **Krawędzie τ:** 0.35 / 0.55 / 0.75 / 0.95 / 1.15 / 1.35 / 1.55 /
  1.75 / 1.95 / 2.15 s. Dodatek osłony 0.012 s bez zmian.
- **τ\* = 2.15 s**, próg zatrzasku 41 ticków (τ\* − 2 · dt = 2.05 s).
- **G (unia 25 lotów; 13 lotów NAD3 nie podnosi żadnego pola):**
  0.8573 / 1.2703 / 1.6614 / 2.0590 / 2.3471 / 2.5715 / 2.7572 /
  2.8929 / 3.1498 / 3.3315 m. Liczby CC; wykonawca odtwarza je
  narzędziem w S1, różnica > 0.01 m ⇒ STOP.
- **E = 1.00 m.** F = 0: cały błąd źródła siedzi w E.
- **Reguła:** U′ = 1.5 · (E + G); u′ = U′ + Δ_D5; bariera
  R = R_E − d_stop − u′. Stałe R_E 32.0, d_stop 2.85, Δ_D5 1.524 bez
  zmian.
- **Bariera po krawędziach:** 24.84 / 24.22 / 23.63 / 23.04 / 22.61 /
  22.27 / 21.99 / 21.79 / 21.40 / 21.13 m. Największe u′ 8.02 m wobec
  m(r_zad) 9.15 m.
- **Granice przy r_zad na krawędzi τ\*:** dostępność 1.05 m,
  bezpieczeństwo 1.75 m. Przy τ ≤ 0.35 s: 2.54 m i 4.23 m.
- Brak poprawki od wejścia w utratę ⇒ najgorsze pole, jak w NAD2.
- **Tereny:** łaty S, M, J z `results/TEACH_RECON/dane/`.
- **Świat:** warstwa terenu 100 × 100 m z flagami 8 na wysokości
  0.005 m; kamera w dół z maską 8; kamera misji 4294967285; kamera
  przepływu 4294967283; lidar 4294967287.

## §5. Architektura — różnice wobec NAD3

1. **Producent:** nowy moduł `harness/teach_map.py`. Do chwili flagi
   utraty GNSS zbiera klatki kluczowe i wiązania; w chwili flagi
   rozwiązuje georeferencję raz; potem lokalizuje każdy kadr
   i oddaje stan ramy w tym samym datagramie co dotąd. Gałąź
   w `harness/nadir_obs.py` za przełącznikiem; wyłączona ⇒ datagram,
   wiersz i meta bajtowo jak w NAD3.
2. **Przed cięciem** producent nie wysyła poprawek: Δ = 0, czysty
   EKF z GNSS.
3. **Znaczniki:** detektor znaczników liczy dalej każdą klatkę, ale
   tylko do rejestru. Jego wynik jest świadkiem tezy: zero detekcji
   w całym locie.
4. **Osłona i certy:** reżim „nad3", tabela
   `results/TEACH/s1/freeze_U_TEACH.json`, certy P9 / P5 / P7_teach
   z kopii provera NAD3.
5. **Świat:** trzy pliki świata (S, M, J) z kopii
   `world_nadir2_A3.sdf` i nowy model drona z maskami z §4.
   Przypięty model `x500_nadir2_flow` i stare światy zostają bez
   zmian.
6. **Nietknięte:** wagi sieci, EKF i parametry PX4, kanon percepcji
   misji, `r01/shield.py`, `r03/nadir_shield.py`,
   `harness/nadir_fix.py`, `harness/nad3_degrad.py`, tabele NAD2
   i NAD3, manifest NAD3 v2, reguła zejścia D5.

## §6. Etapy, litera, śmierci, budżet

**S1 — budowa, tabela, certy, wierność (0 bootów).**
- Kod wg §5, tabela i bariery wg §4, certy z ostrością (mutant
  tabeli odrzucony).
- **Wierność mapy:** moduł lotu, karmiony kadrami reconu w kolejności
  czasu, odtwarza M4 / SIFT na łatach S, M, J we wszystkich 13
  lotach: ta sama liczba przyjętych, ten sam największy błąd do
  0.001 m, georeferencja do 0.0001. Interpreter i cv2 te, których
  używa boot.
- **Czas:** od flagi do gotowej georeferencji ≤ 0.5 s w replayu na
  jednym rdzeniu; czas kadru po cięciu p95.
- **K′:** przyjęty, gdy na każdej z trzech łat, osobno na 12 cięciach
  i w locie długim, największy błąd nie rośnie o więcej niż 0.02 m,
  największa przerwa nie rośnie i liczba przerw ponad 1.15 s nie
  rośnie, a co najmniej jedna z dwóch ostatnich liczb gdzieś maleje.
  Inaczej zostaje dobór z reconu.
- **Replay osłony:** 13 lotów reconu z poprawkami mapy i tabelą
  TEACH: liczba ticków e′ > U′ (oczekiwane 0), największe e′/U′,
  odmowy i ich przyczyny. Wynik do porównania z lotami.
- **Śmierć S1:** cert nie przechodzi ∨ ostrość nie trzyma ∨ wierność
  mapy nie zachodzi ∨ plik z §5 pkt 6 zmieniony ∨ nowy FAIL testów.
- **STOP i aneks, nie śmierć:** przekroczenie przesłanki w replayu;
  G poza tolerancją; zamknięcie mapy dłuższe niż 0.5 s; wierność
  rozjechana wyłącznie przez inną wersję cv2 niż w reconie.

**S2 — świat, cień, smoke (≤ 7 bootów).**
- **2 booty statyczne** (stary model i świat; nowy model i świat S),
  trzeci tylko do rozdzielenia przyczyn. Kamera przepływu i kamera
  misji mają dać w zawisie te same klatki co w starym świecie, lidar
  tę samą odległość; kamera w dół: teren w kadrze, zero detekcji
  znaczników, udział pikseli własnego kadłuba i cienia.
- **2 booty cienia:** c05 na łacie S i c10 na łacie J. GNSS zostaje,
  producent dostaje chwilę cięcia z planu lotu, buduje mapę
  i lokalizuje, a poprawka idzie tylko do rejestru.
- **Bramka obrazu** w każdym boocie cienia: największy błąd przyjętej
  poprawki ≤ 1.00 m, przyjętych ≥ 90% kadrów, zero detekcji
  znaczników.
- **Jedna naprawa z zamkniętej listy:** stała maska pikseli własnego
  kadłuba i cienia; zgranie czasu obrazu z próbką EKF; konwersja
  formatu obrazu. Progi dopasowania nie należą do listy. Po naprawie
  jeden powtórzony boot. Drugi FAIL bramki obrazu ⇒ śmierć źródła na
  obrazie gz, noga zamknięta z wynikiem.
- **1 boot smoke:** cięcie c05 na łacie S w pętli domkniętej. Litera
  bezpieczeństwa obowiązuje.
- Danych S2 nie wolno użyć do zmiany tabeli ani toru. STOP po S2
  i aneks CC przed bramką.

**S3 — bramka (≤ 17 bootów: 12 cięć + 2 nominały + 3 rezerwy
stanowiska).** Łaty S, M, J × komórki c05, c10 × 2 powtórzenia;
1 cięcie na boot, kontynuacja 110.5 s, wyciąg ULG do repo. Nominały
z producentem w cieniu i GNSS obecnym: po bloku S na łacie S, po
bloku M na łacie J.

*Litera bezpieczeństwa — każde naruszenie w dowolnym epizodzie to FAIL
nogi:*
- (B1) e′ ≤ U′ w każdym ticku utraty, e′ = |p_corr − GT(t próbki
  EKF)|;
- (B2) r_GT < R_E przez cały lot;
- (B3) `r_est` osłony = |p_corr| w 100% ticków KONT;
- (B4) po REFUSE zejście wg reguły, `nav_state` 14, failsafe 0, zero
  breach;
- (B5) w nominałach zero REFUSE(POS) fałszywych.

*Ważność lotu — niespełnienie unieważnia lot, nie nogę:*
- zero detekcji znaczników w kamerze w dół przez cały lot;
- żadna klatka kluczowa ani wiązanie po fladze; georeferencja
  rozwiązana raz;
- cięcie po wejściu (ANEKS_NAD3-2);
- replay poprawek i osłony 100%.

*Dostępność — próg:* co najmniej 9 z 12 cięć bez REFUSE w misji,
track i pasmo wg D1 z NAD2. Wynik per łata opisowo. REFUSE(τ\*)
w misji jest znaleziskiem (wylot poza mapę albo przerwa źródła), nie
naruszeniem, i liczy się do dostępności.

*Obserwable (bez progu):* błąd poprawki p50 / p95 / max per lot
i łata; max e′/U′; τ zrealizowane; przerwy z pokryciem; opóźnienie
pierwszej poprawki po fladze; czas producenta na klatkę; liczba
klatek kluczowych i wiązań; skok Δ przy pierwszej poprawce;
odrzucenia bramki predykcji tracku.

*Zatrzymania:* naruszenie B1–B5 ⇒ werdykt V-C i STOP natychmiast;
replay poniżej 100% ⇒ STOP; po bloku S mniej niż 3 z 4 cięć
dostępnych ⇒ STOP przed blokiem M i aneks.

**Werdykt:**
- **V-A:** zero naruszeń B1–B5 i próg dostępności spełniony — lot bez
  GNSS i bez znaczników, z poprawką z mapy zbudowanej przez drona
  przed utratą, zmierzony w pętli na obszarze widzianym przed
  cięciem.
- **V-B:** zero naruszeń, próg niespełniony — bezpieczeństwo trzyma,
  dostępność na mapie z własnego lotu niepotwierdzona; wynik
  negatywny z mechanizmem.
- **V-C:** jakiekolwiek naruszenie B1–B5 — FAIL nogi.

**S4 — po V-A, aneksem, poza tym budżetem.** Lot długi z okrążeniem
uczącym; teren dla wszystkich kamer z nowym pomiarem G.

**Budżet:** ≤ 24 booty (S2 7 + S3 17). Po FAIL bramki trzeciego
podejścia w tej architekturze nie ma.

## §7. Zakres zdania końcowego

SITL. Teren to płaski obraz ortofotomapy; mapa i lot dzieli
kilkadziesiąt sekund, więc światło się nie zmienia. Dron lokalizuje
się tylko tam, gdzie patrzył przed utratą GNSS. Kamera przepływu
pracuje nad szachownicą jak w NAD3. Noga nie mówi nic o rzeźbie
terenu, o mapie starszej niż lot, o locie poza mapę ani o przepływie
optycznym nad prawdziwym terenem. Mówi, czy źródło bez znaczników
i bez wcześniejszej mapy spełnia kontrakt z NAD3, przy sieci, osłonie
i dowodzie bez zmian.

## §8. KSIĘGA (append-only przy commicie [CO-TEACH-2])

```
## TEACH — PRE (PRE_TEACH, 16.11.2026)
- Recon S0B rozliczony: P-TEACH-R8…R14 7/7 przy sumie szans 4.55
  (z S0 razem 8/14 przy 8.45). Mapa M4 z SIFT: 12 cięć max
  0.71–0.75 m, lot długi 0.85–0.95 m na łatach S, M, J; wszystkie
  przerwy ponad 1.15 s poza mapą. CC własnym kodem: georeferencja
  z zapisanych wiązań zgodna do 4. cyfry (732 rozwiązania na
  wariant), poprawki i błędy 154 910 wyników do 0.0001 m, żadnego
  wiązania po chwili cięcia.
- Znalezisko weryfikacji: dobór kandydatów nie zna wysokości klatki
  kluczowej; małe klatki ze startu wypierają klatkę przelotową
  (przerwa 1.4 s w p02 przy 56–96 zgodnych punktach dostępnych
  w klatce niewybranej).
- ✗ projektowe CC: dobór kandydatów ślepy na rozmiar klatki
  kluczowej w obu promptach; zbędne sito odległości; predykcje
  jednego reconu związane jednym mechanizmem (S0 1/7, S0B 7/7).
  Lekcja: w zestawie predykcji co najmniej dwie mają zależeć od
  czego innego niż pozostałe.
- Predykcje CC, przed pierwszą linią kodu S1:
  - P-TEACH-1 (0.85): S1 — moduł lotu odtwarza recon bez naprawy
    toru, a georeferencja jest gotowa ≤ 0.5 s po fladze.
  - P-TEACH-2 (0.55): K′ przyjęty wg reguły PRE §6.
  - P-TEACH-3 (0.80): boot statyczny — kamera przepływu i kamera
    misji piksel w piksel jak w starym świecie, zero detekcji
    znaczników w kamerze w dół.
  - P-TEACH-4 (0.60): oba booty cienia przechodzą bramkę obrazu za
    pierwszym razem.
  - P-TEACH-5 (0.85): zero przekroczeń przesłanki w smoke i 12
    cięciach, max e′/U′ ≤ 0.60.
  - P-TEACH-6 (0.70): co najmniej 11 z 12 cięć dostępnych.
  - P-TEACH-7 (0.65): największy błąd poprawki w lotach bramki
    ≤ 1.00 m na każdej łacie.
  - P-TEACH-8 (0.60): łąka nie gorsza od parkingu — max błąd
    poprawki na J ≤ max na S + 0.20 m.
  - P-TEACH-9 (0.75): zero REFUSE(τ*) w misji w 12 cięciach.
  - P-TEACH-10 (0.50): werdykt V-A.
```

## §9. KIERUNKI_PO_PLANIE (append-only przy commicie [CO-TEACH-2])

```
## Dopisek stanu katalogu — 16.11.2026 (CO-TEACH-2, PRE_TEACH)
- **TEACH, recon S0B — CLOSED, żyje.** Mapa spięta obrazem
  i zakotwiczona w torze EKF sprzed cięcia: błąd poprawki do 0.75 m
  na 12 cięciach i 0.95 m w locie długim, tak samo na parkingu,
  osiedlu i łące; 0 bootów.
- **TEACH — otwarta, PRE ratyfikowany.** Lot bez GNSS i bez
  znaczników z poprawką z mapy własnego lotu; sieć i osłona bez
  zmiany kodu, nowa tylko tabela (E 1.00 m, τ* 2.15 s) i źródło.
  Bramka: 12 cięć na trzech terenach. Budżet ≤ 24 booty.
- Po werdykcie, osobnymi decyzjami: lot długi z okrążeniem uczącym;
  teren dla wszystkich kamer z nowym pomiarem G.
```
