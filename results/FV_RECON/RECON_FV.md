# RECON_FV — recon nogi „weryfikacja formalna" (FV, pozycja 1b)

**Autor:** CC · 11.09.2026 · sesja doc-only/read-only (BEZ bootów, GPU, treningu, instalacji).
**Reżim:** read-only. Każda liczba/cytat ma źródło `ścieżka:linia`. Twierdzenie bez źródła nie istnieje.
**Cel:** zebrać deltę FV wobec dowodów już stojących (R1), zmapować jądro decyzyjne (R2), wyliczyć
kandydackie obligacje dowodowe (R3), zważyć wiązanie model↔kod (R4), inwentarz stretch (ii) (R5),
arytmetyka zakresu + pytania do PRE (R6). PRE pisze CC po decyzjach Olgi; ta sesja NIE buduje nogi.

---

## R1 — Inwentarz dowodów ISTNIEJĄCYCH (delta FV liczona wobec tego)

Sześć certów w `r01/proofs/certs/`. Dla każdego: co dowiedzione, na jakim modelu, którym proverem,
czego JAWNIE NIE obejmuje.

### P1 — własności automatu decyzyjnego (`r01/proofs/certs/P1.json`)
- **Dowiedzione:** 9 liści automatu `_decide` spełnia P1a–P1h (m.in. ALLOW ⇒ ¬geo ∧ ¬pos_bad ∧ ¬terminal;
  REFUSE ⇒ reason ∈ 6-elementowego zbioru; latch monotoniczny; OBSERVE-ALLOW ⇒ auth_ok) —
  `r01/proofs/certs/P1.json` pola `properties` P1a–P1h; werdykt `"PROVED"`, 10 obligacji `unsat`.
- **Model:** automat `r01/shield.py:_decide` z `geo` jako predykatem boolowskim (arytmetyka bariery
  wyłączona do P2), `pos_bad` jako zwalidowana flaga PO debounce, `auth_ok` jako wejście boolowskie
  z authz — `P1.json:assumptions[0..3]`. Priorytet: `latch>R-POS>R-G>abort>hold>return>{OBSERVE∧auth_ok|R-AUTH}>patrol`
  (`P1.json:automaton`).
- **Prover:** `r01/proofs/verify.py` (1-indukcja z3, z3_lib 5.0.0) — `verify.py:1-11`.
- **NIE obejmuje:** arytmetyki geofence (`geo` jest tu nieinterpretowanym Boolem — `P1.json:assumptions[1]`);
  żywotności osłony (założenie „żywej osłony", `P1.json:assumptions[4]` — martwa pętla poza P1);
  zawierania ε_pos (osobno P2-ε).

### P2-analog — bariera geofence (`r01/proofs/certs/P2.json`)
- **Dowiedzione (warunkowo):** `Inv(p,v)=0≤v≤v_max ∧ p+v²/(2·a_brake)≤R_E ⇒ p≤R_E`
  (`P2.json:theorem`); próg ostrości `A_min=1.4469…`, `a_brake≥A_min` (`P2.json:A_min_threshold_ms2`,
  `a_brake_ge_A_min:true`). 6 obligacji `unsat`.
- **Model:** stałe wymierne `v_max=3, t_react=1/5, R_route=2829/100, R_E=32, a_brake=2`
  (`P2.json:constants_rational`); dynamika PX4 zredukowana do bariery — twierdzenie WARUNKOWE, nie
  o pełnym Gazebo (`r01/proofs/geofence.py:1-4`).
- **Prover:** `r01/proofs/geofence.py` (z3 NRA + próg) — `geofence.py:1-14`.
- **NIE obejmuje:** rzutów poza najgorszą oś (założenie „rzut na promień", `P2.json:assumptions`);
  martwej osłony (backstop = natywny GF R_GF=37, `P2.json:assumptions[5]`); błędu estymaty pozycji
  (to P2-ε). Wariant **P2_vmax3p1** (`r01/proofs/certs/P2_vmax3p1.json`) = to samo twierdzenie przy
  `v_max=31/10`, `A_min=1.5550…`, nadal `a_brake≥A_min` — czyli margines trzyma do v_max=3.1.

### P2-eps — zawieranie z błędem pozycji, forma plateau (`r01/proofs/certs/P2_eps.json`)
- **Dowiedzione (warunkowo):** `(r_est≤R_route') ∧ (0≤ε≤ε_cap) ∧ (r_true≤r_est+ε) ⇒ r_true+d_stop≤R_E`
  (`P2_eps.json:theorem`), z ostrością dwustronną: kontrprzykłady `sat` przy `ε_cap+δ` i `R_route'+δ`,
  próg dokładny `unsat` (`P2_eps.json:obligations`, `:sharpness`). `R_route'=199/10=19.9`.
- **Model:** `R_route'=R_E−d_stop−ε_cap` (reguła D11), `ε_cap=37/4=9.25`, `d_stop=57/20=2.85`
  (`P2_eps.json:constants_rational`); Land pokryty przez cap, człon rate USUNIĘTY (model obalony B1 —
  `P2_eps.json:land_note`).
- **Prover:** `r01/proofs/eps_verify.py` (z3 NRA) — `eps_verify.py:1-16`.
- **NIE obejmuje:** dowodu, że ε_pos rzeczywiście ≤ ε_cap w locie — to założenie A-plateau [A4] walidowane
  EMPIRYCZNIE w bramce D13c, nie dowodzone (`P2_eps.json:assumptions[0]`). To jest granica: cert wiąże
  zawieranie z ograniczeniem ε, ale ograniczenie ε jest zewnętrznym pomiarem.

### P4 — admisja/gramatyka/token (`r01/proofs/certs/P4.json`)
- **Dowiedzione (test wyczerpujący + property-based):** 24 checki `true` (m.in. in-grammar⇒ALLOW,
  out⇒COMMAND_INVALID, stale⇒STALE_CMD, geofence-target⇒GEOFENCE, token default-deny, nonce jednorazowy,
  token wiąże epizod, tamper wykryty) — `P4.json:checks`; 2000 sekwencji admisji + 1500 tokenów +
  HMAC-SHA256 (`P4.json:method`).
- **Model:** gramatyka 8 komend (`P4.json:grammar`), authz `r01/authz.py`, język `r01/language.py`.
- **Prover:** `r01/proofs/p4_verify.py` (property-based, BEZ z3) — `p4_verify.py:1-13`.
- **NIE obejmuje:** dowodu symbolicznego (to testy skończonej próbki, nie kwantyfikacja z3);
  siły kryptograficznej HMAC (placeholder klucza, `r01/config.py:52-53`); „secure C2" — jawnie tylko
  authority-gating (`P4.json:properties.token`).

### P5 — konformancja kod↔model (`r01/proofs/certs/P5.json`)
- **Dowiedzione:** per-tick zgodność `verify.py:tau ≡ r01/shield.py.step` (decyzja+reason+stan-po) na
  400 epizodach losowych + 21 celowanych, pokrycie 9/9 przejść, `mismatches:0` (`P5.json:episodes_random`,
  `:coverage`, `:mismatches`). To WIĄŻE P1 z KODEM egzekutora (`P5.json:binds`).
- **Prover:** `r01/proofs/conformance.py` — `conformance.py:1-8`.
- **NIE obejmuje:** ticków spoza próbki (400+21 epizodów, nie kwantyfikacja po wszystkich wejściach —
  choć tau jest dowiedziony po wszystkich, konformancja jest próbkowa); żywotności; arytmetyki bariery.

### Guard prowieniencji
`r01/proofs/certs_selfcheck.py` porównuje `model_sha256` każdego certu z sha proverа — rozjazd = FAIL
(`certs_selfcheck.py:1-13`). To pilnuje, że cert wskazuje żywy prover w repo.

### DELTA FV (co byłoby NOWE wobec R1)
Już stoi: dominacja/latch/reasons/observe-auth (P1, kwantyfikacja z3), bariera geofence warunkowa (P2/P2_eps),
konformancja próbkowa (P5), admisja/token (P4). **Luki, które FV mógłby domknąć:** (i) własności NA KODZIE
wołanym produkcyjnie (P1/P5 dotyczą `_decide`/`step`, ale D5 `safe_descend_step` i histereza `_pos_monitor`
w czasie NIE mają osobnego twierdzenia — patrz R3c/R3e); (ii) semantyka histerezy jako inwariant temporalny
(P5 jest „niezależny od M", `P5.json:r03a_note` — czyli M nie jest dowodzony, tylko pomijany); (iii) własność
żywotności/dead-man jako twierdzenie (dziś: test `r02/test_deadman.py`, `P1.json:assumptions[4]`), nie dowód.

---

## R2 — Mapa jądra decyzyjnego

Pliki: `r01/shield.py` (225 l., `wc`), `r03/controllers/safe_descend.py` (49 l.).

### Ścieżki decyzyjne `_decide` (`r01/shield.py:146-206`) — kolejność = priorytet
1. **R-T latch terminal** — `if self.terminal is not None` → REFUSE(zatrzaśnięty reason) (`shield.py:148-151`).
2. **R-POS** — `if self._pos_refuse` → REFUSE(POS_DEGRADED), stan POSDEG, action VELOCITY_DESCENT; ODWRACALNY,
   PONAD R-G (prekondycja: bariera na niepewnym p niewiarygodna) (`shield.py:157-160`).
3. **R-G geofence** — `viol,_=self._geofence_violation(...)` → REFUSE(GEOFENCE), latch, DONE (`shield.py:163-167`).
4. **R-A abort** — `mode==M_ABORT` → REFUSE(ABORT), latch, DONE (`shield.py:170-173`).
5. **R-H hold** — `mode==M_HOLD` → HOLD, stan HOLDING (`shield.py:176-179`).
6. **R-R return** — `mode==M_RETURN` → HOLD (do przejęcia RTL), stan RETURNING (`shield.py:182-185`).
7. **R-O / R-AUTH observe** — `mode==M_OBSERVE`: `if not auth_ok` → REFUSE(NO_AUTH) stan NOAUTH ODWRACALNY
   (`shield.py:194-198`); wpp ALLOW, stan OBSERVING, applied=target (`shield.py:199-201`).
8. **R-P patrol** — domyślnie ALLOW, applied=target (`shield.py:204-206`).

### Automat — stany/tryby
- Stany: `PATROL, HOLDING, RETURNING, DONE` (`shield.py:36`), `POSDEG` (odwracalny, `:37`),
  `NOAUTH` (odwracalny, `:38`), `OBSERVING` (`:48`). Terminal-latch tylko przez `self.terminal` (R-G/R-A/admisja).
- Reasons (6): `GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT` (`:40-41`), `POS_DEGRADED` (`:42`), `NO_AUTH` (`:43`).
- Tryby wejściowe: `PATROL, HOLD, RETURN, ABORT` (`:45`), `OBSERVE` (`:46`).

### Wejścia `step(k, pos, vel, target, mode, pos_flag=None, auth_ok=True)` (`shield.py:121`)
- `pos`, `target`: krotki 3D (NED); `vel`: prędkość; `mode` ∈ trybów; `pos_flag`: zwalidowana flaga
  dead-reckoning (None ⇒ monitor nieaktywny, `shield.py:80-81`); `auth_ok`: bool z authz.
- **Bounded i skąd granice:** `r_e=32` (`r01/config.py:30`), `v_e=20` (`:31`), `v_max=3` (`:24`),
  `a_brake=2` (`:26`), `dt=0.05` (`:41`), `delta_margin=2.85` (`:27`). ε_cap=9.25 (`r03/config.py:20`),
  `R_route'=19.90` (`:25`), `debounce=2` (`:30`), `hyst=5 s` (`:31`). `v_max` clamp bariery: `_braking_dist`
  bierze `min(hypot(vel), v_max)` (`shield.py:98`) — prędkość wejściowa NIE jest z góry ograniczona w
  argumencie, dopiero saturowana w barierze.

### `_pos_monitor(pos_flag)` (`shield.py:76-94`) — histereza
- Wejście: `pos_flag` (True⇒debounce++, `:83`; próg `pos_debounce_ticks`=2 ⇒ `_pos_refuse=True`, `:85-87`).
- Wyjście: `pos_flag` False resetuje `_pos_bad`; w stanie refuse zlicza `_pos_healthy`, próg
  `pos_hyst_ticks=round(5/dt)` ⇒ re-ALLOW (`:88-94`). To jedyne miejsce z semantyką TEMPORALNĄ (liczniki).

### `_geofence_violation(pos, vel, target)` (`shield.py:101-112`)
- `tr=radial(target)`; `tr>r_e` ⇒ viol (`:104-106`). `pr+_braking_dist(vel)>r_e` ⇒ viol (`:107-109`).
- `|target_z|>v_e ∨ |pos_z|>v_e` ⇒ viol (`:110-111`). `_braking_dist = min(hypot(vh),v_max)²/(2·a_brake)`
  (`:97-99`). To jest kod-odpowiednik modelu bariery certu P2 (`P2.json:code_refs.shield_barrier`).

### `latch_refuse`, `outcome`
- `latch_refuse(reason, rule)`: ustawia terminal raz (`shield.py:115-118`) — monotoniczność latch.
- `outcome(env_success, wrong_action)`: księgowość trójwynikowa SUKCES/ODMOWA/PORAZKA z asercją
  rozłączności `(res=="ODMOWA")==refused` (`shield.py:209-225`).

### Czystość jądra (kluczowe dla FV)
- **Brak nieczystości zewnętrznych:** w `shield.py` NIE ma `time.`, `random.`, IO ani stanu globalnego
  (przegląd pliku; jedyne importy: `math`, `ShieldConfig` — `shield.py:31-32`). `step` liczy `round(k*dt,4)`
  deterministycznie (`:124`).
- **Jądro NIE jest funkcją czystą argumentów** w sensie sygnatury: mutuje atrybuty instancji —
  `self._pos_bad/_pos_healthy/_pos_refuse/n_pos_enter` (`:83-94`), `self.terminal/state`
  (`:117-118,158,165,171,177,183,195,199,204`), `self.trace`, `self.n_hold_enter/_release/_was_hold`
  (`:135-140`). Jest natomiast **deterministyczną funkcją przejścia** (stan-instancji, argumenty) →
  (nowy-stan, decyzja), bez żadnego źródła niedeterminizmu. Dla FV oznacza to: stan trzeba
  zreifikować jako jawny wektor (tak jak już zrobiono dla D5).
- **`safe_descend_step(st, now, cfg)` (`r03/controllers/safe_descend.py:20-49`): CZYSTA** — stan `st`
  wejściem i wyjściem (`:23,49`), zegar `now` ARGUMENTEM (potwierdzone: `:24`, `:34` `st["desc_t0"]=now`,
  `:36` `el=now-st["desc_t0"]`), zero IO/globali. To potwierdza tezę promptu: po ekstrakcji K2 zegar D5
  idzie argumentem. Idealny cel dowodu bezpośrednio-na-kodzie.

---

## R3 — Kandydackie obligacje dowodowe z wyceną

Forma logiczna / narzędzie / trudność (przedział) / tryb porażki. Ostateczne brzmienia zdań = decyzja PRE.

**(a) Dominacja reguł R-POS > R-G > R-AUTH na wszystkich ścieżkach `_decide`.**
- Forma: inwariant priorytetu — `_pos_refuse ⇒ decision=REFUSE ∧ reason=POS_DEGRADED` niezależnie od
  `mode`/`geo`; `¬pos ∧ geo ⇒ reason=GEOFENCE`; R-AUTH tylko w gałęzi OBSERVE poniżej obu.
- Status: **w dużej mierze JUŻ w P1** (P1b/P1f/P1h, `P1.json:properties`). FV dodałby najwyżej jawne
  twierdzenie „krzyżowe" ponad to, co P1 kwantyfikuje. Narzędzie: Z3 wprost (jak verify.py). Trudność: NISKA.
- Tryb porażki: redundancja z P1 (obligacja nic nie dodaje) — ryzyko „pustego" wyniku.

**(b) Latch REFUSE nieodwoływalny.**
- Forma: `terminal≠None ⇒ ∀ kolejnych ticków terminal'=terminal ∧ decision=REFUSE`.
- Status: **P1d już to kwantyfikuje** (`P1.json:properties.P1d`). FV mógłby wzmocnić do inwariantu
  temporalnego po trajektorii (nie tylko 1-krok). Narzędzie: Z3 (k-indukcja) / egzekucja symboliczna.
  Trudność: NISKA–ŚREDNIA. Tryb porażki: R-POS/R-AUTH (odwracalne) mylnie zliczone jako naruszenie
  latch — trzeba precyzyjnie oddzielić latch (terminal) od stanów odwracalnych.

**(c) Semantyka histerezy `_pos_monitor`.**
- Forma: inwariant temporalny — wejście po `debounce` kolejnych True; wyjście po `hyst` kolejnych False;
  brak oscylacji sub-progowej (debounce/hysteresis correctness). To NOWE (P5 jest „niezależny od M",
  `P5.json:r03a_note` — M nie dowodzony).
- Narzędzie: egzekucja symboliczna licznika LUB Z3 z modelem liczników / wyczerpujące pokrycie
  skończonej siatki sekwencji flag (skończoność: liczniki ograniczone przez debounce=2 i hyst=round(5/dt)).
  Trudność: ŚREDNIA. Tryb porażki: przestrzeń sekwencji flag jest nieskończona w czasie — dowód wymaga
  argumentu indukcyjnego po licznikach, nie enumeracji.

**(d) `_geofence_violation` ⇔/⊇ model wymierny P2 na domenie ograniczonej.**
- Forma — WARIANTY do wyboru PRE:
  - (d1) **Równoważność:** `_geofence_violation(pos,vel,target)=False ⟺ Inv(pos,vel) modelu P2` na
    `|v|≤V_env ∧ pozycje w kopercie`.
  - (d2) **Zawieranie (słabsze, bezpieczniejsze):** `¬viol ⇒ Inv_P2` (kod nie przepuszcza nic, czego
    bariera P2 nie uznaje za bezpieczne) — bez odwrotnej implikacji.
  - Różnica: kod ma dodatkowe człony (cel poza R_E `:104`, pion V_E `:110`) których czysta bariera P2
    (pozioma) nie ma — więc (d1) wymaga rozszerzenia modelu P2, (d2) nie.
- Narzędzie: Z3 NRA (jak geofence.py). Trudność: ŚREDNIA (d2) / WYSOKA (d1, bo trzeba pogodzić `min(...,v_max)`
  w `_braking_dist` z modelem oraz człon pionowy). Tryb porażki: `min(hypot(vel),v_max)` (`shield.py:98`)
  wprowadza nieliniowość ucinającą — model P2 zakłada `0≤v≤v_max` z góry; na domenie `|v|>v_max` kod
  saturuje, model nie — rozjazd, jeśli domena nie zostanie ograniczona do `|v|≤v_max`.

**(e) D5: monotoniczność zejścia + przełączenie H_SWITCH + touchdown w skończonych krokach.**
- Forma: dla `safe_descend_step` (czysta) — `el<desc_fast_dur ⇒ vdesc=v_desc_fast`; `el≥desc_fast_dur ⇒
  vdesc=v_desc_land ∧ h_switch wyemitowany dokładnie raz`; `el≥desc_total ⇒ touchdown raz`; zdarzenia
  monotoniczne (każde ≤1×). Wszystko z `safe_descend.py:36-48`.
- Narzędzie: Z3 wprost (funkcja czysta, arytmetyka liniowa po `el`) LUB egzekucja symboliczna. Trudność:
  NISKA (najłatwiejsza obligacja — kod już czysty, zegar argumentem). Tryb porażki: „skończona liczba
  kroków" wymaga założenia o monotonicznym `now` (nie-cofający zegar) — trzeba to dołożyć jako hipotezę.

**(f) Dead-man streamera: „martwa osłona ⇒ cisza setpointów ⇒ natywny failsafe".**
- Gdzie żyje w kodzie: NIE w `r01/shield.py`. Wg certów: egzekutor `r02/gate_run_r02.py:_streamer`,
  dowód własności `r02/test_deadman.py` (`P1.json:assumptions[4]`, `P2.json:assumptions[5]`). N=6=0.3 s
  oznaczone [PROWIZORYCZNE/A4] w certach.
- Forma: `brak odświeżenia setpointu przez N ticków ⇒ strumień milknie ⇒ COM_OF_LOSS_T failsafe`.
- Narzędzie: to własność systemowa (timing streamera), nie czysta arytmetyka — kandydat na model
  temporalny/timed automaton, NIE Z3-arytmetykę. Trudność: WYSOKA (i częściowo poza TCB osłony).
  **Scope-decyzja do PRE** — rekomendacja: poza rdzeniem bramkującym FV (dziś pokryte testem, nie dowodem).

---

## R4 — Wiązanie model↔kod (rdzeń metody; tu noga może pęknąć)

Trzy warianty, ŻADNEGO nie wykonano.

**(α) Ekstrakcja jądra do funkcji czystych używanych PRODUKCYJNIE (wzór D5 z K2).**
- Diff: reifikacja stanu `PatrolShield` (atrybuty z R2: `_pos_bad/_pos_healthy/_pos_refuse/terminal/state/
  liczniki HOLD`) jako jawny `st` + przepisanie `step/_decide/_pos_monitor` na `(st,args)->(st',decyzja)`.
  Dotyka pinu `shield.py` (pin 1/5, `k1/k1_shield_pins.py`) ⇒ wymaga ceremonii INFRA-3 (rozcięcie +
  re-baseline pinu + test bit-w-bit), jak `safe_descend` (`safe_descend.py:4-5`). **Wycena diffu (papier):**
  szacunek ŚREDNI — rzędu 40–90 hunków (jądro + lustro testu bit-w-bit + re-baseline 1 pinu); porównaj:
  D5 to była 1 funkcja (49 l.), tu jest cały automat. NIE WYKONYWAĆ w tej sesji (SR-4).
- Tryb porażki: ceremonia pinu przy błędzie = zmiana zachowania produkcyjnego osłony (regresja na locie).

**(β) Lustro dowodowe + test różnicowy bit-w-bit na ISTNIEJĄCYCH śladach.**
- POLICZONA baza (read-only, ta sesja):
  - `results/K1/S/**`: **4221 rekordów `tick`** w 11 z 14 plików trace; pola: `decision, reason, state,
    pos, dr, descending, r_est, margin_R_E, mono, tick` (enumeracja `results/K1/S/p0_2/boot7/trace.jsonl`).
  - `results/K1/N/**`: 0 `tick`, 50931 `ekf`. `results/K1/E/**`: 0 `tick`, 287396 `ekf`.
    `results/K2/**`: 0 `tick`, 198262 `ekf`. `results/NET/FLY/**`: 0 `tick`, 1128476 `ekf`.
  - **Kompletność pól:** ślady logują WYJŚCIA osłony (`decision/reason/state`) + CZĘŚĆ wejść (`pos`, `dr`=pos_flag)
    ale NIE pełen wektor `step`: brak `target` (proponowany setpoint), `mode`, pełnego `vel` (jest `vx/vy`
    w `ekf`, nie w `tick`), `auth_ok`. Rekonstrukcja pełnej decyzji `_decide` z artefaktów jest więc
    NIEMOŻLIWA dla gałęzi zależnych od `target`/`mode`/`auth_ok` (R-G, R-A, R-H, R-R, R-O/R-AUTH).
  - Odtwarzalne w pełni: **ścieżka D5** (`pos`+`descending` → dokładnie fikstura 4221/1791 już użyta w
    K2/INFRA-3, `bench/tests_safe_descend.py:7,67-68`; `results/INFRA3/RAPORT_INFRA3.md:42`). Częściowo:
    R-POS/pos-monitor (`dr`→`decision` zgodność), bez `target`.
- Wniosek β: baza różnicowa dla PEŁNEGO `shield.step` na istniejących artefaktach = praktycznie 4221 ticków
  K1/S, a i te bez `target/mode/auth_ok` → β domyka tylko D5 (już domknięte) i sanity R-POS; dla reszty
  wymaga RE-INSTRUMENTACJI logów (dopisać per-tick pełen wektor wejść), co samo dotyka egzekutora.
- Tryb porażki: fałszywe poczucie pokrycia — 4221 ticków to niemal wyłącznie D5; „bit-w-bit przeszło"
  nie znaczy „automat pokryty".

**(γ) Dowód bezpośrednio na kodzie (egzekucja symboliczna).**
- Diff: zerowy w kodzie produkcyjnym (nie dotyka pinów) — narzędzie chodzi po `shield.py` jak jest.
  Wymaga narzędzia ES dla Pythona (crosshair/klee-py-podobne) — status narzędzia do R5/PRE.
- Tryb porażki: ES Pythona słabo radzi sobie z mutowanym stanem obiektu + `math.hypot`/nieliniowościami;
  ryzyko niedomknięcia ścieżek (path explosion) lub braku wsparcia dla float-NRA.

**REKOMENDACJA WYKONAWCY (do decyzji PRE):** rdzeń bramkujący FV = **(γ) dla `safe_descend_step` (już czyste,
najtańszy pewny dowód, R3e) + Z3 wprost dla obligacji automatu, które NIE są jeszcze w P1 (R3c histereza)**,
z **(α) zarezerwowanym jako ceremonia INFRA-3 tylko jeśli PRE zdecyduje o reifikacji całego automatu**.
Uzasadnienie mechanizmowe: β jest atrakcyjne pozornie (są ślady), ale POLICZONA baza pokazuje, że pełen
wektor wejść nie jest persystowany — β bez re-instrumentacji domyka to, co już domknięte (D5). γ na
`safe_descend` i Z3 na histerezie dają NOWĄ treść bez dotykania pinów.

---

## R5 — Stretch (ii): weryfikacja NCP-20 / własności złożenia

### Implementacja inferencji w repo i zależności
- `net/models.py:NCP20` — CfC forma zamknięta, `IN=8` (`:97`), `hidden=20`, `bb=20` (`:99`),
  **param_count=1903** (odczyt: `python3 -c "from net.models import NCP20; NCP20(3.0).param_count()"` →
  `1903`, def. `net/models.py:115-116`). Zależność: **czysty numpy, brak torch/jax** (`net/models.py:2,15`).
- Krok: `step_np(x,h)` (`net/models.py:127-138`) — `bb=tanh(·); g=tanh(·); hh=tanh(·); gate=sig(·);
  h2=gate·g+(1−gate)·hh; y=tanh(h2·Wo+bo)·vmax`. **dt zwinięte w wagach** (`net/models.py:11-13`) ⇒ per krok
  jest to STAŁY feedforward tanh/sigmoid, rekurencja tylko przez `h`.
- Wagi: `net/frozen/ncp.npz` (sha `0337d5ea`, memory FREEZE_NET); ładowanie `net/models.py:192-193`.

### Klasy narzędzi (STATUS: DO WERYFIKACJI W BUDOWIE — bez instalacji/uruchomienia w tej sesji)
Poniższe z wiedzy dziedzinowej, NIE zweryfikowane metadanymi w tej sesji (zakaz instalacji, a `pip index`
nie orzeka o wsparciu rekurencji ciągłej):
- Weryfikatory sieci feedforward (klasa α,β-CROWN / Marabou / ERAN-DeepPoly / NNV): deklarują wsparcie
  tanh/sigmoid i BOUNDED-input; rekurencja w czasie ciągłym — brak deklarowanego wsparcia wprost.
- Dla CfC/continuous-time-RNN: brak znanego off-the-shelf narzędzia deklarującego natywne wsparcie —
  do potwierdzenia w budowie. **Ścieżka realna:** ROZWINIĘCIE (unroll) rekurencji po skończonym horyzoncie
  T → sieć feedforward (bo per-krok to feedforward, `net/models.py:127-138`, dt w wagach) → wtedy
  weryfikatory feedforward stają się stosowalne na własnościach bounded-input/bounded-output. To hipoteza
  metodyczna, nie deklaracja narzędzia.
- Predykcja P-CC2-1 (KSIEGA_PREDYKCJI OTWARTE): wariant „samej sieci off-the-shelf" — p≈0.7 na wynik
  częściowy/śmierć na pokryciu narzędzi. Recon jej nie obala.

### Alternatywa: własności ZŁOŻENIA osłona∘sieć (gwarancje NIEZALEŻNE od wyjścia sieci)
Co tor wykonawczy + osłona gwarantują niezależnie od tego, co wypluje NCP:
- **Ograniczoność wyjścia (architektura):** `y=tanh(zo)·vmax` (`net/models.py:135-136`) ⇒ `|y_i|≤vmax`
  ZAWSZE, dla DOWOLNYCH wag/wejść — własność czysto architektoniczna, trywialnie dowodliwa
  (`net/models.py:8` „saturacja architektoniczna ⇒ |v|≤V_MAX ZAWSZE", kontrakt 10⁴, `ANEKS_BENCH-1a.md:12`).
- **`clip_v` (egzekutor):** `r03/controllers/common.py:10-14` saturuje `|v|≤vmax` zachowując kierunek —
  druga, niezależna warstwa ograniczenia prędkości (poza saturacją głowy).
- **Koperta/geometria (osłona):** R-G przecina KAŻDY setpoint z `radial(target)>R_E` lub
  `pos+brake>R_E` lub pion>V_E (`shield.py:104-111`) — niezależnie od tego, czy `target` pochodzi od NCP,
  MLP, czy planera skryptowego. Osłona jest JEDYNĄ ścieżką publikacji setpointów (`shield.py:4`).
- Wniosek: złożenie ma dwie architektoniczne granice (tanh·vmax, clip_v) + jedną bramkę kopertową (R-G),
  wszystkie NIEZALEŻNE od poprawności sieci. To jest weryfikowalne TANIO (Z3/algebra) i jest mocniejszym
  kandydatem na „PASS" niż weryfikacja wnętrza NCP.

### Rekomendowany zakres (ii) z kryterium „wynik częściowy"
- PASS(ii): dowód złożeniowy — „dla dowolnego wyjścia sieci osłona∘clip_v utrzymują `|v|≤vmax` i kopertę R_E".
- Wynik częściowy(ii): własność architektoniczna wyjścia NCP (|y|≤vmax) + udokumentowana mapa narzędzi
  z konkluzją „brak off-the-shelf dla CfC ciągłego, unroll wymagany" — bez pełnej weryfikacji wnętrza.

---

## R6 — Arytmetyka zakresu i propozycje do PRE

### Ile obligacji R3 w 2–4 sesjach (PRZEDZIAŁY — kalibracja CC: chroniczne zaniżanie glue)
- Pewny rdzeń w 2–4 sesjach: **R3e (D5, γ) + R3c (histereza, Z3)** — realistycznie 1–2 sesje łącznie
  (D5 tani, histereza średnia).
- R3a/R3b (dominacja/latch): jeśli traktowane jako WZMOCNIENIE ponad P1 — 0–1 sesji; jeśli PRE uzna je za
  redundantne z P1, wypadają (glue = re-użycie verify.py).
- R3d (geofence⇔P2): wariant d2 (zawieranie) 1–2 sesje; d1 (równoważność) — ryzyko przekroczenia budżetu
  (nieliniowość `min(·,v_max)` + człon pionowy), NIE mieści się pewnie.
- R3f (dead-man): poza budżetem rdzenia; rekomendacja — poza nogą (test, nie dowód).
- **Wniosek zakresu:** rdzeń bramkujący FV = R3e + R3c (+ ewent. R3a/b jako domknięcie P1), reszta = stretch.

### Kandydackie kryteria bramki nogi (propozycja do PRE)
- PASS(i) rdzeń: co najmniej R3e I R3c dowiedzione narzędziem (Z3/ES), z certem + guardem prowieniencji
  (wzór `certs_selfcheck.py`), bez dotykania pinów LUB z ceremonią INFRA-3 jeśli reifikacja (α).
- Wynik częściowy(i): jedna z {R3e, R3c} dowiedziona, druga z policzonym trybem porażki.
- PASS(ii)/częściowy(ii): jak w R5 (złożenie vs wnętrze NCP).
- Kandydackie kryterium ŚMIERCI nogi: jeśli reifikacja (α) okazuje się jedyną drogą do jakiejkolwiek NOWEJ
  treści (bo P1/P5 już pokrywają automat) I ceremonia INFRA-3 jest nieproporcjonalna do przyrostu — noga
  umiera na „brak delty" (wszystko istotne już dowiedzione w R1).

### TRIPWIRE (propozycja do wpisania w PRE)
> **TRIPWIRE-FV:** jeśli którakolwiek obligacja PADA na IMPLEMENTACJI przy wejściach OSIĄGALNYCH
> (kontrprzykład realny, nie artefakt modelu) — to ZNALEZISKO PIERWSZEJ WAGI (bug osłony) i STOP
> DIAGNOSTYCZNY, nie „porażka nogi". Kontrprzykład realny > każdy PASS.

### PYTANIA DO PRE
1. **Delta vs redundancja:** czy R3a/R3b (dominacja/latch) mają być osobnymi twierdzeniami FV, skoro P1d/P1f/P1h
   już je kwantyfikują (`P1.json:properties`)? Jeśli nie — rdzeń FV = R3c+R3e; potwierdzić.
2. **Reifikacja (α) czy nie:** czy PRE dopuszcza ceremonię INFRA-3 na `shield.py` (reifikacja stanu) dla
   dowodu automatu w czasie, czy FV ma się ograniczyć do tego, co dowodliwe BEZ dotykania pinów
   (γ na safe_descend + Z3 na histerezie na modelu-lustrze)?
3. **Forma R3d:** równoważność (d1) czy zawieranie (d2) `_geofence_violation`↔P2, i na jakiej domenie
   ograniczenia `|v|≤V_env` (V_env=v_max=3 czy 3.1 z P2_vmax3p1)?
4. **D5 skończoność:** czy wolno przyjąć hipotezę monotonicznego `now` (nie-cofający zegar) jako założenie
   twierdzenia R3e, czy PRE chce ją oddzielnie uzasadnić?
5. **Dead-man (R3f):** poza nogą (zostaje test `r02/test_deadman.py`) czy w zakresie jako model temporalny?
6. **Stretch (ii) zakres:** czy PRE preferuje dowód ZŁOŻENIA (osłona∘sieć, tani, mocny) jako główny cel (ii),
   z weryfikacją wnętrza NCP jako czystym stretch „wynik częściowy" (zgodnie z P-CC2-1)?
7. **Narzędzie ES/Z3:** czy FV może wprowadzić zależność narzędziową (np. crosshair dla γ) — instalacja
   pakietu w budowie — czy trzymamy się wyłącznie z3 (już w `.certdeps`, `verify.py:11`)?
8. **Baza β:** czy PRE chce re-instrumentację logów (dopisać per-tick pełen wektor wejść osłony) jako osobne
   zadanie infra, skoro obecne ślady (poza D5) nie wystarczają do różnicowego replay `_decide`?
