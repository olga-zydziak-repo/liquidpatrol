# RAPORT_AKW_S2 — desk klifu ω·dt + reguła §5 + re-smoke (ANEKS_AKW-1 §6)

Wykonawca · 10.10.2026 · ARCH-1 = ANEKS_AKW-1.md VERBATIM w korzeniu (commit 80484a5c,
pierwszy w sesji). KAMPANIA NADAL NIEZWOLNIONA (werdykt = ANEKS_AKW-2).

## §1. Bramka wejściowa (§6.1) — PASS w całości

origin/master zawiera cc212d2a ✓ · ahead pusty ✓ · porcelain pusty ✓ · FROZEN
wykonaniem: piny k1_shield 5/5 PASS · certy 9/9 PASS (certs_selfcheck) · narzędzia AKW
3/3 (driver fcff9b30, analyze e9b3bdfb, testy 6ee42fd5) · wrapper 2237cc7c i rejestr
4f58d204 sprzed edycji profilu ✓ · dziedziczone 10/10 (bench_flight 05137098,
bench_judge 8ec0fcfb, feed_vision acc81df7, det_v2.pt 775ead15, det_v2.py e801f7d5,
percep_proc 38a3a765, feed_vision_proc 79633489, feed_registry ee1481f9, ncp.npz
0337d5ea, net_controller e8c1b658).

## §2. S2a desk — lokalizacja klifu admisji (zero bootów)

Przyrząd: `results/AKW/tools/akw_s2a_cliff.py` (NOWY, sha 9b014b57; rozszerzenie
akw_rot_strat per §4 — oryginał S0 w AKW_RECON nietknięty). Wynik:
`results/AKW/s2a_desk/akw_s2a_cliff.json` + 12 replayów zdecymowanych
`results/AKW/s2a_desk/replays_dec2/` (frozen det_replay.py subprocesem, bajt w bajt,
na bootdirach-cieniach z co 2. klatką — brama YOLO+MTI NAPRAWDĘ przeżywa podwojony
obrót międzyklatkowy; pasmo osiągnięte: °/kl p50 1.67–2.47, p90 3.9–5.2).

**WALIDACJA PRZYRZĄDU (bramka wejściowa desku): PASS co do sztuki.** Na dokładnym
podzbiorze S1 (okna epizodów ślepych c01–c03 z trace.jsonl): boot 2 → box 1925 /
fresh 1823 (gate mti 1799 + window 24); boot 3 → box 235 / fresh 0. Identycznie
z tabelą RAPORT_AKW_S1 §3.

### §2a. Odchylenia/doprecyzowania JAWNE wykonania §4

1. **Decymacja percep_feed kampanii NIEWYKONANA** (litera §4b): booty kampanii V2
   i smoke NIE MAJĄ klatek na dysku (zapis = rekordy, nie obrazy), a mti_ok wymaga
   re-egzekucji MTI na klatkach — decymacja rekordów bez klatek byłaby fałszerstwem
   (przypisałaby stare admisje nowemu ω·dt). Kampania V2 weszła do binowania bez
   decymacji (pasmo natywne 0–2.5°/kl); syntetyczne pasmo 1.4–3.4°/kl dają replaye
   dolotu (jedyne booty z frames/).
2. **Rozbicie po reżimie (locked)** — wymusił je pierwszy przebieg: tabela mieszana
   po ω·dt jest NIEMONOTONNA, bo ω·dt korpusu ≠ ruch pikselowy CELU. W śledzeniu
   (locked: nos na celu, box pikselowo ~stacjonarny, px_speed p50 0.003–0.03) admisja
   przeżywa do ≥4.5°/kl; w akwizycji (unlocked: cel TRANSITUJE kadr z prędkością
   ≈ ω·dt) admisja per klatka nie przekracza kilkunastu %. To reżim akwizycji jest
   tym, który skan musi przeżyć, żeby ENTRY zaszło.

### §2b. Tabela admisji vs °/kl (admisja = box ∧ central(edge≥0.10) ∧ mti_ok; cel w FOV)

REŻIM AKWIZYCJI (locked=False) — ten, o który toczy się noga:

| bin °/kl | n_fov_box | adm% | failC% | failM% | px_p50 |
|---|---|---|---|---|---|
| 0.0–0.3 | 53 | 24.5 | 41.5 | 34.0 | 0.009 |
| 1.5–1.8 | 47 | 8.5 | 4.3 | 87.2 | 0.017 |
| 1.8–2.1 | 85 | 5.9 | 20.0 | 74.1 | 0.018 |
| 2.1–2.4 | 77 | 9.1 | 7.8 | 83.1 | 0.018 |
| 3.6–3.9 | 69 | 7.2 | 10.1 | 82.6 | 0.033 |
| 3.9–4.2 | 40 | 15.0 | 15.0 | 70.0 | 0.032 |
| 5.1+ | 145 | 15.9 | 8.3 | 75.9 | 0.071 |

(biny o n<30 pominięte w druku; komplet w JSON). Statystyka per-klatka w akwizycji
jest obciążona przeżywalnością (udany ciąg k=3 ucieka do locked), więc NIE osiąga 90%
nawet w paśmie, gdzie akwizycja ze skanu W LOCIE działała (boot 2, 2.04°/kl, ENTRY
ze skanu c02/c03) — ale rozdziela tryby: smoke_fast acq 4–16% admisji per klatka
(ENTRY wieloprzebiegowe zachodzi), smoke_slow acq 0–3% (ENTRY nie zaszło nigdy).

REŻIM ŚLEDZENIA (locked=True, kontekst): adm% 97–99 w binach 0.6–3.6°/kl, 96–97
w 3.6–4.5, 90–92 w 4.5–5.1, 84 w 5.1+ — potwierdza, że przy boxie pikselowo
stacjonarnym brama toleruje duże ω·dt korpusu; klif S1 NIE był klifem śledzenia.

MIESZANA (prereg §4 literalnie): ≥90% w binach 0.3–3.6, spadek od 3.6 (81.4/85.5/88.8),
60.6→64.6% w 5.1+; bin 0.0–0.3 = 87.0% (hover: wolno poruszający się/odległy cel pada
na MTI — mechanizm znany z DET). Prefiks ciągły ≥90% łamie się na pierwszym binie ⇒
literalne κ₉₀ = 0.0.

### §2c. Dekompozycja członów (który pada pierwszy)

**Pada MTI** — w reżimie akwizycji fail_mti 70–95% klatek z boxem w FOV (koincydencja
box↔komponent MTI SPÓJNY CZASOWO; persystencja 3-z-4 przy move_thr 0.10 nie składa się
nad celem transitującym kadr). fail_central 4–24% (transit przez strefy brzegowe —
edge-margin 0.10). k=3/ENTRY_MOVE_THR **nie binduje**: k3_move_break 0.0% we
wszystkich binach z danymi (≤5.1); conf nie jest bramą (A1). Kolejność: MTI ≫
central ≫ (k=3 nigdy).

### §2d. κ₉₀ i zastosowanie REGUŁY §5 (mechanicznie)

Kandydaci κ₉₀ (wszystkie odczyty definicji, jawnie):

| odczyt | κ₉₀ [°/kl] | ω_safe = 0.85·κ₉₀·7.58 |
|---|---|---|
| literalny (tabela mieszana, prefiks ciągły ≥90%, n≥30) | 0.0 | 0.0 |
| reżim akwizycji (jw. na tabeli acq) | 0.0 | 0.0 |
| dowód skanowy wprost (górna krawędź bina punktu 2.04 = jedynego °/kl z DOWIEDZIONĄ akwizycją ze skanu w locie; następny punkt skanowy 3.96 = 0/235) | 2.1 | **13.53** |

**Nawet najkorzystniejszy obroniony odczyt daje ω_safe = 13.53 < 14 ⇒ ŚCIEŻKA II
(step-and-stare) — decyzja NIEZALEŻNA od interpretacji definicji κ₉₀.** (Odczyt
„największy jakikolwiek bin ≥90%" odrzucony jawnie: wskazywałby 4.8°/kl z danych
czysto śledzeniowych, podczas gdy 3.96°/kl skanu jest zmierzone jako 0/235 — tabela
mieszana nie reprezentuje skanu powyżej 2.4°/kl, patrz §2a pkt 2.)

Profil ścieżki II (wartości prereg z §5, zastosowane bez zmian): krok **40°** rampą
**60°/s** (0.667 s) → **stare 1.2 s** (ω·dt = 0 ⇒ reżim admisji dowiedziony całym
programem) → kolejny krok; dwell po utracie 2.0 s BEZ ZMIAN; pełny przegląd 9 kroków
≈ **16.8 s**. Bramka A′: **t_A = min(23, ⌈(16.8+3)·1.25⌉) = min(23, 25) = 23 s**.

RYZYKO NAZWANE (przed lotem, niebramkujące): PX4 śledzi komendę kątową z lagiem
P=2.8 — po zakończeniu rampy kroku korpus dokręca resztkę wykładniczo (τ≈0.36 s);
rotacja resztkowa spada <15°/s (≈2°/kl w wolnym modzie) po ~0.5 s stare, co zostawia
~0.7 s (≈5 klatek @7.58 Hz) okna cichego na warmup MTI (Δ=3) + k=3 — budżet ciasny
w wolnym modzie. Mierzalne w re-smoke; wartości stare/kroku są prereg (ZAKAZ zmian
poza t_A), więc nie strojone.

## §3. Edycja profilu + testy (zakres §5: WYŁĄCZNIE akw_scan.py + test profilu)

- `r03/controllers/akw_scan.py`: **2237cc7c → b94cdeae** — tryb profilu
  ciągły-30°/s → step-and-stare (stałe FROZEN w kodzie: MODE step_stare, STEP 40°,
  SLEW 60°/s, STARE 1.2 s; dwell 2.0 bez zmian; ψ_last/baza/reset/zegar bez zmian;
  env tylko AKW_DWELL_S diagnostycznie — parametry kroku BEZ env). Dodatkowo
  domknięcie krawędzi kontraktu wrapu: emisja float-owo równa −π ⇒ +π (krok 2/3 s
  nie leży na siatce ticków 0.05 s i trafia w tę krawędź; stary profil 1.5°/tick
  nie trafiał — ujawnione testem §3.2 po edycji).
- `results/AKW/tools/test_pre_akw.py`: **6ee42fd5 → 5549d934** — §3.2 profil
  przepisany na ścieżkę II (wzorzec `_oczekiwany_offset` NIEZALEŻNY od implementacji;
  nowy assert: ψ STAŁA przez całe okna stare 0/1/2; CCW na rampie; 9 cykli = 360°
  i 16.8 s; dwell/wznowienie-od-ψ_last/reakwizycja/reset bez zmian semantyki);
  §3.3 asserty stałych profilu zaktualizowane. **§3.1 pass-through BEZ ZMIAN
  merytorycznych** (jedyny diff poza §3.2/§3.3 = lista importowanych stałych).
- Testy przedlotowe: **12/12 PASS** (w tym §3.1 pass-through: ramię B 5714 tików +
  demo V2 3754 + 411 ważnych tracków V2 — bez zmian, przechodzą na nowym profilu).
- Regresja istniejących: **143 passed / 0 failed** pod ROS env (pełny przegląd
  wszystkich plików testowych repo: bench/net/harness/r01(+proofs FV)/r02/r03/tools
  + results/{DET,2A,R02,AKW}/tools). Nota liczności: S1 raportował „210 passed" —
  różnica = zakres kolekcji (skład 210 nieodtworzony z notatki S1; dzisiejszy
  przegląd obejmuje każdy plik test_*.py + tests_fv_* w repo poza zależnościami).
  Bez ROS env identyczny zbiór daje 3 FAIL w testach rclpy-zależnych
  (test_aneks_det2 ×2, test_aneks3 ×1) — środowiskowe, nie importują akw_scan;
  pod ROS env przechodzą. `r01/brake_test.py`/`r02/test_deadman.py` jak od zawsze
  skrypty rclpy (pod ROS env kolekcjonują 0 testów pytest).
- `results/AKW/FREEZE_AKW.md`: wpis przed/po (tabela S2 + tabela S1 oznaczona
  HISTORYCZNE) + NOTA o opisowym polu `scan_dps_frozen: 30.0` w manifestach drivera
  (driver FROZEN, poza listą edycji — pole od S2 historyczne; prawda =
  akw_scan_sha256 liczony na żywo).

## §4. Re-smoke (§6.4) — boot 4 nogi, `camp/resmoke_r1_V2` — 1 boot, bez naprawczego

Reżim jak S1: driver FROZEN `akwS1_boot.sh` (cooldown, proc_gate SUSTAINED CLEAN 3×30 s,
wyłączność), FEED=V2, CONTROLLER=net_akw (profil II z kodu; env AKW_* nieustawione —
guard aktywny), epizody c00–c03×s01, rc=0, manifest wstrzyknięty (akw_scan_sha256 =
b94cdeae… — zgodny z FREEZE po edycji).

**NOTA MODU (prereg §6.4): boot wylądował w SZYBKIM modzie kadencji — 14.71 Hz p50**
(stwierdzone na żywo z dt percep_feed po ~300 rekordach i potwierdzone całością:
3283 klatki). Bramka A′ liczy się normalnie (poniżej), ale wolno-modowa praca profilu II
pozostaje niezlatana — kampania dostaje BEZPIECZNIK MODU (wpis prereg, egzekwowalny
na bieżąco z dt percep_feed): pierwszy wolno-modowy boot V2 kampanii z ZEREM admisji
przy celu w FOV ⇒ przerwanie na granicy rundy + ANEKS.

### Tabela per epizod (sędzia pełny frozen judge_boot; klasy ENTRY jak R3)

| epizod | ważność (dsim) | t_first_fresh | **t_entry** | ENTRY klasa | D6 | reakw. | osc. ≤5 s | err_fresh p50/p95 |
|---|---|---|---|---|---|---|---|---|
| c00_s01 (kontrolny) | ✓ 0.9769 | 31.01 | 33.39 | F1_cel | ✗ (a_entry, c_sweep) | 1 | 1 | 0.69/1.30 |
| c01_s01 (ślepy) | ✓ 0.9831 | 0.03 | **8.97** | F1_cel | **✓** | 1 | 1 | 0.141/0.461 |
| c02_s01 (ślepy) | ✓ 0.9753 | 8.97 | **11.62** | F1_cel | **✓** | 1 | 0 | 0.104/0.230 |
| c03_s01 (ślepy) | ✓ 0.9764 | 13.14 | **15.78** | F1_cel | **✓** | 1 | 0 | 0.137/0.218 |

- Ważność 4/4 (dsim_dwall 0.975–0.983, deep-stalle bez długich; alive_feed ✓×4).
- **Admisja w epizodach ślepych: 1990/2023 = 98.4%** (gate mti 1985 + window 5) —
  LEPIEJ niż ciągły profil S1 w tym samym szybkim modzie (94.7%); okna stare robią
  robotę zgodnie z mechanizmem.
- **FP tła 0**: wszystkie ENTRY w epizodach F1_cel (err vs GT w normie); 2 ENTRY
  pozaoknowe @108.50 i @182.95 = klasa **F2 lock-przed-epizodem na stagingu**
  (108.50 = 0.1 s przed oknem c00, trk (−0.69, 6.73) ≈ staging z S1 (−1.0, 6.6);
  182.95 = przerwa teleportowa c00→c01, luka GT ±4.4 s) — dokładnie mechanizm
  DET-4 §3 / S1, zero nowych klas.
- err_fresh po akwizycji na ślepych p50 0.104–0.141 — jeszcze lepiej niż S1
  (0.16–0.22) i wielokrotnie lepiej niż DET (0.418); brama REFRESH zdrowa.
- **Mechanizm c00 (kontrolny, bez zmian klasy):** znany lock przedepizodowy F2 na
  fantomie stagingu → skan od ψ_last wskazującego fantom → reakwizycja celu
  STATYCZNEGO (v=0 ⇒ MTI ślepy, admisja wieloprzebiegowa) po 33.4 s — szybciej niż
  S1 boot 2 (63.8 s), nadal poza D6. c00 nie jest bramką A′ (ślepe = c01–c03);
  mechanizm pozostaje nazwany w rejestrze (kandydat na odrębną nogę/decyzję ANEKS).
- NOTA PRZYRZĄDOWA: pola `deg_skanu_do_*` analyzera (FROZEN, poza listą edycji §5)
  liczą stopnie wzorem profilu S1 (30°/s·t) — od S2 są NOMINALNE, nie fizyczne;
  fizyczny przebieg yaw niesie `yaw_sanity_ulog` (p50 |dψ/dt| segmentów rotacji
  14.2°/s = mieszanka kroków 60°/s z lagiem P i stare ~0°/s; 5368° omiecione —
  spójne z profilem II; pasmo 25–35°/s już NIE jest sygnaturą profilu: 1.8% czasu).
- Ryzyko PX4-lag z §2d NIE zmaterializowało się w szybkim modzie (admisja 98.4%,
  t_entry 9–16 s); w wolnym modzie pozostaje otwarte → bezpiecznik modu.

## §5. Werdykty bramek re-smoke (formalnie)

- **A′: PASS 3/3** — ENTRY ze skanu w 3/3 WAŻNYCH ślepych, t_entry 8.97/11.62/15.78 ≤
  t_A = 23 s (wszystkie także ≤ 20 s starej bramki S1 i ≤ 25 s sędziego; D6 sukces
  3/3 ślepych — pierwszy raz w nodze). Werdykt z `akw_s2_gates.py` (NOWY, cienki,
  na wyjściu frozen analyzera) → `camp/resmoke_r1_V2/akw_s2_gates.json`.
- **C: PASS** — breach 0 ×4, REFUSE 0 (wpis: brak zdarzeń, gałęzie puste), stop_now
  false. Program utrzymuje breach 0 / REFUSE 0 we wszystkim, co kiedykolwiek
  poleciało uzbrojone (+1 boot).
- **B (opisowo, nie bramkuje — ANEKS §2):** kadencja p50 14.71 Hz, E2E p95 0.084 s
  (tożsame z bootem 2 S1 — szybki mod bimodalności narzędziowej).

## §6. Budżet i rytm

Booty nogi: **4/≤32** (3 z S1 + 1 re-smoke; boot naprawczy NIEUŻYTY — ważność 4/4).
Launches S2: 1/≤… (jeden start drivera, bez przerwań). Sesje lotne nogi: 2
(S1 + S2); kampania = S3. **KAMPANIA NADAL NIEZWOLNIONA** — czeka **ANEKS_AKW-2**
(werdykt re-smoke; przy PASS zwolnienie KAMPANII 24+3 z bezpiecznikiem modu jak
w §4). STOP-AKW2.
