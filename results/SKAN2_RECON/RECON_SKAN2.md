# RECON_SKAN2 — czas wpatrywania skanu pod gwarantowaną kadencją — STOP-SKAN2R

Egzekutor · 01.11.2026 · wykonanie PROMPT_SKAN2_S0. **Sesja wyłącznie deskowa: 0 bootów, 0 SITL,
0 treningu, 0 edycji istniejących plików; nowe pliki wyłącznie `results/SKAN2_RECON/**`.** Dane
wyłącznie z istniejących logów; FROZEN importowane READ-ONLY (det_labels 8f7430cd, bench/scenarios,
transit_r3 jako wzór formy zamkniętej).

**WYNIK GŁÓWNY:**

1. **Hipoteza w brzmieniu promptu jest sfalsyfikowana przy biurku.** L (p90 stare → fresh
   @14.7 Hz, litera) = **1.384 s**, S (p90 uspokojenia yaw) = **0.86 s**. Warunek stare ≥ S + L =
   2.24 s nie da się pogodzić z t_worst ≤ 9.5 s, więc w tabeli R3 (A) jest **0 kombinacji
   dopuszczalnych**. To jest śmierć przy biurku z §R6, literą.
2. **Ale dane obalają przesłankę, na której stoi to kryterium.** Przy 14.7 Hz admisja nie
   potrzebuje stare. ENTRY na celu w rampie skanu (56–58°/s) w **22/36** przypadków; przy 5 Hz
   12/47. Mediana zdarzeń bez wiatru ma **zero klatek stare** przed fresh. Per klatka, przed
   akwizycją, koincydencja central∧MTI na celu jest **wyższa w rampie (0.38–0.46 przy
   3–5°/klatkę) niż w stare (0.13–0.24 przy 0–2°/klatkę)**. Kanałem MTI jest residuum derotacji;
   wolny cel przy nosie nieruchomym nie daje MTI ruchu. Zdanie ANEKS_AKW-1 §5 „w oknie stare
   ω·dt = 0 ⇒ admisja jak przy nosie nieruchomym" było prawdą epoki 5 Hz, a teraz stare jest
   gorszym miejscem admisji niż rampa.
3. **W modelu admisji w rampie** (odchylenie nazwane, §R3-B), skalibrowanym na profilu FROZEN
   (offset obserwacja − model 0.64–1.64 s, n = 6, bez wiatru), jest **7 kombinacji
   dopuszczalnych, wszystkie z dwell 1.0 s poza jedną**. Najlepsza: **krok 68.3° / stare 0.4 s /
   dwell 1.0 s → najgorszy azymut przyjęty o 8.39 s** (zapas 1.11 s do 9.5 s), czas celu w stożku
   2.25 s ≥ 1.64 s.
4. **Z wiatrem (WK2/WK3, 1.5–3.6 m/s) dźwigni nie ma w żadnym modelu.** Offset p50 2.3 s; ucięte
   4/33 zdarzeń; 2/12 epizodów z chybionym pierwszym przejściem.
5. **Werdykt:** dźwignia **nie istnieje literą promptu**, **istnieje warunkowo w danych** (bez
   wiatru, przez admisję w rampie, nie przez skrócenie stare). Rozstrzyga CC: aneks zamykający
   literą albo PRE z przeformułowaną hipotezą.

## §0. Bramka wejścia — PASS

`git fetch` → origin/master == HEAD == **0e255417 (CO-DET3-0)**; `ANEKS_DET3-0.md` na origin,
sha256 **a2e6947e…2b38f7** zgodne; `origin/master..HEAD` pusty; porcelain czysty poza nazwanymi `??`
(results/DEMO_C/*). FROZEN sha8: akw_scan **b94cdeae** · fantom_scan **e435ed7e** · r02/mti.py
**0889ab39** · r02/config_r02.py **9f334369** · percep_proc **38a3a765** · bench_judge **8ec0fcfb**
(zgodne z RECON_TRANSIT §0). Dane: PERC2 S2 (bA_c08, bB_c1011; `s2_okna.json`), DET3_RECON r1,
FANTOM S2 V2, r3_choreografie/transit_r3.

## §Z. Populacje i przyrząd

- **(a) PERC2 S2 @14.71 Hz**: 8 epizodów (c08_s01–04, c10_s02, c11_s02–04), net_fantom, OPS.
- **(a′) ROZSZERZENIE NAZWANE: net_fantom po PERC2 w reżimie OPS @14.7 Hz** (WK/WK2/WK3, 48
  epizodów, c00–c07, v = 0 / 0.5). Powód: (a) ma < 10 zdarzeń, a te boot-y latają tym samym
  skanem i tą samą percepcją. Warstwy: **bez wiatru** = wk0_b1/b2, g0_b1/b2 (światy
  z `<linear_velocity>0 0 0`), **wiatr** = g15, g3, p1, p2 (1.5–3.6 m/s).
- **(b) korpus DET S1 @15 Hz** (12 bootów; zdarzenie = pierwsza klatka z celem w stożku
  centralnym; z `DET3_RECON/r1`).
- **(c) FANTOM S2 V2 @5 Hz** (48 epizodów), kontrast epoki loterii.
- WABIK pominięty (dwa obiekty w kadrze psują definicję „na celu").

**Przyrząd** (`tools/skan2_r1.py`): GT intruza z MANIFESTU (reguła erratum) wstawiony do
`det_labels.BootGeo` (projekcja FROZEN 1:1). Stożek centralny = rzut celu z edge ≥ 0.10
(`r02/config_r02.py:36`, `r02/target_channel.py:47-49,124`). Stare = |yaw_rate| < 15°/s
(transit_r1:42). Box na celu (det_replay.py:149-152). Koincydencja = box na celu ∧ centralny ∧
mti_ok (`target_channel.py:124-128`). Run ≥ 3 (`config_r02.py:27`). **Fresh na celu** = fresh ∧
|trk − GT|_xy ≤ 3 m (= REFRESH_GATE_M, `feed_vision.py:56`), co odsiewa locki sprzed startu.
Zdarzenia **ucięte** (fresh nie zaszła w odcinku + 0.6 s) liczone jako +∞, nie pomijane.

## §R1. Latencja admisji po wejściu celu w stożek

**Dwie definicje zdarzenia.** (i) **Litera promptu: stożek ∧ stare.** (ii) **Odchylenie
nazwane: stożek przy dowolnym yaw_rate.** Powód: w c10_s02 (jedyny czysty „skan dochodzi do
celu" w PERC2 S2) ENTRY zaszło @8.736 s przy yaw_rate 60–75°/s, **w rampie, bez ani jednej klatki
stare**. Definicja (i) tego zdarzenia nie widzi.

Klasa Z0 ≥ 5 m (pas admisji). Zdarzenia przy Z0 < 5 m (c11_s02–04: cel w strefie martwej, dh ≤ 3.2 m
przy dojściu skanu) to inna klasa, wyłączona z L. `r1_L.json` (wszystkie percentyle).

| populacja / definicja | n | ucięte | mti p50/p90 | koincydencja p50/p90 | run≥3 p50/p90 | **fresh p50/p90/p95** |
|---|---|---|---|---|---|---|
| (a) stare | 2 | 0 | 0.13/0.20 | 0.13/0.20 | 0.33/0.59 | 0.13/0.20/0.20 |
| (b) DET | 12 | 0 | 0.59/1.19 | 0.59/1.19 | 0.72/1.38 | **0.66/1.38/1.72** |
| **(a)+(b) stare — L literą** | **14** | 0 | | | | **p90 = 1.384** |
| (a′) bez wiatru, stare | 6 | 2 | 0.06/1.06 | 0.06/1.06 | 0.20/15.1 | 0.53/∞/∞ |
| (a′) wiatr, stare | 24 | 11 | 0.13/1.06 | 0.20/1.19 | 1.25/17.8 | 1.26/∞/∞ |
| (c) 5 Hz, stare | 47 | 24 | 0.13/1.12 | 0.13/1.45 | 0.99/18.2 | ∞ |
| (a) dowolny | 4 | 0 | 0.07/0.26 | 0.07/0.26 | 0.40/0.92 | 0.20/0.33/0.33 |
| (a′) bez wiatru, dowolny | 17 | 1 | 0.13/0.46 | 0.13/0.46 | 0.26/1.19 | 0.20/1.19/∞ |
| **(a)+(a′ bez wiatru)+(b), dowolny** | **33** | **1** | 0.13/0.72 | 0.13/0.72 | 0.59/1.19 | **0.26/1.19/1.72** |
| (a′) wiatr, dowolny | 33 | 4 | 0.07/0.86 | 0.07/1.45 | 0.72/17.4 | 0.60/∞ (przyjęte p90 3.76) |
| (c) 5 Hz, dowolny | 73 | 29 | 0.46/1.45 | 0.59/1.85 | 1.19/17.2 | 1.39/∞ (przyjęte p90 1.52) |

**Gdzie siedzi czas:** box na celu pojawia się natychmiast (p90 0.0–0.07 s we wszystkich
populacjach). Cały koszt to **MTI → run ≥ 3**. Przy 5 Hz 40% zdarzeń to ucięte, przy 14.7 Hz
bez wiatru 3% (1/33), z wiatrem 12%.
**Wycinek rozstrzygający:** zdarzenia (a)+(a′ bez wiatru) przyjęte **wyłącznie w rampie** (0 klatek
stare przed fresh): **14/21, latencja 0.07–0.59 s**. Zdarzenia, w których admisja przeszła do
stare: 7/21, 0.20–1.19 s, 1 ucięte. Z wiatrem: 14/33 w samej rampie (≤ 0.72 s), 19/33 z udziałem
stare (do 3.83 s, 4 ucięte).

**L = p90 czasu stare → fresh @14.7 Hz (litera): 1.384 s.** Populacja (a) ma tylko 2 zdarzenia
stare, więc zgodnie z promptem uzupełniona jest (b), razem n = 14. Obok: wariant „dowolny
yaw_rate" bez wiatru p90 = 1.188 s (n = 33); z wiatrem p90 = ∞ (ucięte ≥ 10%).

## §R2. Uspokojenie yaw po skoku

`tools/skan2_r2.py` → `r2_S.json`. Rampa = |yaw_rate| ≥ 30°/s przez ≥ 0.3 s, kroki 30–55°.
Uspokojenie ostateczne T15_final = do ostatniej klatki z |yaw_rate| ≥ 15°/s w [t_e, t_e+0.95 s]
(okno ucięte przed rozpędem następnej rampy, który w danych startuje ~1.0 s po t_e).

| warstwa | n kroków | kąt p50 | v rampy p50 [°/s] | T15 pierwsze p90 | **T15_final p50/p90** | przeregulowanie p50/p90 [°] | spokój w 1.2 s stare (p50) |
|---|---|---|---|---|---|---|---|
| (a) PERC2 S2 | 25 | 42.3 | 57.9 | 0.20 | **0.79/0.86** | 7.7/8.5 | 0.50 |
| (a′) bez wiatru | 50 | 41.5 | 56.4 | 0.20 | **0.79/0.86** | 7.9/8.3 | 0.50 |
| (a′) wiatr | 120 | 42.7 | 57.2 | 0.20 | **0.79/0.86** | 7.9/8.3 | 0.50 |
| (c) 5 Hz | 144 | 41.8 | 56.2 | 0.66 | 0.79/1.12 | 6.5/8.3 | 0.56 |

**S = p90 uspokojenia = 0.86 s.** Rampa 60°/s jest realizowana jako **56–58°/s** (p50). Krok
40° wychodzi jako 41.5–42.7° z przeregulowaniem ~8°. Mechanizm (surowy przebieg, g0_b1 c03_s01
t 2.5–7.0 s): po rampie nos przestrzeliwuje o ~8°, wraca wahnięciem −20°/s przez ~0.4 s
i staje ~0.8 s po końcu rampy. **Z 1.2 s stare spokojne jest ~0.35 s**. Pierwsze zejście poniżej
15°/s (0.20 s) to szczyt przestrzału, nie spokój. Dryf < 5°/klatkę przy 14.7 Hz jest spełniony
od pierwszej klatki po rampie (T5 p90 0.068 s), przy 5 Hz T5 p90 0.86 s.

**Speckle po skoku** (klatki w [t_e, t_e+1.2 s]): koincydencja MTI bez celu w kadrze — (a)
39/457 (8.5%), (a′) bez wiatru 14/854 (1.6%), wiatr 23/2104 (1.1%), 5 Hz 32/797 (4.0%). Fresh
z trackiem > 3 m od GT w tym oknie: 8 / 6 / 3 / 0. To locki sprzed startu w kwarantannie albo
błąd zasięgu (§R5b), nie nowe admisje na tle.

## §R3. Forma zamknięta i tabela

`tools/skan2_r3.py` → `r3_tabela.json`; kalibracja `tools/skan2_r3_kal.py` → `r3_kalibracja.json`.

**Odtworzenie 11.15 s** (transit_r3.py:114-132): n = ⌈273.1/68.3⌉ = 4; t_end = 2 + 4·(68.3/60 +
1.2) = **11.35**; koniec okna 1.0 s = 11.35 − 1.2 + 1.0 = **11.15 s**; forma aneksu 2 + 273.1/60 +
4·1.2 − 0.2 = **11.15** ✓.

**„Okno 1-sekundowe" przy stare < 1.0 s — z litery: NIE.** Okno admitowalne TRANSIT to stare ∧
stożek ∧ dh ∧ dryf ≤ 5°/kl przez **≥ 1.0 s ciągłe** (transit_r3.py:17,52, precedens fantom_recon
r3). Stare krótszy niż 1.0 s literą nie mieści takiego okna (rampa nie jest stare). Wartość 1.0 s
to precedens, a nie kod: kod wymaga run ≥ 3 (0.2 s @14.7 Hz). R1 pokazuje jednak, że realny koszt
to MTI → run, p90 1.19–1.38 s, a nie 0.2 s.

**(A) Litera promptu** (okno = cały stare najgorszego azymutu; dopuszczalna ⇔ t_worst ≤ 9.5 ∧
stare ≥ S + L = 0.86 + 1.384 = **2.244 s**). Wybór z 40 wierszy (pełna tabela w JSON):

| krok \ stare (dwell 2.0) | 0.4 | 0.5 | 0.7 | 0.9 | 1.2 |
|---|---|---|---|---|---|
| 40° (n=7) | 9.47 | 10.17 | 11.57 | 12.97 | 15.07 |
| 50° (n=6) | 9.40 | 10.00 | 11.20 | 12.40 | 14.20 |
| 60° (n=5) | 9.00 | 9.50 | 10.50 | 11.50 | 13.00 |
| 68.3° (n=4) | 8.15 | 8.55 | 9.35 | 10.15 | 11.35 |

(dwell 1.0 = każda wartość − 1.0). Część wierszy mieści się w 9.5 s, ale **żaden nie spełnia stare
≥ 2.244 s**. **Kombinacji dopuszczalnych: 0.**

**(B) Model admisji w rampie (odchylenie nazwane).** Krawędź czołowa stożka dochodzi do
najgorszego azymutu po obrocie 273.1° od końca dwell. T_rot = k·(krok/60 + stare) + reszta/60;
cel zostaje w stożku przez obrót o 86.9°. **(B-kal)** zamiast L używa offsetu O zmierzonego na
profilu FROZEN: obserwowana akwizycja − (dwell + T_rot do azymutu celu), epizody z azymutem stałym
(v=0 c01–c03, v=1.0 c10), bez wiatru, pierwsze przejście: **O = 0.64 / 0.83 / 0.86 / 1.12 / 1.12 /
1.64 s (O_max 1.64)**. **Chybione pierwsze przejście: 1/7** (wk0_b1 c02_s01, akwizycja 24.6 s).
Z wiatrem: O p50 2.29 s, chybienia 2/12, kilka 2.1–4.5 s (drugi cykl).
Dopuszczalna ⇔ dwell + T_rot(273.1) + O_max ≤ 9.5 ∧ czas w stożku ≥ O_max.

| krok | stare | dwell | T_rot 273° | czas w stożku | **t_adm najgorszy** | frakcja rampy |
|---|---|---|---|---|---|---|
| **68.3** | **0.4** | **1.0** | 5.75 | 2.25 | **8.39** | 0.74 |
| 68.3 | 0.5 | 1.0 | 6.05 | 2.45 | 8.69 | 0.69 |
| 60 | 0.4 | 1.0 | 6.15 | 2.25 | 8.79 | 0.71 |
| 50 | 0.4 | 1.0 | 6.55 | 2.25 | 9.19 | 0.68 |
| 60 | 0.5 | 1.0 | 6.55 | 2.45 | 9.19 | 0.67 |
| 68.3 | 0.7 | 1.0 | 6.65 | 2.85 | 9.29 | 0.62 |
| 68.3 | 0.4 | 2.0 | 5.75 | 2.25 | 9.39 | 0.74 |

**7 dopuszczalnych (B-kal); 14 w nieskalibrowanym (B) z L = 1.188 s.** W (B) mieści się też obrót
ciągły 60°/s (t_adm 6.74–7.74 s), ale w (B-kal) odpada: czas w stożku 1.45 s < O_max 1.64 s.
Kontrola modelu: profil FROZEN 40/1.2/2.0 w (B-kal) daje 2 + 11.75 + O ≈ 14.4–15.4 s dla
najgorszego azymutu, zgodnie z obserwacjami c03 (270°): 12.4–13.4 s przy azymucie 226.5°,
nie najgorszym. **Z wiatrem: 0 dopuszczalnych w każdym modelu.**

## §R4. Litera, dwell i liga dźwigni

- **Stałe** (`r03/controllers/akw_scan.py:38-42`): krok 40.0, slew 60.0, stare 1.2, dwell 2.0;
  „parametry kroku/stare BEZ env — zmiana wartości = ANEKS" (akw_scan.py:30-32);
  `AKW_DWELL_S` tylko diagnostycznie, driver bramkowy odmawia (akw_scan.py:30, PRE_AKW.md:42-44).
- **Po co dwell 2.0 s — litera:** „okno odzysku REFRESH przed odkręceniem nosa; θ_age 3.0 −
  TRACK_LOSS 1.0" (PRE_AKW.md:39-40; akw_scan.py:14-15). θ_age = 3.0 (`r02/config_r02.py:52`),
  TRACK_LOSS_S = 1.0 (`r03/controllers/net_controller.py:35`). Dwell chroni **re-akwizycję po
  utracie**: nos czeka tam, gdzie cel był. „Pierwsze wejście w hold w epizodzie: dwell liczy się
  tak samo" (PRE_AKW.md:41-42) to wybór uproszczenia, nie kontrakt bezpieczeństwa. Na starcie
  epizodu ψ_last = 0 (akw_scan.py:22-23; reset), więc dwell nie trzyma żadnej informacji o celu.
- **Interakcja z kwarantanną FANTOM** (`fantom_scan.py:14-23`): wyjście K1 = (A) invalid→valid,
  (B) skok trk > 5 m, (C) T_q = 3.0 s. Predykaty zależą od feedu, nie od yaw. W kwarantannie
  delegat widzi „brak tracku", więc hold → dwell → skan biegnie od t0. Krótszy dwell na starcie
  przyspiesza (B), bo kamera wcześniej widzi realny cel, i **nie łamie żadnego predykatu
  literą**. Kontrola c08 (cel w stożku od t0): fresh 0.02–0.73 s we wszystkich 16 epizodach
  bearing 0 (c00/c04/c08) @14.7 Hz, a cel zostaje w stożku 43.45/60 = 0.72 s rampy po dwell, więc dwell 1.0 s
  wystarcza z zapasem.
- **Reguła ANEKS_AKW-1 §5 przeliczona na nową kadencję:** ω_safe = 0.85·κ₉₀·f. Przy κ₉₀ = 2.1°/kl
  (ANEKS_AKW-1:57,63) i f = 14.7 Hz ω_safe = 26.2°/s ≥ 14, więc ta sama reguła wybrałaby dziś
  **ścieżkę I (ciągłą)**, ω ≤ 30°/s. κ₉₀ w sensie litery (≥ 90% per klatka) nie da się zmierzyć
  z danych przed akwizycją, bo selekcja zaniża frakcję. `r4_kappa.json`: koincydencja per klatka
  przy celu w stożku, przed akwizycją: bez wiatru 0.24/0.13/0.25/0.46/0.38 dla 0–1/1–2/2–3/3–4/4–5
  °/kl i **0.00 przy 7–12 °/kl**. Sufit obrotu przy 14.7 Hz to ~5°/kl ≈ 73°/s.
- **Liga dźwigni (wrapper):** NOWY plik, np. `r03/controllers/skan2_scan.py` (`net_skan2`), nad
  `FantomScan`, wpis rejestru additive w `r03/controllers/__init__.py` (SR-9, wzór net_akw/
  net_fantom). **Musi:** (1) w fazie hold nadpisać `yaw` własnym profilem (krok/stare/slew) przez
  WSZYSTKIE ticki hold, z własnym ψ_last (wewnętrzny ψ_last AkwScan staje się nieistotny, bo
  wrapper nadpisuje każdy tick hold); (2) **dwell 1.0 s wyłącznie przy pierwszym hold epizodu**
  (po `reset()`), a **2.0 s po utracie** (litera PRE_AKW: okno odzysku REFRESH zostaje); (3) poza
  hold pass-through cmd bez zmian (test bajtowy jak AkwScan/FantomScan); (4) telemetria
  kwarantanny `q_*` przechodzi nietknięta. **Nie wolno:** akw_scan.py, fantom_scan.py,
  percepcji, admisji (`r02/*`, `harness/feed_vision*.py`, percep_proc), pinów/profilu OPS,
  sędziego, bench_flight ani manifestu.

## §R5. Ryzyka z danych

- **(a) Udział rampy:** w kombinacjach dopuszczalnych rampa to 62–74% cyklu (dziś 36%). Według
  §R1/§R4 to nie koszt, tylko miejsce, gdzie admisja zachodzi. Ryzyko: przy > 5°/kl koincydencja
  spada do 0, a rampa 60°/s @14.7 Hz to ~4°/kl. Przy spadku kadencji (sonda OPS FAIL) rampa
  wypada z reżimu, dlatego OPS jest warunkiem wejścia.
- **(b) Fałszywe admisje** (`tools/skan2_r5_fp.py` → `r5_fp.json`): ENTRY przed akwizycją
  z |trk − GT|_xy > 3 m: (a) 1/5, (a′) bez wiatru 2/12, wiatr 2/24, 5 Hz 0/47. **Wszystkie 5 to
  cel prawdziwy z błędem zasięgu**, nie tło. Trzy przy GT 14.7–15.2 m z trackiem na 11.2–13.3 m
  (|trk − GT| 3.25–3.57 m; dwa w rampie, jeden w stare, akwizycja 0.07–0.33 s później).
  Dwa przy GT 2.6/3.7 m (strefa martwa, box ucięty, przeszacowanie do 8–9 m). **ENTRY na tle: 0
  w 104 epizodach.** Ryzyko nazwane do PRE: większy udział rampy oznacza więcej ENTRY z błędem
  zasięgu ~3.3–3.6 m na 15 m. Proponowany próg FP: 0 ENTRY z |trk − GT| > 5 m przy GT ≥ 5 m.
- **(c) Kontrole:** bearing 0 (c00/c04/c08, 16 epizodów): admisja w dwell 0.02–0.73 s, dwell 1.0 s jej nie dotyka.
  c10 (180°, dziś 8.74 s): przy 68.3/0.4/1.0 θ = 136.55°, więc 1 + T_rot(136.55) = 1 + 1.538·1 +
  68.25/60 = **3.68 s + O (0.64–1.64) ≈ 4.3–5.3 s**, czyli wcześniej. c11 (270°): θ = 226.55°,
  1 + 3·1.538 + 21.65/60 = 5.98 s + O ≈ **6.6–7.6 s** przy dh 7.4–8.4 m, w pasie i przed t\* 10.75–11.41 s.
  Chybienie pierwszego przejścia (1/7 bez wiatru) w nowym profilu kosztuje pełny obrót
  (~8.4 s), więc dla v=1.0 jest śmiertelne. Do PRE jako predykcja.

## §R6. Wycena i śmierci (propozycja dla PRE; predykcje zapisze CC)

- **Śmierć przy biurku literą §R6 (brak kombinacji w R3): ZASZŁA (A = 0).** Jeżeli CC trzyma
  literę, pozycja zamyka się aneksem za 0 bootów.
- **Jeżeli CC przeformułuje hipotezę na „admisja w rampie + krótki dwell startowy"** (B-kal = 7):
  - S1 = T6 (6 epizodów, 2 booty) + kontrole c08_s01/s02 i c10_s02 (1 boot) wrapperem
    `net_skan2`, profil **68.3° / 0.4 s / dwell startowy 1.0 s (2.0 po utracie)**, reżim OPS,
    sędzia 8ec0fcfb ze świadkiem; ≤ 8 bootów z doleceniami.
  - Kryterium: c11 (270°) ≥ 2/3 D6 PASS ∧ t_acq ≤ 10.0 s; c10_s02 t_acq ≤ 8.74 s; c08 bez
    regresji (t_acq ≤ 1.0 s); **0 ENTRY z |trk − GT| > 5 m przy GT ≥ 5 m**.
  - Śmierci w locie: c11 < 2/3 ∨ regresja kontroli ∨ FP ∨ chybione pierwsze przejście w ≥ 2/6 T6.
  - Zakres: **wyłącznie bez wiatru**; teza nie przenosi się na kanon wiatru (V-A3), bo z wiatrem
    0 dopuszczalnych.
- **Budżet:** S1 3–4 booty + dolecenia ≤ 8. Oczekiwane 4–5.

## Pliki (wyłącznie nowe)

`tools/skan2_r1.py`, `skan2_r1_agg.py`, `skan2_r2.py`, `skan2_r3.py`, `skan2_r3_kal.py`,
`skan2_r4_kappa.py`, `skan2_r5_fp.py`; `r1_zdarzenia_{stare,any}.json`, `r1_L.json`, `r2_S.json`,
`r3_tabela.json`, `r3_kalibracja.json`, `r4_kappa.json`, `r5_fp.json`.
Odtworzenie: `SKAN2_MODE={stare,any} skan2_r1.py r1_zdarzenia_<m>.json <boot>,<warstwa> …` (lista
warstw w docstringu) → `skan2_r1_agg.py` → `skan2_r3_kal.py` → `skan2_r3.py`; `skan2_r2.py`,
`skan2_r4_kappa.py`, `skan2_r5_fp.py` z tymi samymi bootami i warstwami.
