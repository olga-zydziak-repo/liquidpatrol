# RAPORT_D_B4 — DEMO-B blok B4: runnery per-akt + sędzia ważności + kadr-check + rehearsal online

Data: 2026-08-17. Zakres: **wyłącznie B4** — integracja żywa BEZ prób: runnery per-akt, sędzia
ważności (zamrożony PRZED próbami), kadr-check, 1 rehearsal online/akt. NIE: próby ≤3/akt i nagrania
dowodowe (B5), montaż (B6). **`r01/proofs/` i `r01/shield.py` NIETKNIĘTE** (SR-F1). Reżim bez zmian;
prowieniencja per liczba; FAIL=FAIL; **push = Olga**.

## Stan wejściowy / wyjściowy (SR-F5, SR-F1, SR-F2)

- **SR-F5 (pierwsza czynność):** `git log origin/master..HEAD` = PUSTE (Olga pushnęła B3). HEAD =
  origin/master = `7ed9371`, drzewo czyste. (Poprzednie 2 tury: STOP na SR-F5 bo B3 niepushowany;
  Olga pushnęła, wznowiono.)
- **`certs_selfcheck` bieg #1: 6/6 · bieg #2: 6/6** — `r01/proofs/`+`shield.py` NIETKNIĘTE (SR-F1).
- **SR-F2:** żaden bieg NIE oznaczony/użyty jako „próba" — wszystkie `rehearsal_online_1`, note
  „REHEARSAL/integracja — NIE próba (B5); percepcja NIERAPORTOWALNA". Licznik prób NIE wystartował.
- **SR-F6:** dwa niepowodzenia po drodze były EXPLAINED (env-var `SCENARIO` vs `SCEN`; nakładka biegów
  przy relaunchu) — nie „niewyjaśnione". Naprawione, potem 3 czyste booty. GUI=brak we wszystkich (ANEKS-H).

## §1 — Runnery per-akt

Wyprowadzone z patched `gate_run_r02` (A1/A2, scenariusze `scenario_A1`/`scenario_A2`) i `gate_run_r03`
(A3, SCEN=S2). Orkiestrator wieloaktowy OUT (A3-aneks). Rdzeń deterministyczny w `acts/act_common.py`
(testowany `tools/test_act_common.py` 7/7): trajektoria intruza f(sim_t) ze spec, budowa manifestu
(hashe z plików), **assert A4 `token_gated=True`** (start z False ⇒ RuntimeError).

- Choreografia: kanał GT-fed (deterministyczny ENTRY) + intruz WIDOCZNY teleportowany tym samym f(sim_t)
  (`set_pose`, MODEL — mechanizm zgodny z REGATE) w wątku ~2 Hz (poza torem decyzji). Beat operatora =
  skryptowany sygnatariusz (A5) na `on_entry + 3.0` (delay ze spec). `admission_seq` na żywo, `intr_ned`
  live (domyka lukę (f) z B3).
- **Manifest per akt** (`manifest.json`): HEAD, hash świata (z pliku), hash spec, hashe certów (z P*.json),
  echo `token_gated=True`, kontencja, wersja schematu trace, blok ANEKS-H.
- Launchery `acts/run_act.sh` (A1/A2), `acts/run_A3.sh` (A3); bridge+capture kamery filmowej (pipeline R2).

## §2 — Sędzia ważności (ZAMROŻONY, ANEKS_D3)

`tools/act_judge.py` — kryteria PRE_D §5 **1:1** (mapowanie w ANEKS_D3). Wejście = trace+manifest+spec,
wyjście = VALID/INVALID + kryteria. „Trace kompletny" = `gen_subtitles.REQUIRED_EVENTS` (jedno źródło).
**FREEZE:** `sha256 = 79b1e936…526a671a` (ANEKS_D3; zmiana ⇒ adnotacja + ratyfikacja, SR-F3).

Testy `tools/test_act_judge.py` **9/9**: pozytywne (A1/A2/A3 fixtures VALID, wszystkie kryteria),
negatywne (usunięte zdarzenie ⇒ INVALID z nazwą; A3 refuse>0.15 ⇒ INVALID; A1 no_auth po tokenie ⇒
INVALID; brak manifestu ⇒ aneks_h FAIL), B3 fixtures trace-kompletne. Fixtures `tools/b4_fixtures/`
(oznaczone `fixture`, judge-tuned; osobne od B3 pod timing/geometrię).

## §3 — Kadr-check i rehearsal online (integracja, NIE próby)

Kadr-check: render klatki filmowej per akt (intruz w pierścieniu) — A1 mean=200.2/min=22, A3
mean=210.6/min=39 (ciemne sylwetki obecne). Pipeline kamera→pliki: 21/21/16 klatek. Frame'y `.npy`
(56 MB/akt) gitignore; dowód = `kadr_check.log`. **Światy nietknięte po freeze B2** (hashe zgodne z
ANEKS_D2, SR-F4). Framing geometrycznie poprawny (konwencja x=x codebase); ocena pikselowa = B5.

**1 rehearsal online/akt** (pełny SITL, headless, ANEKS-H) — werdykt SĘDZIEGO (integracja/kontrola/token/
timing; percepcja NIERAPORTOWALNA):

| Akt | świat | ANEKS-H | sędzia | dowód integracji |
|---|---|---|---|---|
| **A1** | `d7e3db24` | headless, tj 0, EKF 0, hash✓ | **VALID 5/5** | ENTRY r=8.03∈[7,9]; **NO_AUTH 25.3s < grant 28.4s**; OBSERVE 447t, min_d 6.44, 0 naruszeń D_safe; token wydany |
| **A2** | `dd0c85e2` | headless, tj 0, EKF 0, hash✓ | **INVALID** (`trace_complete`) | ep0 pełne (NO_AUTH→token→OBSERVE→EXPIRE); **re-admisja NIE — limit GT-fed** (niżej) |
| **A3** | `486a0cea` | headless, tj 0, EKF 0, hash✓ | **VALID 4/4** | **REFUSE(POS_DEGRADED) 0.102s ≤ 0.15**; velocity-descent (166t POS); **touchdown r_est 14.81m ≤ R_E=32** |

Napisy z realnego trace A1 (pierwszy realny trace przez `gen_subtitles.py`): OK, 11 segmentów, 6 plansz;
wykryte entry/refuse_no_auth 25.3, grant 28.4, observe 28.4, expire 51.0 — sanity generatora (nie materiał
dowodowy). A2: `gen_subtitles` POPRAWNIE ODMÓWIŁ (asert kompletności: brak readmit/grant2).

Regresja: **76 testów PASS** (r01 22, r02/r03 34, tools 20 [9 subs + 9 judge + 7 common − pokrycie]).

## Rozbieżności (jawnie)

1. **A2 re-admisja nie zaszła w rehearsalu — ZNALEZISKO (GT-fed).** Kanał rehearsalu = projekcja
   geometryczna (deterministyczna), NIE modeluje ZASIĘGU detekcji. Spec `intruder_far_enu=[70,0,11.5]`
   (70 m przed dronem) jest geometrycznie w FOV → box → brak EXPIRE-po-zasięgu → brak re-admisji. (A1
   EXPIRE zadziałało bo parking jest NISKO = poza FOV poziomej kamery.) **W locie LIVE (detektor z
   limitem zasięgu, B5) 70 m niewykrywalne → EXPIRE.** Re-admisja UDOWODNIONA deterministycznie
   (`test_act_judge` fixtures A2 VALID + `test_token_authz` consume/admission_seq/nowy-token). Spec B2
   zamrożony NIE ruszany; poprawka FOV-exit = B5 albo osobna adnotacja.
2. **Sędzia „VALID" na A1/A3 to werdykt INTEGRACJI, nie percepcji** (§3: percepcja nieraportowalna).
   Kryteria geometryczne (entry_in_ring) liczone z GT-projekcji (deterministyczne). Dowód percepcji
   LIVE = B5 (próby, detektor).
3. **A3 = gate_run_r03 SCEN=S2** (denial czasowy t=12 s w patrolu), mapuje spec radial-denial (≤R_route'
   =20.5): oba dają containment (touchdown ≤ R_E). Ścieżka R0.3a NIETKNIĘTA (RAPORT_R03A S2 proven).
4. **RTF nie próbkowany gz-stats** w rehearsalu (integracja) — w manifeście `rtf=0.992` wyprowadzone z
   tick-period p50=0.0504 s (stall_dist R3, ZMIERZONE). gz-RTF = B5. ANEKS-H timejump 0/EKF 0 zmierzone wprost.
5. **Dwa niepowodzenia środowiska (EXPLAINED, nie SR-F6):** (a) env-var `SCENARIO` vs `SCEN` w
   run_act.sh → pierwszy A1 boot poszedł jako G1; naprawione. (b) nakładka biegów przy pośpiesznym
   relaunchu → kolizja portów. Po pełnym teardownie 3 czyste booty (A1/A2/A3).

## STOP

Blok B4 domknięty: runnery per-akt (assert A4, live intr_ned, manifest), sędzia ZAMROŻONY (hash w
ANEKS_D3, 9 testów), kadr-check (render OK), 3 rehearsale online (A1 VALID · A2 INVALID/znalezisko GT-fed
· A3 VALID), 76 testów regresji, selfcheck 6/6 ×2. **B5 (próby ≤3/akt, reguła „pierwsza ważna", nagrania
dowodowe, detektor LIVE) — osobny prompt po przeczytaniu raportu przez Olgę. Push = Olga.**
