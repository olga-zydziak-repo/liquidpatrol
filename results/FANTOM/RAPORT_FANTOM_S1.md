# RAPORT_FANTOM_S1 — budowa kwarantanny + desk T1/T2 + smoke — STOP-FANTOM1

Wykonawca · 15.10.2026 · PRE_FANTOM (ratyfikowany 15.10) + PROMPT_FANTOM_S1.
ARCH-1 = PRE_FANTOM.md VERBATIM w korzeniu (commit a7f3073c, pierwszy w sesji).
**Budżet nogi: booty 1/≤30 (smoke 1, zapas NIEUŻYTY).**

## §0. Bramka wejścia — PASS

origin/master zawiera 15c31143 ✓ · ahead pusty ✓ · porcelain pusty ✓ · FROZEN
wykonaniem: piny 5/5 PASS, certy 9/9 PASS; akw_scan **b94cdeae**, rejestr (przed
wpisem) 4f58d204, FREEZE_DET (det_v2 775ead15, percep 38a3a765, klient 79633489,
rejestr feedów ee1481f9), bench 05137098/8ec0fcfb, ncp 0337d5ea, feed_vision acc81df7.

## §1. Budowa (PRE §1 verbatim)

- **NOWY `r03/controllers/fantom_scan.py`** (sha **e435ed7e**): `FantomScan`
  deleguje `AkwScan` (profil II b94cdeae NIETKNIĘTY); po `reset()` kwarantanna ON;
  t_ref = now_s pierwszego `step()`; w kwarantannie delegat dostaje fd „brak tracku"
  (podmiana NOWYM dictem WYŁĄCZNIE dla fd ważnego — fd nieważny idzie surowy:
  sterowanie identyczne, net_controller.py:108, a echo telemetrii w extra prawdziwe;
  zero mutacji współdzielonych obiektów); wyjście JEDNORAZOWE per epizod; po wyjściu
  pass-through VERBATIM (ten sam obiekt fd, cmd delegata bez kopii). Telemetria:
  `q_active`/`q_exit_reason`/`q_exit_t` w `cmd["extra"]` WYŁĄCZNIE na tickach
  kwarantanny + ticku wyjścia; dziennik diagnostyczny env `FANTOM_QLOG` (jsonl).
- **Rejestr**: wpis `net_fantom` ADDITIVE w `r03/controllers/__init__.py`
  (4f58d204 → **87203d29**). Nota jawna: „+1 linia" PRE = fizycznie 2 linie
  (import + wpis słownika) — identycznie jak precedens net_akw („2 linie additive",
  FREEZE_AKW).

## §2. T1 — tożsamość delegacji (12/12 PASS)

NOTA WYKONAWCZA (interpretacja litery PRE §3.1, dowód w kodzie): delegat niesie
sieć REKURENCYJNĄ (ncp), której stan ewoluuje wyłącznie na tickach track
(net_controller.py:106-111 — invalid fd wraca przed siecią). Bit-w-bit wobec
kontrfaktycznego net_akw, który W CZASIE kwarantanny konsumował co innego, nie może
zajść z definicji kwarantanny — dlatego T1 ma dwie formy, obie dosłowne:
- **T1a świadek-delegat** (ramię B i V2): na KAŻDYM ticku cmd `net_fantom` (modulo
  klucze q_* w kwarantannie) == cmd `net_akw` karmionego strumieniem EFEKTYWNYM —
  pełna tożsamość delegacji, obie gałęzie (track/hold);
- **T1b wprost-vs-net_akw** (epizody ślepego startu — strumień efektywny ≡ realny):
  cmd `net_fantom` == cmd `net_akw` BIT-W-BIT na każdym ticku; od ticku po wyjściu
  dosłowna równość obiektów pól (zero q_*).
Do tego TP (predykat: fantom-statyczny→C; czysty start→A natychmiast; skok>5 m→B;
B-ślad statyczny→C [koszt nazwany]; jednorazowość; reset ponownie uzbraja; zero
mutacji fd; parametry FROZEN) i TR (rejestr + regresja net/net_akw). **Razem 12/12
PASS**; pełna regresja repo: **155 passed / 0 failed pod ROS env ×2** (nota: w
pierwszym przebiegu jednorazowa flaka `test_cykl_zycia_percep_proc` — DET-tools,
klasa środowiskowa, nie importuje fantom_scan; dwa kolejne przebiegi czyste).

## §3. T2 — desk-replay + reguła wyboru (PRE §2, mechanicznie) ⇒ **K1 FROZEN**

Przyrząd `results/FANTOM/tools/fantom_t2.py` (wynik `t2_desk.json`); GT z wartą luki
teleportu (interpolacja przez lukę = artefakt — wykluczona). Odczyt jawny litery
(iii): kwantyfikator „dla ≥8/9" obejmuje całą koniunkcję kryterium.

**K2 (fresh-po-starcie): NIE spełnia wszystkiego — pada (ii):**
- (i) 6/6 N6 trzymane ✓ (K2 nigdy nie odpala fresh na fantomie — zmierzono).
- (ii) 48 śladów B: wyjście 0.508–0.548 s ✓; ALE **lock-real c05_s04: C@3.04 — FAIL**
  (pomiar surowy: track realnie położony przy spawn NIE jest odświeżany w epizodzie
  przez pierwsze 3 s — age rośnie monotonicznie 0.14→3.18, expire 3.04; założenie
  PRE „wychodzi freshem ≤~0.6 s" nie zachodzi w danych); **czyste V2: outlier
  c04_s03 delay 2.97 s — FAIL** (track ważny od 0.04 s, ale to admisja przedstartowa
  o pozycji dalekiej od GT — real_adm 16.06; K2 trzyma do C@3.0).
- (iii) żywe-PASS: 8/9 ✓ (c01_s03 poza — admisja przedstartowa o realnej pozycji).

**K1 (A/B/C) ze złagodzonym (ii) ≤T_q: spełnia wszystko ⇒ WYBRANY:**
- (i) 6/6 N6 trzymane ✓ (zero odpaleń A/B na fantomie-daleko-od-GT).
- (ii) wszystkie wyjścia ≤T_q ✓; **koszt nazwany: wyjście (C) +3 s na 12/48
  epizodach B** (valid-statyczne bez skoku i bez utraty) — reszta B wychodzi
  szybko przez A (pierwszy valid) lub B (skok na spawn).
- (iii) 8/9 ✓ (c01_s03 poza, jak wyżej; c09_s01: wyjście B/A@1.68 = realna admisja,
  pred 5.6 ≤ 1.68+4 ✓).
Tabela per epizod (N6 + c05_s04 + 9 żywych-PASS + 48 B): `t2_desk.json` (rows).
Parametry FROZEN po wyborze: **K1, T_q=3.0 s, D_JUMP=5.0 m; ε=0.5 s (K2) zapisany
jako kandydacki-nieużyty** — `results/FANTOM/FREEZE_FANTOM.md`.

## §4. Smoke — 1 boot V2 (`camp/smoke_s1_V2`; zapas NIEUŻYTY)

Driver-kopia `results/FANTOM/tools/fantomS1_boot.sh` (kopia akwS3_boot; zmiany:
CONTROLLER=net_fantom, KIND=fantom, ścieżki, FANTOM_QLOG→OUTDIR, blok manifestu
„fantom" z fantom_scan_sha256 NA ŻYWO + zdarzenia kwarantanny). Sekwencja epizodów
**[c08_s02, c01_s01, c09_s01]** (ids 20,1,9 — kolejność zachowywana przez bench,
bench_flight.py:164-166): pierwszy epizod bootu = klasa parking-świata; c01_s01 po
epizodzie z intruzem = klasa poprzedni-epizod; c09_s01 = kontrola regresji. rc=0,
ważność **3/3** (dsim 0.921–0.931), mod kadencji **WOLNY 7.58 Hz** (odnotowany;
E2E p95 0.084), yaw ulog p50 13.8°/s (sygnatura profilu II), 3388° omiecione.

**WARUNEK WAŻNOŚCI SMOKE: SPEŁNIONY** — c08_s02 ma ŻYWY fantom@t0 (lock, age≤1,
d(trk, GT_spawn)=16.7 m — parking świata); c01_s01 ma fantom@t0 w wariancie MARTWYM
(lock d=14.4, age>1 — konsument w hold od ticku 0; obie podklasy mechanizmu zaszły).

| epizod | fantom@t0 | kwarantanna (qlog) | realna akwizycja [s] | t_entry sędziego | D6 | AKW (odniesienie) |
|---|---|---|---|---|---|---|
| c08_s02 (N6) | **ŻYWY** (d 16.7) | q_enter(valid)→**wyjście B @0.88 s** (przechwyt skokiem — kanał przeanchorował się na realny cel) | **0.88** | 2.51 | **✓** | FAIL, ślepota 26.8 s |
| c01_s01 (N6) | martwy (d 14.4, age>1) | q_enter(valid)→**C @3.0** (trzymany) | **5.9** | 8.60 | **✓** | FAIL, ślepota 22.3 s |
| c09_s01 (kontrola) | brak (czysty start) | q_enter(invalid)→C @3.0 | 5.34 | 5.09 | **✓** | PASS (1.6 s) — bez regresji |

**Bramki:**
- **A′ PASS**: epizody fantomowe — kwarantanna aktywna od startu ✓ (qlog), q_exit
  zgodny z zamrożonym predykatem ✓ (B-przechwyt / C-fallback), akwizycja 0.88 i
  5.9 s ≤ t_A=23 ✓. **Obie podklasy N6 skonwertowane w locie.**
- **B PASS**: c09_s01 D6 ✓ (akwizycja 5.34 s zgodna z przewidywaniem czystego
  startu 5.6 s z desku — zero regresji; nota: w tym boocie c09_s01 wypadł czysty,
  bez fantomu z kampanii — kontrola pokryła wariant czysty + przewidywanie).
- **C PASS**: breach 0, REFUSE 0 (gałęzie puste), ważność V2′+żywość 3/3, admisja
  ślepych (c01_s01+c09_s01 @FOV) **98.0%** — w paśmie 96–99 bez zmian; manifesty
  1. klasy (blok fantom: sha wrappera/delegata/rejestru na żywo, predykat,
  q_events) ✓.

**Odchylenia jawne:** (1) końcowy print drivera mówi „controller=net_akw"
(odziedziczona linia printu; TREŚĆ manifestu poprawna — blok fantom z właściwymi
sha; czysto kosmetyczne, do poprawy przy kopii kampanijnej S2); (2) kadencja
PASS_kadencja=False w gate_b — litera progu 8 Hz z DET; w nogach AKW/FANTOM B jest
telemetrią opisową (ANEKS_AKW-1 §2), mod WOLNY odnotowany wprost; (3) c01_s01
wystąpił w wariancie martwym (age>1 @t0), nie żywym jak w kampanii — mechanizm
zaszedł, konwersja zmierzona; wariant żywy tej podklasy zweryfikuje kampania S2.

## §5. Budżet i rytm — STOP-FANTOM1

Booty nogi: **1/≤30** (zapas smoke nieużyty). Testy: 12/12 + regresja 155.
FREEZE_FANTOM: predykat K1 + parametry + sha (wrapper e435ed7e, rejestr 87203d29,
test 73c7825f, t2 b7bf402a, driver — sha w commicie). Artefakty: `t2_desk.json`,
`camp/smoke_s1_V2/**` (w tym fantom_qlog.jsonl, akw_summary.json), monitor log.
Porcelain po commicie: pusty. Push = Olga. Dalej: **ANEKS_FANTOM-1** (przyjęcie +
zwolnienie kampanii S2 albo korekty). STOP.
