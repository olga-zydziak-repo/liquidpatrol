# ANEKS_WK4-0 — zamknięcie nogi WK-IV „turbulencja i sufit wiatru" decyzją przed lotami sieci (B0 w gołym gz wykonane, przyczyna zacięć ustalona: zegar ścienny WSL) + zamknięcie wątku wabikowego decyzją (CO-WK4-0)

CC · 31.10.2026 (wersja 2, po STOP-CO-WK4-0 egzekutora) · łańcuch WK4 (na
origin: 1f61bc1b STOP-WK4R, 1c0e1643 PRE_WK4 ARCH-1). Aneks zamykający,
samowykonalny (§5): zero bootów wydanych, zero do wydania; sesja CO deskowa.
PROMPT_WK4_S1 traci ważność — sygnały STOP-WK4-1 i STOP-WK4-RTF nie wystąpią.
Sygnały bez numeru odrzucasz.

## §1. Stan faktyczny

- Recon WK-IV (STOP-WK4R) przyjęty po weryfikacji CC z repo wykonaniem: serie
  Drydena D2…D6 przeliczone niezależnie co do liczby (σ, czasy korelacji,
  pasma; w oknie lotu σ niższe niż na całym pliku), oba booty nauczyciela
  przesędziowane sędzią bazowym 8ec0fcfb — D6 pełny i ze świadkiem 4/4 przy
  D4 i 4/4 przy D6, opór z własnej regresji 0.497 / 0.498 /s; droga A (wiatr
  z topiku `/world/<W>/wind`, publikator sterowany czasem symulacji) działa
  i jest deterministyczna (max |Δw| 0.0016 m/s).
- PRE_WK4 ratyfikowany 31.10 i w repo verbatim (1c0e1643, sha a530ebb5…1891).
- **B0 wykonane częściowo, w gołym gz (31.10, 00:21–00:55; bez PX4, bez lotów
  sieci; pliki nieśledzone w `results/WK4/` do czasu CO — wg raportu
  egzekutora STOP-CO-WK4-0, CC weryfikuje z repo po pushu):** A/B (i)–(iv)
  z PRE §2 B0 z próbnikiem zacięć (`tools/wk4_b0_ab.sh`, `tools/wk4_zaciecia.py`)
  oraz diagnostyka zegara (`zegar_realtime_vs_monotonic.txt`,
  `zegar_gz_mono_vs_real.txt`, `host_pauza_bez_gz.txt`, `diag_rownolegle.txt`).
  Etap PX4-bez-uzbrojenia i boot kontrolny: **nieodbyte**.
- **Zero bootów sieci, zero B0 z PX4.** Decyzja Olgi 31.10: zamknąć nogę bez
  lotów. Powód jest programowy, nie techniczny: materiał programu idzie na
  zewnątrz 1.11, a WK-IV zmieniłby w nim jedno zdanie, którego raport nie
  potrzebuje.

## §2. WERDYKT: WK-IV CLOSED-BY-DECISION przed lotami sieci; kanon wiatru zostaje na V-A3

- Noga zamknięta kosztem **0 bootów sieci** (2 booty nauczyciela reconu
  rozliczone w RECON_WK4; 2 próby bez uzbrojenia nazwane tam i naprawione;
  B0 w gołym gz = sondy, nie booty).
- **Kanon wiatru programu = V-A3 (ANEKS_WK3-1 §2)** bez zmian: wiatr zmienny
  w czasie z porywami do 3.6 m/s i obrotem kierunku ±30°, habitat k ≈ 0.49 /s,
  P1 8/8 · P2 7/8, z kaveatem „sinus deterministyczny — wiatr zmienny
  o znanym profilu, nie turbulencja". Słowo „turbulencja" w cytowaniach
  programu pozostaje zabronione. Sufit wiatru nie został zmierzony; wolno
  mówić wyłącznie „do 3.6 m/s", nic o tym, co wyżej.
- **Zamknięcie jest decyzją, nie koniecznością:** po §3 bloker techniczny
  S1 nie istnieje (przyczyna zacięć leży w zegarze hosta i ma trywialne
  remedium), noga jest dziś tańsza do polecenia niż wczoraj (oczekiwane
  7–9 bootów). PRE_WK4 zostaje w repo jako prerejestracja ważna literą;
  **wznowienie wymaga ponownej ratyfikacji** (zamrożone sha mogą się
  zestarzeć) i przejścia reszty B0 (PX4 bez uzbrojenia, boot kontrolny
  dsim/dwall ≥ 0.98) po restarcie WSL.
- Wątek wiatru programu: W (29.09), WK (V-C), WK-II (V-A2), WK-III (V-A3),
  WK-IV (decyzja) — **zamknięty w całości**.

**Zdanie kanoniczne (do cytowań):** „Noga turbulencji została przygotowana
do lotu — widmo Drydena z zamrożonym ziarnem odtwarzane w świecie
deterministycznie, nauczyciel 4/4 przy średniej 4 i 6 m/s, bloker ważności
rozpoznany jako skoki zegara ściennego gościa — i zamknięta decyzją przed
pierwszym lotem sieci; kanon wiatru programu pozostaje przy wietrze zmiennym
o znanym profilu do 3.6 m/s, bez roszczeń do turbulencji i bez zmierzonego
sufitu."

## §3. Nota techniczna: zacięcia = skoki zegara ściennego WSL, nie symulacja (ustalone w gołym gz)

Z B0 (wg raportu egzekutora; liczby do potwierdzenia przez CC z plików po
pushu):
- **gz nie zamiera.** Według CLOCK_MONOTONIC: 0 zacięć, dsim/dwall 1.000.
- Według CLOCK_REALTIME (`time.time()`, z którego liczony jest V2′ przez
  `rtf_stream.jsonl`): 3 zacięcia na ~90 s, dsim/dwall 0.931.
- Różnica realtime − monotonic skacze o **+2.2–3.3 s co ~35 s**; dryf ~6.5 %;
  źródło: korekty timesyncd w gościu WSL2. Publikator WK4 i inne procesy
  hosta wykluczone (A/B (ii)–(iv), `host_pauza_bez_gz.txt`).
- Sygnatura z bootów nauczyciela (14 zacięć × ~2.2 s co ~32 s czasu
  symulacji, PX4 „time jump detected" ×14) jest z tym spójna: agent uXRCE
  i próbnik RTF używają zegara ściennego, PX4 w lockstepie — czasu symulacji.
  **Nie potwierdzono po restarcie WSL** (etap PX4 nieodbyty) — to jedyna
  niedomknięta część diagnozy.
- **Remedium:** `wsl --shutdown` przed sesją bootów i kontrola
  realtime − monotonic przed uzbrojeniem; przy wznowieniu nogi — w B0.

**Konsekwencja metodologiczna (forward, bez retroakcji):** miernik ważności
V2′ = dsim/dwall opiera się na zegarze ściennym gościa, więc mierzy także
zegar, nie tylko symulację. Skoki zaniżają V2′ (epizod fizycznie ważny może
wypaść nieważny), nigdy nie zawyżają — próg 0.90 pozostaje bezpieczny
w stronę ostrożną, a werdykty żadnej zamkniętej nogi nie wymagają rewizji
(w WK-III dsim/dwall 0.9986 ⇒ skoków nie było). Na przyszłość: próbnik RTF
zapisuje oba zegary (`wall_monotonic` obok `wall`), a V2′ liczy się
z monotonicznego — zmiana narzędzia do wprowadzenia PRZY NASTĘPNEJ nodze
z lotami, z własnym pinem, nie teraz i nie w tym commicie.

Aktywa gotowe do użycia: serie `results/WK4_RECON/series/D2…D6.json` (sha
w `.sha256`), publikator `wk4_publisher.py` 746a958b, świat `world_wk4`
7acf407f, driver nauczyciela `wk4_calib_boot.sh` a4d2175f, próbnik zacięć
i A/B w `results/WK4/`, walidacja serii i rachunek sufitu w RECON_WK4.

## §4. Katalog i KSIĘGA (treść do skopiowania, append-only)

Dopisek do `KIERUNKI_PO_PLANIE.md` (zastępuje osobny plik
DOPISEK_MULTITARGET_CLOSED — jeden blok):

```
## Dopisek stanu katalogu — 31.10.2026 (CO-WK4-0, ANEKS_WK4-0 §2–§4)

- **Noga WK-IV „turbulencja i sufit wiatru"** (pozycja 2b, otwarta 30.10:
  recon 1f61bc1b, PRE 1c0e1643) → **CLOSED-BY-DECISION przed lotami sieci
  (0 bootów sieci)**. Recon zweryfikowany przez CC (serie Drydena co do
  liczby, nauczyciel D6 4/4 przy D4 i D6, k 0.497/0.498). B0 wykonane
  częściowo w gołym gz (31.10, bez PX4; `results/WK4/`): **zacięcia
  symulacji z reconu to skoki zegara ściennego gościa WSL2** (realtime −
  monotonic +2.2–3.3 s co ~35 s, timesyncd; gz wg CLOCK_MONOTONIC 0 zacięć,
  dsim/dwall 1.000) — nie świat, nie publikator; etap PX4-bez-uzbrojenia
  i boot kontrolny nieodbyte; remedium `wsl --shutdown` przed sesją.
  Zamknięcie jest decyzją Olgi 31.10, nie koniecznością. **Kanon wiatru
  programu pozostaje przy V-A3 (ANEKS_WK3-1 §2):** wiatr zmienny o znanym
  profilu do 3.6 m/s, nie turbulencja, sufit niezmierzony. PRE_WK4 ważny
  literą; wznowienie = ponowna ratyfikacja + reszta B0. **Konsekwencja
  metodologiczna (forward):** V2′ liczony z zegara ściennego zaniża ważność
  przy skokach zegara, nigdy nie zawyża — werdykty zamkniętych nóg bez
  rewizji; próbnik RTF przy następnej nodze z lotami zapisuje oba zegary,
  V2′ z monotonicznego (własny pin). Aktywa: serie D2–D6 z sha, publikator
  746a958b, świat world_wk4 7acf407f, RECON_WK4, `results/WK4/` (B0). Wątek
  wiatru (W, WK, WK-II, WK-III, WK-IV) zamknięty w całości.
- **MULTI-TARGET / TOŻSAMOŚĆ TRACKA** → **CLOSED-BY-DECISION (31.10, Olga:
  „zamykamy wabik")**. Wątek wabikowy zamknięty w całości na tym stanowisku,
  z wynikiem: (1) reguła v1 (FREEZE_WABIK) nigdy nie podpisała celu
  wchodzącego na 65 uderzających (ANEKS_WABIK3-1 §2); (2) trzy dźwignie
  skrócenia etykiety (czas, tor, geometria) zamknięte deskiem za 0 lotów
  (ANEKS_WABIK2-1, ANEKS_WABIK3-1); (3) imitacje poniżej rozdzielczości toru
  kamery (RECON_WABIK3 R4); (4) priorytet między ≥ 2 obiektami nazwany
  i wyceniony (RECON_WABIK3 R1 ii), nieotwarty. Trigger ponownego otwarcia
  wyłącznie zewnętrzny: partner z realnymi lotami i sensorami poza kamerą
  albo odpowiedź praktyka, że obrona odróżnia wabik i chce tego jako
  polityki kolejności. Aktywa w repo: bench WABIK-II (126 lotów),
  wabik_sig 475c972e / wabik_sig2 a8397cb4 / wabik3_recon 5dbc94ec /
  wabik3_uderzajacy, klasa uderzający/niedochodzący.
- Stan: katalog **7 → 6 otwartych pozycji** (PERCEPCJA-II, ODPOWIEDŹ-EKONOMIA,
  1b(ii) weryfikacja sieci z pytaniem o GRU, 2c, 2d, 2e). Breach 0 / REFUSE 0
  programowo bez zmian. Program w trybie katalogu; następne ruchy poza
  stanowiskiem (warstwa 0: raport EN, karta technologii, rozmowa z pilotem).
```

Sekcja do `results/KSIEGA_PREDYKCJI.md`:

```
## NOGA WK-IV (turbulencja i sufit wiatru) — ZAMKNIĘTA DECYZJĄ przed lotami sieci (ANEKS_WK4-0, 31.10.2026)
Prerejestrowane 31.10.2026 (`PRE_WK4.md`, sha a530ebb5…1891); S1 nie odbyła się
poza częścią B0 w gołym gz.
- **P-WK4-5 (0.60) ✗** — przyczyna zacięć NIE leżała po stronie publikatora ani
  transportu: wariant bez publikatora miał te same „zacięcia" w zegarze
  ściennym, a wg CLOCK_MONOTONIC zacięć nie było wcale; źródło = skoki
  CLOCK_REALTIME gościa WSL2 (timesyncd). CC szukał przyczyny w nowej
  infrastrukturze, bo była nowa — a miernik był stary i mierzył zegar.
- **P-WK4-1…4, 6, 7: n.r.** (wzór FANTOM / WABIK-II: predykcje sesji, która nie
  zaszła, bez rozliczenia).
- **Rozliczalne już dziś — ✗ kalibracyjne CC:** w PROMPT_WK4_S0 §R2 CC napisał,
  że Dryden przy 2 m/s będzie „łagodniejszy w σ od P2, a szerszy w paśmie";
  recon pokazał łagodniejszy (σ_x 0.33 vs 1.06) i WOLNIEJSZY (90 % mocy poniżej
  0.06 Hz vs 0.25–0.34 Hz). Przy adwekcji V = Ū = 2 m/s skale Drydena
  (L_u ≈ 67 m) dają czasy korelacji rzędu dziesiątek sekund — rachunek, który
  CC mógł zrobić przed napisaniem zdania.

**Suma nogi WK-IV: 0 ✓ / 1 ✗ / 6 n.r. (+1 ✗ kalibracyjne poza numeracją).**

Lekcje kalibracyjne: (1) gdy miernik ważności pada po zmianie infrastruktury,
pierwszy A/B to miernik przeciw drugiemu zegarowi, nie infrastruktura przeciw
sobie — podejrzany „nowy element" był tu fałszywym tropem o pewności 0.60;
(2) widmo turbulencji porównywać z profilem odniesienia liczbą (σ i f90) PRZED
tezą o „szerszym paśmie" — intuicja „turbulencja = szybsza" jest fałszywa przy
małej prędkości adwekcji; (3) recon, który dostał próbnik czasu symulacji vs
ściennego, znalazł problem przed lotami sieci — zasada zostaje: każda nowa
infrastruktura świata dostaje taki próbnik w reconie.
```

## §5. Zlecenie CO-WK4-0 — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git fetch` → origin/master == **1c0e1643**; `origin/master..HEAD`
puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista zamknięta):

1. Korzeń **`ANEKS_WK4-0.md`** (ARCH-1, verbatim, pierwszy w commicie;
   byte-check sha256 podany przez CC w wiadomości z aneksem i potwierdzony
   przez Olgę „sha ok" — odchylenie tej samej klasy co przy CO-WABIK3R,
   nazwane w opisie commitu).
2. **`results/WK4/**`** — B0 w gołym gz jako dowód §3: narzędzia
   (`tools/wk4_b0_ab.sh`, `tools/wk4_zaciecia.py`), przebiegi A/B (i)–(iv),
   pliki diagnostyczne zegara; bez edycji, tak jak leżą; w opisie commitu
   jedno zdanie, co to jest i że PX4 nie brał udziału.
3. **EDYCJA `KIERUNKI_PO_PLANIE.md`** — dopisek §4 verbatim, append-only.
4. **EDYCJA `results/KSIEGA_PREDYKCJI.md`** — sekcja §4 verbatim, append-only.

ŻADNYCH edycji PRE_WK4, RECON_WK4, serii, świata, publikatora, próbnika RTF,
sędziego, raportów ani kodu; żadnych bootów. Raport płaski: diff-stat, lista
plików `results/WK4/` z rozmiarami, pełna treść dopisków, porcelain. **Push =
Olga („wypchnięte" — CC sprawdza byte-check, append-only, verbatim, i liczby
§3 z plików B0: realtime − monotonic, zacięcia wg obu zegarów).** STOP.

## §6. Status

WK-IV: CLOSED-BY-DECISION, 0 bootów sieci; bloker techniczny rozpoznany
i nazwany (zegar gościa), remedium trywialne, noga wznawialna. Wątek wiatru
i wątek wabików zamknięte w całości; katalog 6 otwartych pozycji, żadna nie
jest zarazem tania i ważna dla tezy. Materiał programu (raport „Stan na
31 października", demo v6) jest spójny z tym stanem i gotowy do wyjścia na
zewnątrz. Breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co kiedykolwiek
poleciało uzbrojone.
