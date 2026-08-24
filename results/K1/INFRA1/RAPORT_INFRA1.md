# RAPORT_INFRA1 — stabilność boot-health (M4) · wersja CZĘŚCIOWA przed resetem operatorskim

LiquidPatrol · zadanie infrastrukturalne · 2026-08-24 · ANEKS_INFRA1-2 (reset operatorski)
Status: §1–§3 domknięte, §4 (dziesiątka) czeka na shakeout po resecie, §5 nota do RAPORT_K1.

## §1. Diagnoza źródła — HIPOTEZA OBCIĄŻENIA (M4) OBALONA (N1)

Przesłanka M4: „głód CPU dławi most gz↔PX4 → time jump → EKF reset → arm denied". **Obalona pomiarem:**

- **I1 w spoczynku** (żaden boot): loadavg 1-min próbkowany co 30 s przez ~10 min = **0.02–0.28**,
  CPU 99.6% idle, mem_avail ~30 GB, brak procesów WSL trzymających load. ⇒ **źródło load NIE jest
  zewnętrzne (host Windows) ani leftover** — maszyna w spoczynku jest czysta.
- **Kontrprzykład rozstrzygający (4 kolejne booty po `wsl --shutdown`, wszystkie headless):**

  | boot | loadavg | „Ready for takeoff" | px4 timejumps |
  |------|--------:|:---:|:---:|
  | S boot4 | ? | ✗ | 7 |
  | S boot5 | ? | ✗ | 6 |
  | S boot6 | **18.1** | ✗ | 7 |
  | E boot0 (shakeout) | **2.25** | ✗ | 8 |

  boot6 padł przy load **18**, boot0 padł IDENTYCZNIE przy load **2.25**. ⇒ **awaria jest
  NIEZALEŻNA od obciążenia CPU.** Hipoteza obciążenia obalona.

- **Rzeczywisty mechanizm (cytat, `E/p0_0/boot0/px4.log`):** stan terminalny to zapętlony cykl
  `[timesync] time jump detected. Resetting time synchroniser.` → `time sync no longer converged`
  → `time sync converged`, ×8, przy `Preflight Fail: High Gyro Bias / horizontal velocity unstable`,
  który NIGDY się nie czyści. Skorelowane z głębokimi stallami gz RTF (min 0.01, 9× rtf<0.5):
  gz stutteruje zegar sim → PX4 timesync resetuje → EKF nie zbiega → arm denied. GUI wykluczone
  (wszystkie booty `GUI_PROCS=[brak]`). Chain zgodny z komentarzem `run_stack.sh:31`, ale wyzwalany
  przez lockstep/render, nie przez load.

**Wniosek I1(c): źródło NIEUSTALONE co do load (spoczynek czysty), ale DRIVER awarii = pętla timejump
lockstepu gz↔PX4, load-niezależna.** To odpowiada na pytanie M4 „dlaczego wcześniej nie armowała".

## §2. Zmiana I2 (zachowana, ale NIE jest środkiem zaradczym) (N1)

Jedna zmiana przed-lotowa w `k1/run_k1_boot.sh` (dwa elementy, semantyka „nie startuj/nie armuj na
chorej maszynie"): (a) **bramka obciążenia** przed startem stacku (loadavg1<8.0, czekaj ≤10 min,
inaczej env-block); (b) **arm po zbieżności** — min settle 90 s, potem czekaj na `Ready for takeoff!`
w px4.log do 300 s, inaczej env-fail (zamiast ślepego `sleep 90`). Sygnał już logowany, obecny w
bootach udanych (N4/S2), nieobecny w env-failach (S4/5/6).

**Status po N1: ratyfikowana na przesłance, która upadła. Zachowana w repo bo NIESZKODLIWA i wyłącznie
przed-lotowa (nie dotyka segmentu roszczenia denial→touchdown; frozen judge/shield/config/gate NIETKNIĘTE
— zweryfikowane).** NIE liczy się jako remedium: convergence-wait tylko OBSERWUJE pętlę timejump do
timeoutu, nie leczy jej. Diff: patrz commit; ANEKS_SHA nota, że warstwa przed-lotowa nie zmienia
lotów sprzed hartowania (S boot3 diag, N boot4 crit pozostają ważne bez gwiazdki).

Dodatkowo (narzędzia diagnostyczne w tools/, nie „harness"): `infra1_empty_flight.py` (pusty lot
60 s hover), `infra1_empty_finalize.py` (manifest pustego bootu + habitat hoveru), `infra1_campaign.sh`
(seria 10, cooldown ≥5 min), `infra1_gate.py` (bramka ≥9/10), `infra1_shakeout_check.py` (§3).

## §3. Shakeout po resecie — kryterium i interpretacja ZAMROŻONE TERAZ (N3)

`tools/infra1_shakeout_check.py` (commit przed resetem, sha w manifeście):

- **PASS ⟺ arm_ok ∧ n_timejumps ≤ 1 ∧ (0 głębokich stalli rtf<0.5 w oknie preflight→arm).**
- **FAIL ⟺ cokolwiek innego.**
- **Interpretacja (zamrożona):**
  - **PASS** ⇒ zły lockstep był PRZEJŚCIOWy po restarcie ⇒ wracamy do **I3 (dziesiątka liczona)** na
    NIEZMIENIONYM kodzie.
  - **FAIL** ⇒ pętla timejump = TRWAŁA własność habitatu ⇒ **STOP + osobny dokument INFRA-2** na
    właściwy cel (most gz↔PX4: wersja/plugin gz + tryb lockstep, `PX4_SIM_SPEED_FACTOR`, źródło zegara
    sim, headless vs render, sterownik GPU w WSL — kandydaci do ZBADANIA, nie wdrożenia bez dokumentu).
- **Dokładnie JEDEN shakeout. Bez powtórki** (powtarzanie do skutku = selekcja).

Walidacja frozen-check na E boot0 (przed resetem): **FAIL** (arm_ok=false, n_timejumps=8, deep_stalls=9) —
zgodnie z oczekiwaniem.

**Reset operatorski (N2, Olga):** zamknięcie sesji wykonawcy → `wsl --shutdown` → ~60 s → pełny restart
maszyny jeśli możliwe (czyści stan sterownika GPU — korzeń D8). Odnotowany w manifeście shakeoutu.

## §4. Bramka 10 bootów — CZEKA na shakeout PASS po resecie

(Uzupełnić po resecie: tabela 10 kolejnych pustych bootów, n_arm/n_habitat_valid, werdykt ≥9/10.)

## §5. Nota do RAPORT_K1 §IV (charakterystyka env)

Rodzina D8/B5 w tej kampanii: gz RTF deep-stalls (rtf do 0.01, ~9/boot) + pętla PX4 `time jump
detected` (6–8/boot) niezależna od load (boot6@18 ≡ boot0@2.25) ⇒ intermittent arm-fail projektu to
własność lockstepu gz↔PX4/rendera, nie obciążenia. Osłona/sędzia/kryteria niezmienione.

## Kalendarz (N5) — bez udawania

Jeśli shakeout N3 = FAIL: **K1 nie wznawia się przed INFRA-2**; pakiet na 2026-09-01 = **DEMO-B v1.0
z erratami + RAPORT_K1_B1_STOP** jako uczciwy status nogi w toku. Planowane teraz, nie „licząc, że
maszyna sama się naprawi".
