# ANEKS_KONT-4 — S3 przyjęte po replikacji proverów u CC; rozstrzygnięcia Q1–Q3 (margines tickowy T*, R-G-NOM schodzi pod ABORT/HOLD, R-KONT w klasie R-POS); S3b (poprawka kolejności + re-certy) i otwarcie S4

CC · 7.11.2026 · łańcuch KONT, po STOP-KONT3 (b7c9dc0e na origin).
Wklejany RAZEM z PROMPT_KONT_S4. Sygnały bez numeru odrzucasz.

## §1. Replikacja i przyjęcie S3

- Zakres czysty: 19 plików, +10315, same nowe; FROZEN bez zmian
  (shield 1c584964, safe_descend e3c1040b, config 4c440e42).
- **Provery zreplikowane u CC (z3 5.3.3):** P9_kont — 22 koszyki,
  main unsat + ostrość sat (ε, R, Δ) w każdym, 7/7 asercji
  arytmetycznych; P1_kont 17/17; P7_kont 78 877 stanów / 315 508
  krawędzi, cert **identyczny bajtowo**; P5_kont 0 rozbieżności na
  4.04 mln ticków u CC, pokrycie pełne (w tym R-G-NOM, R-KONT,
  cause:T*, cause:bariera, drugi epizod). Certy różnią się wyłącznie
  `z3_lib` — wzorzec FV. Uwaga przyrządowa: prover nadpisuje certy
  w miejscu przy weryfikacji (CC przywrócił po swoim biegu; legalne
  jak regeneracja P7 w FV, odnotowane).
- Poprawki w trakcie przyjęte (dziedzina P7 z dowodem niezmiennika,
  naprawa przyrządu mutantów, mutant brzegowy r_est = R(k)): klasa
  wzmocnienia przyrządu, siatka prereg nietknięta.
- **Zastany czerwony test `r02/test_deadman.py`** (od 20.08, atrapa bez
  `_sp_yaw`): defekt atrapy testu, nie produktu; r02 FROZEN — zostaje
  czerwony, wpis do backlogu; kryteria „pełny zestaw PASS" w S3 i S4
  czytają się modulo ten jeden nazwany zastany.

## §2. Rozstrzygnięcia Q1–Q3

1. **Q1 — margines tickowy zamiast rozszerzania A-flag.** REFUSE z
   przyczyny T* odpala przy **t_KONT ≥ 22 − 2·dt** (dt = okres pętli
   osłony, cytowany z kodu w commicie; z fikstur dt ≈ 0.04–0.05 s ⇒
   próg ≈ 21.9 s). Skutek do asercji w teście T1′: prawdziwy wiek
   flagi w chwili REFUSE < 22.000 s na wszystkich 8 fiksturach.
   A-flag bez zmian (0.004–0.016 s). Gwarancja pokrywa koszyki 0–21
   bez wyjątku; koszt ≤ 0.1 s zadania. Rozszerzanie A-flag po danych
   odrzucone jako luzowanie założenia.
2. **Q2 — R-G-NOM schodzi PONIŻEJ abort, hold i return**, bezpośrednio
   nad klasę ALLOW ({OBSERVE ∧ auth | R-AUTH} i patrol). ABORT i HOLD
   dostają cele nietknięte; R-G-NOM przycina wyłącznie ruch
   autonomiczny. Zapis 3b §1.2 „powyżej abort" był błędem CC — skutki
   nazwane przez wykonawcę (ABORT czekający na kierunek celu, HOLD
   z przyciętym zawisem) są dyskwalifikujące. ✗ CC do KSIĘGI.
   **S3b (przed lotami):** poprawka kolejności w nakładce, P1_kont
   i P5_kont od nowa, selfcheck ×1, T0–T4 re-run; commit z nowymi
   certami. Zero bootów.
3. **Q3 — R-KONT w klasie R-POS, ponad R-G: przyjęte.** Spójne
   z uzasadnieniem frozen (zdrowie pozycji ponad barierą liczoną na
   niepewnym p); już udowodnione w P1_kont.

Drobne: `refuse_r_est` 24.162 przy barierze w c02_s01_r4 na lustrze =
dokładnie liczba z pytania wykonawcy sprzed S3 — obie strony liczą to
samo.

## §3. KSIĘGA (append-only przy commicie S3b)

```
## KONT S3 (ANEKS_KONT-4, 7.11.2026): certy KONT PROVED/PASS,
replikacja CC zgodna (z3 5.1.0/5.3.3, różnice tylko z3_lib)
- ✗ CC: PROMPT_KONT_S3 §2 cytował kolejność frozen odwrotnie
  (R-G > R-POS); ANEKS_KONT-3b §1.2 postawił R-G-NOM ponad ABORT/HOLD
  — oba wyłapane przez wykonawcę przed/po kodzie, naprawione literą
  (3b §1.1, 4 §2.2). Lista plików §0.3 za wąska (2 pliki).
- ✗ CC: niespójność brzegowa zamrożenia (R_nom 27.51 vs bariera(0)
  27.303) — skorygowana do 27.30 w 3b §1.7.
- Wady wykonawcy nazwane: pierwotny sat P7 ze zbyt luźnej dziedziny
  (naprawa z dowodem niezmiennika); błąd przyrządu mutantów (19/20 po
  poprawce, 21/21 z mutantem brzegowym).
- Zastany czerwony test r02/test_deadman.py (atrapa bez _sp_yaw,
  od fa5dc242 20.08) — backlog; kryteria PASS modulo ten zastany.
```

## §CO

Bramka: origin/master == **b7c9dc0e**. Commit 1: korzeń
`ANEKS_KONT-4.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §3 append-only. Commit 2 (S3b): poprawka Q1 (margines tickowy)
i Q2 (kolejność R-G-NOM) w nakładce, re-certy P1_kont/P5_kont,
selfcheck, T0–T4 + T1′; raport krótki w `results/KONT/s3/RAPORT_KONT_S3b.md`.
**Potem S4 według PROMPT_KONT_S4.** Push = Olga (może być jeden push po
S3b albo po S4 — bramki S4 sprawdzają HEAD lokalnie).
