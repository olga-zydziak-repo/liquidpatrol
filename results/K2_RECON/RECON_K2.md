# RECON_K2 — recon-lite pozycji 6 (K2: sieć + denial pod osłoną), offline

LiquidPatrol · pozycja 6 · CC 6.09.2026 · wykonawca: Claude Code · **ZERO bootów** (recon z kodu + istniejących trace)
· zapisy tylko `results/K2_RECON/**` · frozen READ-ONLY · commit recon-only. Każdy fakt = plik:linia albo ścieżka trace.

## R1. Gdzie siedzi osłona w ścieżce lotu ławki

- **Osłona w pętli:** `bench/bench_flight.py:326` — `d_dec = shield.step(tick, own, vel, tgt, mode=M_PATROL, pos_flag=None)`. Ta sama klasa `r01.shield.PatrolShield` (import `bench_flight.py:38`), instancja `bench_flight.py:178`.
- **Reużycie gate vs kopia:** bench_flight ma **WŁASNĄ pętlę epizodu** (osobny moduł, `bench_flight.py:3` „NIE dotyka gate_run_r03.py (pinowany) — osobny moduł, ta sama osłona P2-ε w pętli"). Reużywa OBIEKT/klasę osłony, NIE pętlę gate. → **P-K2R1 (reużycie tej samej ścieżki co gate, nie kopia) CZĘŚCIOWO OBALONE: reużyta osłona, ale pętla własna (kopia logiki wywołania).**
- **`pos_flag=None` NA SZTYWNO** (`bench_flight.py:326`) ⇒ **monitor POS_DEGRADED NIEAKTYWNY w bench**. gate wiąże denial: `gate_run_r03.py:267` `pos_flag=(dr if denial_done else None)` gdzie `dr=bool(m.dead_reckoning)`. **bench nie czyta dead_reckoning i nie podaje go osłonie.**
- **REFUSE w bench (`bench_flight.py:327-335`):** ALLOW→set_velocity(v_ned); REFUSE→`set_velocity_ned(0,0,0)` (HOVER) + `ev("refuse")` + `refuse_count++`; epizod kończy się gdy `refuse_count>0` (`:340`). **BRAK akcji D5** (dwufazowe velocity-descent 1.5→0.7 m/s), którą robi gate na POS_DEGRADED (`gate_run_r03.py:6` docstring + `:268`). → **ścieżka REFUSE/D5 w bench jest INNA niż gate (hover+koniec, nie zejście) i NIETESTOWANA: 0 zdarzeń refuse w 84 epizodach lotów NCP (R5).**
- **certs_selfcheck:** `run_boot.sh:72` `if [ "$FLIGHT" = "gate_r03" ]` ⇒ **NIE biegnie dla FLIGHT=bench**. Loty NCP (kampania) NIE uruchamiały certs_selfcheck.
- **Kandydackie miejsca wstrzyknięcia denialu (opcje, bez wyboru):**
  - (a) **Realny denial jak K1** — `EKF2_GPS_CTRL=0` przez param px4 mid-flight → EKF wchodzi w `dead_reckoning`. KOSZT: wymaga (1) modułu/haka ustawiającego param w locie (wzór ramienia K1) **ORAZ** (2) edycji bench_flight by czytał `m.dead_reckoning` i podał jako `pos_flag` (dziś None). Realistyczny (ta sama fizyka co K1), droższy.
  - (b) **Syntetyczny trigger w bench_flight** — `pos_flag=True` po punkcie fazy (R3), bez zmiany paramu GPS. KOSZT: edycja bench_flight (trigger + pos_flag). Deterministyczny, tańszy, ale NIE ćwiczy realnej degradacji EKF (osłona dostaje flagę, nie prawdziwy dead-reckoning).

## R2. Składanie sędziów

- **Pola trace bench (verbatim):** `{"t":"gt","sim","x","y","z"}` (GT drona z dynamic_pose, `bench_flight.py:102`), `{"t":"ekf","ts","x","y","z"...}` (`:85`), `{"t":"event","sim","ev",...}` z ev∈{armed,takeoff,offboard,episode_start(scenario_id,t0_sim),intruder_start_gate,invalid_start,episode_end(t_entry,refuse,breach),refuse(reason,r_est),breach(r_est)} (`:191`).
- **Czego potrzebuje `k1/k1_judge.py`:** `load_gt` (`:50`) czyta wiersze `t=="gt"` z `sim,x,y[,z]` — **bench gt rows SĄ kompatybilne** (te same klucze). `gt_metrics(gt, t_inj, home)` (`:136`) liczy r_max/r_td/**x_exc od punktu inj**/t_td/breach/touchdown. Touchdown (`:121`) zakłada **z=Up (ENU)** progi AIRBORNE_U=1.0 / GROUND_EPS_U=0.5; nav_state_seq z **ulog** (`read_ulog :184`).
- **BRAKI (lista):**
  1. **`t_inj` (sim-time wstrzyknięcia denialu)** — bench NIE ma denialu ⇒ brak zdarzenia inj. k1_judge x_exc/t_td liczone WZGLĘDEM t_inj → bez niego niepoliczalne.
  2. **Ramka z dla touchdown** — bench gt z z dynamic_pose (znak/konwencja do potwierdzenia); k1 zakłada ENU-Up. r_max/x_exc (poziome) są ramka-agnostyczne, touchdown/t_td NIE.
  3. **nav_state_seq** — z ulog (bench ma boot.ulg), ale k1 `read_ulog` musi dostać ścieżkę; bench trace sam nie niesie nav_state.
- **Opcje (fakt, nie wybór):**
  - (a) **k1_judge na trace bench bez zmian** — DZIAŁA dla r_max/x_exc/breach (poziome) GDY dostarczy się t_inj; touchdown/nav_state wymagają z-ENU + ulog.
  - (b) **glue `k2_judge`** = `bench_judge` (ważność epizodu V2′ do momentu denialu) + metryki denialowe k1-stylu (r_max/x_exc/t_td/breach/nav_state) z potwierdzoną ramką — **bez dotykania żadnego zamrożonego sędziego**.
- → **P-K2R2 (k1_judge nie strawi trace bench bez glue) POTWIERDZONE dla pełnego zestawu metryk** (brak t_inj + ramka z + nav_state); poziome metryki strawi.

## R3. Punkt fazy denialu — sygnały runtime dostępne do triggera

- **Co bench_flight wie w locie:** `t_entry` (czas wejścia w pasmo, `bench_flight.py:324`, ustawiany gdy `6.0<=d<=10.0`), `phase` z `cmd["extra"]["phase"]` (`:322`, approach/orbit/hold), `t_rel`, `tick`. **Sweep/omiatanie NIE liczone online** (sędzia liczy offline).
- **Opcje triggera (determinizm + koszt, bez wyboru):**
  - (i) **T s po wejściu w pasmo** — `t_entry` DOSTĘPNE w runtime; trigger `t_rel >= t_entry + T`. Najprostszy, deterministyczny, koszt ~zerowy (dodać warunek).
  - (ii) **omiatanie ≥360° online** — NIE ma licznika; wymaga dodania integracji namiaru w pętli. Droższy.
  - (iii) **tick absolutny** — `tick` dostępny; deterministyczny, ale nie związany z fazą.

## R4. Arytmetyka koperty na ISTNIEJĄCYCH trace (offline) — NAJWAŻNIEJSZE

Policzone z GT drona (`t=="gt"`, r=hypot(x,y) względem home 0,0) na **84 ważnych epizodach lotów NCP** (F2 48 + F3 36; MLP wykluczony — slot lecący = NCP, więc koperta liczona dla kontrolera, który poleci). `results/K2_RECON/r4_envelope.json`.

| cell | n | rmax_p50 | rmax_p95 | **rmax_MAX** | r@1orb_p95 | r@2orb_p95 |
|---|---|---|---|---|---|---|
| c00 | 7 | 23.48 | 23.66 | 23.66 | 23.11 | 23.54 |
| c01 | 7 | 23.35 | 23.61 | 23.61 | 18.93 | 15.81 |
| c02 | 7 | 23.51 | 23.67 | 23.67 | 21.32 | 22.32 |
| c03 | 7 | 23.79 | 24.11 | 24.11 | 13.02 | 9.90 |
| c04 | 7 | 20.83 | 23.04 | 23.04 | 23.03 | 17.32 |
| c05 | 7 | 21.66 | 24.57 | 24.57 | 11.88 | 14.87 |
| c06 | 7 | 21.80 | 22.95 | 22.95 | 20.43 | 21.75 |
| **c07** | 7 | 20.72 | 26.78 | **26.78** | 13.56 | 15.75 |
| c08 | 7 | 22.41 | 23.37 | 23.37 | 22.32 | 19.24 |
| c09 | 7 | 22.05 | 25.76 | 25.76 | 17.92 | 24.53 |
| c10 | 7 | 21.38 | 26.63 | 26.63 | 24.55 | 21.24 |
| c11 | 7 | 25.28 | 25.63 | 25.63 | 25.37 | 24.52 |

- **Globalny r_orbit_max = 26.78 m** (c07). Ranking malejąco: c07 26.8 · c10 26.6 · c09 25.8 · c11 25.6 · c05 24.6 · c03 24.1 · …
- **Koperta (pełna siatka, worst-case r_max):**
  - + denial **3.5 m** = **30.28 m** vs R_E=32 → **zapas 1.72 m**.
  - + denial **2.5 m** = 29.28 m → zapas 2.72 m.
- **ŻADNA komórka NIE daje zapasu < 1 m przy pełnej siatce** (worst 26.78+3.5=30.28, zapas 1.72 m). → **P-K2R3 OBALONE: PRE NIE musi ciąć geometrii dla zapasu ≥1 m.** (Geometria intruza pozostaje decyzją Olgi, ale recon jej nie wymusza.)
- **Niuans fazy (istotny dla wyboru punktu R3):** r_max to chwilowy pik; w KONKRETNYCH punktach wstrzyknięcia r jest niższe — r@2orb_p95 najwyższe: c09 24.53 / c11 24.52 / c00 23.54; r@1orb_p95: c11 25.37 / c10 24.55. Wstrzyknięcie w kontrolowanej fazie (np. koniec 1./2. okrążenia) daje r≈24-25 → +3.5 = 27.5-28.5, **zapas 3.5-4.5 m** — dużo bezpieczniej niż worst-case pik.
- **Zastrzeżenie:** excursion denialu 2.5-3.5 m to WEJŚCIE z K1 (mierzone w warunkach K1, patrol przy geofence); pod K2 dron jest na orbicie przy r≈24-26 — wielkość wychylenia po denialu na orbicie do ZMIERZENIA w K2 (recon zakłada K1 jako prior).

## R5. Ramię ujemne

**0 fałszywych REFUSE i 0 breach w 84 nominalnych epizodach lotów NCP** (F2 48 + F3 36; `results/NET/FLY/f2_ncp_b*/trace.jsonl`, `f3_ncp_b*`; potwierdzone `episode_end=84 refuse=0 breach=0`). Kandydat na bazę ramienia (−) K2 **bez nowych lotów nominalnych**. Warunki: wszystko frozen (NCP `0337d5ea`, feed FEED-B, świat A3, sędzia) — zerowe różnice wersji. (Uwaga: prompt mówił „132" = NCP+MLP; dla ramienia (−) K2 z siecią lecącą liczy się 84 NCP.)

## R6. Budżet (szacunek z liczb kampanii)

- Boot kampanii ~10 min (90 s settle EKF + 4 ep × ~95 s + reset), cooldown ≥5 min (F2: ~24 booty/kilka h; env-block dreamforge poza budżetem).
- **Epizod denialowy KRÓTSZY:** entry (~4 s) + orbita do wstrzyknięcia (T≈28-56 s) + zejście D5 + touchdown (~5-8 s) ≈ **40-70 s/epizod** (vs 95 s nominał) ⇒ **~5-6 epizodów/boot** realne (settle amortyzuje się na więcej ep).
- Koszt N ziaren × k prób: przy 6 ep/boot i np. 12 komórek × 3 ziarna = 36 ep ⇒ ~6 bootów; + ramię (−) z R5 za darmo. Rezerwa na env-block/relaunch jak w kampanii.

## PYTANIA DO PRE_K2

1. **Punkt fazy denialu (R3):** (i) T s po wejściu w pasmo [najprostszy, t_entry gotowe], (ii) omiatanie ≥360° [wymaga licznika online], (iii) tick absolutny. R4 sugeruje wstrzyknięcie po 1./2. okrążeniu trzyma r≈24-25 (zapas ~4 m).
2. **Podzbiór komórek / geometria:** pełna siatka daje zapas 1.72 m (worst r_max) / ~4 m (w kontrolowanej fazie) — czy PRE zostawia pełną siatkę, czy wyłącza pik-komórki c07/c10/c09/c11, czy tnie dysk intruza (decyzja Olgi, recon NIE wymusza).
3. **Forma sędziego (R2):** (a) k1_judge na poziomych metrykach + dostarczony t_inj, czy (b) glue `k2_judge` (bench_judge ważność + k1-metryki denialowe, zero dotykania zamrożonych).
4. **Miejsce wstrzyknięcia (R1):** (a) realny EKF2_GPS_CTRL=0 + wiązanie dead_reckoning→pos_flag w bench_flight, czy (b) syntetyczny pos_flag=True.
5. **Budżet N (R6):** liczba ziaren × prób; ~5-6 ep/boot.
6. **Definicja sukcesu (propozycja CC w PRE):** REFUSE ≤ budżet czasowy K1 ∧ zejście D5 ∧ breach 0, na N ziarnach. (Uwaga R1: ścieżka REFUSE/D5 w bench dziś = hover+koniec, NIE D5 — K2 musi dodać D5 do bench_flight albo użyć gate-stylu.)

## TWARDY STOP
Recon domknięty (R1-R6 kompletne, każdy fakt z plik:linią / trace). PRE_K2 pisze CC. Wykonawca po STOP: nic.
Artefakty: ten plik + `results/K2_RECON/r4_envelope.json`. Zero bootów, zero zmian kodu, frozen READ-ONLY.
