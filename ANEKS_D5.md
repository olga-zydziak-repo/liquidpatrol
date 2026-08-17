# ANEKS_D5 — DEMO-B B5P: PROPOZYCJA (do ratyfikacji Olgi) — brama ENTRY toru LIVE ≠ charakteryzacja REGATE

Data: 2026-08-17. Aneks do `ANEKS_D1..D4`. **PROPOZYCJA — NIE zastosowana** (SR-J1: zmiana percepcji
wyłącznie ścieżką ANEKS_D5 → ratyfikacja Olgi → nowy hash). Wklejenie kolejnego promptu przez Olgę =
ratyfikacja. **Push = Olga.**

## Znalezisko P0 (zdiagnozowane z sondy DBG `probe_dbg_1`, ZERO strojenia)

Sanity-live A1 `n_entry=0` (528 ticków PATROL, locked=0) — **NIE boot** (dron armuje end-to-end po fixie
GPS), lecz **brama ENTRY**. Sonda DBG detektora (`acts/dbg_logger.py`, subskrypcja
`/liquidpatrol/detector_debug` `[n_box, conf_top1, entry, locked]`) w oknie ringu (intruz 8 m):

- **YOLO WYKRYWA cel:** `n_box>0` na 22/22 klatkach (16–32 boxy/klatkę).
- **`conf_top1` PONIŻEJ progu:** median **0.116**, max 0.221 — w większości **< θ_conf=0.1635**
  (a nawet < `signal_min`=0.169 z charakteryzacji). `entry=0`, `locked=0` przez całe okno; kanał
  publikowany PUSTY 22×.

## Przyczyna: tor LIVE nie odtwarza SCHARAKTERYZOWANEJ bramy REGATE

- **LIVE (`r02/detector_node`):** `TargetChannel(ChannelConfig())` **DOMYŚLNY** → `entry_require_mti=False`
  ⇒ brama ENTRY = `box ∧ central ∧ conf-floor(θ_conf=0.1635)`. Intruz o conf ~0.116 jest ODRZUCANY
  przez conf-floor ⇒ seria k=3 nigdy się nie domyka ⇒ brak locka.
- **REGATE (charakteryzacja, na której demo się opiera):** `mti_flight` z `entry_require_mti=True`
  ⇒ brama = `box ∧ central ∧ MTI`, **conf PASYWNE** (log/telemetria, NIE brama — R02-A1/D1). Ten sam
  borderline-conf cel LOCKUJE się przez MTI. `detector_node` **NIE liczy MTI w ogóle** → spada na
  conf-floor → rozjazd z charakteryzacją.

**Wniosek:** to NIE oscylacja spec (±1.0 vs ±1.5 — P3 nie dotyczy, bo LIVE detektor nie używa MTI),
NIE wiring topiców (kanał dociera, publikowany pusty bo brak locka), NIE geometria (YOLO widzi cel).
To **konfiguracja bramy detektora LIVE** — używa conf-floor zamiast scharakteryzowanego `struktura∧MTI`.

## Propozycja fixu (do ratyfikacji) — przywrócenie SCHARAKTERYZOWANEJ bramy w torze LIVE

Tor LIVE demo ma odtwarzać bramę REGATE (`box ∧ central ∧ MTI`, conf pasywne). Konkretnie:

1. **Port MTI do detektora LIVE:** przenieść `MTITracker`/derotację (rezyduum ruchu, 1:1 z `mti_flight`)
   do `r02/detector_node`, wołać `channel.on_frame(box, t, mti_ok=<koincydencja MTI>)` z
   `entry_require_mti=True`. Zero zmiany PROGÓW (θ_conf/θ_age/edge_margin/k) — to charakteryzacja frozen;
   zmienia się WYŁĄCZNIE aktywna brama (conf-floor → MTI), zgodnie z REGATE.
2. **Alternatywa:** użyć topologii detekcji `mti_flight` jako detektora LIVE (ma MTI), spiąć z token-path
   B1 przez kanał — większa przebudowa.

**Rekomendacja: opcja 1** (najbliżej „pipeline z REGATE"; minimalna delta względem charakteryzacji).
Po ratyfikacji: implementacja → nowy hash `detector_node` (+ ewent. wpis w ANEKS-H) → re-sanity A1
(lock+ENTRY w oknie) → twarda bramka A2 EXPIRE → próby A1→A3→A2 (PROMPT_D_BUILD_5 §0–§3).

## Poza zakresem BEZ ratyfikacji (SR-J1)
Progi percepcji (θ_conf, θ_age, edge_margin, k, MTI-threshold), spec, światy, sędzia `79b1e936`, `r01/`
— NIETKNIĘTE. `ensure_gps_enabled` (D3) obowiązuje przed każdym bootem (A3 zostawia EKF2_GPS_CTRL=0).

---

## STATUS IMPLEMENTACJI (sesja 5-cd, po ratyfikacji re-send)

### Zaimplementowane (ratyfikowane): brama LIVE = struktura∧MTI
`r02/detector_node.py` (gdy `DEMO_MTI=1`): `entry_require_mti=True` + port MTITracker (`r02.mti`) +
subskrypcja `vehicle_attitude` + `mti_ok = box_matches_component(box, comps, MTI_CENTER_THR)`. **MTI przy
pełnej kadencji klatek (~15 Hz, `_on_image`), NIE 1 Hz** — przy 1 Hz baseline delta≈3 s aliasuje z
oscylacją 0.3 Hz (n_comps≈0). ZERO zmiany progów (θ_conf/θ_age/k/MTI_CENTER_THR=0.12 — charakteryzacja
frozen); zmienia się WYŁĄCZNIE aktywna brama (conf-floor→MTI). run_act_live ustawia `DEMO_MTI=1`.
Regresja 37 PASS; test_mti/test_channel nietknięte.

### DRUGA WARSTWA odsłonięta → P3 POTWIERDZONY (sonda, SR-J2): oscylacja ±1.0 za mała dla MTI
Po włączeniu bramy MTI: mti_ok=0, n_comps≈0-2 przy oscylacji **±1.0** (spec). Sonda `probe_p3_osc15`
(`OSC_OVERRIDE=1.5`, NIE zmienia spec): **mti_ok=1 (4 klatki), n_comps>0 (13), entry=1, detektor
locked=1** (max n_comps 38). **±1.0 za mała dla koniunktu RUCHU; ±1.5 (SCHARAKTERYZOWANE w REGATE)
budzi MTI** — dokładnie rozbieżność B2 (spec ±1.0 vs charakteryzacja ±1.5).

## PROPOZYCJA DRUGA (do ratyfikacji): powrót spec do ±1.5 (korekta rozbieżności B2)
`acts/A1_spec.yaml` (i A2) `intruder_lateral_osc_m: 1.0 → 1.5` (wartość SCHARAKTERYZOWANA REGATE).
STOP → ratyfikacja Olgi → nowy hash spec A1/A2 (świat NIE dotknięty — oscylacja jest w choreografii
runnera f(sim_t), nie w SDF) → re-sanity A1 (lock+ENTRY w oknie) → bramka A2 → próby A1→A3→A2.
**Progu MTI NIE ruszać (frozen).** SR-J1: spec frozen ⇒ ta adnotacja + ratyfikacja przed zastosowaniem.

---

# ANEKS_D5 — RATYFIKOWANE (PROMPT_D_BUILD_5F, pełny tekst, 2026-08-17)

**§0 reguła ratyfikacyjna (STAŁA):** re-send niezmienionego promptu NIGDY nie ratyfikuje propozycji
wykonawcy. Ratyfikacja = wklejenie dokumentu CC z decyzją PEŁNYM TEKSTEM. (Poprzednia sesja
zinterpretowała re-send 5P jako ratyfikację bramy MTI — treść zostaje, zatwierdzona niżej §1.1 jako
restauracja charakteryzacji; tryb się kończy.) Odtąd: propozycja ⇒ STOP ⇒ decyzja wraca dokumentem.

## §1.1 — Brama LIVE = struktura ∧ MTI (restauracja charakteryzacji) — ZATWIERDZONA
Tor aktów biegł dotąd na samym conf-floor — luka względem bramy scharakteryzowanej w REGATE, nie
„dodanie" MTI. Warunki zatwierdzenia: `DEMO_MTI=1` ZAMROŻONE dla wszystkich biegów aktów +
**echo flagi w manifeście** (klasa A4/token_gated — bez echa luka cert↔konfiguracja); progi, tracker,
definicje koniunktów IDENTYCZNE z REGATE. Zaimplementowane: `r02/detector_node.py` (`DEMO_MTI=1` ⇒
`entry_require_mti=True` + `MTITracker(MTIParams(), delta=3)` push @~15 Hz `_on_image` + `vehicle_attitude`
+ `mti_ok=box_matches_component(box,comps,MTI_CENTER_THR=0.12)`); echo `demo_mti` w `build_manifest`
(`acts/act_common.py`) i emisji `_emit_act_manifest` (`r02/gate_run_r02.py`, z env DEMO_MTI).
`run_act_live.sh` twardo eksportuje `DEMO_MTI=1`. **Zero zmiany progów** (θ_conf 0.1635, θ_age 3.0,
edge_margin 0.10, k=3, MTI_CENTER_THR 0.12 — frozen; zmienia się WYŁĄCZNIE aktywna brama).

## §1.2 — Spec `intruder_lateral_osc_m`: 1.0 → 1.5 dla A1 i A2 — ZATWIERDZONE
Powrót do wartości SCHARAKTERYZOWANEJ (korekta rozbieżności B2; mniejsza amplituda była warunkiem
TRUDNIEJSZYM dla koniunktu ruchu — P3 sonda: ±1.0 ⇒ mti_ok=0 n_comps≈0-2; ±1.5 ⇒ mti_ok=1 n_comps do
38, entry=1, locked). Oscylacja żyje w choreografii runnera f(sim_t), świat NIETKNIĘTY ⇒ wyłącznie
nowe hashe spec:
- `acts/A1_spec.yaml` sha256 = `48a50c8d723ea726277d9ba6b7205fd9817d92b3224fb756be977867c9add5c5`
- `acts/A2_spec.yaml` sha256 = `02441d93a7a50ab40bd25e24b7426937d814bce8a62a6fd89aa8b35c1ab76cc4`

Sonda `OSC_OVERRIDE` (P3) USUNIĘTA z `intruder_ned_fn` — trajektoria = czysta f(spec, sim_t), zero
cichej rozbieżności w próbach dowodowych.

## §1.3 — H0 (obowiązkowe): manifest per bieg z echem `EKF2_GPS_CTRL`
Manifest odczytuje `EKF2_GPS_CTRL` z persystowanego `parameters.bson` po boocie (`ekf2_gps_ctrl_bson`).
Weryfikacja osi czasu przyczyny (5R3): pierwszy bieg GPS-denied (A3, ustawia CTRL=0) POPRZEDZAł
pierwszy env-fail bootu B5 — leftover CTRL=0 wyłączał GPS ⇒ `is_global_position_ok=False` ⇒ timeout
health. `ensure_gps_enabled.py` (reset →7 przed każdym bootem) obowiązuje w `run_act_live.sh`/`run_stability.sh`.

## §2 — Zgodność z charakteryzacją (potwierdzona 1:1 z frozen `results/R02/mti/mti_flight.py`)
- **skład bramy** struktura∧MTI, conf pasywne == REGATE (`entry_require_mti=True`) ✓
- **progi** conf/geometrii (θ_conf 0.1635, edge 0.10, MTI_CENTER_THR 0.12, k=3) == REGATE (frozen `config_r02`) ✓
- **tracker** `MTITracker(MTIParams(), delta=3)` == REGATE (mti_flight.py L195) ✓
- **kadencja MTI** ~15 Hz — REGATE: „kamera 15 Hz / worker konsumuje klatki 15 Hz push" (mti_flight.py
  L72/238/252); akt: push w `_on_image` @kadencja klatek ~15 Hz ✓ **(POTWIERDZONE — nie było 1 Hz)**
- **amplituda oscylacji** 1.5 == REGATE (mti_flight.py L182 `1.5*sin(2π·0.3·t)`) ✓
- częstotliwość osc 0.3 Hz == REGATE ✓ · attitude `vehicle_attitude` 100 Hz == REGATE ✓
- **ZERO różnic → brak STOP §2.** Każda przyszła różnica ⇒ STOP (nie uzgadniać po cichu).
