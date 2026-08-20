# ANEKS_D7 — DEMO-B: kryterium habitatu (RATYFIKOWANY, 2026-08-19)

Aneks do `ANEKS_D1..D6`. Ratyfikowany dokumentem CC `ANEKS_D7` (wklejenie = ratyfikacja Olgi).
**Push = Olga.** Kontrakty frozen: `r01/` nietykalne, sędzia `79b1e936…`, trace v2, manifest-po-arm,
token B1, progi/tracker/percepcja frozen (SR-M1). Bramka A2 PASS przyjęta (EXPIRE n=2, re-admisja
seq 0→1, 2 tokeny wydane+skonsumowane, `detection_channel=gt_fed`).

## §7a — Jawna rewizja kryterium (po zobaczeniu danych, odnotowana jako taka)

Kryterium §5c/§6d było źle wyspecyfikowane: porównywało bieg scenariuszowy (start, offboard, patrol, RTL)
do statycznego baseline'u R2. Stare liczby i werdykty zostają w `RAPORT_D_B5` z adnotacją
**„under superseded criterion"**, wraz z informacją, co by przeszło, a co nie, pod starym brzmieniem.

## §7b — Nowe kryterium habitatu (per bieg, liczone `acts/habitat_gate.py`)

- **H1 (twarde) lockstep przez CAŁY bieg:** `timejump_total = 0`, brak nieciągłości sim-time
  (sim monotoniczny; brak cofnięć / skoków wprzód >> upływu wall).
- **H2 segmenty ROSZCZEŃ** (A1/A2: dwell+OBSERVE; A3: denial→touchdown): `frac(rtf<0.5) = 0`,
  `p10 ≥ 0.99`, `Δsim/Δwall ≥ 0.95`. `p10`/`frac` z baseline'u R2; **próg `Δsim/Δwall` ustanowiony
  TERAZ** jako dopuszczenie narzutu scenariusza — zapisany jako NOWY (`H2_DSIM_DWALL_MIN=0.95`
  w `habitat_gate.py`), NIE udający, że pochodzi z R2 (R2 baseline ~0.9998).
- **H3 prowieniencja:** wszystkie liczby-wyniki z sim-time — weryfikacja + lista wielkości w raporcie.
  Metryki kosztu (`Δsim/Δwall, frac<0.5, p10`) liczone z gz sim-clock (`rtf_stream.sim`) vs unix wall
  ⇒ z definicji sim-derived. Zegar wewn. osłony (`trace.t = time.time()-t0`, `age`, `θ_age`) jest
  wall-elapsed; POD H1-lockstep (RTF≈1, timejump=0) `wall ≡ sim` w tolerancji ⇒ choreografia i θ_age
  wierne w sim. Tezy warstwy (default-deny tokenu, consume/re-admisja, POS_DEGRADED dominacja,
  containment promień touchdown) niezmiennicze względem ramki zegara. **Żadna teza nie stoi na zegarze
  ściennym**; H1-lockstep jest warunkiem umożliwiającym i sam jest bramkowany.
- **H4 tranzyt/start/RTL:** dipy raportowane liczbowo, oznaczone istniejącą planszą
  **„beyond characterized envelope — transit"**; ZERO roszczeń w tych segmentach, ZERO bramki.

## §7c — Antyselekcja (warunek ważności rewizji)

Skrypt segmentacji + progi **commitowane PRZED pierwszą próbą** (ten commit). Granice segmentów
wyprowadzane ze SPEC (choreografia), **NIGDY z przebiegu RTF**:
- A1/A2: okna = STAŁE `timeline_s` (`intruder_ring_hold`, `ep0/ep1_ring_hold`, `expire_gap`),
  mapowane trace-t → unix przez `manifest.arm_wall_unix` (= `self.t0` osłony przy arm) → selekcja
  próbek `rtf_stream` po `wall`. Zależność od RTF: ZERO.
- A3: okno = `[on_denial, on_touchdown]` (zdarzenia WYKONANEJ choreografii, `mono` z trace/act.log)
  → sim przez pary `gt (mono,sim)`. Zależność od RTF: ZERO.

Ocena habitatu (`habitat.json`) wchodzi do artefaktów **każdej** próby. Bieg naruszający H1 albo H2 =
**INVALID (habitat)** i liczy się do ≤3. Biegi diagnostyczne §3 (`results/demo/A1/regate_A1_ah4`,
`results/demo/A2/gate_A2_gtfed`) **NIE** są przeliczane jako dowodowe — posłużyły wyłącznie do
zdiagnozowania błędu kryterium (§7a).

## §7d — Backend

FF async (`GzPoseClient async_apply`, `19.4 Hz`, `Δsim/Δwall~0.977`, dipy w tranzycie) zostaje domyślny.
Jeśli w próbach H2 padnie przez dip wchodzący w segment roszczenia — przełączyć na **blokujący klient
in-process z §6d** (`async_apply=False`; 0% głębokich dipów, jednostajne 0.919; przy GT-fed kadencja
nie wpływa na detekcję) i powtórzyć próbę. `§7c/INVALID` dotyczy WYŁĄCZNIE fallbacku subprocess.
**Trzecia porażka habitatu na akcie ⇒ STOP dokumentem.**

## Tor prób (po tym commicie)

Próby **A1 → A3 → A2** wg `PROMPT_D_R §4` (`ANEKS_D6 §4`): ≤3/akt, pierwsza VALID sędziego
`79b1e936` ∧ VALID(habitat) kończy akt → `RAPORT_D_B5 §FINAL` → B6 montaż (materiał TYLKO z prób
osądzonych, plansze §1c). Push = Olga.

## Artefakty tego commitu (§7c, przed pierwszą próbą)

- `acts/rtf_sampler.py` — próbnik sim↔wall in-process (`/world/W/clock`), format `{wall,sim,rtf}`.
- `acts/habitat_gate.py` — bramka H1/H2/H3/H4; progi `H2_FRAC_LT_05_MAX=0`, `H2_P10_MIN=0.99`,
  `H2_DSIM_DWALL_MIN=0.95` (FREEZE). Segmentacja `segments_A1A2` / `segments_A3`.
- `acts/run_act_demo.sh`, `acts/run_A3.sh` — próbnik + `habitat_gate` wpięte (habitat.json per bieg).
- `r02/gate_run_r02.py` — `manifest.arm_wall_unix` (mapowanie okien; wyłącznie selekcja, nie z RTF).
