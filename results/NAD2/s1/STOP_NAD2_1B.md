# STOP-NAD2-1B — S1 NADIR-II kompletne (0 bootów): litera Z2 + T1, tabela U w osłonie, osłona w ramie poprawionej; P9/P1/P7_nad2 PROVED, P5_nad2 PASS z obligacją wejścia; W1, W2, T PASS

11.11.2026 · wykonawca · PROMPT_NAD2_S1 (sha256 3f163d9d) wznowione od §1.2 po ANEKS_NAD2-1 (sha256 92d4dfcb PASS,
„ratyfikuję NAD2-1", commit [CO-NAD2-1] `84a4e064`). **0 bootów**: żadnego uruchomienia gz / PX4 / kolejki. Jądro
`r01/shield.py`, wagi, parametry PX4, manifest v2 i kanon percepcji nietknięte. `STOP_NAD2_1.md` (STOP-NAD2-1-FREEZE) zostaje
jak jest. Śmierci S1 (§2): **żadna nie zaszła**.

## Budowa

**`harness/nadir_fix.py`** (+43/−6 wobec CO-NAD2-0, commit STOP-NAD2-1-FREEZE, od tamtej pory bez zmian). Litera wybierana
jawnie: `Rama(litera=…)`, domyślnie env `NADIR_LITERA`, a brak env oznacza `NADIR1`.
- NAD2: bok ≥ 16 px, najbliższy r_h < 10 m, partner pary bez limitu, koszyk 0–4, T1 (wiek pary ≤ 2 s).
- `RamaKlient.tryb` — tryb poprawki trafia z datagramu do tabeli U.
- Przy NADIR1 rekord bajtowo jak dotąd.

**`r03/nadir_shield.py`** (+129/−2). Reżim `nad2` wybierany jawnie: argument, domyślnie env `NADIR_LITERA == NAD2`, aktywny
tylko przy `nadir_mode`.
- Stałe tabeli wkompilowane z sha tabeli, PRE i ANEKS (`nad2_tabela_check`).
- `przedzial_nad2` liczy z τ + 0.012 s. `u_nad2` / `r_nad2`. REFUSE(τ*) przy τ ≥ τ* − 2·dt = 0.95 s. Brak poprawki ⇒ pole
  (jeden, 4).
- `_step_nad2` ma kształt 1:1 z `KontShield.step`, z jedną różnicą: **wybór ramy po aktualizacji monitora GNSS** — utrata ⇒
  pozycja i cel poprawione, NOMINAL ⇒ EKF. r_est liczony z ramy wybranej.
- `applied` przeliczane do ramy EKF (oryginał w `d["nad2"]["applied_rama"]`), a pole `d["nad2"]` niesie ramę, Δ, przedział,
  tryb i r_est.
- Przy `nad2=False` ścieżka starej nakładki jest bez zmian (W1(3)).

**`results/NAD2/tools/nad2_krok.py`** (nowy, 20 linii). Jedyna ścieżka wołania osłony przez driver: pozycja i cel w obu ramach;
zwraca pozycję bramki komend w ramie wybranej. Moduł jest wydzielony, żeby C3(b) sprawdzało kod lotu, a nie jego opis.

**`results/NAD2/tools/nad2_flight.py`** (nowy; kopia `nadir_s4_flight.py` ze zmianami „NAD2:”, 69 linii diffu). Decyzje
projektowe wykonawcy, zgodnie z ANEKS_NAD2-1 §2.6:
- reżim jawny — `NADIR_LITERA=NAD2`, inaczej kod 8; passthrough `NADIR_MODE=0` tylko z env `NAD2_PASSTHROUGH=1` (wzór S3N B1,
  osłona-cień i `passthrough.jsonl`, do smoke (2));
- **tick wejścia w KONT:** ramę wybiera osłona w tym samym ticku, w którym monitor przechodzi w utratę (po debounce), więc
  pierwszy tick KONT jest już w ramie poprawionej, a ticki debounce jeszcze w EKF (NOMINAL — wejścia bez zmian, PRE §3.4);
- **wyjście:** pierwszy tick NOMINAL po histerezie wraca do EKF;
- **HOLD / REFUSE / zejście:** `applied` (hold-setpoint) liczone w ramie wybranej i przeliczane do EKF; komendy prędkości są
  niezmiennicze względem przesunięcia ramy, więc D5 + trzymanie yaw bez zmian;
- **R-G-NOM:** projekcja promieniowa w `kont_gate.patrol` dostaje pozycję w ramie osłony;
- **zdarzenie „breach” z estymaty** liczone z r_est ramy wybranej (w utracie EKF dryfuje do 8.5 m — w S4 surowy r_est mógł dać
  fałszywy breach i globalny STOP); `breach_gt` bez zmian;
- kontynuacja od `t_inj_sim`, nastawa 110.5 s;
- selfcheck certów + `nad2_certs_selfcheck.py`;
- log tk i ramy z `nad2` i trybem, obs z koszykiem, literą i T1; meta z sha tabeli, PRE, ANEKS, drivera, kroku i fix.
- Launcher i boot NAD2 (env `NADIR_LITERA=NAD2` dla `nadir_obs` i drivera) — poza §1, do promptu smoke.

**`results/NAD2/tools/nad2_freeze.py`** ⇒ `results/NAD2/s1/freeze_U.json`.
- Odtworzenie w kanonie `timestamp_sample`: G, F_para, F_jeden — różnica 0.0000 we wszystkich polach wobec PRE §4 +
  ANEKS_NAD2-1 §2.2.
- **sha256 tabeli 6a118fd4…1073**.
- u′(τ ≤ 0.25 s) 2.757–3.141 m, bariera 26.01–26.39 m (zgodnie z ANEKS §2.2).

**`results/NAD2/tools/nad2_analyze.py`** (nowy). Litera B1–B5, D1 i obserwable wg PRE §5 + ANEKS §2.4:
- B1 wobec U przedziału użytego przez osłonę;
- e_corr z GT w chwili `timestamp_sample` próbki EKF ticku, dopasowanej po wartości z ULG;
- kontynuacja od `t_inj_sim`;
- e_corr i błąd zakotwiczenia poprawek w raporcie płaskim per epizod.

Test analizatora:
- na syntetycznych logach w formacie drivera NAD2 (rama z replayu W2) B1 odtwarza W2 co do cyfry (c08_s01 e/U 0.398,
  c11_s02 0.2846);
- na logach S4 w starym formacie B1 i B3 zgłaszają FAIL (brak pól NAD2), a B2, B4, B5 i D1 działają.

## Certy (r01/proofs/p9_nad2_verify.py, sha 256 fb9ade23…; certy w r01/proofs/certs/)

- **C1 P9_nad2 — PROVED:** 50 obligacji (przedział 0–4 × koszyk 0–4 × tryb). Twierdzenie główne unsat, ostrość
  trójstronna (U, R, Δ_D5) sat, arytmetyka 11/11 (tabela ≡ freeze, R nierosnąca w i i k, u′ ≤ m_p50, próg 19 ticków,
  0.95 + 0.012 ≤ 1.05, pole braku = max U). Założenie w cercie: |p_corr − GT| ≤ U **oraz** r_est osłony = |p_corr|.
- **C2 P1_nad2 — PROVED:** P1a–P1o + nom_applied + P1p (wyłączność i wyczerpanie liści); model `p9_kont_verify._p1_model`
  READ-ONLY.
- **C3 P5_nad2 — PASS:**
  - konformancja lustro NAD2 ≡ produkcja: siatka 500, fuzz 4.04 mln, fikstura S4 63 010 ticków (12 cięć + 4 nominały,
    poprawki z replayu nowej litery), tau ≡ produkcja na 143 684 tickach;
  - 0 rozbieżności, passthrough 0 na 1.01 mln; pokrycie 67 elementów — wszystkie reguły, przyczyny, obie ramy i 50 pól;
  - **(b) obligacja wejścia:** r_est = |p_corr| w 27 230/27 230 ticków utraty i = |p_EKF| w 35 780/35 780 ticków NOMINAL
    (max |Δ| 0.0); **mutant ze starą ścieżką wykryty** w 27 230/27 230 ticków utraty (max |Δ| 7.008 m);
  - **przejścia ramy:** wejście (pierwszy tick KONT w ramie poprawionej) i wyjście (pierwszy tick NOMINAL w EKF) — PASS;
  - **(c)** applied = applied ramy − Δ w 100% ticków utraty, bez zmian w NOMINAL; pozycja bramki = rama wybrana w 100%.
- **C4 P7_nad2 — PROVED:** 10 grafów (pole × wejście poprawki), próg 19 ticków, instancja zredukowana z przełączaniem pól,
  z3-duplikat 4/4 unsat.
- Selfcheck: `nad2_certs_selfcheck.py` 18/18 (kanon 9 + NADIR 4 + NAD2 4 + tabela U). Protokół oczekiwanej niezgodności
  (`--prover` z obcym plikiem) daje FAIL 14/18. Stare: kanon 9/9, NADIR 13/13.

## W1, W2, T

- **W1 PASS** (`w1_wiernosc.json`, bieg na końcowym kodzie):
  - nowy `nadir_fix` z literą NADIR1 odtwarza 29 801 zapisanych poprawek 16 bootów S4 w 100% (|Δp_fix| = 0.0);
  - `Rama(litera=NAD2)` ≡ replay reconu T1Z2C0 w 100% klatek;
  - **P5_nadir na starej fiksturze S2 PASS** na zmienionej osłonie (0 rozbieżności, 4.03 mln ticków fuzzu).
- **W2** (`w2_replay.json`): replay 12 cięć S4 kodem produkcyjnym (litera, osłona, krok drivera).

| pomiar | wynik W2 | odniesienie CC (ANEKS_NAD2-1 §1.3) |
|---|---|---|
| ticki utraty | 27 230 | 27 253 |
| przekroczenia B1 | 0 | 0 |
| max e_corr/U | 0.398 (c08_s01) | 0.398 |
| REFUSE | 0 | 0 |
| zapas bariery min | 1.706 m (c11_s02) | 1.71 m (c11_s02) |
| ticki trybu „jeden” | 44 | — |
| B3 r_est = \|p_corr\| | 100% ticków | — |
| max (horyzont prawdziwy − (τ + 0.012 s)) | −0.004 s (oczekiwanie ≤ 0) | — |

  - Wszystkie ticki leżą w przedziale 0.
  - Różnica 23 ticków: liczę od wejścia osłony w KONT (po debounce), a CC od flagi.
  - Ticki trybu „jeden” to ticki zużywające poprawkę jednym znacznikiem; CC podał 11 poprawek na 6602 klatki.
- **T** (`regresja_s1.tsv`, ROS jazzy i `ros2_ws` załadowane jak w S3): 43 pliki — wynik identyczny z bazą S3
  (`regresja_s3.tsv`) co do każdego pliku, czyli PASS modulo zastane: `r02/test_deadman.py` rc=1 i `test_aneks_det2`
  1 failed / 3 passed jak w S3. Nowych porażek 0.
  - Nowy `results/NAD2/tools/test_nad2_s1.py`: 8/8 passed.
  - Pierwszy bieg bez załadowanego ROS dał 2 dodatkowe porażki (`No module named 'rclpy'` / `'px4_msgs'`) — środowisko, nie
    kod; powtórzone poprawnie.

## Odstępstwa i decyzje nazwane wprost

1. Breach z estymaty w ramie wybranej (wyżej) — decyzja projektowa wykonawcy, poza listą ANEKS §2.6.
2. W tickach debounce przed wejściem w KONT osłona pracuje w ramie EKF (NOMINAL wg PRE §3.4), choć flaga utraty już jest.
3. Próg REFUSE(τ*) w kodzie to float `1.05 − 2·0.05 = 0.9500000000000001`, ta sama formuła co NADIR-I i lustro. Test
   S1 sprawdza brzeg tą wartością.
4. Prover przeliczony raz po usunięciu martwego wiersza; certy zapisane na końcowym sha `fb9ade23`.

## Reprodukcja

```
python3 results/NAD2/tools/nad2_freeze.py
PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nad2_verify all
PYTHONPATH=.certdeps:. python3 results/NAD2/tools/nad2_certs_selfcheck.py
PYTHONPATH=.certdeps:. python3 results/NAD2/tools/nad2_w1.py
python3 results/NAD2/tools/nad2_w2.py
python3 results/NAD2/tools/nad2_analyze.py <katalog_bootu>
source /opt/ros/jazzy/setup.bash; source ros2_ws/install/setup.bash; pytest -q <43 pliki z regresja_s3.tsv> + results/NAD2/tools/test_nad2_s1.py
```

Porcelain: poza commitem wyłącznie zastane ?? `results/DEMO_C/…`.

**Sygnał: STOP-NAD2-1B.** Push = Olga; CC replikuje certy, przelicza W2 i pisze prompt smoke i bramki albo aneks.
