# ANEKS_NAD2-2 — zamknięcie nogi: bramka S3 PASS — litera bezpieczeństwa B1–B5 bez naruszeń w 28 epizodach, dostępność 12/12 przy progu 10; lot bez GNSS pod dowodem, którego przesłanka trzyma na świeżych lotach; NADIR-II CLOSED

CC · 12.11.2026 · łańcuch NAD2, po STOP-NAD2-3 (0d19996f na origin).
Zamyka nogę. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

1. **Kod lotu nietknięty.** Diff bd975df5…0d19996f jest pusty dla
   `harness/`, `r01/`, `r03/`, drivera, kroku, launchera, bootu,
   analizatora i tabeli; doszły tylko narzędzia kolejki S3. Meta 12
   cięć niesie jedną czwórkę sum (tabela 6a118fd4, driver 35f2dd70,
   krok c6844f98, fix 3baa340e).
2. **Księga kampanii:** 16 pozycji, po jednym ważnym boocie. Dwa
   starty nie doszły do bootu: c01_s03 (env-block launchera —
   w katalogu sam stub) i c05_s01 (zawieszenie w bramce procesów —
   katalogu lotu nie ma). W obu stos nie ruszył; żaden lot nie został
   odrzucony ani powtórzony.
3. **Wierność:** własny replay litery NAD2 (partner pary w kolejności
   produkcji) — 27 897 klatek z 16 bootów, decyzja zgodna w 100%;
   17 048 przyjętych poprawek, tryb i koszyk zgodne w 100%,
   |Δp_fix| ≤ 5e-5 m. Bariera z logu = `r_nad2` w 100% ticków.
4. **(B1):** 28 513 ticków KONT z tabelą, **0 przekroczeń**; max
   e_corr/U 0.374 (c10_s02), max e_corr 0.50 m (c05_s01).
5. **(B2):** margines do R_E min 6.43 m w cięciach (c08_s01), min
   8.54 m w nominałach.
6. **(B3):** `r_est` osłony = |p_corr| w 29 584 z 29 584 ticków
   KONT; w NOMINAL rama EKF w 9306 z 9306.
7. **(B4):** z wyciągów ULG — `nav_state` 14 i failsafe 0 od flagi
   do przyziemienia w 12/12; zdarzeń breach i REFUSE(POS) 0. 1071
   ticków KONT_REFUSE: wszystkie po komendzie zejścia, z τ ≥ 0.95 s
   i przyczyną τ*.
8. **(B5):** 16 epizodów nominalnych, 26 470 ticków misji — zero
   REFUSE, zero ticków poza NOMINAL.
9. **(D1):** kontynuacja 110.500–110.552 s od `t_inj_sim`, track
   1.000, pasmo ≥ 0.946, zero REFUSE w misji — **12 z 12**.
10. **Zgodność z raportem pełna.** Jedno doprecyzowanie: wartość
    0.965 dla błędu zakotwiczenia w c02_s01 pochodzi z poprawki
    jednym znacznikiem 31 s przed cięciem (GNSS zdrowy, tabela
    nieużywana); w fazie KONT maksimum to 0.67 zapasu (c10_s01).

## §2. Werdykt

1. Litera bezpieczeństwa B1–B5: **0 naruszeń w 28 epizodach.**
2. Litera dostępności D1: **12 z 12** przy progu 10.
3. **Bramka S3: PASS. NADIR-II — CLOSED, PASS.** Budżet nogi 18/22
   (smoke 2, bramka 16). Breach 0, REFUSE(POS) fałszywy 0.

## §3. Zdanie, które stoi

Po utracie GNSS, nad polem znaczników naziemnych (37 znaczników 1 m
co 10 m w promieniu 32 m), sieć NCP-20 prowadzi zadanie na pozycji
poprawianej kamerą w dół, a zawieranie w R_E jest dowiedzione
(P9_nad2 z P1/P5/P7_nad2, replikowane przez CC) przy przesłance
|p_corr − GT| ≤ U i r_est = |p_corr|. Przesłanka została sprawdzona
na 12 świeżych lotach po 110 s bez GNSS: 28 513 ticków, zero
przekroczeń, największe zużycie granicy 37%. Dowód nie ma limitu
czasu — bariera odnawia się z każdą poprawką; zmierzone jest 110 s
na lot.

**Granice zdania:** SITL, jedna sceneria, pełna widoczność
znaczników. Przesłanka jest sprawdzona na skończonej próbie, nie
dowiedziona. Bez pola znaczników zostaje 22 s z twierdzeniem (2d).
Przy ziemi znaczniki wychodzą z kadru i osłona odmawia z reguły τ*,
więc metoda działa na wysokości misji, nie w zejściu.

## §4. Gdzie było ciasno (obserwable, bez progu)

- **Zapas bariery:** min 0.479 m w c08_s01 (r_est do 25.85 m; ta
  komórka w replayu S4 miała 3.05 m) i 0.826 m w c11_s01. Dostępność
  12/12 zależała od realizacji trajektorii; próg 10 z 12 był
  uzasadniony.
- **Klatki bez poprawki:** po jednej w c05_s01 i c10_s02 — po trzy
  ticki w drugim przedziale, τ max 0.380 s, bez odmowy.
- **Dodatek τ + 0.012 s:** horyzont prawdziwy przekroczył go o 4 ms
  w c01_s01. Dodatek wzięty z maksimum próby S4 nie jest obwiednią;
  (B1) w tym epizodzie 0.231.
- **Składniki przesłanki w KONT:** przyrost EKF do 0.47, błąd
  zakotwiczenia do 0.67 dopuszczalnego — zrywy w świeżych lotach nie
  były większe niż w S4.
- **u′ > m:** 55 ticków w 4 epizodach (rachunek planistyczny).

## §5. Proces

Dwa starty bez bootu wynikły z wad kolejki, nazwanych przez
wykonawcę. Pierwszą poprawkę poprzedził STOP-NAD2-3-GUARD i decyzja
Olgi. Druga (bramka zdrowia w procesie potomnym, e6670f52) weszła po
ręcznym zatrzymaniu kolejki, bez STOP-u i bez sygnału. Zmiana
dotyczyła wyłącznie kolejki, kod lotu jest nietknięty (§1.1), więc
werdyktu nie dotyka. Na przyszłość: każda zmiana narzędzia w trakcie
kampanii przechodzi przez STOP.

## §6. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-II — bramka i zamknięcie nogi (ANEKS_NAD2-2, 12.11.2026)
- Smoke S2 (2 booty): passthrough bitowy 6405/6405; cięcie c11_s02 —
  sprawdziany 100%, B1 max 0.359, 0 REFUSE w misji.
- Bramka S3 PASS (16 bootów, wszystkie ważne): B1–B5 0 naruszeń w 28
  epizodach; D1 12/12 przy progu 10. B1: 28 513 ticków, max
  e_corr/U 0.374, max e_corr 0.50 m; margines do R_E min 6.43 m;
  r_est = |p_corr| w 29 584/29 584 ticków KONT; nominały 16/16.
  CC przeliczył całość własnym kodem z repo, w tym B4 z wyciągów
  ULG; zgodność z raportem pełna.
- P-NAD2-1 (0.75) — ✗ (śmierć S1 po literze: F_jeden nie odtworzyło
  się; naprawa ANEKS_NAD2-1). P-NAD2-2 (0.80) ✓, P-NAD2-3 (0.85) ✓,
  P-NAD2-4 (0.45) ✓, P-NAD2-5 (0.60) ✓, P-NAD2-6 (0.90) ✓ (18
  bootów). Noga: 5/6 przy sumie szans 4.35.
- Gdzie było ciasno: zapas bariery min 0.479 m (c08_s01) i 0.826 m
  (c11_s01) — dostępność 12/12 zależała od realizacji trajektorii;
  dwie klatki misji bez poprawki (τ max 0.380 s); horyzont prawdziwy
  ponad τ + 0.012 s o 4 ms w jednym cięciu (dodatek z maksimum próby
  nie jest obwiednią); składniki przesłanki w KONT do 0.47
  (przyrost) i 0.67 (zakotwiczenie) zapasu.
- Lekcje nogi: przesłanka mierzona na wielkości, którą dowód
  konsumuje, z próby rzędu ekspozycji bramki i z zapasem na sumie,
  przeszła świeże loty przy zużyciu 37%; obligacja wejścia w cercie
  łapie klasę błędu, która w S4 przeszła niezauważona; chwila
  porównania z GT ma jeden kanon dla wszystkich autorów liczb;
  litera musi rozstrzygać remisy (partner pary przy równej bazie —
  kanonem kolejność produkcji).
- Proces: dwa starty bez bootu z wad kolejki; druga poprawka kolejki
  (e6670f52) weszła po ręcznym zatrzymaniu, bez STOP-u i sygnału —
  kod lotu nietknięty, werdykt bez wpływu; odtąd każda zmiana
  narzędzia w trakcie kampanii przechodzi przez STOP.
- Wykonawca: recon z kalibracją własnego replayu, znalezisko r_est,
  STOP na konwencji czasu zamiast obejścia, obligacja wejścia jako
  wydzielony moduł lotu, kampania 16/16.
```

## §7. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 12.11.2026 (CO-NAD2-2, ANEKS_NAD2-2)
- **NADIR-II — CLOSED, bramka PASS.** Lot po utracie GNSS nad polem
  znaczników naziemnych pod dowodem zawierania, którego przesłanka
  trzyma na świeżych lotach: 12/12 cięć × 110 s, 28 513 ticków,
  0 przekroczeń przesłanki (zużycie do 37%), 0 odmów w misji,
  margines do R_E min 6.43 m, 16/16 epizodów nominalnych czystych;
  certy P9/P1/P5/P7_nad2 replikowane przez CC. Budżet 18/22.
- Zakres: SITL, jedna sceneria, pełna widoczność znaczników;
  przesłanka sprawdzona na 12 lotach, nie dowiedziona; bez znaczników
  zostaje 22 s z twierdzeniem (2d); dowód nie ma limitu czasu,
  zmierzone jest 110 s na lot.
- Niezamknięte, nazwane: lot długi 600 s (PRE_NAD2 §5 S4, ≤ 2 booty,
  na sygnał Olgi); inna sceneria i gorsza widoczność znaczników —
  niezmierzone; zrywy EKF przy obrocie kadłuba — mechanizm częściowo
  zmierzony, estymator nietknięty.
- Wątek lotu bez GNSS: 2d (22 s z twierdzeniem), KOTW (granica
  geometrii, 0 bootów), NADIR (110 s zmierzone, dowód nieważny),
  NADIR-II (110 s pod ważnym dowodem). Breach 0 / REFUSE(POS)
  fałszywych 0 programowo bez zmian (~240 bootów programu).
```

## §CO

Bramka: origin/master == **0d19996f**. Jeden commit [CO-NAD2-2]:
korzeń `ANEKS_NAD2-2.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §6 i `KIERUNKI_PO_PLANIE.md` §7 append-only. Zero bootów,
zero zmian kodu i raportów. Pliki `boot.ulg` zostają na dysku. Lot
długi (PRE_NAD2 §5 S4) pozostaje dostępny na osobny sygnał Olgi —
CC wyda wtedy prompt. Push = Olga.
