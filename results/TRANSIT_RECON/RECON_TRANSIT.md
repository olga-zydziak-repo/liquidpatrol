# RECON_TRANSIT — recon pozycji AKW-TRANSIT (cel przechodzi pod ślepym skanem) — STOP-TRANSITR

CC · 22.10.2026 · wykonanie PROMPT_TRANSIT_S0. **Zero bootów, zero SITL, zero treningu,
zero edycji istniejących plików**; narzędzia NOWE w `results/TRANSIT_RECON/tools/`
(transit_r1 / transit_r2 / transit_r3), dane WYŁĄCZNIE z istniejących artefaktów
(FANTOM S2, manifest ławki, indeks POSCIG_RECON); FROZEN importowane READ-ONLY
(poscig_recon — metoda R1-POSCIG i sędzia 8ec0fcfb; det_labels 8f7430cd — etykieta
on-target). Czeka decyzja CC: **aneks zamykający sufitem profilu misji ALBO
PRE_TRANSIT numerowany**.

**WYNIK GŁÓWNY (uprzedzając szczegóły):**

1. **Anatomia 6 utrat jest jednorodna: klasa (ii) 6/6 — cel BYŁ w stożku ENTRY przed
   bliskim przejściem, detektor go widział (box centralny, on-target), a padała
   ADMISJA** (koniunkcja central∧MTI nigdy nie osiągnęła k=3 kolejnych klatek —
   max run 0–2 vs 3–405 przy realnych wejściach kontroli). Klasy (i) „nigdy w FOV"
   i (iii) „admisja była, za późno z innego powodu": **0/6**. Percepcja FROZEN ⇒
   ratunek mógłby być tylko geometryczny — i tu rachunek mówi „nie ma gwarancji":
2. **Próg konwersji t\* = 10.75–11.41 s JEDNOLICIE dla całego T6** (wiążące zawsze
   d_min: pościgowiec musi opuścić home, zanim ślepy tranzyt zejdzie <4 m), ale
   terminem jeszcze twardszym jest PODŁOGA ADMISJI: cel radialny v=1.0 opuszcza
   empiryczny pas admisji dh≥5 m o **t=10.0 s**, a **gwarantowane (niezależne od
   azymutu nadejścia) pokrycie stare perymetru w nietykalnych (dwell 2.0 + slew
   60°/s + stare 1.2 s, stożek 86.9°) kończy okno najgorszego azymutu najwcześniej
   o 11.15 s** (forma zamknięta: 2 + 273.1°/60 + 4×1.2 − 0.2; krok optymalny 68.3°)
   — pełny przegląd perymetru NIE MIEŚCI SIĘ przed zamknięciem pasa admisji
   (deficyt ≥1.15 s); wobec t\* deficyt w 3/6 epizodów i margines ≤0.26 s
   w pozostałych 3. Warianty, które „domykają 6/6"
   geometrycznie (krok 90°/86.9°), robią to wyłącznie dzięki wyrównaniu nagłówków
   z korytarzami SIATKI ławki (bearingi {0,90,180,270}°) — stres bazą +45° daje
   **0/6 i regresję 5/6 kontroli**; a wszystkie ich okna są klasy RADIAL, w której
   admisja przy kadencji 5 Hz jest empirycznie loterią (**4/7** w danych kampanii,
   z twardymi kontrprzykładami c08_s03/s04 w IDENTYCZNEJ geometrii co PASS c08_s02).
3. Mikro-orbita NIE gwarantuje separacji (ścieżka celu przecina każdy okrąg wokół
   home: frakcja faz z d_min≥4 m = **0.00–0.50**, mediany 0.68–4.54 m) i niesie
   nienazwane dotąd ryzyko MTI (derotacja WYŁĄCZNIE rotacyjna — r02/mti.py:3);
   zmiana wysokości zawisu = POZA LIGĄ (kontrakt misji/przyrządu, §R3d).
   **Rekomendacja: wariant (i) — aneks zamykający pozycję jako ZMIERZONY SUFIT
   PROFILU MISJI** (zawis na home + separacja ≥4 m + detekcja celu przecinającego
   w nietykalnych percepcji i reżimu skanu); uczciwa alternatywa pomiarowa w §R5(iii).

## §0. Bramka wejścia — PASS

`git fetch` → origin/master zawiera **2d5f3f24 (CO-POSCIG)** ✓ · `origin/master..HEAD`
puste ✓ · porcelain pełny pusty ✓. FROZEN wykonaniem: **piny 5/5** (k1_shield_pins:
SHIELD FROZEN True; shield 1c584964 · config 4c440e42 · gate_run 5647ae20 · base
7fc45cf2 · safe_descend e3c1040b) · **certy 9/9** (certs_selfcheck PASS). Sha
przeliczone i ZGODNE: fantom_scan **e435ed7e** · rejestr kontrolerów
`r03/controllers/__init__.py` **87203d29** · akw_scan **b94cdeae** · bench_flight
`05137098` · bench_judge `8ec0fcfb` · ncp `0337d5ea` · FREEZE_DET w całości
(det_v2.pt 775ead15 · det_v2.py e801f7d5 · percep_proc 38a3a765 · feed_vision_proc
79633489 · feed_registry ee1481f9 · feed_vision acc81df7 · net_controller e8c1b658).
**Reguła erratum zastosowana:** GT intruza do rachunków = manifest analitycznie
(wolny od tranzientu; walidacja per epizod p50 0.060–0.068 m), a kolumna świadka
|ned−cmd|_xy>1 m zliczona OBOK na surowym gt_intruder (tabela R1; 0–6 próbek na
epizod, wyłącznie brzeg startu — werdykty T6 po erratum REALNE, zgodnie
z ERRATUM_DMIN).
**Kolizja nazwy „TRANSIT":** w kodzie WYŁĄCZNIE jako etykieta segmentu świata DEMO
(`acts/habitat_gate.py:135-147` — plansza „transit" H4; `tools/gen_subtitles.py:47`)
+ stringi w results/demo; **zero** env `TRANSIT_*`, zero katalogów `results/TRANSIT*`,
zero kontrolerów. Rekomendacja bez zmian: env **`TRANSIT_*`**, katalog
**`results/TRANSIT/`**, kontroler (gdyby powstał) `net_transit` — wpis rejestru
additive jak net_akw/net_fantom.

## §Z. Zbiór odniesienia — rozstrzygnięcie kontroli z telemetrii

**T6** (zamknięty promptem) = c08_s03 (r9_V2), c08_s04 (r12_V2), c10_s02 (r6_V2),
c11_s02 (r6_V2), c11_s03 (r9_V2), c11_s04 (r12_V2) — wszystkie FANTOM S2 V2, valid,
FAIL z t_entry pasywnym 4.91–5.20 s. **Kontrole** (c08–c11 na V2 PRZESZŁY w FANTOM
S2; nazwane z indeksu/telemetrii): **c08_s01 (r3_V2, t_acq 1.28 s), c08_s02 (r6_V2,
2.33 s), c09_s03 (r9_V2, 6.56 s), c09_s04 (r12_V2, 5.80 s), c10_s01 (r3_V2, 9.34 s),
c10_s04 (r12_V2, 9.60 s)** — admisje wczesne 1.3–9.6 s. c09_s01 (r3_V2) PASS ale
`valid_final=False` — wykluczony jawnie (poza n_common). Komórka c11 nie ma ANI
JEDNEJ wygranej V2 w kampanii (c11_s01 FAIL poza T6 — poza n_common wg POSCIG §Z).

**Geometria siatki (wspólna przyczyna ekspozycji, dowód plik:linia):** każdy
scenariusz c08–c11 startuje na perymetrze r=15 m na bearingu komórki i — ponieważ
r=15 > 14 — PIERWSZY segment ma heading `atan2(−y,−x)` = **prosto na home**
(`bench/scenarios.py:52-54`); przy v=1.0 cel osiąga okolicę home w 11.9–16.3 s.
Bliskie przejście nie jest pechem ziaren — to deterministyczna cecha generatora
dla KAŻDEGO epizodu v=1.0; różni się tylko to, czy admisja zdąży przed nim.

## §R1. Anatomia 6 utrat — serce

**Przyrząd:** stożek ENTRY ±43.45° wokół FIZYCZNEGO yaw (efektywny: edge-margin
cx∈[0.10,0.90] ⇒ atan(0.4·640/270) — RECON_AKW.md:91); yaw z `own_q` percep_feed
per klatka (konwencja akw_rot_strat recon AKW); stare = |yaw_rate| ≤ 15°/s (rampa
profilu II = 60°/s, akw_scan.py:40); on-target = kryterium FROZEN det_labels
(identyczne z det_replay.py:147-151); jednostka dryfu celu w kadrze = **°/klatkę**
(reguła ANEKS_AKW-1). Łańcuch admisji (litera): ENTRY = k=3 KOLEJNE klatki boxa
centralnego (edge≥0.10, ruch środka ≤0.15) ∧ koincydencja MTI
(`r02/config_r02.py:26,36`, `r02/target_channel.py:124-127`), a samo mti_ok wymaga
persystencji komponentu ≥3 z 4 ostatnich klatek przy ruchu ≤0.10 (`r02/mti.py:38-40`)
i blobu ≤20% kadru (`r02/mti.py:35`); REFRESH bramkowany central∧mti LUB oknem
predykcji (`harness/feed_vision.py:202-216`). Kadencja T6: **wszystkie 6 epizodów
w modzie WOLNYM ~5.0 Hz** (akw_mode_fuse dt_p50 0.196 s; stare 1.2 s = ~6 klatek).
Kwarantanna: 6/6 czyste `q_enter(fd_invalid)→q_exit C @3.0 s` — bez udziału
w mechanizmie. Dane: `r1_anatomia.json`.

| epizod | bearing | t_acq [s] | bliskie przejście d3@t_rel (dh/dz, faza) | pokrycia FOV PRZED przejściem (t, dh, dryf °/kl) | los percepcji w pokryciach | max run central∧mti | klasa |
|---|---|---|---|---|---|---|---|
| c08_s03 | 0 | 19.53 | 3.478@11.85 (3.10/1.58, hold, ślepy) | 1.08–1.34 (dh 13.9–13.6; 0.57) + 2.20–3.25 (12.7–11.7; 0.20) | box 10/10, on-tgt 10/10, mti 0+3 | **2** | **(ii)** |
| c08_s04 | 0 | 26.18 | 1.632@15.05 (0.04/1.63, hold, ślepy) | 2.48–2.81 (12.5–12.2; —) + 4.33 (10.7; 3.52) | box 4/4, on-tgt 4/4, mti 0 | **0** | **(ii)** |
| c10_s02 | 180 | 29.18 | 1.807@13.85 (1.02/1.49, hold, ślepy) | 9.03–11.93 (5.8→2.8; 4.55–5.12) | box 9/11, centr 6, on-tgt 7, mti 2 | **1** | **(ii)** |
| c11_s02 | 270 | 31.16 | 1.565@16.30 (0.22/1.55, hold, ślepy) | 12.56–12.96 (2.5–2.1; 0.6) + 13.62–14.80 (1.4–0.4; 8.44) | box 10/11, centr 2+0, on-tgt 0, mti 2+0 | **2** | **(ii)** |
| c11_s03 | 270 | 22.26 | 0.444@14.70 (0.43/0.12, hold, ślepy) | 12.80–13.26 (1.9–1.5; 8.16) + 14.12 (0.7; —) | box 3/4, on-tgt 2, mti 0+1 | **1** | **(ii)** |
| c11_s04 | 270 | 25.10 | 1.002@14.75 (0.98/0.22, hold, ślepy) | 12.55–14.00 (2.4–1.2; 5.42–5.52) | box 7/8, centr 4, on-tgt 5, mti 1 | **1** | **(ii)** |

**Liczniki klas: (i) = 0 · (ii) = 6 · (iii) = 0.** ENTRY przed przejściem: 0/6;
fresh przed przejściem: 0/6. Świadek erratum w oknach: 0–6 próbek (wyłącznie brzeg
startu; realne d_min powyżej liczone z manifestu — zgodne z d_min sędziego co do
0.003–0.004 na czystych epizodach).

**Dwie sygnatury wewnątrz klasy (ii):**

- **(ii-a) najazd czołowy w pierwszym oknie (c08, bearing 0 = na nagłówku startowym
  skanu):** cel w stożku od t0 (dwell+stare1 pokrywają azymut 0±43.45), dh 10.7–15,
  dryf w kadrze 0.2–0.6°/kl (poniżej KAŻDEGO progu geometrycznego), box centralny
  on-target w 100% klatek — **pada WYŁĄCZNIE koincydencja MTI**: cel nadlatujący
  czołowo rośnie w kadrze, ale środek stoi (ruch pozorny ~0) — residuum derotacji
  pod progami diff_thr=22/min_area=8 px (`r02/mti.py:30-34`) bywa puste; przy 5 Hz
  w oknie jest ~6–10 klatek i run central∧mti doszedł do 2 (c08_s03) lub 0 (c08_s04)
  vs wymagane 3. **Kontrprzykład w tej samej geometrii: c08_s02 (5 Hz, ten sam
  bearing, dwell) run=3 ⇒ ENTRY @2.33 s; c08_s01 @14.3 Hz run setki.** Admisja
  czołowa przy 5 Hz = rzut monetą (pomiar: 1/3 w oknie dwell; łącznie radialne
  okna ≤5.1 Hz: 4/7 — §R3).
- **(ii-b) skan dociera do korytarza po czasie (c10/c11, bearing 180/270):** CCW od 0
  osiąga azymut 180° @~8.4 s, 270° @~15.1 s; cel (1 m/s, radialnie) jest wtedy już
  na dh ≤5.8 m (c10_s02) albo ≤2.5 m (c11_*) — w **strefie martwej admisji**: dryf
  w kadrze 4.5–11.4°/kl rwie spójność centralności (centr 0–6/11), a blob przy
  dh<4–5 m przekracza max_area_frac=0.20 MTI i wypada z etykiety (on-tgt 0 przy
  dh<2). **Empiryczna PODŁOGA dh admisji zmierzona na WSZYSTKICH 3267 klatkach
  fresh 12 epizodów: min 5.01 m** (p50 8.6) — żadna realna admisja kampanii nie
  zaszła bliżej. Po przejściu cel się oddala i wszystkie T6 admitują późno
  (19.5–31.2 s) — okno sędziego spalone (POSCIG R1).

**Kalibracja przyrządu na kontrolach:** 6/6 kontroli ma ENTRY w pierwszym
przewidzianym oknie pokrycia (t_acq realne 1.28–9.60 vs przewidziane końce okien
1.96–9.40 — §R3 kolumna CH0); wszystkie admisje kontrolne przy dh 5.0–15 i dryfie
≤2.2°/kl (ENTRY) — obraz spójny z progami empirycznymi §R3.

## §R2. Próg konwersji t\* (metoda R1-POSCIG, sędzia FROZEN litera)

t\* = najpóźniejszy start idealnego pościgowca (|v_cmd|≤3.0, r01/config.py:24;
prefix = REALNE GT ślepego zawisu; werdykt `judge_episode` 8ec0fcfb; intruz
z manifestu — świadek obok w R1), przy którym D6 jeszcze domyka się. Skan 0.5 s +
bisekcja 0.05 s; prowadzenie OGON (intercept w t\* liczony kontrolnie — **PASS we
wszystkich 6**, zgodnie z POSCIG „intercept≡ogon"). Dane: `r2_tstar.json`.

| epizod | t_dmin ślepe [s] | t\* [s] | d_min symulacji @t\* | t_acq realne [s] | deficyt akwizycji [s] |
|---|---|---|---|---|---|
| c08_s03 | 11.85 | **11.28** | 4.024 | 19.53 | 8.25 |
| c08_s04 | 15.05 | **11.41** | 4.026 | 26.18 | 14.77 |
| c10_s02 | 13.85 | **11.06** | 4.035 | 29.18 | 18.12 |
| c11_s02 | 16.30 | **11.34** | 4.000 | 31.16 | 19.82 |
| c11_s03 | 14.70 | **10.75** | 4.017 | 22.26 | 11.51 |
| c11_s04 | 14.75 | **10.91** | 4.008 | 25.10 | 14.19 |

- **t\* jest jednolite (10.75–11.41 s) i wszędzie wiążące przez d_min** (symulacja
  na t\* kończy z d_min 4.00–4.04): idealny pościgowiec musi opuścić home z wyprzedzeniem
  0.6–5.0 s względem ślepego przejścia, żeby wyciągnąć separację ≥4 m — stąd próg
  leży PRZED t_dmin, nie na nim. Powyżej t\* FAIL natychmiast (bez wysp PASS).
- **Wcześniejsza akwizycja ELIMINUJE bliskie przejście — zmierzone na kontrolach:**
  realne d_min kontroli = 4.94–6.90 m, wszystkie w fazie orbit z trackiem ważnym
  (dron w orbicie r=8/alt 12 kontroluje geometrię zamiast wisieć na trasie celu);
  symulacje od realnych t_acq kontroli: d_min 6.5–7.0. Kontrole t\*: c08/c09 —
  cały horyzont (ich trajektorie nie schodzą <4 m pod ślepym zawisem), c10_s01/s04:
  t\* 23.0/21.1 (drugi nawrót celu).
- Rezerwa na szum/E2E jak w POSCIG R5 (~0.2 s) — wobec rozstępów deficytu ≥8.25 s
  nie zmienia żadnej klasyfikacji.

## §R3. Przestrzeń choreografii (projekt, bez budowy) — rachunek na GT

**Liga dźwigni:** wyłącznie NOWY wrapper nad fantom_scan (nowy plik + wpis rejestru
additive; percepcja/admisja/profil II b94cdeae/kwarantanna e435ed7e NIETYKALNE).
Wspólne nietykalne reżimu: dwell 2.0 / slew 60°/s / stare 1.2 s (akw_scan.py:39-42);
admisja w rampie nie istnieje (dowód smoke S1 AKW: 0/235 przy 3.96°/kl —
akw_scan.py:24-25; rampa @5 Hz = 11.8°/kl). **Okno admitowalne** (progi EMPIRYCZNE
z kampanii): stare ∧ stożek ±43.45° ∧ **dh∈[5,18] m** (podłoga = min dh realnych
fresh 5.01 m) ∧ dryf ≤5°/kl (p99 fresh; ENTRY do ~6.8) przez ≥1.0 s (precedens
fantom_recon r3). Klasa okna RADIAL = kąt prędkości celu do −LOS <25° (najazd
czołowy — loteria MTI przy 5 Hz). Dane: `r3_choreografie.json`.

**(b) Tabela wariantów — przewidziany koniec pierwszego okna admitowalnego [s]
(konwersja = ≤ t\*):**

| epizod (t\*) | CH0 40°CCW (baseline) | CH90 90° | CH90 baza+45° (stres) | CH87 86.9° (bez klina) | CH180 naprzem. | CHFAN ±40° | ORACLE baza=korytarz |
|---|---|---|---|---|---|---|---|
| c08_s03 (11.28) | **2.0** | **2.0** | 20.8 ✗ | **2.0** | **2.0** | **2.0** | **2.0** |
| c08_s04 (11.41) | **2.0** | **2.0** | 26.2 ✗ | **2.0** | **2.0** | **2.0** | **2.0** |
| c10_s02 (11.06) | **9.4** | **7.2** | 29.0 ✗ | **7.2** | **6.0** | 20.4 ✗ | **2.0** |
| c11_s02 (11.34) | 30.0 ✗ | **9.8** | 31.6 ✗ | **9.8** | 29.4 ✗ | 30.4 ✗ | **2.0** |
| c11_s03 (10.75) | 22.4 ✗ | **9.8** | 26.2 ✗ | **9.8** | 25.2 ✗ | 33.6 ✗ | **2.0** |
| c11_s04 (10.91) | 24.4 ✗ | **9.8** | 26.2 ✗ | **9.8** | 25.2 ✗ | 23.0 ✗ | **2.0** |
| **konwersja geometryczna T6** | 3/6 | **6/6** | 0/6 | **6/6** | 3/6 | 2/6 | 6/6 |
| w tym okna RADIAL | 3/3 | **6/6** | — | **6/6** | 3/3 | 2/2 | 6/6 |
| kontrole: admisja ≤ realna+2 s | 6/6 | 6/6 | **1/6** (5 opóźnionych) | 6/6 | **4/6** (c09 NIGDY) | **2/6** (4 opóźnione) | 6/6 |
| max przerwa rewizyty azymutu [s] | **13.9** | 34+ (klin stały 3.1°) | 34+ (klin) | 12.0 | 32.0 | 30.1 | 13.9 |

**Kalibracja uczciwości (CH0 = rzeczywistość kampanii):** przyrząd przewiduje dla
CH0 konwersję geometryczną **3/6** (okna dwell c08_s03/s04 + okno 8.4–9.4 c10_s02)
— **realnie 0/6**: oba okna c08 przegrały loterię MTI czołowego (identyczne okno
wygrał c08_s02), okno c10_s02 w locie zaszło przy dh 5.8→2.8 i padło (mti 2/11,
run 1). Na kontrolach przyrząd trafia 6/6 bez opóźnień. ⇒ **liczby „konwersji
geometrycznej" są GÓRNĄ granicą; nakładka empiryczna admisji okien RADIAL przy
≤5.1 Hz = 4/7** (PASS: c08_s02, c09_s03, c09_s04, c10_s04; FAIL: c08_s03, c08_s04,
c10_s02), a dla najsłabszej podklasy okien (pojedyncze ~1.0 s przy dh 6.4→5.0)
= **1/2** (c10_s04 TAK / c10_s02 NIE). Oczekiwana konwersja najlepszego wariantu
(CH90/CH87): **~2–4 / 6, bez gwarancji** — i to przy założeniu, że predyktor okien
nie myli się na niekorzyść (na c10_s02 realne okno było o ~0.6 s późniejsze
i płycej niż przewidziane).

**(a) Sektor startowy z priorytetem korytarza nadejścia:** polityki realizowalnej
NIE MA — korytarz = bearing komórki, rozłożony jednostajnie na {0,90,180,270}°,
a wrapper w t0 nie ma żadnego prioru (kwarantanna właśnie skasowała track; fantom
pochodzi z poprzedniego epizodu, bez związku z korytarzem bieżącego). ORACLE
(baza=korytarz) daje 6/6 okien @2.0 s — to GRANICA GÓRNA informacji, nie dźwignia.
Stała baza ≠ 0 przesuwa problem między komórkami (symetria siatki).

**Teoremat sufitu (rachunek zamknięty, `min_360` w JSON):** nowy łuk do pokrycia
po dwell = 360−86.9 = 273.1°, więc koniec ostatniego stare t_end(n) = 2 + 273.1/60
+ 1.2·n; minimalne n bez klina stałego = ⌈273.1/86.9⌉ = 4 ⇒ **koniec 1-sekundowego
okna najgorszego azymutu ≥ 11.15 s** (krok optymalny 68.3°; krok 40° baseline:
14.87 s; krok 90°: 12.6 s z KLINEM STAŁYM 3.1° — azymuty 45/135/225/315 nigdy
niepokryte; krok 120°: 11.4 s z klinem 33°). Tymczasem **pas admisji celu
radialnego v=1.0 zamyka się o 10.0 s** (dh≥5 — podłoga empiryczna §R1), a t\* =
10.75–11.41 s. **11.15 > 10.0 ⇒ NIE ISTNIEJE choreografia w nietykalnych
gwarantująca okno admitowalne przed zamknięciem pasa admisji dla DOWOLNEGO azymutu
nadejścia** (a wobec samego t\*: deficyt w 3/6 T6, margines ≤0.26 s w pozostałych 3
— zero zapasu na PX4/lag/warmup). CH90/CH87 osiągają 6/6 wyłącznie
dlatego, że korytarze SIATKI leżą na/przy nagłówkach (overfit do ławki): stres
bazą +45° (równoważny siatce obróconej o 45°) ⇒ **0/6 + regresja 5/6 kontroli**.
Werdykt z takiej kampanii nie byłby twierdzeniem o misji, tylko o wyrównaniu
choreografii z generatorem scenariuszy.

**(c) Mikro-orbita wokół home podczas skanu (parallaksa + zejście z trasy):**
geometria mierzona na T6 (24 fazy startowe, `orbit` w JSON): r=2 m/v=0.5 —
d_min ślepego przejścia ≥4 m w **0–46% faz** (minima fazowe 0.05–1.18 m, mediany
0.68–3.89); r=3 m/v=0.75 — ≥4 m w **0–50% faz** (minima 0.05–0.30). Ścieżka celu
przecina KAŻDY okrąg wokół home (pierwszy segment celuje w home) ⇒ separacja jest
loterią fazy, nie mechanizmem. Parallaksa: v=0.5–0.75 m/s na dh 5–15 m zmienia dryf
o ±(1.9–8.6)°/s = ±0.4–1.7°/kl @5 Hz — tam gdzie dryf był problemem (4.5–11°/kl),
nie wystarcza; tam gdzie nie był (czołowe ~0), dodaje ruch pozorny TŁA: derotacja
MTI kompensuje WYŁĄCZNIE rotację (`r02/mti.py:3-6`), translacja łamie założenie
statycznego tła (podłoże ~10–12 m pod kamerą ⇒ przepływ do ~2.9–4.3°/s w dolnej
części kadru) — wpływ na admisję/FP NIEMIERZALNY deskiem przy percepcji FROZEN.
Koszty nazwane: energia zawisu→lotu ciągłego; kontrakt hold (hover-hold
`net_controller.py:107-109`, home_hover_alt executor_params) — wrapper musiałby
nadpisywać PRĘDKOŚĆ delegata w hold, nie tylko yaw = nowa klasa ingerencji
w komendę (dotąd wrappery zmieniały wyłącznie pole yaw — akw_scan.py:8-9);
osłona: ruch w strefie home bez tracku = nowa obwiednia do charakteryzacji.
**Werdykt: nie kupuje** (separacji nie gwarantuje, admisji nie poprawia, koszty
systemowe realne).

**(d) Zmiana wysokości zawisu: POZA LIGĄ.** Rachunek jednowierszowy: separacja
pionowa gwarantująca d_min≥4 wymaga zawisu ≥14 m AGL (cel z=10 — `bench/scenarios.py:20`
Z_INTR); kontrakt misji/przyrządu: patrol ALT_M=10 (`r01/config.py:19`), zawis
`home_hover_alt_m=10.0` i orbita `z_orb_alt_m=12.0` (`bench/executor_params.json`),
a geometria elewacji kamery (det_v2 charakteryzowany na tym profilu; historycznie
detekcja wymaga właściwego tła — `r02/config_r02.py:75-78`) jest częścią zamrożonej
percepcji. Zmiana = inny profil misji i inna dystrybucja wejścia detektora ⇒
wyceniona nie-projektowana.

## §R4. Ryzyka (mechanizmy)

- **Kwarantanna:** w T6 6/6 przebiegów czystych `q_enter(fd_invalid)→q_exit C@3.0 s`
  (fantom_qlog); predykat K1 (A/B/C) jest funkcją feedu i czasu, NIE choreografii —
  wyjście C (3.0 s) wypada w dwell(2.0)+pierwsza rampa niezależnie od wzorca skoków;
  wyjście B (skok >5 m) zależy od odświeżeń fantomu przez percepcję (nietkniętą).
  Jedyne sprzężenie: inna choreografia ustawia nos gdzie indziej w t∈[0,3] ⇒ inne
  prawdopodobieństwo odświeżenia starego fantomu (wyjścia A/B zamiast C) — bez
  wpływu na bezpieczeństwo (delegat i tak ślepy do wyjścia), do odnotowania
  w telemetrii q_* przyszłej kampanii.
- **Bezpiecznik modu:** trip = mod WOLNY ∧ admisje fresh ślepych@FOV == 0 na boot
  (akwS3_campaign.sh:100-102). Choreografia zmienia udział klatek rampy w FOV
  (CH90: rampa 1.5/2.7 s cyklu vs CH0 0.667/1.867) ⇒ statystyka n_fresh/n_fov_blind
  SPADNIE, ale trip wymaga zera freshów — admisje po-akwizycyjne i okna stare
  utrzymują >0; ryzyko tripu niskie, próg bez zmian.
- **Mody kadencji (5.10/7.58/14.71 Hz) — rachunek per-klatka:** stare 1.2 s daje
  6.1/9.1/17.7 klatek; łańcuch admisji potrzebuje k=3 kolejnych klatek central∧mti
  + persystencję MTI 3/4 (warmup ~4 klatki od wejścia celu/stabilizacji nosa) ⇒
  w modzie najwolniejszym pojedyncze stare ma margines ~2 klatek na CAŁY łańcuch —
  to jest zmierzone źródło loterii czołowej (§R1 ii-a: run 2 vs 3). Okno 1.0 s
  (predyktor R3) = 5.1 klatki @5.10 Hz — na progu. Każda choreografia skracająca
  pokrycie azymutu do JEDNEGO stare na obrót (CH90/CH87) stawia całą konwersję na
  tych ~2 klatkach marginesu; T6 w kampanii leciało w 100% w modzie 5 Hz (pomiar),
  a mod jest środowiskowy per boot — wynik ewentualnej kampanii byłby sprzężony
  z losowaniem kadencji.
- **Symetria ramienia B:** w FANTOM S2 OBA ramiona latały kontrolerem `net_fantom`
  (akw_summary r9_B/r9_V2: controller=net_fantom; różnica ramion = feed B/V2) —
  nowy wrapper choreografii musiałby lecieć w OBU ramionach tak samo (wzór
  kampanii FANTOM), inaczej Δ przestaje mierzyć percepcję.
- **Porównywalność z trzema kampaniami-wzorcami:** choreografia skanu to zachowanie
  WRAPPERA (yaw w hold — akw_scan.py:8-9), nie ławki: scenariusze/teleporty/sędzia/
  mosty bez zmian (jedyny most feed→kontroler `bench_flight.py:359-360`; bench
  05137098 i sędzia 8ec0fcfb FROZEN). Zmiana NIE dotyka choreografii epizodów —
  potwierdzone literą: wybór kontrolera = wpis rejestru (additive), reszta toru
  identyczna. Werdykty nowej kampanii byłyby jednak NIEPORÓWNYWALNE wprost z Δ
  łańcucha 34→12→7 (inny kontroler w gnieździe) — jak każda nowa pozycja.
- **Ryzyko systemowe erratum (odziedziczone):** każdy przyszły werdykt d_min na
  surowym gt_intruder wymaga świadka-filtra OBOK (ERRATUM_DMIN §2) — w tym recon
  zastosowano (manifest + kolumna świadka w R1).

## §R5. Wycena dalszej drogi

- **(i) ZAMKNIĘCIE SUFITEM PROFILU MISJI — 0 bootów (REKOMENDACJA).** Prerejestrowany
  warunek zamknięcia ZACHODZI z dokładnym rachunkiem: (1) klasa (ii) = 6/6 —
  admisja, nie geometria pokrycia per se; percepcja FROZEN; (2) okno życia celu
  w pasie admisji [5,15] m trwa 10.0 s od startu epizodu, t\* = 10.75–11.41 s,
  a gwarantowane pokrycie najgorszego azymutu w nietykalnych kończy okno ≥11.15 s
  — **żadna choreografia bez prioru nie gwarantuje okna przed zamknięciem pasa
  admisji ani (z zapasem) przed progiem konwersji**;
  (3) warianty wyrównane do siatki (CH90/CH87) dają tylko okna RADIAL z empiryczną
  admisją 4/7 (oczekiwanie ~2–4/6, zero gwarancji) + klin/jednostrzałowość pokrycia;
  (4) mikro-orbita nie gwarantuje separacji (0–50% faz), wysokość poza ligą.
  Pozycja AKW-TRANSIT zamyka się jako **zmierzony sufit profilu misji** (zawis na
  home + separacja ≥4 m + cel przecinający dysk) — pełnoprawny wynik: sufit ma
  trzy zmierzone składowe (deterministyczny najazd generatora scenarios.py:52-54,
  strefa martwa admisji dh<5 m, arytmetyka przeglądu perymetru vs t\*).
- **(ii) PRE_TRANSIT z nowym wrapperem (gdyby mimo rachunku):** desk-testy wrappera
  (pass-through bajtowy poza hold, wzór PRE_AKW §3.1) → smoke 1+1 → kampania
  verbatim 12×{B,V2} 24+3 (progi PRE_2A + warstwa pozycji na T6 wzór FANTOM,
  świadek-filtr w werdyktach OBOWIĄZKOWY) ⇒ **~27–29 bootów, 2 sesje lotne**;
  sufit nogi (propozycja): **≤30**. Przewidywanie z tego recon: najlepszy kandydat
  CH87 (86.9°, bez klina, rewizyta 12.0 s) konwertuje **~2–4/6** par T6 zależnie
  od loterii MTI czołowego i losowania modu kadencji; werdykt POZYCJI na T6 (wzór
  N6: sukces ≥5/6) **przewidywany FAIL/strefa opisowa** — kampania kupowałaby
  głównie potwierdzenie stopy loterii za ~27 bootów. Zarys FREEZE_TRANSIT: sha
  nowego wrappera + sekwencja nagłówków (stała, np. krok 86.9°) + odziedziczone
  FREEZE_FANTOM/AKW/DET verbatim + świadek-filtr d_min + reguła OBU ramion na
  wrapperze. **Czego NIE wolno dotknąć:** percepcja (det_v2 775ead15, percep_proc,
  progi admisji, MTI), osłona + piny 5/5, kwarantanna fantom_scan e435ed7e, profil
  II akw_scan b94cdeae (nowy wrapper = NOWY plik), wagi net/frozen (ncp 0337d5ea),
  rejestry (wpis WYŁĄCZNIE additive), sędzia 8ec0fcfb (świadek obok), bench
  05137098, parametry misji (ALT_M, home_hover_alt_m, executor_params).
- **(iii) Sonda celowana (tania, bez interpretacji progowej — słabość wprost):**
  jedyna wielkość niezmierzona wprost to STOPA admisji MTI na celu czołowym
  w stare @5 Hz (dziś 4/7 z kampanii, n małe). Sonda: ~6–8 bootów (T6-geometrie +
  2 kontrole) z wrapperem CH87 ALBO czysty re-bieg c08 ×k — wynik mechanizmowy
  (stopa loterii), bez Δ i bez werdyktu pozycji. Ma sens WYŁĄCZNIE, jeśli CC
  chce pomiaru stopy przed podpisaniem aneksu zamykającego; rachunku sufitu
  (min-360 vs t\*) żadna stopa nie uchyla.

## Artefakty

`tools/transit_r1.py` → `r1_anatomia.json` (oś czasu, pokrycia, admisja, przejścia,
kwarantanna, świadek) · `tools/transit_r2.py` → `r2_tstar.json` (t\*, deficyty,
eliminacja przejścia) · `tools/transit_r3.py` → `r3_choreografie.json` (warianty,
min-360, rewizyty, mikro-orbita). Progi empiryczne przyrządu R3 wyprowadzone
z pomiaru 3267 klatek fresh kampanii (podłoga dh 5.01 m; dryf p99 5.0°/kl) —
wartości w JSON (`progi`).

**Rekomendacja końcowa: wariant (i)** — pozycja AKW-TRANSIT zamyka się reconem jako
ZMIERZONY SUFIT PROFILU MISJI (anatomia: admisja 6/6, nie pokrycie; arytmetyka:
przegląd perymetru ≥12.59 s > t\* 10.75–11.41 s; empiria: okna wyłącznie RADIAL
z admisją-loterią przy 5 Hz; mikro-orbita i wysokość nie kupują w nietykalnych).
Dalej: CC pisze **aneks zamykający** (sufit profilu misji z trzema składowymi
i odsyłaczami) ALBO **PRE_TRANSIT numerowany** (wtedy: dźwignia = wrapper CH87,
przewidywanie konwersji ~2–4/6 jako WSKAŹNIK nie-bramka, progi dwuwarstwowe wzór
FANTOM, jednostki per-klatka dla progów sprzężonych z kadencją, świadek-filtr
obowiązkowy). Sygnały bez numeru odrzucam. **STOP-TRANSITR.**
