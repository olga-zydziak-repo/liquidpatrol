# STOP-NAD2-1-FREEZE — S1 zatrzymane na §1.4: F_jeden nie odtwarza się w tolerancji 0.01 m w konwencji czasu reconu; w konwencji CC odtwarza się co do 0.0004 m. Rozstrzyga CC.

11.11.2026 · wykonawca · PROMPT_NAD2_S1 (sha256 3f163d9d PASS) po CO-NAD2-0 `8f005433` (PRE_NAD2 sha256 eea6fcc8 PASS,
„ratyfikuję PRE_NAD2"). **0 bootów.** Śmierć/STOP S1 z §2: „F_jeden nie odtwarza się w tolerancji". Zgodnie z literą
nie wybieram konwencji, przy której liczby przechodzą. Budowa jest wstrzymana: osłona, driver, analizator i certy
**nie** zostały zbudowane.

## 1. Co się nie odtwarza

F_jeden to błąd zakotwiczenia rozwiązania jednym znacznikiem z T1, liczony produkcyjną `harness/nadir_fix.Rama(litera="NAD2")`
w każdej klatce z przyjętą obserwacją okna bez GNSS 12 cięć S4, |p_jeden − GT(t_a)| poziomo. Dla koszyka 4 (n < 100) stosuję
regułę PRE §4: max(własna, maksimum bieżące niższych koszyków, pula trybu), a potem maksimum bieżące.

| koszyk r_h | 0–2 | 2–4 | 4–6 | 6–8 | 8–10 |
|---|---|---|---|---|---|
| n | 551 | 2630 | 3034 | 366 | 20 |
| **PRE §4 (CC)** | 0.253 | 0.329 | 0.440 | 0.442 | 0.442 |
| t_a = `timestamp_sample` próbki EKF (konwencja reconu: R1, R3, F_para) | 0.2562 | 0.3376 | 0.4445 | **0.4527** | **0.4527** |
| różnica | +0.0032 | +0.0086 | +0.0045 | **+0.0107** | **+0.0107** |
| t_a = `timestamp` próbki EKF (publikacja, ~4 ms później) | 0.2527 | 0.3294 | 0.4400 | 0.4420 | 0.4420 |
| różnica | −0.0003 | +0.0004 | 0.0000 | 0.0000 | 0.0000 |

**Diagnoza.** CC liczył F_jeden z GT w chwili `timestamp` próbki EKF. Recon wykonawcy (R1(c), R3, R5, a więc i F_para
wpisane do PRE §4) liczył z `timestamp_sample`.
- Ta sama różnica tłumaczy rozbieżność F_pary z PRE §1.4 („do 0.007 m"): w konwencji `timestamp` F_para wynosi
  0.1899 / 0.2352 / 0.2296 / 0.2107 / 0.2577 (CC: 0.190 / 0.235 / 0.230 / 0.211 / 0.258).
- W `timestamp_sample` F_para wynosi 0.1968 / 0.2372 / 0.2337 / 0.2107 / 0.2577 (PRE §4 po maksimum bieżącym:
  0.1968 / 0.2372 / 0.2372 / 0.2372 / 0.2577).
- **Tabela zamrożona w PRE §4 łączy dwie konwencje:** F_para z `timestamp_sample`, F_jeden z `timestamp`.

**Która konwencja jest fizyczna.** `timestamp_sample` to czas, którego dotyczy stan EKF, a `timestamp` to chwila publikacji
(R1: oba pola dopasowują się po wartości do tej samej próbki, różnica ~4 ms). Δ ramy liczy się względem stanu, więc kandydatem
jest `timestamp_sample`. Ta sama konwencja musi obowiązywać w (B1) analizatora: e_corr = |p_corr − GT(czas próbki EKF ticku)|.

**Skutek liczbowy.** F_jeden w `timestamp_sample` jest wyższe o ≤ 0.011 m, co daje U wyższe o ≤ 0.016 m i u′(τ ≤ 0.25 s,
jeden, koszyki 3–4) = 3.142 zamiast 3.125 m. Tryb jeden w Z2 to 11 z 6602 klatek misji bez GNSS w S4.

**Do rozstrzygnięcia przez CC (opcje, bez rekomendacji wykonawcy co do werdyktu):**
- (a) kanon `timestamp_sample`: F_jeden = 0.256 / 0.338 / 0.445 / 0.453 / 0.453 (sprostowanie PRE §4), F_para bez zmian;
- (b) kanon `timestamp`: F_jeden jak w PRE; F_para z PRE §4 jest wtedy zawyżone o ≤ 0.007 m (ostrożne);
- (c) inna decyzja CC.

Analizator (B1) i narzędzie FREEZE dostaną tę samą konwencję.

## 2. Co zostało zbudowane przed STOP-em (0 bootów)

**`harness/nadir_fix.py`** (diff-stat: +43/−6). Litera wybierana jawnie: `Rama(litera=…)`, domyślnie z env `NADIR_LITERA`,
a brak env oznacza „NADIR1” (stara litera, zachowanie bez zmian).
- Litera „NAD2” (PRE §3.1–3.2): bok ≥ 16 px, najbliższy r_h < 10 m, partner pary bez limitu r_h (największa baza),
  koszyk 0–4, T1 (obrót wektora poziomego kamera→znacznik o δψ ostatniej przyjętej pary, wiek ≤ 2 s).
- Datagram przy NAD2 niesie pole `litera` i `t1`. Pole `tryb` było już w datagramie; `RamaKlient` zapamiętuje teraz `tryb`
  ostatniej przyjętej poprawki.
- Przy NADIR1 rekord jest bajtowo jak dotąd: brak nowych pól, `far` pusty, dobór partnera identyczny.

**W1 — wierność** (`results/NAD2/tools/nad2_w1.py` ⇒ `w1_wiernosc.json`): **PASS**.
1. Nowy `nadir_fix` z literą NADIR1 odtwarza zapisane fx 16 bootów S4 w 100% klatek (29 801): ok, tryb, kosz, ids, d_ne,
   |Δp_fix| = 0.0.
2. Kontrola krzyżowa: `Rama(litera="NAD2")` ≡ replay reconu (wariant T1Z2C0) w 100% klatek (Δ wewnętrzne ≤ 1e-9 m, zapis
   p_fix 4 cyfry).
3. P5_nadir na starej fiksturze S2 (prove_p5 bez zapisu certu): **PASS** — 0 rozbieżności, 0 passthrough, pełne pokrycie,
   4.03 mln ticków fuzzu.

**Narzędzie FREEZE** (`results/NAD2/tools/nad2_freeze.py`):
- odtwarza G (różnica 0.0000) i F_para (0.0000) z reconu;
- F_jeden jak w §1 ⇒ kod 3, `freeze_U.json` nie powstał; diagnoza obu konwencji w `results/NAD2/s1/freeze_STOP_diagnoza.json`;
- po decyzji CC narzędzie zapisze tabelę U, u′ i R z sumą sha256 tabeli (gotowe w kodzie).

**Nie zbudowane (wstrzymane):** `r03/nadir_shield.py` (tabela U, wybór ramy po aktualizacji monitora), driver
`results/NAD2/tools/nad2_flight.py` z krokiem osłony w osobnym module (do obligacji wejścia C3), `nad2_analyze.py`,
prover `r01/proofs/p9_nad2_verify.py` (P9/P1/P5/P7_nad2), W2, T.

## 3. Projekt drivera i osłony (zapisany przed budową — do oceny CC razem z decyzją §1)

- **Wybór ramy w tym samym ticku.** Osłona NAD2 dostaje w każdym ticku obie pozycje i oba cele (EKF i poprawione).
  Po aktualizacji monitora GNSS sama wybiera ramę: w KONT poprawioną, w NOMINAL EKF. Wejście w KONT i wyjście z niego są więc
  dokładne co do ticku. r_est = |pozycja w wybranej ramie|. Wyjście (`applied`) przeliczane do EKF: applied_EKF = applied − Δ
  (x, y). R-G-NOM i projekcja promieniowa w warstwie komend (`kont_gate.patrol`) dostają pozycję w tej samej ramie.
- **τ i przedział.** Osłona zna tylko τ = now − t_fix. Horyzont prawdziwy (czas próbki EKF − t_a) różnił się w S4 od τ osłony
  o −0.036…+0.008 s. Proponuję przedział z τ + 0.02 s, żeby osłona nigdy nie wybrała przedziału niższego niż prawdziwy.
  To odstępstwo do zatwierdzenia.
- **REFUSE(τ*).** Proponuję τ ≥ τ* − 2·dt = 0.95 s (konwencja NADIR-I i replay R5) zamiast literalnego τ > 1.05 s, żeby
  między tickami τ nie wyszło poza tabelę. Do zatwierdzenia.
- **Brak poprawki od wejścia w utratę:** pole (jeden, koszyk 4), τ od zera zegara utraty.
- **Boot i launcher NAD2** (env `NADIR_LITERA=NAD2` dla producenta ramy i drivera): poza listą §1, do promptu smoke.

## Reprodukcja

```
PYTHONPATH=.certdeps:. python3 results/NAD2/tools/nad2_w1.py
python3 results/NAD2/tools/nad2_freeze.py          # kod 3 + freeze_STOP_diagnoza.json
```

Porcelain: poza commitem tylko zastane ?? (`results/DEMO_C/…`).

**Sygnał: STOP-NAD2-1-FREEZE.** Push = Olga; decyzja konwencji czasu = CC.
