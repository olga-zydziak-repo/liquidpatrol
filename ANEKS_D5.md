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
