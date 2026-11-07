# RAPORT_KONT_S3b — poprawka Q1 (margines tickowy T*) i Q2 (R-G-NOM pod ABORT/HOLD/RETURN), re-certy, 0 bootów

Wykonawca · 7.11.2026 · łańcuch KONT. Podstawa: ANEKS_KONT-4 (sha f266fa43, commit 1 `ANEKS-4` z KSIĘGĄ §3).
Bramka: origin/master == b7c9dc0e (spełniona).

## §1. Zmiany

- **Q1 (4 §2.1):** REFUSE z przyczyny T* przy `t_KONT ≥ T* − 2·dt` = 21.9 s; `dt = self.cfg.dt` = `DT = 1/TICK_HZ`
  = 0.05 s (`r01/config.py:41`), stała `T_MARGIN_TICKS = 2` w `r03/kont_shield.py`. A-flag bez zmian.
- **Q2 (4 §2.2):** R-G-NOM tylko dla ruchu autonomicznego: priorytet latch > R-POS > R-KONT > R-G > abort > hold >
  return > **R-G-NOM** > {OBSERVE∧auth | R-AUTH} > patrol. ABORT/HOLD/RETURN dostają cele nietknięte.
- **Q3:** bez zmian w kodzie (R-KONT w klasie R-POS, już dowiedzione).
- Pliki zmienione: `r03/kont_shield.py` (sha8 0520348f), `r01/proofs/p9_kont_verify.py` (lustro, tau_kont, P7, P9,
  siatka S3b), cztery certy KONT, `test_kont_s3.py` (+T1′, +T2 tryby), `kont_mutants.py` (+2 mutanty, siatka S3b
  w zbiorze wejść). `r03/kont_gate.py` bez zmian (1336beef). FROZEN bez zmian: shield 1c584964, safe_descend
  e3c1040b, config 4c440e42, freeze ae19f66c. Wyniki S3 (`provery_all.log`, `selfcheck.log`, `mutanty.json`,
  regresje) nietknięte — nowe pliki z sufiksem `_s3b`.

## §2. Certy (jeden bieg `all`, 142.2 s, `provery_s3b.log`)

Aneks wymienia re-certy P1_kont i P5_kont. Cztery certy mają wspólny prover (3b §1.6), więc jego edycja zmienia
model_sha256 wszystkich — przeliczone wszystkie cztery, a P7 i P9 i tak zmieniają treść przez próg Q1.

| cert | wynik | co nowego |
|---|---|---|
| P9_kont | PROVED | 22 × (main unsat + 3 ostrości sat); asercje 8/8, nowa `refuse_threshold_T_minus_2dt` (22 − 2/20 = 21.9) |
| P1_kont | PROVED | 18/18 unsat; nowa **P1o** (ABORT/HOLD/RETURN niezależne od nom), P1l z przesłanką trybu PATROL/OBSERVE |
| P7_kont | PROVED | próg 438 ticków: 78 473 stanów / 313 892 krawędzi, max wiek ALLOW w KONT 437, REFUSE z czasu dokładnie przy 438; 11/11, z3 5/5 unsat |
| P5_kont | PASS | 0 rozbieżności: siatki 463 ticki (S3 382 + S3b 81), fuzz 4 042 863, fikstura 17 725, tau_kont 82 762; pokrycie pełne |

Siatka uzupełniająca prereg `p5_kont_grid_s3b.json` (18 epizodów: brzeg progu 21.85/21.899/21.9/21.901 i zegar
drobny 21–22 s; R-G-NOM × {ABORT, HOLD, RETURN, OBSERVE auth/¬auth, PATROL} × {nominal, KONT}) zbudowana przed
pierwszym biegiem P5 po poprawce; pierwsza siatka nietknięta.
Mutanty 23/23 (`mutanty_s3b.json`; nowe `b_no_margin`, `p_nom_above_abort`). `b_tstar_strict` przeżył w pierwszym
biegu, bo przyrząd czytał tylko pierwszą siatkę; po dołączeniu siatki S3b wykryty — wada przyrządu po mojej stronie.
Selfcheck ×1 (`selfcheck_s3b.log`): 13/13, kanon 9/9.

## §3. Testy

`test_kont_s3.py` **14/14** (T0–T4 + T1′ + T2 tryby).
**T1′ (4 §2.1):** prawdziwy wiek flagi w chwili REFUSE < 22.000 s na 8/8 fiksturach:

| lot | przyczyna | t_KONT przy REFUSE | wiek flagi (ulog) |
|---|---|---|---|
| c00_s02_r3 | T* | 21.908 | 21.948 |
| c02_s01_r4 | bariera | 10.416 | 10.464 |
| c08_s02a_r2 | T* | 21.924 | 21.976 |
| c08_s02b_r2 | T* | 21.904 | 21.956 |
| c08_s04_r3 | T* | 21.916 | 21.964 |
| c11_s02_r3 | T* | 21.932 | 21.976 |
| c11_s03_r4 | T* | 21.900 | 21.948 |
| c11_s04_r3 | T* | 21.944 | **21.988** |

Najmniejszy zapas to 0.012 s (c11_s04_r3).
Regresja (`regresja_s3b.tsv`): 43 pliki, wyniki starych plików jak w bazie; jedyny czerwony to zastany
`r02/test_deadman.py` (4 §1: kryteria modulo ten zastany).

## §4. Stan

Commit S3b po ścieżkach, 0 bootów, noga 24/45. Następnie S4 według PROMPT_KONT_S4. Push = Olga.
