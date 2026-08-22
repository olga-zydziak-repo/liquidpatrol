# ERRATUM_42M — „AUTO.LAND ucieka 42 m" była asercją, nie pomiarem

PRE_K1 §0 · 2026-08-22 · pierwszy commit buildu K1 (przed jakimkolwiek bootem i przed hashem sędziego).
Podstawa: RAPORT_K1_AUDIT.md (`2bd76d9`). **Nic nie jest kasowane; tagi v1.0/v3.x nietknięte.**

## 1. Co

Liczba **„AUTO.LAND flyaway = 42 m pod utratą GNSS"** była w repo cytowana jako **pomiar**. Audyt K1
wykazał, że to **asercja z 2026-08-09 bez zachowanego biegu**: nie ma kodu wariantu `action.land`,
nie ma trace, nie ma ulogu. Źródło pierwotne = nota `FINDING_clock_and_regime.md:97` + komentarz
`b1bis_fly.py:118`. Maks. promień w JAKIMKOLWIEK zachowanym śladzie = **38.1 m** (`f5_corner`, lot
zejścia prędkościowego, który `action.land` UNIKAŁ) — czyli nie jest to bieg 42 m. Szczegóły: RAPORT_K1_AUDIT §1–§3.

## 2. Gdzie (inwentarz cytowań — 16 miejsc zaadnotowanych in-place)

Każde poniższe miejsce dostało w kodzie/tekście adnotację:
> ERRATUM_42M (PRE_K1 §0): „42 m" asserted 09.08, run not preserved — superseded by K1 measurement (PRE_K1).

| plik:linia | rola |
|---|---|
| `results/R03/recon/B1bis/instrument/FINDING_clock_and_regime.md:97` | **źródło pierwotne** (asercja) |
| `results/R03/recon/B1bis/b1bis_fly.py:118` | **źródło pierwotne** (komentarz uzasadniający porzucenie `action.land`) |
| `acts/A3_spec.yaml:39` (`auto_land_flyaway_m: 42.0`) | **stała-korzeń** renderowana na planszę |
| `acts/A3_spec.yaml:32` | komentarz spec |
| `tools/gen_subtitles.py:254` | render `flyaway=cp.get("auto_land_flyaway_m")` → szablon `:60` |
| `PRE_D.md:44`, `PRE_D.md:186` | plansza kontrastu / PROVED |
| `PRE_R03A.md:287`, `:294`, `:327` | uzasadnienie wykluczenia AUTO.LAND |
| `RAPORT_R03A.md:96`, `:133` | „ZNALEZISKO KRYTYCZNE" / OBALONE |
| `RAPORT_D_B2.md:50`, `RAPORT_D_B3.md:58`, `:75` | plansza kontrastu / test guard |
| `r03/config.py:35` | komentarz listy komend osłony |

**Artefakty generowane (nie adnotowane ręcznie, regenerowane w §6 per §0.3):**
`results/demo/rehearsal/A3/**/planszas.json` (m.in. `proba_1/planszas.json:40` „flyaway 42.0 m"),
oraz montaże `DEMO_B_*` z planszą CONTRAST. Zostają jako są do §6; wtedy regenerowane z liczbą zmierzoną.

RAPORT_K1_AUDIT.md **nie jest adnotowany** — to sam audyt, opisuje „42 m" poprawnie jako asercję.

## 3. Dlaczego przeszło (mechanizm defektu)

Plansza CONTRAST renderuje dwie liczby: `td` (touchdown) — czytane z **wyniku biegu** — oraz
`flyaway` — czytane ze **stałej w spec** `acts/A3_spec.yaml: contrast_plansza.auto_land_flyaway_m: 42.0`
(`tools/gen_subtitles.py:254` → szablon `:60`). Guard `test_gen_subtitles.py::…contrast…` (i teza
`contrast_number_from_spec_not_hardcoded`, `RAPORT_D_B3:75`) sprawdzał tylko, że liczby **nie ma
w SZABLONIE** — a więc przeniesienie stałej z szablonu do spec **przechodziło test**, mimo że spec
to nadal nieźródłowana stała, nie odczyt z pliku wyników z identyfikatorem biegu. Innymi słowy:
antyhardcode-guard mierzył lokalizację stałej, nie jej **prowieniencję**.

## 4. Reguła naprawcza (obowiązuje od teraz)

1. **Liczby na planszach pochodzą wyłącznie z plików wyników z identyfikatorem biegu (`source_run`),
   nigdy ze stałych w kodzie/spec ani z szablonu.**
2. **Generator plansz dostaje asercję: każda liczba renderowana na planszę ma pole `source_run`**
   (id biegu + ścieżka pliku wyniku). Brak `source_run` ⇒ generator odmawia renderu liczby.
3. Egzekucja asercji w generatorze **oraz** re-montaż planszy CONTRAST z liczbą zmierzoną —
   **dopiero w §6** (per §0.3: jeden montaż, z liczbą z pomiaru K1, nie z pustym miejscem).
   Do §6 stała `42.0` pozostaje w spec (nic nie kasujemy), oznaczona jako superseded.

## 5. Status w roszczeniu (do §6)

Do czasu pomiaru K1 (§2–§4 PRE_K1) **nie cytować „42 m" jako zmierzonej liczby**. Dozwolone brzmienie
opisowe: „natywny AUTO.LAND pod utratą GNSS ucieka poziomo (mechanizm: position-hold na dryfującej
estymacie, potem blind-land coasting); dokładna figura zostanie zmierzona w K1". Po §6 asercja zostaje
zastąpiona liczbą `x_exc`/`r_max` z identyfikatorem biegu.
