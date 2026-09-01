# RAPORT_RESHAKEOUT — bramka startu intruza → freeze v1.1/v1.2 → re-shakeout → STOP-1b

LiquidPatrol · pozycja 2 · CC 2.09.2026 · push=Olga. Commity: B3 `d10c5b2` (gate+freeze v1.1), B3b (fix v1.2),
B4 (re-shakeout, ten commit). Zero lotów kryterialnych, egzekutor BAJT-W-BAJT (SR-3).

## 1. Preflight
- git: `origin/master` = `7ce6bf9` (B0/B1/B2 pushnięte = ratyfikacja STOP-1 per §0); `origin/master..HEAD` puste na wejściu.
- pytest wejściowy: 37/38 — jedyny fail `test_proc_gate_blocks_cpu_eater_then_passes` = środowiskowy (dreamforge
  a15f @68-100% CPU kontaminuje maszynę; bramka §3 poprawnie wykrywa obcy proces). 37 pozostałych (w tym WSZYSTKIE bench) PASS.
  Po dodaniu bramki: suite 43/44 (proc_gate live nadal wykluczony pod dreamforge; przechodzi na czystym hoście — dowód INFRA-3/RECON).
- sha: piny zgodne; EGZEKUTOR `840514361e…` + PARAMETRY `12c14adb…` = FREEZE_BENCH (bajt-w-bajt do końca sesji).

## 2. Bramka startu intruza
- Pliki: `harness/intruder_motion.py` (`intruder_start_gate` — czysta logika testowalna, `TOL_START=0.20`;
  fix v1.2: `run_episode` przerywalny `should_stop`), `bench/bench_flight.py` (async twin bramki: prestart set_pose
  do pozy startowej + hover, czekaj aż GT ≤ TOL, 5 s→retry→5 s→INVALID_START; log per epizod).
- **TOL_START = 0.20 m** — FAKT: p95 błędu set_pose (|zastosowana−komenda|) w shakeout gt_intruder = **0.10 m**
  (n≈14850/boot, mean 0.05, p50 0.04, p95 0.10; max 21 m = tranzient teleportu). 0.20 = 2× p95.
- **Mechanika t0: PRZESUNIĘTA** (t0 = po potwierdzeniu intruza w pozie startowej, wcześniej niż lot). Więc c00
  porównywany PASMEM powtarzalności, nie bit-w-bit. Relatywna geometria epizodu (position_at(t_rel)) bez zmian.
- Testy bramki: OK (poza≤TOL→OK / 2×timeout→INVALID_START / determinizm / interruptible v1.2). Suite bench 43/43.

## 3. Freeze v1.1 → v1.2
- v1.1 (`FREEZE_BENCH_v1.1`): delta intruder_motion `c58d308d→0397fa80` + bench_flight `7b1eff82→df1250ad`.
- v1.2 (`FREEZE_BENCH_v1.2`): delta WYŁĄCZNIE intruder_motion `0397fa80→937ae17c` (fix interruptible).
- NIEZMIENIONE do końca: EGZEKUTOR `840514361e…`, PARAMETRY `12c14adb…`, sędzia `8ec0fcfb…`, feed `674d78ab…`,
  cechy `9adc1505…`, manifest `e0527026…`, piny. SR-3: zero strojenia egzekutora.

## 4. Re-shakeout — 2 booty diag (§4 + wyjątek)
Bramka §3 CLEAN oba (loadavg 0.45/0.04; env-block nie wystąpił). Start gate: **OK 4/4 oba booty, 0 INVALID_START**,
attempts=1, n_setpose 3–19, wait_sim 0.10–0.96 s, pose@t0 = dokładna poza startowa. 0 REFUSE, 0 breach 8/8. |v|≤VMAX.

boot1 (v1.1, tylko bramka) i boot2 (v1.2, bramka+mover-fix), sędzia `bench_judge` (sim/GT):

| epizod | boot | wejście[s] | frac[6,10] | omiat.[°] | d_min @t_rel | d_min_orb | REFUSE/breach | D6 |
|---|---|---|---|---|---|---|---|---|
| c00 v0/0° | b1 | 2.98 | 1.000 | 895 | 8.55 @4.78 | 8.55 | 0/0 | ✓ |
| c00 | b2 | 2.96 | 1.000 | 894 | 8.56 @4.74 | 8.56 | 0/0 | ✓ |
| c05 v0.5/90° | b1 | 2.86 | 0.971 | 1025 | 6.98 @27.6 | 6.98 | 0/0 | ✓ |
| c05 | b2 | 2.38 | 1.000 | 947 | 8.10 @5.32 | 8.10 | 0/0 | ✓ |
| c10 v1.0/180° | b1 | 0.04 | 0.980 | 1066 | 6.94 @0.06 | 8.03 | 0/0 | ✓ |
| c10 | b2 | 0.0 | 0.965 | 1034 | 7.88 @4.79 | 7.88 | 0/0 | ✓ |
| **c11 v1.0/270°** | b1 | 3.43 | 0.918 | 923 | **1.41 @0.05** | 5.84 | 0/0 | **✗(d)** |
| **c11** | b2 | 0.0 | 0.967 | 905 | **6.53 @0.06** | 7.48 | 0/0 | **✓** |

**D6: boot1(v1.1) 3/4, boot2(v1.2) 4/4.**

## 5. Odczyt §5 (PASS/FAIL, prerejestrowane)
- **c11 = przyczyna (a) TRANZIENT, (b) OBALONE.** Postęp d_min: shakeout 0.26/1.23 → v1.1(bramka) 1.41 (orbit-phase
  3.23→**5.84**, orbita naprawiona) → v1.2(bramka+mover-fix) **6.53** (D6 PASS). Dowód (a): minimum d_min zawsze na
  GRANICY (t_rel≈0.05 s), NIE w środku przy zmianie kursu; orbit-phase d_min ≥4 już po bramce; po fix v1.2 nawet
  boundary ≥4. Egzekutor (bajt-frozen) nigdy nie był przyczyną. **P-RS2 (c11 nadal łamie) OBALONE.**
- **c00/c05/c10: D6 ✓** oba booty (v1.2 frac 1.0/1.0/0.965). WZGLĘDEM shakeout: frac WZROSŁO poza ±0.006
  (c00 0.949→1.0, c05 0.925→1.0) — **NIE korupcja, lecz USUNIĘCIE TRANZIENTU STARTU**: te epizody miały w shakeout
  własny messy-start (intruz nie w pozie startowej), który depresował frac; bramka go usunęła. Steady-state (d_min_orb,
  tempo omiatania) spójne; egzekutor bajt-frozen. Pasmo ±0.006 vs shakeout FAIL w kierunku POPRAWY — nazwane, benign.
  Uczciwie: to znalezisko §5 (bramka zmienia frac przez tranzient), ale kierunek = poprawa, przyczyna = tranzient, nie steady-state.
- **REFUSE=0, breach=0, |v|≤VMAX** wszędzie. Ważność V1 4/4 odrzuca (deep-stalle), V2 1/4, V3 0/4 (logowane do testu inwariancji D9).

## 6. Predykcje
- P-RS1 (c00/c05/c10 w paśmie): frac≥0.965 — **w paśmie [6,10] TAK**; pasmo ±0.006 vs shakeout NIE (poprawa, wyżej). Mieszana.
- **P-RS2 (c11 nadal łamie d_min): CHYBIONA** — c11 PASS po fixach; (b) nierealne.
- P-RS3 (≤2 set_pose ponad pierwsze, 0 INVALID_START): **0 INVALID_START ✓**; n_setpose 3–19 (>2 ponad pierwsze) —
  częściowo (bramka poluje ~20 Hz przez wait 0.1–0.96 s aż pose/info potwierdzi; koszt bramki mały, wait ≤1 s).

## 7. Commity (niepushowane, dla Olgi)
- `d10c5b2` B3 (§0 decyzja + §2 bramka + §3 freeze v1.1)
- B3b (fix v1.2 interruptible + freeze v1.2)
- B4 (re-shakeout 2 booty + ten raport)

## 8. Noty (nienaprawione poza dozwolonym §4)
- N1 (gt_intruder frac vs shakeout, §5): bramka poprawia frac przez usunięcie tranzientu — kierunek poprawy, nie defekt.
- N2 (koszt bramki): wait 0.1–0.96 s sim/epizod, n_setpose do 19 (poll 20 Hz aż GT≤TOL). Dla kampanii 48 epizodów ≈
  +5–45 s sim łącznie — pomijalne wobec ~72 s/epizod.
- N3 (proc_gate live test): wykluczany gdy dreamforge aktywny (środowiskowe); przechodzi na czystym hoście.
- N4 (blok2/D6): D6 liczone na blok1/48 w kampanii (per §0), booty diag nie wchodzą.

## Werdykt re-shakeout
Bramka startu intruza działa (0 INVALID_START), c11 ROZSTRZYGNIĘTE = **(a) tranzient** (egzekutor czysty, bajt-frozen);
D6 4/4 po v1.2. **STOP-1b.** CC: ANEKS_BENCH-1 (zgoda na kampanię blok1/48) — egzekutor zostaje zamrożony, ewentualne
strojenie = nowa seria po kampanii (SR-3).
