# ANEKS_D6 — DEMO-B: re-scope kanału detekcji (RATYFIKOWANY, 2026-08-19)

Aneks do `ANEKS_D1..D5`. Ratyfikowany dokumentem CC `PROMPT_D_R` (wklejenie = ratyfikacja Olgi).
**Push = Olga.** Kontrakty frozen bez zmian: `r01/` nietykalne, sędzia `79b1e936…`, trace v2,
manifest-po-arm, token B1, progi/tracker/percepcja frozen (SR-M1).

## Geneza (8a FAIL z mechanizmem POLICZONYM)

`RAPORT_D_B5 §AKTUALIZACJA-12`: probe pionowej osc (== REGATE `mti_flight.py:183` `0.6·sin(2π·0.23·t)`)
GATE 8a **FAIL**. Mechanizm z per-klatkowego logu (`results/demo/A1/probe_8a_vosc/mti_frame.jsonl`,
374 klatek): **`diff_max` mediana 177 przy progu `diff_thr=22` (frac>22 = 100%)** ⇒ magnituda ruchu celu
NIGDY nie była limiterem; **`mti_ok` centralny 1/57 in-window**, `n_kept` mediana 1 ⇒ znajdowane komponenty
to REZYDUUM DEROTACJI TŁA przy zawisie, nie intruz. **Wniosek o kopercie: brama live-MTI jest
scharakteryzowana dla lotu z ruchem WŁASNYM (REGATE, `cov_entry_once=1.0` @7–9 m, ego-motion), NIE dla
dwell-hold.** Spec A1 zamawia roszczenie percepcji w dwell-hold ⇒ port `mti_flight` sam z siebie tego nie
naprawia (wymagałby zmiany profilu lotu w oknie ENTRY). Stąd re-scope niniejszym aneksem.

## §1a — Kanał detekcji w aktach = GT-fed, JAWNIE ETYKIETOWANY

Akty A1/A2 biegną kanałem **GT-fed** (`GT_FED=1`, konfiguracja z B4, w której sędzia orzekł **A1 VALID 5/5**
i **A3 VALID 4/4**). **Live-MTI NIE jest przedmiotem roszczenia dema.** Echo **`detection_channel: gt_fed`**
w manifeście (`_emit_act_manifest`, `gate_run_r02.py`); **bieg aktu bez tego echa = INVALID z definicji**
(SR-M3). Kanał GT-fed = idealizowany detektor (perfekcyjna detekcja + szum obserwacyjny + dropout ZOH),
projekcja `project_to_pixel` (None poza FOV → EXPIRE); token path B1, progi kanału frozen.

## §1b — Przeformułowanie roszczenia (semantyka, nie kosmetyka)

Demo twierdzi: **warstwa certyfikowana zachowuje się dowiedzenie PRZY DANEJ DETEKCJI** — default-deny bez
tokenu, konsumpcja i re-admisja, dominacja GEOFENCE / POS_DEGRADED, containment GPS-denied. **Kanał
detekcji jest PRZESŁANKĄ, nie tezą.** Segment „claim" D3(a) (`gen_subtitles.py`) zmienia TREŚĆ: dotyczy
zachowania OSŁONY i BRAMY (token/dominacja/EXPIRE/containment), NIE wykrywalności celu.

## §1c — Plansze OBOWIĄZKOWE (do `gen_subtitles`, treść w słowniku)

Dwie plansze, wymagane w każdym montażu (SR-M2 — brak którejkolwiek albo sformułowanie roszczące percepcję
live = naruszenie):
1. **„detection channel: ground-truth-fed (idealized detector)"**
2. **„live perception characterized separately — REGATE: cov_entry_once=1.0 @7–9 m, ego-motion flight;
   not claimed in dwell-hold"**

**Zakaz** jakiegokolwiek sformułowania sugerującego, że demo dowodzi działania percepcji live.

## §1d — Znalezisko o kopercie (do RAPORTU, nie do zamiatania)

Live-MTI w zawisie NIE izoluje celu centralnie — rezyduum derotacji tła przekracza próg GLOBALNIE. Liczby
z 8a: **`diff_max` mediana 177, `frac>22 = 100%`, `mti_ok` in-window 1/57, `n_kept` mediana 1**. To wynik
NEGATYWNY domknięty bramką — zostaje w repo jako materiał osobnej nogi badawczej PO demie; **w tej sesji
nie jest przedmiotem żadnej naprawy.**

## §2 — Fix A2: far POZA FOV (ratyfikowany; nowy hash spec A2)

Znalezisko B4 wraca z kanałem GT-fed: kanał projekcyjny nie modeluje zasięgu, więc `far=[70,0,11.5]` (dead-
ahead 70 m) jest geometrycznie W FOV (`az≈0°, el≈1.2°`) ⇒ box ważny ⇒ brak EXPIRE ⇒ brak re-admisji.
**Zmiana spec A2: `intruder_far_enu [70,0,11.5] → [30,60,11.5]`** — POZA FOV. Wyliczone z geometrii kamery
mono (`horizontal_fov=1.74 rad`, `PX4-Autopilot/.../mono_cam/model.sdf`): krawędź HFOV/2 = 0.87 rad =
**49.8°**; wybrane far ma **`az=63.4°` (margines +13.6°)**, range **67.1 m** (nadal „far"), `el=1.3°`.
Zweryfikowane `project_to_pixel(pos=[0,0,-10], yaw=0, far_ned) = None(OUT→EXPIRE)`, przy czym ring
`[7.86,0,11.5]` pozostaje `BOX(in-FOV)`. Wzorzec = parking A1 `[7,0,3]` (`el=-45°` poza VFOV/2=41.6° →
EXPIRE działa). Zmiana WYŁĄCZNIE w spec A2 (choreografia runnera f(sim_t)), świat NIETKNIĘTY → tylko nowy
hash spec A2. **Zakaz** dokładania modelu zasięgu do kanału GT-fed w tej sesji (nowe twierdzenie o
detektorze — osobny dokument).

- `acts/A2_spec.yaml` sha256 (nowy) = zapisany po zmianie w tej sekcji przy commicie §2.

## §3 — Koszt: re-bramka §6d w konfiguracji docelowej

Wymóg kadencji aplikowanej ≥15 Hz istniał WYŁĄCZNIE dla live-MTI (ruch w każdej klatce). Przy GT-fed
wiążące jest tylko: poprawna geometria toru intruza + płynność materiału filmowego. Klient FF (19.4 Hz,
sim_t) zostaje jako ulepszenie; `pose_backend`/`teleport_hz` nadal echem, fallback subprocess = INVALID
(§7c). Kolejność: (i) wariant **C** — drenaż/nieakumulowanie reply w FF (artefakt 3 dipów) → (ii) pełna
re-bramka §6d (FILM=1): `Δsim/Δwall` w budżecie ANEKS-H ∧ `min/p10/frac<0.5` w klasie R2. Jeśli po C
FAIL wyłącznie na rezyduum dipów: obniżyć kadencję aplikowaną do wartości z B4 (uzasadnienie: przy GT-fed
kadencja nie wpływa na detekcję) i powtórzyć. Trzecia porażka ⇒ STOP dokumentem.

## §4 — Tor prób i montaż

Bramka A2 (EXPIRE far po §2) → próby A1→A3→A2 (≤3/akt, pierwsza VALID sędziego `79b1e936` kończy akt) →
`RAPORT_D_B5 §FINAL` → B6 montaż (materiał TYLKO z prób osądzonych, plansze §1c). Manifest per próba:
komplet ech (`token_gated`, `demo_mti`, `det_hz`, `detection_channel`, `pose_backend`, `teleport_hz`,
`EKF2_GPS_CTRL`, `contention`).

## Stop-rules (SR-M1..M6) — patrz `PROMPT_D_R`
