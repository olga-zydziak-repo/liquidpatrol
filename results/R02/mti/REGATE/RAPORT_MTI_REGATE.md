# RAPORT_MTI_REGATE — re-bramka ENTRY-once live: pomiar kryterium + rozstrzygnięcie D1

Data: 2026-08-16. PX4 v1.16.2, Gazebo Harmonic, ROS2 Jazzy, MAVSDK, YOLO-World (struktura), MTI klasyczny
(derotacja z XRCE `vehicle_attitude` 100 Hz). Świat **`world_demo_v1.1`** sha256 **a76a38c8** (84 bloki
`tex_*`, ANEKS-H). Reżim: kryteria `PRE_R02C` ZAMROŻONE; definicja bramy zrewidowana jawnie
(`ANEKS_MTI_2`, ratyfikacja Olgi, wzorzec A-drift→A-plateau); **FAIL = FAIL, zero strojenia po wynikach**;
prowieniencja per liczba; księgowość trójwynikowa.

Łańcuch commitów (dowodzi freeze→pomiar): `ANEKS_MTI_2` (dokumenty) → patch instrumentu + unit-testy
SR-R1 → **biegi ×3** → ten raport. **Push = Olga.**

---

## (I) WYNIK BRAMKI PER KRYTERIUM

**Kryterium (ANEKS_MTI_2 AM2.2):** (+) dla d: ENTRY osiągnięte ORAZ `coverage_entry_once` (frakcja LOCKED
po admisji, kanał karmiony strukturą) ≥ 0.8 mediana per boot, na **{7, 9} m**; (−) 0 fałszywych ENTRY na
obu scenach (pusta ∧ ruch tła), pełne długości jak B5. **5 m informacyjnie (R-5).**

### ANEKS-H — ważność habitatu per boot

| boot | headless | timejump (stack) | ekf hits | rtf start→end | trace | werdykt |
|---|---|---|---|---|---|---|
| **regate1** | GUI=brak ✓ | 0 / 0 | 2 (settle) | 1.00013 → 0.99973 | 793/793 ✓ | **WAŻNY** |
| **regate2** | GUI=brak ✓ | 0 / 0 | 0 | 1.00025 → 0.99963 | 776/776 ✓ | **WAŻNY** |
| **regate3** | GUI=brak ✓ | 0 / 0 | 0 | 0.99993 → **0.03968** | 774/774 ✓ | **WAŻNY** (flaga ↓) |
| regate3_envfail1 | GUI=brak ✓ | — | — | — | — | **NIEWAŻNY** — ARM FAIL (High Gyro Bias) |

**Flaga prowieniencji regate3:** `rtf_end=0.040` = kolaps RTF w **teardown** (nie w pomiarze) + 37
`time jump detected` w px4.log w oknie **settle** (kontencja renderu — równoległy `fabryka/train_epoch1`).
Faza pomiarowa zdrowa: `content_resid` p95/median ≈ 1.03 (33.7 s stały offset — **brak time-jumpa w oknie
parowania**), `dur_s` = wall-target (30/30/30/90/240 s). Precedens B5 (fix2 „→ (teardown)" WAŻNY).
Env-fail `regate3_envfail1` = kontencja (SR-N7 znany fix, relaunch armed); **1 env-fail, SR-R5 nie wyzwolony**.

### (+) ENTRY-once — POMIAR [world_demo_v1.1, SITL]

| zasięg | `coverage_entry_once` (r1/r2/r3) | mediana | admisja | czas-do-ENTRY [s] (r1/r2/r3) | `coverage_gate` (telemetria) |
|---|---|---|---|---|---|
| **7 m** | 1.0 / 1.0 / 1.0 | **1.0** | **3/3** | 2.17 / 2.22 / 5.98 | 0.491 / 0.429 / 0.464 |
| **9 m** | 1.0 / 1.0 / 1.0 | **1.0** | **3/3** | 1.63 / 2.75 / 10.87 | 0.684 / 0.732 / 0.589 |
| 5 m (info) | 1.0 / 1.0 / 1.0 | 1.0 | 3/3 | 7.29 / 3.62 / 28.03 | 0.464 / 0.415 / 0.423 |

`coverage_seen = 1.0` wszędzie (struktura widziana co tick). **(+) PASS** na 7 i 9 m (mediana 1.0 ≥ 0.8,
admisja 3/3). 5 m także admisja 3/3 (regate3 t_entry 28 s — powolna admisja pod kontencją, w oknie dwell).

### (−) ε_FP — POMIAR [z dekompozycją koniunktów, R-2]

| boot | fp_empty false_ENTRY | fp_bg false_ENTRY | `false_gate_frames` | dekompozycja fp_bg (n_box / n_central / n_mti / n_gate) |
|---|---|---|---|---|
| regate1 | 0 | 0 | 61 | 439 / 135 / 161 / **61** |
| regate2 | 0 | 0 | 54 | 406 / 189 / 148 / **54** |
| regate3 | 0 | 0 | 41 | 424 / 143 / 114 / **41** |

**(−) PASS** — 0 fałszywych ENTRY, ×3 booty × 2 sceny. YOLO strzela na tło (`n_box` 406–439 z ~443–456
ticków), lecz pełna koniunkcja box∧central∧mti_ok (`n_gate` 41–61) **nigdy nie tworzy serii K=3** →
0 admisji (persist + streak pochłaniają). Dekompozycja = pierwszy raz jawna (R-2).

### Zdanie wprost (SR-D4 z DIAG, honorowane): projekcja przewiduje, pomiar rozstrzyga

**Projekcja DIAG (D3) przewidziała: (+) PASS pod ENTRY-once (7/9 m, `coverage_locked_post_entry`=1.0),
(−) intakt. POMIAR dał: (+) PASS (`coverage_entry_once` mediana 1.0), (−) PASS.** Projekcja i pomiar
zgodne. Dodatkowo pomiar przebił projekcję na 5 m: DIAG raportował fix3@5m brak ENTRY (B5), REGATE ma
admisję 3/3 @5m — świeże booty, admisja bez fix3-owej luki.

---

## (II) DEKOMPOZYCJA KONIUNKTÓW + WERDYKT D1 (analiza post-hoc z trace)

Etykieta: **ANALIZA POST-HOC** (nie bramka). Źródło: `trace.jsonl` ×3 (koniunkty osobno).
Skrypt `REGATE/posthoc.py` → `REGATE/posthoc.json`.

### Który koniunkt ograniczał `coverage_gate` (per komórka)

| | 5 m | 7 m | 9 m |
|---|---|---|---|
| limitujący koniunkt | **central** (3/3 booty) | **central** (3/3) | central (2/3), mti (1/3) |
| `fail_central` : `fail_mti` (klatki) | 20:10, 20:11, 22:8 | 17:12, 22:10, 16:14 | 9:9, 9:6, 21:2 |

**Werdykt R-3 POTWIERDZONY POMIAREM:** klatkowy spadek `coverage_gate` napędza **przede wszystkim
CENTRALNOŚĆ** (box zdryfowany od środka), nie człon MTI (8/9 komórek limituje `central`). Teza
RAPORT_MTI „człon MTI przerywany klatkowo" była atrybucją nieuprawnioną z agregatów — **trace ją
obala**. (I tak bez znaczenia dla (+): ENTRY-once mierzy pokrycie PO admisji.)

### Hipoteza pościgu (DIAG D1) — test na trace

Predykcja DIAG: *missy MTI klastrują przy ruchu pozornym ~0 (cel quasi-statyczny nullowany geometrią
pościgu); hity przy manewrach.* Test: mediana pozornego ruchu celu `|Δ(cx,cy)|/klatkę` dla hitów vs
missów MTI:

| | mti **HIT** ruch pozorny (med) | mti **MISS** ruch pozorny (med) | manewr platformy vlat [m/s] |
|---|---|---|---|
| 5 m (r1/r2/r3) | 0.208 / 0.193 / 0.368 | 0.341 / 0.579 / 0.690 | 2.39 / 2.45 / 2.44 |
| 7 m | 0.146 / 0.172 / 0.213 | 0.307 / 0.629 / 0.486 | 2.31 / 2.29 / 2.33 |
| 9 m | 0.103 / 0.090 / 0.158 | 0.593 / 0.498 / 0.852 | 2.27 / 2.24 / 2.34 |

**WERDYKT D1: hipoteza pościgu OBALONA (znak odwrócony, 9/9 komórek jednomyślnie).** MTI **HITuje przy
NISKIM ruchu pozornym** (0.09–0.37) i **MISSuje przy WYSOKIM** (0.31–0.85) — dokładnie ODWROTNIE niż
przewidywał DIAG. Cel NIE jest quasi-statyczny (platforma manewruje vlat ~2.3 m/s stale → ego-motion
obecne). **Mechanizm rzeczywisty:** wysoki pozorny ruch = transjent ego-motion; derotacja jest homografią
WYŁĄCZNIE rotacyjną (`K·R(Δq)·K⁻¹`, translacja NIEKOMPENSOWANA — nazwana słabość PRE_MTI R2) → rezyduum
przy translacji → komponent MTI przesunięty względem boxa YOLO → `box_matches_component` (koincydencja
≤0.12) zawodzi → miss. Niski pozorny ruch = stabilne LOS → derotacja czysta → koincydencja → hit.
To zamyka otwartą pozycję DIAG: (+) FAIL B5 **nie** wynikał z nullowania quasi-statycznego celu, lecz z
(a) centralności (dominująca) i (b) rezyduum translacji derotacji w transjentach ego-motion.
*(Nota kalibracyjna DIAG: predykcja służyła falsyfikacji — sfalsyfikowana.)*

---

## (III) D2 / D4 — INFORMACYJNIE (post-hoc, nie kryterium)

**D2 — tabela K (gate_sim na realnych śladach bramy per-tick).** Na 7/9 m brama admituje przy
**consecutive K=2..5** (`entry=True`, `cov_post=1.0`); dopiero K≥6 wymaga okna m-of-M. **Wniosek: okno-K
(dźwignia a) jest ZBĘDNE** — ENTRY-once przy obecnym K=3 admituje wszędzie. `gate_coverage_raw` per-tick
0.42–0.73 (spójne z `coverage_gate`). Tabela pełna: `posthoc.json` → `D2_ktable`.

**D4 — wykonalność MTI-P (test anty-statyczny).** Z `vehicle_local_position` (dołożony w patchu) baseline
platformy per bieg **B_perp = 7.8–18.3 m** (kwadrat OBSERVE daje realną geometrię), rozrzut bearingu
celu az ~95–99°, el ~70–76°. **D4 ODBLOKOWANE względem DIAG** (tam: brak pozy → niewykonalne). Pełny
rezydual triangulacji „obiekt statyczny" (cel vs paralaksa tła) wymaga jeszcze synchronicznego
bearing↔poza per klatka — **teraz DOSTĘPNY w trace** → policzalny w następnej iteracji. Tu: wykonalność
+ geometria potwierdzone (`posthoc.json` → `D4_mtip`, `feasible=True` wszędzie).

---

## (IV) GRANICA ROSZCZENIA · rozbieżności · rejestr [A4]

- **Granica roszczenia:** wynik w **`world_demo_v1.1`** (84 bloki `tex_*`, paralaksa tekstury) pod
  **PX4 SITL + gz Harmonic (WSL2/D3D12/ogre2)**. Liczby percepcyjne NIE przenoszą się między światami
  (R-M1). Roszczenie: *brama ENTRY-once struktura∧MTI admituje ruchomego intruza ≥7 m przy ε_FP=0 w tym
  habitacie, w locie OBSERVE-motion.* NIE jest to roszczenie o zasięgu operacyjnym w terenie rzeczywistym.
- **Rozbieżność 1 (kontencja):** regate3 armował dopiero po relaunch (env-fail #1 = High Gyro Bias pod
  równoległym `fabryka/train_epoch1`); jego rtf_end skolapsował w teardown (0.04) i miał 37 timesync-resync
  w settle. Faza pomiarowa zdrowa (dur_s=wall, content_resid stabilny) → WAŻNY z flagą. Gdyby powtórzyć:
  bieg bez kontencji GPU/CPU (świeży slot) usunąłby flagę.
- **Rozbieżność 2 (t_entry@5m regate3 = 28 s):** admisja bardzo późna pod kontencją, w oknie dwell 30 s —
  admituje, lecz margines cienki; 5 m i tak informacyjne (R-5).
- **Rejestr [A4] (prowizoryczne, nie z pomiaru tej sesji):** `DEADMAN_TICKS=6` (nietknięte), `L_deliver=0.1`,
  `θ_age=3.0`, `θ_conf=0.1635` (telemetria pasywna, nietykalne); `content_resid` stały offset per boot
  31–38 s (origin timesync bootu; Δq WZGLĘDNE → nieszkodliwe, potwierdzone ε_FP=0 ×3 jak B5); mono_cam
  intrinsics fx=fy=270 (D4 bearing). Derotacja translacja-niekompensowana = nazwana słabość (D1 mechanizm).

### WERDYKT

**Re-bramka ENTRY-once: (+) PASS · (−) PASS** (×3 świeże booty, world_demo_v1.1, ANEKS-H).
Percepcja live domknięta pod zrewidowaną bramą. **Rdzeń bezpieczeństwa NIETKNIĘTY** (SR-R4:
`target_channel`/`shield.step`/certy bez zmian — target_channel realizował admission-only MTI już przed
sesją; B5 (+) FAIL był artefaktem metryki `coverage_gate`). D1 rozstrzygnął mechanizm na trace
(centralność + rezyduum translacji derotacji; hipoteza pościgu obalona), nie na agregacie.

**STOP. Push = Olga.** Jeśli (+) PASS ratyfikowany → następny prompt: noga D (akty dema, DEMO-B).
Otwarte (osobne, nie-blokujące): pełny rezydual MTI-P (D4, dane już w trace); dźwignia „centralność"
(dominujący limiter `coverage_gate`, gdyby kiedyś chciano podnieść per-frame coverage — poza ENTRY-once
zbędne) — wyłącznie decyzją Olgi.

Artefakty: `results/R02/mti/REGATE/{regate1,regate2,regate3,regate3_envfail1}/`,
`B_regate_aggregate.json`, `posthoc.json`, `aggregate_regate.py`, `posthoc.py`, `test_regate.py`.
