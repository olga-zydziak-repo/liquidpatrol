# PRE_WK4 — prerejestracja nogi WK-IV „turbulencja i sufit wiatru": NCP-20 na kamerze pod turbulencją o widmie Drydena i pierwsza średnia wiatru, przy której misja pada

CC · 31.10.2026 · po STOP-WK4R (1f61bc1b), zweryfikowanym z repo wykonaniem.
Wymaga ratyfikacji Olgi; po niej PROMPT_WK4_S1 — na start DWA dokumenty.
**Ostatnia noga wiatrowa programu: każdy z werdyktów §3 zamyka kanon wiatru.**

**Weryfikacja reconu (CC, z repo):** zakres czysty (175 nowych plików, zero
delecji); pięć serii odtworzonych z sha; moja własna walidacja daje co do
liczby to samo, co recon (D2: σ/cel 0.865 · 0.866 · 1.037, czasy 1/e 19.2 /
16.4 / 5.1 s, f90 0.04 / 0.06 / 0.28 Hz; D6: 0.971 · 0.888 · 0.985; P2 WK-III
σx 1.06, f90 0.25 Hz). **Dodatek CC:** w oknie faktycznie latanym (próbki
70–390 s pliku, czyli t_sim 110–430) σ zrealizowane są jeszcze niższe niż na
całym pliku (D2: u 0.79 · v 0.70 celu) — to jest powód, dla którego literą
turbulencji w tej nodze jest PLIK, a nie cel normy. Oba booty nauczyciela
przesędziowane sędzią bazowym 8ec0fcfb: **D6 pełny i ze świadkiem 4/4 i 4/4**
(D6: c06_s01 d_min 4.49 w pełnym vs 7.71 ze świadkiem — glitch GT, przypadek
ERRATUM-DMIN); opór z własnej regresji na (w(t) − v): **0.497 / 0.498 /s**
(recon 0.496 / 0.4975), habitat bez zmian. **Przyczyna ryzyka V2′ znaleziona
w sygnaturze, nie w źródle:** w obu bootach symulacja ZAMIERA 14 razy po
2.1–2.5 s czasu ściennego, co ~32 s czasu symulacji (pierwsze zacięcie przy
t_sim 5.0, przed uzbrojeniem), łącznie ~31 s na boot ⇒ dsim/dwall 0.93; PX4
loguje 14× „timesync: time jump detected" wobec 2× w bootach WK-III; log
publikatora nie ma luk w t_sim (publikator nie jest ofiarą — jest podejrzanym
albo świadkiem). Źródła nie znam; w WK-III epizody sieci z percepcją miały
V2′ 0.92–0.95, więc **z tym zacięciem S1 nie może wystartować** (§2 B0).

## §1. Teza i pytania (FROZEN)

Teza Olgi: **mała sieć umie latać.** Po WK-III wolno mówić „pod wiatrem
zmiennym o znanym profilu, nie turbulencją". Ta noga pyta o dwie rzeczy
i o nic więcej:

- **Q1 (D2):** turbulencja o widmie Drydena (forma niskiej wysokości, jedna
  zamrożona realizacja) przy średniej kanonu 2 m/s — czy zdanie „turbulencja"
  wolno wypowiedzieć. D2 jest w σ poziomym ~3× łagodniejsze od P2 i wolniejsze
  (90 % mocy poniżej 0.06 Hz); nowe są pion (σ_z 0.21 m/s) i brak okresowości.
  Nie wolno sugerować, że D2 jest „ostrzejsze" od P2.
- **Q2 (drabinka D3…D6, ta sama realizacja szumu, intensywność ∝ średniej):**
  pierwsza średnia Ū, przy której D6 sieci ≤ 4/8 — **sufit misji z liczbą
  i mechanizmem**. Drabinka kończy się na 6 m/s: jeśli sufit leży wyżej, noga
  mówi „> 6 m/s" i nie goni dalej.
- **Ramię odniesienia:** nauczyciel (egzekutor, feed emulowany) 4/4 przy D4
  i D6 z reconu; na szczeblu sufitu, jeśli nie jest to D4/D6 — ≤ 2 booty
  nauczyciela w S1. Nauczyciel padający na szczeblu ⇒ sufit płatowca/kamery.

## §2. Projekt (FROZEN)

- **Turbulencja = pliki:** `results/WK4_RECON/series/D2…D6.json` z sha
  6e09f653 · df2369db · a4c085f9 · caa10794 · 673e09e1 (pełne w `.sha256`
  obok), ziarno 20261030, 20 Hz, t_off 40 s, próbka wg floor((t_sim−40)/0.05).
  Litera cytowania to σ ZREALIZOWANE w oknie lotu (u · v · w, m/s): D2 0.30 ·
  0.27 · 0.21; D3 0.49 · 0.44 · 0.30; D4 0.69 · 0.61 · 0.40; D5 0.90 · 0.78 ·
  0.50; D6 1.09 · 0.95 · 0.60; cel normy (σ_w = 0.1·Ū, σ_u,v = 1.89·σ_w)
  podaje się jako cel projektowy, nie jako roszczenie. Jedna realizacja na
  szczebel; oba booty szczebla lecą tę samą realizację z innymi komórkami.
  Żadnej regeneracji serii w nodze.
- **Świat:** `worlds/world_wk4.sdf` 7acf407ff97e71ef10ce9cad15a12aa591e195703b6360c194d9560f3eedd1b1
  (s063, wiatr bazowy 0, `time_for_rise` 0.01 w horizontal i vertical, bez
  `<sin>`/`<noise>`). **Publikator** `wk4_publisher.py` 746a958b (sha z
  manifestu n_D6) — chyba że B0 wymusi wersję 2 (wtedy nowy plik, nowe sha,
  determinizm dowiedziony ponownie, §2 B0).
- **Driver:** NOWY `results/WK4/tools/wk4_boot.sh` = kopia `wk3_boot.sh`
  039e368c + hunki H3/H4/H5/H6 drivera reconu (świat i seria z pełnym sha,
  profil jako argument, publikator przed `run_boot` z oczekiwaniem na %CPU
  i serwis scene/info, kill po locie, blok `wk4` w manifeście) + sprzątanie
  dzieci `run_boot` przed uzbrojeniem (lekcja n_D4b). Piny mono_cam 3354ae1e,
  x500_base 13c9174d, profil a68a450b, sonda 8df528bb bez zmian. Pełny diff.
- **Konfiguracja:** net_fantom (rejestr 87203d29), NET_ARM=ncp, FEED=V2,
  INTRUDER=1, sonda kadencji PASS przed uzbrojeniem, **V2′ ≥ 0.90 bez zmian**.
- **Siatka:** c00–c07 × s01, 8 epizodów na szczebel (4 na boot).
- **Kontrola oporu per boot:** regresja bilansu sił na (w(t) − v) z pliku
  serii (metoda reconu / CC); odchylenie > 20 % od 0.494 ⇒ STOP do adjudykacji.
- **B0 — bramka budowy PRZED pierwszym lotem sieci (obowiązkowa):**
  1. Diagnoza zacięć w gołym gz (0 bootów), z próbnikiem czasu ściennego
     i symulacji: (i) `world_wk4` + publikator 20 Hz; (ii) `world_wk4` bez
     publikatora; (iii) `world_wk3_p2` + sam subskrybent zegara w Pythonie;
     (iv) publikator bez pliku logu; (v) publikator napędzany `/stats` zamiast
     `/clock`. Kryterium „zacięcie": ≥ 1 s czasu ściennego przy przyroście
     czasu symulacji < 0.1 s. Przebiegi po ≥ 150 s.
  2. Jeśli trzeba, PX4 bez uzbrojenia (≤ 3 próby, nie liczą się do budżetu
     bootów, każda nazwana) — sygnatura w px4.log: „time jump detected".
  3. Usunięcie przyczyny; każda zmiana publikatora = nowy plik z sha
     i ponowny dowód determinizmu (dwa starty, max |Δw| ≤ 0.02 m/s) i zgodności
     odtworzenia (σ ±10 %, opóźnienie ≤ 0.1 s) na sondzie.
  4. **Boot kontrolny** (nauczyciel, D2, c00/c04/c06/c04_s02; liczony do
     budżetu): **dsim/dwall ≥ 0.98 w 4/4 epizodach ∧ ≤ 2 zacięcia > 1 s
     w całym boocie ⇒ GO.** Inaczej **STOP-WK4-RTF**: raport z A/B,
     decyzja Olgi (lot z ryzykiem progu 0.90 albo zamknięcie nogi bez lotów
     sieci). Próg V2′ nie jest ruszany pod żadnym pozorem.
- **Kolejność (sekwencyjna):** B0 → **D2** (2 booty) → bramka ≥ 6/8 ⇒ **D6**
  (2 booty) → D6 ≤ 4/8 ⇒ **D4** (2 booty) → bisekcja: D4 ≥ 5/8 ⇒ D5, D4 ≤ 4/8
  ⇒ D3 (2 booty). D6 ≥ 5/8 ⇒ sufit „> 6 m/s", drabinka zamknięta. D2 < 6/8 ⇒
  STOP, V-C4, drabinka nie leci.
- **Sędzia:** bazowy 8ec0fcfb, werdykty ze świadkiem ERRATUM-DMIN i bez;
  bramki ze świadkiem; rozjazd rozstrzygający ⇒ STOP do adjudykacji CC.
- **Epizod nieważny V2′:** jednorazowe dolecenie, liczone do budżetu.
- **Mechanizm każdej porażki — obowiązkowa etykieta z danych:** AKWIZYCJA
  (t_entry > 25 s albo brak toru do wejścia w pas), TRACK (tor utracony po
  wejściu, przed końcem okna), ORBITA (tor trzymany, sweep < 630° lub frakcja
  pasma < 0.85), NASYCENIE (komenda na |v| = 3.0 m/s > 20 % ticków okna),
  BREACH. Obok: kadr — frakcja ticków z celem poza kadrem (geometria GT)
  i czy poprzedza utratę toru.

## §3. Osłona, STOPy, werdykty

- Twarde STOPy verbatim: **breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.**
  Fałszywy REFUSE(GEOFENCE) ⇒ STOP; prawdziwy = epizod ważny, D6 FAIL, liczony
  osobno; ≥ 3 prawdziwe na szczeblu ⇒ STOP.
- **Ryzyko nazwane 1 (zacięcia V2′):** rozstrzyga B0, nie lot sieci.
- **Ryzyko nazwane 2 (przechył):** nauczyciel przy D6 miał p95 24–27°, max
  37.5°, pion ±2 m/s; wypadanie dołem zaczyna się statycznie od ~8 m/s, ze
  szczytem porywu od ~5–6 m/s przy r ≤ 8 m. Utrata celu z kadru jest WYNIKIEM
  (mechanizm „kamera sztywna"), nie artefaktem.
- **Werdykty (prereg):**
  - **V-A4** (D2 ≥ 6/8 ∧ drabinka rozstrzygnięta): „NCP-20 prowadzi pełną
    misję na własnej kamerze pod turbulencją o widmie Drydena (jedna
    deterministyczna realizacja, σ zrealizowane u·v·w = …) przy średniej
    2 m/s: D6 a/8. Sufit misji w tej drabince: pierwsza średnia z D6 ≤ 4/8 to
    Ū_c = X m/s (D6 b/8; szczebel niżej c/8), mechanizm porażek: …;
    nauczyciel na szczeblu sufitu d/4. Habitat k ≈ 0.49 /s, komórki v ≤ 0.5."
    Wariant „> 6 m/s", gdy D6 ≥ 5/8.
  - **V-B4** (D2 ≥ 6/8 ∧ drabinka nierozstrzygnięta budżetem/STOP-em):
    „turbulencja przy 2 m/s: a/8; sufit ≥ X m/s (ostatni zdany szczebel)".
  - **V-C4** (D2 < 6/8): „turbulencja łagodna przy średniej kanonu łamie
    misję: a/8" + mechanizm; drabinka nie leci.
  - **STOP-WK4-RTF** (B0 nie przeszło): noga bez lotów sieci; decyzja Olgi.
  - Każdy werdykt zamyka nogę I wątek wiatru; brak nowych pozycji katalogu
    z tej nogi.
- **Pomiary opisowe:** sweep/stock per scenariusz (baza FANTOM S2 ze
  świadkiem) i wobec P2; przechył p50/p95/max w oknach epizodów; cel poza
  kadrem; czas akwizycji; frakcja ticków z komendą na vmax; k per boot;
  residuum wiatru odtworzonego z drona wobec pliku (p50/p95).

## §4. Predykcje CC (do KSIĘGI)

- **P-WK4-1 (0.80):** D2 ≥ 7/8.
- **P-WK4-2 (0.55):** D6 ≤ 4/8 (sufit w drabince, nie ponad nią).
- **P-WK4-3 (0.70):** D4 ≥ 5/8.
- **P-WK4-4 (0.65):** ≥ 2/3 porażek sieci w całej drabince ma etykietę
  AKWIZYCJA lub TRACK, nie ORBITA/NASYCENIE.
- **P-WK4-5 (0.60):** przyczyna zacięć leży po stronie publikatora/transportu
  (wariant (ii) B0 bez publikatora jest wolny od zacięć, wariant (i) nie).
- **P-WK4-6 (0.70):** nauczyciel na szczeblu sufitu 4/4 (sufit sterownika lub
  percepcji, nie płatowca).
- **P-WK4-7 (0.90):** breach 0.

## §5. Budżet, higiena, cytowanie

**Budżet twardy: ≤ 12 bootów** (B0 kontrolny 1 + D2 2 + D6 2 + bisekcja 4 +
dolecenia/nauczyciel na szczeblu sufitu ≤ 3); oczekiwane 7–9. Próby bez
uzbrojenia (świat/stack nie wstał) nie liczą się do budżetu, liczą się do
higieny: każda nazwana w raporcie. 1–2 sesje + CO. Env `WK4_*`, katalog
`results/WK4/`, nowe pliki wyłącznie: driver, narzędzia, ewentualny
publikator v2. ZERO edycji istniejących plików (serie, świat, recon
nietykalne); REPO-1/REPO-2, proc_gate, cooldown. Cytowanie zdaniami z §3
z literą pliku (ziarno, σ zrealizowane, okno) i „widmo Drydena, forma niskiej
wysokości, jedna realizacja, V = Ū, W₂₀ = Ū". Od tej nogi wolno: „turbulencja
symulowana o nazwanym widmie". Nadal nie: „odporna na wiatr", nic o realnym
sprzęcie, nic o turbulencji ponad zmierzony sufit.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
