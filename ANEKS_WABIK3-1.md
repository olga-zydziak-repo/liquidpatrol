# ANEKS_WABIK3-1 — ścieżka „geometria zbliżenia" zamknięta przy biurku: kandydat R2 odtworzony co do liczby i obalony na koszcie, którego kryterium WABIK-II nie liczyło (CO-WABIK3R)

CC · 30.10.2026 · łańcuch WABIK3 (po STOP-WABIK3R, commit 12b88e38 na origin).
Aneks zamykający ŚCIEŻKĘ na etapie recon, samowykonalny (§6): zero bootów
wydanych, zero do wydania; PRE_WABIK3 nie powstaje. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-WABIK3R

Przyjęte po weryfikacji CC z repo WYKONANIEM. Zakres czysty: wyłącznie nowe
pliki `results/WABIK3_RECON/**` (RECON 495b2643, tool 5dbc94ec, r2 7cee6f96),
FREEZE_WABIK, wabik_sig 475c972e, wabik_sig2 a8397cb4, s1_tabela a54e7667,
manifesty 046fa12b / 86268b02 nietknięte.

**R2 odtworzone niezależnie** — bench wzięty literą zamrożenia (okna epizodów,
populacja 115 NULL i zegar z `wabik_sig2`, czyli przedmiot zamrożenia), reguła
napisana od zera z prozy reconu, nie z jego kodu: kandydat dron·H10·R7·T4,
odwołanie podłoga+atak ⇒ TP≤15 **5/6**, TP_final 5, FP 0/3, ORB 2/2, NULL
ever/final **51/10**; czasy flag 9.8 / 7.4 / 10.1 / 22.3 / 11.8 / 4.2 s co do
0.1 s; krawędź Pareto (3,0)·(4,2)·(5,10); wyspa R=5 (NULL 15) / R=9 (TP 3,
final 0); ORB 7.8→33.1 i 6.4→28.5 s; lista 10 NULL-final identyczna.
**R5 potwierdzone** na spornym epizodzie: c04_s04 w kampaniach r11 ma GT 6.08 m
w OKNIE LOTU (74–76 s; zejście GT do 2.5 m przypada na 88–93 s, których nie
latano) — klasa wędrowca stoi. **R1** litera potwierdzona (`det_v2.py` —
`boxes.conf.argmax()` przed bramką). **R3 / R4** przyjęte z JSON-ów reconu
(spójne wewnętrznie: 8 estymatorów TP≤15 0/6; statyczne MAD 0.14–0.49 m),
bez własnego przeliczenia — nie niosą werdyktu tego aneksu.

Cztery rzeczy, których proza reconu nie mówi, a JSON albo wykonanie mówi:

1. **Dolny brzeg wyspy to porażka bezpieczeństwa, nie tylko NULL.** Przy R=3
   i R=5 flagę dostaje **c08_s03 — cel atakujący** (`r2_dcpa_tabela.json`,
   `fp_ever: ["c08_s03"]`); proza pisze tylko „R=5 daje NULL_final 15".
2. **Maska DCPA na S2 testowana na JEDNEJ trajektorii atakującej.** Przy R=7
   c08_s03 ma najdłuższy streak W 2.7 s wobec progu 4 s (margines 1.3 s);
   c10_s02 i m00_s01 w ogóle nie wchodzą w W — blokuje je stara litera
   strefy/podłogi, nie geometria zbliżenia.
3. **Zegar i dziedzina reguły są na dwóch strumieniach.** Zegar (litera v1):
   pierwsza klatka z torem w percep_feed; dane reguły: demo.jsonl od t0 —
   a demo.jsonl w 46/126 epizodów (4/11 S2) niesie na starcie tor-ducha
   (pozycja zamrożona 6.9 m od home, |v| do 3.2 m/s, ~9 s, zanim percepcja
   cokolwiek zobaczy). Liczenie reguły wyłącznie od zegara daje te same liczby
   (sprawdzone), ale pierwsze przeliczenie CC z zegarem od pierwszej klatki
   demo dało TP≤15 **3/6** (w00a 18.6 s, w02a 20.8 s) — ta sama reguła, inny
   zegar, inny werdykt.
4. **„Bez ponownej flagi po odwołaniu" jest nośne:** z ponowną flagą
   NULL_final = **14 > 13**, kandydat pada. Prędkość z okna pozycji 1 s (jak
   v1) zamiast `trk_vel`: w02b 4.2 → 8.8 s, NULL_final 11 — przechodzi.

Żadne z czterech nie zmienia liczb reconu; każde wchodziłoby do PRE literą kodu.

## §2. Pomiar CC poza pytaniami reconu: koszt liczony na celach, które uderzają

Kryterium WABIK-II (odziedziczone przez R2) liczy koszt jako **NULL_final** —
etykietę, która zostaje. Etykieta, która pada na cel idący na home i jest
cofnięta dopiero, gdy ten cel jest 5 m od chronionego punktu, w tym kryterium
kosztuje zero. Na pytanie „ile czasu na decyzję zyskuje etykieta" to jest
dokładnie odwrotna strona bilansu, więc CC ją policzył.

**Definicje (wykonywalne, na zamrożonym benchu):** *uderzający* = epizod NULL,
którego trajektoria GT (`bench.scenarios.position_at`, krok 0.1 s) schodzi
< 5 m od home w oknie lotu [0, t1−t0); *niedochodzący* = pozostałe.
*Etykieta na uderzającym* = flaga „wabik" KIEDYKOLWIEK (z litery reguły flaga
pada tylko przy dh_min ≥ 5 m, więc każda taka flaga wisi, gdy cel jeszcze jest
> 5 m od home). *Wchodzący w chwili flagi* = średnia 1 s z v_trk·p̂ względem
home < −0.2 m/s.

**Bench:** 115 NULL = **65 uderzających** (v=1.0: 41, v=0.5: 24) +
**50 niedochodzących** (36 statycznych v=0, 14 wolnych v=0.5 — to jest klasa
wędrowców R5, tu nazwana jawnie).

**Kandydat reconu (dron·H10·R7·T4):** etykieta na **37/65 uderzających**
(v=0.5: 21, v=1.0: 16). W chwili flagi cel **wchodzi do home w 20** przypadkach
(v_rad < −0.2 m/s), styczny 2, oddala się 15; mediana odległości od home
w chwili flagi 9.9 m, mediana czasu flagi 7.6 s od pierwszego toru. Odwołanie:
podłogą 25 (mediana trwania etykiety 11.2 s — cofnięta, gdy cel już jest przy
5 m), klauzulą ataku 12 (mediana 5.0 s); trwanie etykiety ogółem mediana 8.7 s,
p90 42.7 s, max 62.6 s. Z 65 uderzających **50 leci praktycznie prosto**
(zejście < 5 m w ≤1.5× czasu lotu prostego 15→5 m) — etykietę dostaje **22
z tych 50**. Komórka c08_s01 (v=1.0, start z azymutu 0°, lot radialny) dostaje
etykietę **w 3/3 kampaniach** (DET r3, AKW r3, FANTOM r3) w 7.5–8.7 s, przy
prędkości radialnej −0.9…−1.0 m/s — cel idzie prosto na home i jest podpisany
„wabik" przez 1.4–1.6 s, do podłogi. S2 c08_s03 uciekło tej samej regule
o 1.3 s streaku (§1 p. 2); „FP 0/3" w S2 jest statystyką próby trzech lotów,
a bench, na którym kandydata wybrano, zawierał 37 kontrprzykładów —
niewidocznych w NULL_final.

**Baza — litera FREEZE_WABIK (v1, T_FLAG 12) na tych samych 65:** etykieta na
**11/65** (final 1 = c08_s04, utrata toru przed zejściem — klasa percepcji
z R5); w chwili flagi **wchodzących 0**, oddalających 11 (v_rad +0.25…+0.83),
mediana odległości od home 14.6 m, najwcześniejsza flaga 12.5 s, trwanie mediana
25.3 s / max 49.1 s — etykieta pada na cel, który się oddala, i jest cofana, gdy
zawraca. Niedochodzący: ever/final 12/12.

**Mechanizm (zmierzony pośrednio, spójny z kwalifikatorem 4 reconu):** „atak"
liczony względem DRONA jest prawdziwy wtedy, gdy ZBLIŻA SIĘ DRON — w fazie
wejścia na orbitę. Po wejściu dron krąży wokół celu: prędkość względna jest
styczna, TCPA ≈ 0, maska gaśnie niezależnie od tego, czy cel idzie na home. Stąd
flagi na wchodzących: cel z v_rad −1 m/s pod dronem na orbicie jest dla maski
nieodróżnialny od wabika. Warianty ref=home mierzą zamiar, ale płacą na
uderzających, którzy błądzą przed uderzeniem (home·R5·T4: 24/65) — dokładnie
klasa trajektorii benchu (polilinie 7–9 odcinków) i dokładnie klasa Gerbery.

**Uczciwa krawędź Pareto** (siatka streak podłoga+atak, ref∈{home,dron} ×
H∈{10,∞} × R∈{3,5,7,9,11} × T∈{4,…,12}, 100 konfiguracji, warunek FP(S2) 0 ∧
ORB 2/2; oś kosztu = uderzający z etykietą): TP≤15 **0 → 0/65**, 1 → 12, 2 → 19,
**3 → 16**, 4 → 24, **5 → 26**. Żadna konfiguracja z TP≤15 ≥ 3 nie schodzi
poniżej 16/65 — czyli poniżej poziomu bazy (11) nie ma nic, co flagowałoby
wabiki w czasie. Czas zyskany na wabiku kupuje się etykietą na co czwartym do
co drugim celu, który uderza.

## §3. WERDYKT: ścieżka (a) DCPA/TCPA-first ZAMKNIĘTA PRZY BIURKU (0 bootów); (b) tor-first zamknięta R3; (c) bezprzedmiotowa; IMITACJE zamknięte R4

Lot S2 na świeżych wariantach mierzyłby wariancję próby wokół liczby, którą
zamrożony bench już podaje: **37/65**. Nie ma czego walidować. Pozycja
„WABIK — tor i geometria zbliżenia" zamyka się kosztem 0 bootów (szóste
rozstrzygnięcie kierunku deskiem w programie — po AKW-TRANSIT jako czwartym
i WABIK-II jako piątym; drugie w wątku wabików).

**Zdanie kanoniczne (do cytowań):** „Geometria zbliżenia (DCPA/TCPA względem
drona albo home) skraca etykietę wabika do ≤15 s w 5/6 przypadków, ale na
zamrożonym benchu 126 lotów podpisuje jako wabik 37 z 65 celów, które
uderzają — 20 z nich w chwili, gdy idą prosto na chroniony punkt — i cofa
etykietę medianowo 11 s później, przy 5 m. Żadna z 100 konfiguracji
reguły streak z maską zbliżenia nie daje ≥3/6 wabików w czasie przy mniej niż
16/65 etykiet na uderzających. Reguła zamrożona v1 (T_FLAG 12) nigdy nie
podpisuje celu wchodzącego (0/11; jej 11 etykiet na uderzających pada w fazie
oddalania, mediana 14.6 m od home, i jest cofane przy zawróceniu). Przy
jednym obiekcie w polu widzenia tor sam w sobie nie odróżnia wabika od celu,
który uderzy za chwilę — szybciej niż ten cel sam to pokaże."

**Co stoi po tym aneksie (bez poluzowania):** własność v1 „zero etykiet na celu
wchodzącym" jest zmierzona na 65 uderzających, nie na 3 — mocniejsza niż
dotychczas cytowane „0/3"; jej cena to etykieta w fazie oddalania na 11/65
i nierozróżnialność wędrowców (14/50 niedochodzących v=0.5). Zdanie raportu
programu „zero fałszywych alarmów na celach atakujących" stoi w czytaniu
mocnym (cel idący na home) i dostaje w raporcie kwalifikator o fazie oddalania
(errata forward w RAPORT_PROGRAMU, plik CC poza repo; plansza v6 bez zmian —
jej linia mówi o celach atakujących i jest prawdziwa).

**Czego ten aneks nie twierdzi:** że wabików nie da się rozpoznać. Twierdzi,
że przy JEDNYM obiekcie i tylko torze — nie szybciej niż cel sam się ujawni.
Pozostaje mechanizm, w którym etykieta nie musi wyprzedzać uderzenia, bo jej
sens jest inny: przy ≥2 obiektach naraz „ten, który krąży i nie schodzi"
dostaje niższy priorytet niż „ten, który schodzi" — i to jest MULTI-TARGET,
nie reguła czasowa. Warunek wstępny jest zmierzony w R1: feed trzyma top-1
detektora, surowych detekcji nie loguje nic, kampanie NULL nie mają klatek —
offline tego nie ma; wycena reconu (ii): zrzut klatek + nowy replay det_v2
wszystkich ramek, zero dotyku FROZEN.

## §4. Katalog (dopisek do KIERUNKI_PO_PLANIE.md — treść do skopiowania, append-only)

```
## Dopisek stanu katalogu — 30.10.2026 (CO-WABIK3R, ANEKS_WABIK3-1 §4)

- **WABIK-III „tor i geometria zbliżenia"** → **CLOSED-BY-RECON+DESK (0 bootów,
  1 sesja deskowa + CO)**. Recon `results/WABIK3_RECON/RECON_WABIK3.md`
  (12b88e38): R1 feed = top-1 przed bramką, multi-target offline NIE; R2 kandydat
  DCPA/TCPA (dron·H10·R7·T4) TP≤15 5/6 · FP 0/3 · ORB 2/2 · NULL_final 10/115
  — odtworzony przez CC co do 0.1 s; R3 tor NIE (0/6 przy 8 estymatorach);
  R4 IMITACJE zamknąć (MAD 0.21 m ≈ 6.7 px, AUC 0.59); R5 13 NULL-final =
  12 wędrowców v=0.5 + 1 percepcja. **Pomiar CC (ANEKS_WABIK3-1 §2,
  odtworzony narzędziem `results/WABIK3_RECON/tools/wabik3_uderzajacy.py`):**
  115 NULL = 65 uderzających (GT < 5 m w oknie lotu) + 50 niedochodzących;
  kandydat podpisuje jako wabik **37/65 uderzających** (20 w chwili, gdy idą
  na home; cofnięcie medianowo 11.2 s później, przy podłodze; c08_s01 w 3/3
  kampaniach), baza v1 **11/65** (0 wchodzących, wszystkie w fazie oddalania);
  uczciwa krawędź Pareto (TP≤15 → min uderzających z etykietą, 100
  konfiguracji): 0→0, 3→16, 5→26 — poniżej poziomu bazy nie ma nic, co
  flagowałoby w czasie.
  **Zdanie kanoniczne:** „Geometria zbliżenia skraca etykietę wabika do ≤15 s
  w 5/6 przypadków, ale na zamrożonym benchu podpisuje jako wabik 37 z 65 celów,
  które uderzają — 20 z nich, gdy idą prosto na chroniony punkt. Reguła v1
  nigdy nie podpisuje celu wchodzącego (0/11). Przy jednym obiekcie tor sam
  w sobie nie odróżnia wabika od celu, który uderzy za chwilę — szybciej niż
  ten cel sam to pokaże."
  **Lekcja kryterium:** NULL_final (WABIK-II) nie widział etykiet na celach,
  które uderzają; każde przyszłe kryterium wabikowe liczy koszt na klasie
  UDERZAJĄCY (GT < 5 m w oknie lotu) jako „etykieta kiedykolwiek", osobno od
  wędrowców (klasa nazwana: niedochodzący v=0.5, dziś 14/50).
- **IMITACJE / MIKRO-SYGNATURA** → **CLOSED-BY-RECON** (R4: szum pozycji celu
  statycznego MAD 0.21 m ≈ 6.7 px @ 8.5 m, residuum 1 s 3–5 cm, AUC 0.59 —
  mikro-ruch poniżej rozdzielczości toru tej kamery).
- **TOR-CECHY** → **CLOSED-BY-RECON** (R3: żaden z 8 estymatorów v_rad przy
  niezmienionej regule nie przesuwa TP do ≤15 s; jump_0.5 czyści NULL kosztem
  2 TP). Pozycja scalona TOR-CECHY ∪ MULTI-TARGET rozpada się: zostaje
  **MULTI-TARGET / TOŻSAMOŚĆ TRACKA** jako jedyna otwarta droga wabikowa,
  z nową treścią: etykieta jako PRIORYTET między ≥2 obiektami, nie wyprzedzenie
  uderzenia. Warunek wstępny (R1 ii): zrzut klatek kamery + nowy replay det_v2
  wszystkich ramek (zero dotyku FROZEN), dopiero potem bench wieloobiektowy.
  **Trigger: decyzja Olgi po rozmowie z pilotem** (pytanie trzecie: czy obrona
  odróżnia wabik, czy zakłada uzbrojenie każdego celu — jeśli to drugie,
  priorytet między obiektami jest jedynym sensem etykiety).
- **DEMO-C v6 — errata forward do V-A3 (ANEKS_WK3-1 §2):** w reżimie demo
  (zrzut klatek, WindEffects) take1 c04@P2 był VALID (V2′ 0.950, k 0.490,
  breach 0) i padł na sędzim D6 przez sweep 570° < 630° — orbita zwalniała
  i zawracała (38 % ticków z ujemną prędkością styczną, 8 zmian znaku; take2:
  16 %, 2) — pierwsza porażka pod wiatrem, która nie jest akwizycją. Wynik
  reżimu demo pod P2: 1/2 (`results/DEMO_C/RAPORT_DEMO_C.md`, Akt 6). Kanon
  V-A3 (kampania WK-III 7/8) bez zmian; zdanie „jedyna porażka to akwizycja"
  dotyczy kampanii, nie reżimu demo. Plansza „~140 bootach" → „>150" przy
  następnym montażu.
- Stan: wątek wabikowy po trzech nogach i dwóch zamknięciach deskowych:
  5 bootów łącznie (WABIK S1+S2), breach 0 / REFUSE 0; katalog 8 → 7 otwartych
  pozycji (IMITACJE zamknięte; pozycja scalona TOR-CECHY ∪ MULTI-TARGET trwa
  jako MULTI-TARGET z nową treścią, człon TOR-CECHY skreślony).
```

## §5. KSIĘGA (sekcja do dopisania w `results/KSIEGA_PREDYKCJI.md`, append-only)

```
## ŚCIEŻKA WABIK-III (tor i geometria zbliżenia) — ZAMKNIĘTA DESKIEM przy CO-WABIK3R (ANEKS_WABIK3-1, 30.10.2026)
Bez PRE i bez predykcji numerowanych (recon 0 bootów → zamknięcie deskowe). Jedna
ocena CC do rozliczenia: po odtworzeniu R2 CC wycenił przeżycie kandydata na
świeżych wariantach na „pół na pół" — zanim policzył koszt na uderzających.
Bench już zawierał 37 kontrprzykładów. **✗ jako kalibracja**: ocena wydana przed
policzeniem kosztu na właściwej klasie.

Lekcje kalibracyjne: (1) **kryterium odziedziczone z poprzedniej nogi sprawdzać
przeciw pytaniu bieżącej nogi, zanim się na nim selekcjonuje** — NULL_final był
dobrą miarą dla WABIK-II („czy etykieta zostaje"), a złą dla WABIK-III („czy
etykieta wyprzedza uderzenie bez szkody"); koszt liczyć na klasie, której etykieta
szkodzi (uderzający), jako „kiedykolwiek", nie „na końcu"; (2) „FP 0/N" z próby
N=3 nie jest własnością reguły, gdy bench ma 65 egzemplarzy tej klasy — zawsze
liczyć na pełnej populacji, nie na epizodach z etykietą FP; (3) maska względem
poruszającego się obserwatora mierzy ruch obserwatora (tu: fazę wejścia drona na
orbitę) — zanim ref=dron wejdzie do kryterium, trzeba pokazać, że gaśnie przy
celu wchodzącym pod dronem na orbicie (tu: nie gaśnie, 20/37).
```

## §6. Zlecenie CO-WABIK3R — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git fetch` → origin/master == **12b88e38**; `origin/master..HEAD`
puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista zamknięta):

1. Korzeń **`ANEKS_WABIK3-1.md`** (ARCH-1, verbatim, pierwszy w commicie;
   byte-check sha256 podany przez CC w wiadomości z aneksem).
2. **NOWE narzędzie `results/WABIK3_RECON/tools/wabik3_uderzajacy.py`** + wynik
   **`results/WABIK3_RECON/r2_uderzajacy.json`** — reprodukcja §2 W REPO,
   niezależna od kodu CC (CC pisze liczby, egzekutor pisze narzędzie z definicji
   §2): klasa uderzający/niedochodzący z `bench.scenarios.position_at` na oknie
   [0, t1−t0) krokiem 0.1 s; etykieta kandydata z silnika `wabik3_recon.py`
   (import READ-ONLY, konfiguracja dron·H10·R7·T4·floor+atak); etykieta bazy
   z `wabik_sig2.evaluate` (baza(i)); wchodzący/oddalający z 1-s średniej
   v_trk·p̂ (demo.jsonl, `trk_vel_ned`); trwanie etykiety i przyczyna odwołania
   (podłoga / atak / brak); „prosto" = GT < 5 m w ≤1.5× czasu lotu prostego;
   uczciwa krawędź Pareto po siatce §2 (100 konfiguracji). **Liczby muszą
   zgadzać się z §2 DOKŁADNIE:** 65/50 (41+24 / 36+14), kandydat 37/65
   (21+16), odwołania 25/12, baza 11/65 (final 1), niedoch. 14/10 (kandydat)
   i 12/12 (baza), prosto 50 → 22, krawędź 0→0 · 1→12 · 2→19 · 3→16 · 4→24 ·
   5→26; tolerancja wyłącznie na estymatorze kierunku (wchodzący 20 ± 2,
   oddalający 15 ± 2) i na medianach trwania (± 0.5 s). **Rozbieżność ⇒ STOP
   z tabelą obu kolumn, zero edycji aneksu** (CC wystawia erratum forward).
3. **EDYCJA `KIERUNKI_PO_PLANIE.md`** — dopisek §4 verbatim, append-only.
4. **EDYCJA `results/KSIEGA_PREDYKCJI.md`** — sekcja §5 verbatim, append-only.

ŻADNYCH edycji RECON_WABIK3, FREEZE, raportów, PRE ani kodu zamrożonego;
`wabik3_recon.py` i `wabik_sig2.py` wyłącznie importem. Raport płaski:
tabela §2-vs-narzędzie (kolumna CC / kolumna repo), diff-stat, pełna treść
dopisków, porcelain. **Push = Olga („wypchnięte" — CC czyta narzędzie i JSON
z repo i porównuje z własnym przeliczeniem).** STOP.

## §7. Status

Ścieżka WABIK-III: **CLOSED — 0/≤4 bootów.** Wątek wabikowy po trzech nogach:
jedna rzecz zmierzona mocniej niż przed aneksem (v1 nigdy nie podpisuje celu
wchodzącego — 0/11 na 65 uderzających, nie 0/3), jedna rzecz zamknięta
liczbą (przy jednym obiekcie tor nie wyprzedza uderzenia), jedna droga otwarta
z nową treścią (MULTI-TARGET jako priorytet między obiektami; warunek wstępny:
klatki + replay detektora). Breach 0 / REFUSE 0 programowo bez zmian — w tej
ścieżce nic nie latało. Program w trybie katalogu: 7 otwartych pozycji;
następny ruch po rozmowie z pilotem.
