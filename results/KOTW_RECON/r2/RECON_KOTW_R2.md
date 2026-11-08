# RECON_KOTW_R2 — kotwice na obwodzie strefy (jedyna reformulacja KOTW) — STOP-KOTWR2

Egzekutor · 8.11.2026 · wykonanie PROMPT_KOTW_R2. **0 bootów, 0 SITL, 0 renderów, 0 treningu, 0 edycji istniejących
plików; nowe pliki wyłącznie `results/KOTW_RECON/r2/**`.** Bramka: ANEKS_KOTW-1 zacommitowany na `662293ae`
(commit `f4b01cfb`, byte-check bd5d3332 ✓, KSIĘGA §3 append-only). Narzędzia reconu 1 (`results/KOTW_RECON/tools/`)
importowane read-only lub przepisane w kopiach, bez bytecode'u w ich katalogu (porcelain `tools/` czysty).

## Raport płaski

- **Najgorsza przerwa orbity przy najlepszej konfiguracji:** R_a 32 m, n 6, φ0 = π/n, h 2 m (litera R1′: stożek ∧
  zasięg [3, 45] m) — **9.4 s** (c10_s02). Start ~0 s (max 0.06 s), kotwica widoczna w 87% orbity. Hipoteza
  geometryczna potwierdzona: obwód skraca najgorszą przerwę z 37–43 s (recon 1) do 9–15 s.
- **Kombinacje dopuszczalne w R5′: 0/576.** Najlepsza (ta sama geometria, OPT, 1 kotwica) domyka 33/48 komórek
  i start, ale najgorsza przerwa orbity nie domyka się w swojej komórce: ε_fix 2.50 + ε_b(9) 3.105 + Δ_D5 1.524 =
  7.12 > m 5.17. Dopuszczalny ε_fix to 0.54 m, a poprawka z obwodu ma 2.5 m. **Wąskim gardłem nie jest już czas,
  tylko jakość poprawki z 23–44 m** (zasięg najbliższej widocznej kotwicy w oknie: p5 23 / p50 29 / p95 44 m).
- **Dwie kotwice w kadrze naraz:** 35% orbity przy n 6 / R 32 (γ p50 60°), 5% przy n 4, 0% przy n 2. Para nie
  pomaga: usuwa błąd kursu, ale zostawia radialny błąd elewacyjny przy płytkiej depresji, a słaba geometria
  przecięcia go mnoży. Przy 30/35 m i γ 80° para daje 3.0 m (OPT). Najlepszy tryb „2” domyka 5/48 komórek.
- **R4′ jednym zdaniem:** w literalnym paśmie admisyjnym [5, 18] m przejęcia są **niemożliwe geometrycznie** (0 próbek
  w 24 geometriach — dron nie zbliża się do obwodu bliżej niż ~20 m w kierunku kamery). Koincydencja ≤ 5° z intruzem
  zachodzi jednak na 18–45 m w 0–8.3% próbek orbity. Gdyby noga żyła, bramka pozycji przewidywanej byłaby warunkiem
  PRE, bo pasmo [5, 18] m nie jest zmierzoną granicą detekcji.
- **Bias yaw −3° (zastrzeżenie reconu 1) rozdzielony: to NIE jest artefakt dopasowania czasu.** Opóźnienie z regresji
  przed cięciem jest niespójne co do znaku (−0.12…+0.15 s). Stały bias kursu estymatora przy zdrowym GNSS wynosi
  −0.6…−5.1°, jest prawdziwy i zostaje w budżecie: δψ_ZMIERZ = 5.8°.
- **Werdykt: ŚMIERĆ CAŁEJ NOGI** — prereg R6′ „zero kombinacji dopuszczalnych w R5′ ⇒ KOTW CLOSED W CAŁOŚCI”
  (ANEKS_KOTW-1 §2: trzeciego podejścia nie ma). Wycena PRE nie dotyczy.
- Diff-stat i porcelain: na końcu. Sygnał: **STOP-KOTWR2**.

## §R1′. Widoczność obwodu

`tools/kotw2_obwod.py` → `r1p_obwod_raw.json` (per konfiguracja × epizod), agregat w `r1p_obwod.json`. Źródła, ramki
i stożek jak w reconie 1 (`kotw_r1.py`; GT ENU z `trace.jsonl`, fazy z `demo.jsonl`, pin mono_cam f = 269.5 px,
edge ≥ 0.10).

**Konfiguracje:**
- kotwice: n ∈ {2, 4, 6} na okręgu R_a ∈ {32, 36} m, h ∈ {2, 4} m;
- azymut startowy φ0 ∈ {0, π/n} — prompt mówi „równomiernie”, a dla n 2 orientacja ma znaczenie, więc obie;
- razem 24 geometrie × 148 epizodów.

Widoczność = stożek ∧ zasięg [3, 45] m (litera). Jako czułość liczę też próg rozdzielczości f·W/D ≥ 10 px
(założenie reconu 1, niezmierzone).

| geometria | widoczna 1 / 2 kotwice (orbita) | start p50 / max [s] | orbita wewn. p50 / p95 / max [s] | zasięg najbliższej p5 / p50 / p95 [m] |
|---|---|---|---|---|
| R32 n6 φ½ h2 | 0.87 / 0.35 | 0.02 / 0.06 | 2.6 / 7.2 / **9.4** | 23.1 / 28.6 / 43.9 |
| R32 n6 φ0 h2 | 0.88 / 0.35 | 0.02 / 0.06 | 2.3 / 6.7 / 14.7 | 23.3 / 28.5 / 43.5 |
| R32 n4 φ0 h2 | 0.85 / 0.05 | 0.02 / 0.06 | 2.0 / 8.9 / 14.4 | 23.2 / 31.1 / 43.5 |
| R36 n6 φ½ h4 | 0.73 / 0.20 | 0.02 / 0.06 | 4.1 / 9.8 / 17.2 | 26.5 / 34.3 / 44.8 |
| R32 n2 φ0 h2 | 0.46 / 0.00 | 1.06 / 15.3 | 6.8 / 19.4 / 37.4 | 23.5 / 35.1 / 43.7 |

(Pełne 24 geometrie, tryb „2” i warianty progu w `r1p_obwod.json`.)

**Wnioski:**
- Start przestaje być problemem przy n ≥ 4: z centrum kamera pozioma widzi obwód na 30–35 m przy depresji ~15°.
- R 36 i n 2 wydłużają przerwy.
- **Z progiem 10 px obwód jest prawie bezużyteczny:** W 1 m jest użyteczne do 26.9 m, a zasięgi p50 wynoszą 29–35 m.
  Przy W 1 m 19–145 epizodów nie ma żadnego okna, przy W 0.5 m — wszystkie 148. Najlepsza kombinacja z progiem
  domyka 11/48 komórek.

Werdykt R5′ nie zależy od tego założenia, bo pada też bez progu.

## §R2′. Poprawka z obwodu — 1 i 2 kotwice

`tools/kotw2_r2r5.py` → `r2p_poprawka.json`.

**Model 1 kotwicy** = recon 1: e_lat = D·tan δψ + D·px/f; e_rad = min(rozmiar, elewacja); Δz = 12 − h.

**Model 2 kotwic (nowy):** zasięgi poziome do obu kotwic z e_rad każdej (bez członu kursu), pozycja z przecięcia
okręgów; ograniczenie ε2 = √(e_a² + e_b² + 2·e_a·e_b·|cos γ|)/sin γ. Kurs wynika z namiaru, więc pozycja i kurs są
obserwowalne razem i błąd yaw przestaje obracać namiar.

**Warianty błędów:**
- **OPT:** px 1, δψ 2°.
- **ZMIERZ:** px 2, δψ 5.8°.
- **ZMIERZ_h1.8:** jak ZMIERZ, δz 1.8 m.
- Wspólne założenia: δθ 0.5°, δz 0.2 m.

| D [m] (h 2, W 1) | 1 kotwica OPT / ZMIERZ / h1.8 | | pary (r_a/r_b, γ) | 2 kotwice OPT / ZMIERZ / h1.8 |
|---|---|---|---|---|
| 25 | 1.57 / 3.10 / 5.37 | | 20/25, 80° | 1.64 / 1.94 / 6.01 |
| 30 | 2.04 / 3.85 / 7.32 | | 25/30, 80° | 2.29 / 2.73 / 8.78 |
| 35 | 2.58 / 4.65 / 8.88 | | 30/35, 80° | 3.03 / 3.65 / 11.36 |
| 40 | 3.17 / 5.51 / 10.50 | | 30/35, 40° | 5.68 / 6.83 / 21.30 |
| 45 | 3.81 / 6.43 / 12.20 | | 35/40, 80° | 3.87 / 4.69 / 13.70 |

**Co daje para:**
- przy wariancie ZMIERZ para wygrywa z pojedynczą kotwicą tylko przy γ ≈ 80° (zysk ~1 m);
- przy γ 40° przegrywa;
- przy biasie wysokości przegrywa zawsze, bo elewacja jest jej jedynym źródłem zasięgu.

Częstość pary w kadrze: tabela R1′.

**Rozdzielenie biasu yaw** (`tools/kotw2_yaw.py` → `r2p_yaw.json`, 12 cięć S4). Zmiany względem reconu 1: heading
EKF interpolowany na chwile GT, ψ̇ z GT, regresja w 20 s przed cięciem: err = b + L·ψ̇.

| | zakres w 12 cięciach |
|---|---|
| L (opóźnienie) | −0.116…+0.147 s (znak niespójny ⇒ brak systematycznego artefaktu czasu) |
| b (stały bias kursu, GNSS zdrowy) | −0.61…−5.14° |
| residuum przed cięciem | −5.98…+2.22° |
| residuum w kontynuacji (err − L·ψ̇) | −5.81…+2.66°, max |·| = **5.81°** |

Wniosek: bias ~−3° to prawdziwy błąd kursu estymatora (obecny już przy zdrowym GNSS), a nie artefakt złączenia.
Poprawka z jednej kotwicy go dziedziczy, więc ZMIERZ używa δψ 5.8°. Mechanizm biasu nie jest mierzony w tym reconie.

## §R5′. Piła na obwodzie

`tools/kotw2_r2r5.py` → `r5p_pila.json`.

**Siatka:** 576 kombinacji = 24 geometrie × próg {brak, 10 px} × W {0.5, 1} × 3 warianty × tryb {1, 2}.

**Kryteria:**
- **Orbita:** per komórka najgorsza wewnętrzna przerwa orbity, ε_fix z poprzedzającego okna; warunek
  ε_fix + ε_b(τ) + Δ_D5 ≤ m_komórki (m z `r4_margin.json`). Komórka z epizodem bez okna nie domyka się.
- **Start:** przerwa od t0 do pierwszego okna, margines startu m_s = R_E 32 − D_STOP 2.85 − r_max(przerwa).
  ε_fix startu = ε pierwszego okna — przybliżenie, bo dane epizodowe nie niosą poprawki sprzed epizodu.
- **Dopuszczalna** ⇔ ≥ 24/48 komórek ∧ najgorsza orbita siatki domyka się w swojej komórce ∧ start domyka się
  we wszystkich epizodach.
- ε_b z `s2_freeze_bf.json` (×1.5 wliczone), τ ≥ 70 s ⇒ nie domyka.

**Wynik: 0/576 dopuszczalnych.** Rozkład warunków:

| ≥ 24 komórek | najgorsza orbita | start | kombinacji |
|---|---|---|---|
| ✗ | ✗ | ✗ | 397 |
| ✗ | ✗ | ✓ | 155 |
| ✓ | ✗ | ✓ | **14** |
| ✗ | ✓ | ✗ | 10 |

**14 „prawie dopuszczalnych”** — wszystkie bez progu px, tryb 1. W nie ma tu wpływu, bo zasięg radialny bierze się
z elewacji.

| geometria | wariant | komórki | najgorsza orbita (komórka, τ, ε_fix, ε_b, m) | suma | dopuszczalny ε_fix |
|---|---|---|---|---|---|
| R32 n6 φ½ h2 | OPT | 33/48 | c10_s02, 9.4 s, 2.50, 3.105, 5.17 | 7.12 | 0.54 |
| R32 n4 φ0 h2 | OPT | 31/48 | c09_s04, 14.4 s, 2.15, 3.478, 5.37 | 7.15 | 0.37 |
| R32 n4 φ0 h4 | OPT | 31/48 | c09_s04, 13.9 s, 2.46, 3.478, 5.37 | 7.46 | 0.37 |
| R32 n6 φ0 h2/h4 | OPT | 31/48 | c03_s04, 14.7 s, 1.36/1.51, 3.478, 4.55 | 6.36/6.52 | **< 0 (−0.45)** |
| R32 n6 φ½ h4 | OPT | 27/48 | c08_s04, 11.0 s, 1.66, 3.478, 3.07 | 6.67 | **< 0 (−1.93)** |
| R32 n4 φ0 h4 | ZMIERZ | 24/48 | c09_s04, 13.9 s, 4.21, 3.478, 5.37 | 9.21 | 0.37 |

(każdy wiersz ×2 dla W 0.5/1.)

**Zdanie śmierci:**
- Przy najlepszej konfiguracji obwodu najgorsza przerwa orbity (9.4 s) zostawia na poprawkę 0.54 m, a poprawka
  z 23–44 m ma 2.5 m nawet w wariancie optymistycznym — przekroczenie 4.6×.
- W trzech z siedmiu geometrii z ≥ 24 komórkami najgorsza komórka nie domyka się nawet przy poprawce idealnej
  (ε_b(11–14 s) + Δ_D5 > m 3.07–4.55).

## §R4′. Ryzyko przejęcia tracku

`tools/kotw2_obwod.py` (pole `r4`) i `tools/kotw2_r4_szersze.py` → `r4p_pasma.json`. Intruz z `gt_intruder.jsonl`
(`ned` → ENU, złączenie ≤ 0.1 s, 353 949 próbek w R32 n6 φ0 h2). Filtr-świadek |ned − cmd| > 1 m: 0 trafień do
odfiltrowania.

| pasmo zasięgu kotwicy | odsetek próbek orbity z kotwicą w stożku ≤ 5° od intruza |
|---|---|
| [5, 18] m (litera R4′) | **0.0 we wszystkich 24 geometriach** |
| (18, 30] m | 0.0000–0.0203 (max R32 n6 φ½ h4) |
| (30, 45] m | 0.0161–0.0832 (max R32 n6 φ½ h2) |

**Mechanizm zera:** dron nie oddala się od środka dalej niż ~23 m (r_max p50 komórek 23.4), więc kotwica w stożku
jest zawsze ≥ 19.9 m od kamery. Koincydencje kątowe istnieją (kąt min p5 3.5° w r2_V2), ale dalej niż 18 m.

**Warunek PRE, gdyby noga żyła:** pasmo [5, 18] m pochodzi z promptu, a nie z pomiaru detekcji. DET3 zmierzył
detektor do 14.9 m, a powyżej korpusu nie ma klatek, więc zachowania det_v2 na 18–45 m nie znamy. Bramka pozycji
przewidywanej dla odświeżenia tracku (`harness/feed_vision.py:202`, nowy wrapper poza kanonem) byłaby warunkiem PRE.

## §R6′. Wycena i śmierci

**Prereg:** zero kombinacji dopuszczalnych w R5′ ⇒ **KOTW CLOSED W CAŁOŚCI — ZACHODZI (0/576).** Wycena etapów
S1–S4 nie dotyczy.

**Mechanizm całej nogi** (oba reconu razem):
- **Kotwica w środku:** przegrywa czasem — przerwy 37–43 s, bo kamera patrzy na zewnątrz.
- **Kotwice na obwodzie:** przegrywają dokładnością — 23–44 m przy płytkiej depresji.
  - Jedna kotwica: błąd kursu estymatora (≤ 5.8°) × zasięg.
  - Dwie kotwice: błąd elewacyjny × słaba geometria przecięcia.
- Budżet 5.79 m (p50) minus Δ_D5 1.524 zostawia na sumę ε_fix + ε_b(τ) ≤ 4.27 m. Żadne miejsce kotwicy osiągalne
  dla poziomej kamery nie daje jednocześnie krótkiej przerwy i bliskiego zasięgu.

## Pliki

- `RECON_KOTW_R2.md` (ten raport).
- `r1p_obwod_raw.json` (8.6 MB) i `r1p_obwod.json` (agregat R1′ + R4′).
- `r2p_poprawka.json`, `r2p_yaw.json`, `r4p_pasma.json`, `r5p_pila.json`.
- Narzędzia w `tools/`: `kotw2_obwod.py`, `kotw2_yaw.py`, `kotw2_r2r5.py`, `kotw2_r4_szersze.py`.

Odtworzenie (z korzenia repo, `PYTHONDONTWRITEBYTECODE=1`):

```
python3 results/KOTW_RECON/r2/tools/kotw2_obwod.py results/KOTW_RECON/r2/r1p_obwod_raw.json "FANTOM_S2=results/FANTOM/camp/r*" "PERC2_S2=results/PERC2/s2/b*" "SKAN2_S1=results/SKAN2/s1/b*" "KONT_S4=results/KONT/s4/[cn]*"
python3 results/KOTW_RECON/r2/tools/kotw2_yaw.py results/KONT/s4/c0[1258]_s0? results/KONT/s4/c1[01]_s0? results/KONT/s4/c08_s01_r2 > results/KOTW_RECON/r2/r2p_yaw.json
python3 results/KOTW_RECON/r2/tools/kotw2_r2r5.py results/KOTW_RECON/r2
python3 results/KOTW_RECON/r2/tools/kotw2_r4_szersze.py results/KOTW_RECON/r2/r4p_pasma.json "FANTOM_S2=results/FANTOM/camp/r*" "PERC2_S2=results/PERC2/s2/b*" "SKAN2_S1=results/SKAN2/s1/b*" "KONT_S4=results/KONT/s4/[cn]*"
```

## Diff-stat i porcelain

```
 results/KOTW_RECON/r2/RECON_KOTW_R2.md          |   ~215 +
 results/KOTW_RECON/r2/r1p_obwod.json            |   3390 +
 results/KOTW_RECON/r2/r1p_obwod_raw.json        |      1 +  (8.6 MB, jeden wiersz)
 results/KOTW_RECON/r2/r2p_poprawka.json         |    568 +
 results/KOTW_RECON/r2/r2p_yaw.json              |    422 +
 results/KOTW_RECON/r2/r4p_pasma.json            |    218 +
 results/KOTW_RECON/r2/r5p_pila.json             | 197252 +  (576 kombinacji × 48 komórek)
 results/KOTW_RECON/r2/tools/kotw2_obwod.py      |    190 +
 results/KOTW_RECON/r2/tools/kotw2_r2r5.py       |    184 +
 results/KOTW_RECON/r2/tools/kotw2_r4_szersze.py |     52 +
 results/KOTW_RECON/r2/tools/kotw2_yaw.py        |     45 +
 11 plików, wyłącznie nowe; 0 linii usuniętych; żaden istniejący plik nie zmieniony
```

Porcelain przed commitem: `?? results/KOTW_RECON/r2/` plus zastane `??` results/DEMO_C/**; `results/KOTW_RECON/tools/` czysty (bez `__pycache__`).

**STOP-KOTWR2.** Push = Olga („wypchnięte” — CC przelicza niezależnie R1′ i R5′). Potem CC: aneks zamykający KOTW
w całości (prereg) albo PRE_KOTW, gdyby przeliczenie dało ≥ 1 kombinację dopuszczalną.
