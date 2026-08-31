# RAPORT_INFRA3 — rozcięcie kontroler/osłona + wrapper bootu

LiquidPatrol · pozycja 1a planu · baza `3065b8b` · wykonawca Claude Code · push=Olga.
Liczby z etykietą przyrządu (nav=EKF/mav=MAVSDK/sim=Gazebo/wall=zegar) i ścieżką pliku.

Commity: A1 `31fe970` · A1b `9b6c006` · A2.0 `f134a2a` (pushnięte) · A2 artefakty (ten commit) · B (dalej).

---

## §1. D0 — inwentarz (pełny w `results/INFRA3/D0_inventory.md`)

sha256 pinów zgodne na wejściu: shield `1c584964`, config `4c440e42`, gate `72619513` (przed A1),
k1_judge `4e0dc0af`, act_judge `79b1e936`. Bloki setpointów w `gate_run_r03.py`: init trasy (200),
init stanu (206–207), wp/dx/dy/dist/inkrement/tgt (225–230), v_ned (291).

**Macierz ścieżka × mechanizm (proza):**
- `k1/run_k1_boot.sh` (K1 S/N/E): watchdog EKF2, higiena CAL_MAG, higiena GPS, bramka obciążenia I2a,
  próbnik RTF, headless, kopia ulogu, certs_selfcheck(S), finalize, settle 90 s, b4_state. **Bez** hasha
  świata (stock `default`), **bez** spawnu intruza.
- `acts/run_act.sh` (A1/A2 DEMO-B): hash świata, spawn intruza, bridge kamery, headless, settle 150 s.
  **Bez** watchdoga/higieny mag/higieny GPS/bramki I2a/RTF/ulogu/certs/b4.
- `acts/run_A3.sh` (A3 GPS-denied): hash świata, RTF, bridge kamery, headless, settle 90 s, finalize.
  **Bez** watchdoga/higieny/I2a/spawnu/ulogu/certs/b4.

Predykcja CC potwierdzona: `acts/*` bez watchdoga/mag/I2a; `run_k1_boot.sh` bez hasha/spawnu. Luka domykana wrapperem §B.

---

## §2. A — rozcięcie kontroler/osłona

### Diff-summary gate'a (pełny verbatim: ANEKS_SHA §W12)
`r03/gate_run_r03.py` dotknięty WYŁĄCZNIE: (i) import pakietu kontrolerów; (ii) konstrukcja `ctrl`
(env `CONTROLLER` default `route`, `reset()`); (iii) wiersz `meta` +`controller`/+`controller_sha`;
(iv) blok wp/dx/dy/dist/seg_i/tgt → `ctrl.step(...)` z odczytem `seg_i`/`dist`/`wps` (triggery S4/K1);
(v) wiersz ALLOW `set_velocity_ned` z `cmd["v_ned"]`. Gałąź `is_pos`/zejście D5, `shield.step`,
denial/recovery, timeouty, `outcome`/restore — NIETKNIĘTE (SR-3, potwierdzone diffem). Pin `72619513…`→`c3ccabe0…`.
`k1_finalize.py` +2 linie (przepisanie `controller`/`controller_sha` meta→manifest, SR-2 dozwolone).

### Wynik testu równoważności A1.3 (verbatim, `tests_controller_split.py`)
```
korpus S/K1 z wierszami tick: 11 lotów
Łącznie ticków porównanych bit-w-bit: 4221  → WSZYSTKIE IDENTYCZNE (tgt, v_ned, seg_i, dist)
test syntetyczny przejścia narożnika (dist 1.01→0.99): OK
test descending=True ∧ dist<1.0 ⇒ brak inkrementu seg_i (obie impl.): OK
R0.3a v1 (bez tick): pominięte zgodnie z A1.3(ii)
pytest: 5 passed
```

### Regresja glue A1.4
`judge.json` BAJT-IDENTYCZNY (kopia `results/K1/S/p0_65/boot3`, stary gate przywrócony w drzewie → pin
się zgadza → sędzia liczy). Manifest porównywany z wyłączeniem pól pomiarowych chwili uruchomienia
(`session`: mem_free/loadavg — snapshot środowiska, D5 ANEKS_INFRA3-1); realna różnica = tylko nowe pola
`controller`/`controller_sha`. Przepisanie meta→manifest zweryfikowane na trace z wstrzykniętym meta.

### Loty równoważności (A2.1, `tools/run_k1_boot_infra3.sh`, `CONTROLLER=route`, KIND=crit)
Wrapper = kopia `run_k1_boot.sh`, diff 3 linie (OUTDIR + marker read + marker write → `results/INFRA3/`;
nota §6). Referencja: `results/K1/S/p0_65/boot3` (x_exc 3.470, r_max 15.448, t_refuse 0.10, t_td 3.680,
seq LOITER→PRECLAND→OFFBOARD→DESCEND→OFFBOARD). Sędzia `4e0dc0af`. B4 pre-series: brak procesu >50% CPU.

Skład serii (ANEKS_INFRA3-2 §3 SKAŻONA → ANEKS_INFRA3-3 §2 nowy budżet decydenta). ref = `results/K1/S/p0_65/boot3(K1)`.
**boot4 = decydent na czystej maszynie (pierwszy ważny+porównywalny, rozstrzyga).** boot1–2 = etykieta
odchylenia procesowego (liczby pełne, w progach). boot3 = diag env-fail (habitat INVALID, nie liczony).

| metryka (etykieta) | ref | boot1(dev) | boot2(dev) | boot3(diag) | **boot4 DECYDENT** | próg | ok |
|---|---|---|---|---|---|---|---|
| **run_valid ∧ habitat** | VALID | VALID | VALID | INVALID(hab) | **VALID** | ważny | ✅ |
| pairing dr [m] (nav) | — | 0.789 | 0.312 | 0.105 | **0.462** | ≤1.0 | ✅ |
| pairing dv [m/s] (nav) | — | 0.008 | 0.024 | 0.021 | **0.050** | ≤0.3 | ✅ |
| pairing dhead [°] (nav) | — | 6.215 | 2.885 | 2.265 | **3.437** | ≤10 | ✅ |
| pairing dz [m] (sim GT) | — | 0.481 | 0.426 | 0.438 | **0.131** | ≤0.5 | ✅ |
| breach | False | False | False | False | **False** | False | ✅ |
| nav_state_seq (ulog) | 5-stan | identyczna | identyczna | identyczna | **identyczna** | ==, bez AUTO_LAND | ✅ |
| t_refuse_rel_s (nav) | 0.10 | 0.10 | 0.08 | 0.12 | **0.12** | [0.05,0.15] | ✅ |
| x_exc [m] (sim GT) | 3.470 | 3.112 | 2.914 | 3.04 | **2.72** (\|Δ\|0.750) | \|Δ\|≤0.905 | ✅ |
| t_td_s (ulog) | 3.680 | 3.4 | 4.06 | 4.12 | **3.8** (\|Δ\|0.120) | \|Δ\|≤0.5 | ✅ |
| controller / _sha (meta+manifest) | — | route/`e0fcc7d2` | route/`e0fcc7d2` | route/`e0fcc7d2` | **route/`e0fcc7d2`** | route | ✅ |

Cytaty: `results/INFRA3/A2/S/p0_65/boot{1,2,3,4}/{judge.json,manifest.json}`.
`controller_sha` = sha256 `r03/controllers/route_follower.py` = `e0fcc7d2…` (w meta i manifeście WSZYSTKICH lotów).
**boot4 habitat:** H1 timejump=0 PASS, H2 Δsim/Δwall=**1.0** (czysto, zero stalla) — kontrast do boot3 (0.6127).
boot4 higiena: inwentarz pre/post/during verbatim (`proc_inventory_boot4_{pre,during,post}.txt`); during-sampler
złapał WYŁĄCZNIE własny stack (gz/px4/rtf_sampler) — zero cudzego procesu w trakcie; loadavg pre 0.04.

**boot3 diagnoza (env-fail, diag):** H1=0 PASS; H2 Δsim/Δwall=0.6127<0.95 — POJEDYNCZY głęboki stall na segmencie
roszczenia (frac<0.5=0.0196, min_rtf 0.0213), **NIE w oknie reakcji** (n_stall=0). env-bound stall gz↔px4
(RAPORT_INFRA1/E1d/P3), ortogonalny do refaktora; wszystkie progi A2.3 spełnione, nieważność tylko na habitacie.

### Werdykt A2: **PASS** (decydent boot4 ważny+porównywalny, wszystkie progi A2.3; ANEKS_INFRA3-3 §2).
Ścieżka: seria A2 na skażonej maszynie NIEROZSTRZYGNIĘTA (ANEKS-2 §3, boot3 env-fail) → CC odrzucił „PASS mimo
nieważności" i revert (ANEKS-3 §2 b/c) → nowy budżet decydenta na czystej maszynie → **boot4 rozstrzyga PASS**.
Refaktor kontroler/osłona równoważny; osłona identyczna z natywnym blokiem setpointów. Dowód niezależny od
środowiska: A1.3 = 4221 ticków bit-identycznych; 4/4 loty (1,2,3,4) w progach A2.3 z poprawnym controller_sha.
Predykcje: P2 ✓ (pod skażeniem), P3 ✓ (habitat env INVALID w boot3), P5 ✓ (boot4 ważny+w progach za 1. razem),
P4 kierunkowo (dz najciaśniej: 0.131–0.481 przy 0.5). Werdykt A2 do potwierdzenia linią CC „A2 PASS" (ANEKS-3 §5).
Predykcje: P2 częściowo (2 loty porównywalne, progi w oknie, ale ważność decydenta padła na env); P3 zamanifestowana
(habitat INVALID env-bound) już w A2; P4 kierunkowo (dz najciaśniejszy margines: 0.481/0.426/0.438 przy 0.5).

---

## §3. B — jeden wrapper bootu programu

### B1 — `harness/run_boot.sh` (mechanizmy ↔ źródło: ANEKS_SHA §W13)
Kompozycja ISTNIEJĄCYCH mechanizmów (przyrządy zamkniętych serii `k1/run_k1_boot.sh`, `acts/run_act.sh`,
`run_A3.sh` NIETKNIĘTE). Kroki 1–11 §B1.1: B4+cooldown (marker program-wide `results/.last_boot_end`
+fallback K1) · **bramka procesowa §3** (`proc_gate.py`+`proc_allowlist.txt`: `top -b -n2 -d5`, cudzy >2% CPU
lub loadavg>1.5 ⇒ env-block+stub) · certs(gate_r03) · higiena GPS/CAL_MAG · I2a · świat+hash
(`world_hash.sh`, worlds/ i stock) · stack/headless/clock/RTF/watchdog(bezwarunkowy, max 2 reinity)/settle(min 90)/timejump ·
intruz+`model_in_state`+film(opc.) · moduł lotu(empty/gate_r03/arm_n) · ulog→`ulog_sha.txt`(sha256+rozmiar) ·
finalize+**łapacz stub**(`stub_manifest.py`, lekcja R5)+augment(`augment_manifest.py`: world_hash/ulog_sha/model_in_state→manifest,
NIE dotyka sędziego) · marker końca. sha256 6 plików: §W13.

**Test `tests_harness_infra3.py` B1.2 (verbatim): 6/6 PASS**
```
(i)   stub-manifest na finalize-fail (crash_reason, run_valid=null, idempotencja): OK
(ii)  ulog_sha (sha256+rozmiar == hashlib): OK
(iii) world_hash worlds/ (world_demo_A3) i stock (default): OK
(iv)  SETTLE_S=30 odrzucone (exit 2, OUTDIR nie powstaje): OK
(v)   §3 bramka: yes-eater blokuje z PID, po ubiciu przepuszcza; allowlista (claude pasuje, yes nie): OK
pytest tests_harness_infra3.py + tests_controller_split.py: 11 passed
```

### B2 — bramka zdrowia: 6 bootów kolejnych (`results/INFRA3/B/boot{1..6}`)
boot1–5 `FLIGHT=empty WORLD=default` (arm→takeoff→60 s hover OFFBOARD→land); boot6 `FLIGHT=empty
WORLD=world_demo_A3 INTRUDER=1`. Kampania 01:09–01:58, cooldown 300 s między bootami, maszyna czysta
(bramka §3 CLEAN każdy boot), zero równoległych prac.

| boot | świat | arm_ok (cytat px4.log) | wd_reinits | komplet 13/13 | habitat (nie-bramkujący) | model_in_state |
|---|---|---|---|---|---|---|
| boot1 | stock default | **True** „Armed by external command" | 1 | ✅ | INVALID (timejump 0) | — |
| boot2 | stock default | **True** „Armed by external command" | 0 | ✅ | INVALID (timejump 0) | — |
| boot3 | stock default | **True** „Armed by external command" | 0 | ✅ | INVALID (timejump 0) | — |
| boot4 | stock default | **True** „Armed by external command" | 0 | ✅ | **VALID** | — |
| boot5 | stock default | **True** „Armed by external command" | 1 | ✅ | INVALID (timejump 0) | — |
| boot6 | repo world_demo_A3 | **True** „Armed by external command" | 0 | ✅ | INVALID (timejump 0) | **1** (spawn data:true) |

Komplet artefaktów (13): b4_state, proc_inventory, gps_hygiene, mag_hygiene, headless_proof, world_hash,
rtf_stream, ekf_watchdog, timejump_pre/post, ekf_health_hits, ulog_sha, manifest — **6/6 bootów pełne**
(miss=none). `ulog_sha.txt` = sha256+rozmiar (49–52 MB) każdy. Żaden boot nie potrzebował stub (finalize
przeszedł 6/6, kind=empty). wd reinity 1/0/0/0/1/0 (preflight-only, raportowane osobno, nie dyskwalifikują).

### Werdykt B2: **PASS**
- arm **6/6** ≥ 5/6 ✅ · komplet artefaktów **6/6** ✅ · boot6 intruz obecny **1/1** ✅.
- habitat hover: 5 INVALID / 1 VALID, wszystkie timejump=0 — RAPORTOWANY, NIE bramkujący (RAPORT_INFRA1 §7:
  env-bound na oknie hoveru, znana cecha mostu; P3 zamanifestowana zgodnie z predykcją).
Wrapper `harness/run_boot.sh` zdrowy: składa wszystkie mechanizmy, bramka procesowa §3 działa (CLEAN 6/6),
world-hash/ulog_sha/model_in_state w manifeście, łapacz stub gotowy (nie wyzwolony — brak awarii finalize).

---

## §4. Re-baseline pinu (A2.0, commit `f134a2a`)

`k1/k1_shield_pins.py`: `r03/gate_run_r03.py` `72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a`
→ `c3ccabe04b9cae8ea57cfa899b8e363451fe9a6b4dbaffc8b1b0910ad192b729` (D1). `+r03/controllers/base.py`
`7fc45cf2216d4a9eae86fa9ee714d70354fafbc64721f76bff7c0575bb9fb8f9` jako 4. pin (D2: kontrakt kontroler↔osłona).
`shield.py`/`config.py` sha256 BEZ ZMIAN. Odsyłacz: ANEKS_SHA §W12. Weryfikacja: self-check SHIELD FROZEN=True (4/4),
`tools/test_k1_shield.py` 5/5.

---

## §5. Wpięcie kontrolera dla ławki (5 zdań)

1. Napisz klasę dziedziczącą `SetpointSource` (interfejs `r03/controllers/base.py`) implementującą
   `reset()` i `step(tick, pos_ned, vel_ned, now_s, descending)`.
2. `step` zwraca dict z kluczami `tgt_ned`/`v_ned`/`yaw`/`seg_i`/`dist`/`wps`/`extra` — nazwy obowiązujące,
   bo pętla i triggery K1/S4 czytają dokładnie te klucze.
3. Zarejestruj klasę w `r03/controllers/__init__.py` (`_REGISTRY`) pod nazwą kanału i wskaż ją env
   `CONTROLLER=<nazwa>` przy uruchomieniu (default `route`).
4. Osłona (`r01.shield.PatrolShield`) widzi WYŁĄCZNIE `cmd["tgt_ned"]` (jako `tgt` do `shield.step`) i
   `cmd["v_ned"]` (gałąź ALLOW) — nie widzi wnętrza kontrolera; decyzja osłony pozostaje niezależna.
5. Do manifestu trafia `controller` (nazwa) i `controller_sha` (sha256 pliku modułu kontrolera) — tożsamość
   wtyczki jest audytowalna per boot, bez ruszania żadnego pinu (`base.py` pinowany, wtyczki nie).

---

## §6. Odchylenia i noty

- **N1 (KIND=eq→crit):** PROMPT_INFRA3 §A2.2 podał `KIND=eq`, ale zamrożony `k1_finalize` przyjmuje tylko
  `{crit,info}` (SR-2 zabrania poszerzenia). ADJUDYKACJA CC INFRA3-A2.2 (30.08): loty A2 lecą `crit`
  (referencja boot3 też crit; izolacja od K1 katalogiem `results/INFRA3/`, nie etykietą kind). Zastosowano crit.
- **N2 (wrapper diff = 3 linie, nie 2):** marker `.last_boot_end` występuje w `run_k1_boot.sh` DWUKROTNIE
  (odczyt cooldownu, zapis końca) — dla spójnego łańcucha cooldownu serii INFRA3 oba muszą wskazywać
  `results/INFRA3/.last_boot_end`; z OUTDIR daje to 3 zmienione linie. Predykcja „2 linie" rozminęła się o 1;
  obie zmiany mieszczą się w dwóch pojęciach (ścieżka wyjścia + marker). Zero innych różnic (SR-7: brak `results/K1`).
- **N3 (dz blisko progu, P4):** pairing `dz` = 0.481 (boot1) / 0.426 (boot2) przy tol 0.5 — rozrzut z_gt
  wstrzyknięcia (lekcja 0.50) jest realnym ryzykiem porównywalności, w obu lotach zmieścił się.
- **N4 (higiena procesowa serii A2 — gałąź SKAŻONA, ANEKS_INFRA3-2 §2/§3):** booty 1–2 poleciały przy
  aktywnych cudzych procesach (inwentarz `proc_inventory_preseries.txt`): pilot `dreamforge-arc`
  (`arc_a12a_controlled_repair_pilot.py`, 3.5% CPU) + druga sesja Claude (`872 claude --continue`). Próg
  B4 (>50% CPU) nie przekroczony, ale reguła kampanii („zero cudzych procesów") naruszona → CLARIFY-A2 C2
  odpowiedź: NIE (bez wygładzania). Per §3 booty 1–2 = etykieta odchylenia procesowego, dane NIE unieważnione.
  **boot3 = decydent na czystej maszynie:** przed bootem `dreamforge-arc` sam zszedł; sesję `872` ubiłem za
  wyraźną zgodą Olgi („ubij 872"), SIGTERM, potwierdzone martwe; inwentarz `proc_inventory_boot3_pre.txt`
  verbatim (loadavg 0.09, jedyny konsument CPU olga = moja sesja `598227`; pozostały 2 osierocone idle
  log-followery 0% CPU `4684 tail`/`4687 ugrep` po `872` — zero kontencji). boot3 poleciał czysto, ale
  **habitat INVALID** (env-bound stall, §2) → per §3 **NIEROZSTRZYGNIĘTE**. Diagnoza CC: podejrzany #1 = env-habitat
  (P3), NIE skażenie 1–2, NIE refaktor (wszystkie progi A2.3 spełnione we wszystkich 3 bootach). Hipoteza, nie werdykt.
- **N5 (martwe inicjalizacje przed pętlą gate'a — nota, NIE fix):** po rozcięciu kontroler/osłona
  pre-pętlowe inicjalizacje `wps = C.corner_waypoints_r03()` (`r03/gate_run_r03.py:210`), `seg_i = 0`
  (`:216`) i `dist = 1e9` (`:217`) stały się MARTWE — pętla nadpisuje je co tick z kontrolera
  (`seg_i = cmd["seg_i"]; dist = cmd["dist"]; ... wps = cmd["wps"]`, `:237`) PRZED jakimkolwiek odczytem
  (ścieżka `if m is None: continue` też ich nie czyta). W oryginale (3065b8b) były żywe (blok setpointów
  liczył je inline). ZOSTAWIONE świadomie: (1) A1.1 „jeśli błąd — nota, nie napraw"; (2) usunięcie tknęłoby
  plik pinowany poza dozwolonymi hunkami SR-3, a po A2.0 `gate_run_r03.py` jest zapięty (`c3ccabe0`).
  Efekt: zerowy (nadpisywane, nie czytane); to porządek kosmetyczny do ewentualnego przyszłego okna zmiany pinu.
- **Błąd w logice setpointów:** brak (A1.1 „nota, nie fix") — nie znaleziono.
- **CONTROLLER=route:** przekazane env przy wywołaniu wrappera (wrapper bajt-czysty poza 3 liniami ścieżek);
  gate i tak konstruuje kontroler z default `route`, więc `controller_sha` pojawia się niezależnie.
