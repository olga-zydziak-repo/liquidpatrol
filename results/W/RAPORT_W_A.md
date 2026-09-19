RAPORT_W_A — faza W-A nogi W (wiatr): sonda kalibracyjna pod wyłącznością (S1)
=============================================================================
CC · 19.09.2026 · PROMPT_W_S1 §3 · booty przez tools/w_launcher.sh → harness/run_boot.sh (frozen),
FLIGHT=empty (infra1_empty_flight, hover K1_HOVER_S=90, ALT=8), OUTDIR results/W/probe/**, cooldown ≥300 s.
W-A NIE używa osłony (infra1 bez shield) — to pomiar WEJŚCIA toru pos_flag. w_judge w W-A nie orzeka.

ZAKRES WYKONANY: 4 poziomy {0, 1.5, 3.0, 4.5} + 1 retry (3.0). Booty lotne: 5 (≤6 budżet W-A).
Wyłączność: lock results/W/.executor_lock (PID) + pgrep-check przed każdym; zero kolizji, zero killi.


§1. TABELA WYNIKÓW (liczby per boot, okno hoveru [hs,he] sim; przechył z boot.ulg w_tilt)
------------------------------------------------------------------------------------------
boot  poziom  świat(sha16)      rc arm took_off  GT_z_hover  climb?  dead_reck  eph_max eph_p95  xy_reset  GT_dryf/znos      |vel|EKF  przechył_mean  habitat
1     0.0     s0 921bdda7        0  T   T         ~6.28 m     TAK     False(0t)  0.1536  0.1522   0         dryf 0.131m       0.083     0.085°         INVALID(Δs/w0.944)
2     1.5     s1p5 b8380e8a      0  T   T         ~5.71 m     TAK     False(0t)  0.1535  0.1521   0         osiadł 2.07m dw   0.287     9.144°         INVALID(Δs/w ~0.94)
3     3.0     s3 73214a2d        0  T   T(event)  −0.013 m    NIE     False(0t)  0.1524  0.1521   0         ślizg 0.55m dw    0.030     1.118°(ground) INVALID(min_rtf0.0018)
3b    3.0     s3 73214a2d(retry) 0  T   T(event)  −0.013 m    NIE     False(0t)  0.1524  0.1521   0         ślizg 0.56m dw    0.029     1.097°(ground) INVALID
4     4.5     s4p5 cf9df7b8      0  T   T(event)  −0.013 m    NIE     False(0t)  0.1524  0.1521   0         ślizg 0.74m dw    0.038     1.148°(ground) INVALID

Legenda: „climb?"=czy dron fizycznie wzniósł się (GT z>1 m). „took_off" event = komenda w skrypcie
(nie fizyczny climb). „dw"=downwind (+x East ENU). przechył s3/s3b/s4p5 = spoczynek na ziemi (no-climb),
NIE hover. Odniesienie bezwietrzne (INFRA3/B, RECON_W §R2): dryf 0.416–4.05 m, eph~0.15.


§2. WNIOSKI PER POZIOM
---------------------
- **0.0 (kontrola):** czysty hover, przechył 0.085° (poziom), dryf 0.131 m, eph 0.154, dead_reckoning=False.
  Rozszerza bazę bezwietrzną — zgodne z INFRA3/B.
- **1.5:** czysty hover, dron OSIADŁ ~2.07 m downwind (kontroler prędkości trzyma zerową prędkość ground
  stałym wychyleniem), **przechył 9.14°** (wyraźny podpis wiatru vs 0.085° przy 0), eph 0.154 (bez zmian),
  dead_reckoning=False. Poziom UZBRAJALNY i HOVEROWALNY.
- **3.0 (V_MAX):** dron UZBROIŁ się (arm_ok=True) i skrypt przeszedł sekwencję (takeoff/offboard/hover/land),
  ale **FIZYCZNIE NIE WZNIÓSŁ się** — GT z=−0.013 m przez cały ślad (91→285 s sim), `timeout_land`
  (airborne_seen nigdy nie zaszło). **REPRODUKOWALNE ×2** (boot3 + boot3b) → NIE losowy env-stall
  (reprodukcja obala hipotezę env), lecz systematyczny brak wzniesienia infra1 przy 3.0. eph 0.152,
  dead_reckoning=False — WEJŚCIE pos_flag CZYSTE mimo braku wzniesienia.
- **4.5 (arm-attempt, informacyjny, bez retry — H2):** **arm_ok=True** (UZBROIŁ się), ale NO climb
  (jak 3.0), ślizg 0.74 m downwind, eph 0.153, dead_reckoning=False. arm-attempt NIE dał arm-fail.


§3. WYNIKI KLUCZOWE (cross-level)
--------------------------------
(A) **WEJŚCIE pos_flag CZYSTE na WSZYSTKICH poziomach 0–4.5 m/s:** dead_reckoning=False (0 ticków true),
    eph_max 0.152–0.154 (≈ pasmo bezwietrzne ~0.15), xy_reset delta 0 — ZERO oznak, by wiatr (stały,
    ≤4.5 m/s, w zawisie LUB na ziemi) wypychał EKF w dead-reckoning. To bezpośrednia, mocna poszlaka
    dla tezy dostępności (H1): przy tych poziomach mechanizm fałszywego REFUSE(POS) się NIE pojawia
    (pos_flag = dead_reckoning nigdy nie wszedł w true). Rozstrzygnie kampania W-B (z osłoną).
(B) **PRÓG WZNIESIENIA infra1:** climb OK przy ≤1.5 m/s; brak climbu przy ≥3.0 (3.0 ×2, 4.5 ×1).
    Recon: 6.0 = arm-FAIL + dywergencja EKF + ślizg 5.77 m. Zatem: ≤1.5 hover · 3.0–4.5 arm-OK/no-climb ·
    ≥6.0 arm-FAIL. Ślizg na ziemi rośnie z wiatrem (3.0: 0.55 m · 4.5: 0.74 m).
(C) **PRZECHYŁ (airborne):** 0.085° (0) → 9.14° (1.5) — monotoniczny, wyraźnie separuje. Dla 3.0/4.5
    NIEMIERZALNY w hoverze (no-climb; wartości 1.1° to spoczynek na ziemi).
(D) **habitat INVALID we wszystkich** — Δsim/Δwall 0.936–0.944 (<0.95) + głębokie chwilowe dipy RTF
    (min_rtf do 0.0018), timejump=0. Znany env-bound deep-stall mostu gz↔px4 (nie bramkuje W-A —
    kalibracja, nie kryterium). NIE jest przyczyną no-climbu 3.0 (reprodukcja + 90 s sim w oknie).


§4. REGUŁA WYŁĄCZENIA §4 (LITERALNIE — o UZBROJENIU)
---------------------------------------------------
Reguła PRE §4 wyłącza poziom, który „nie uzbroi się w ≤2 podejściach". Wszystkie badane poziomy
{0, 1.5, 3.0, 4.5} **UZBROIŁY się** (arm_ok=True). Zatem LITERALNIE żaden poziom nie WYPADA z reguły
wyłączenia. 1.5 uzbroił się I hoverował ⇒ **BRAK triggera ŚMIERCI** (§7). Siatka kryterialna po regule
literalnej: **{0, 1.5, 3.0}** — bez zmian.

ALE (do decyzji ANEKS_W-1, NIE rozstrzygam — SR-W-6/S1-B): **3.0 UZBRAJA się, lecz w infra1 NIE
hoveruje (no-climb ×2)** — kalibracja hoveru dla 3.0 NIEOSIĄGNIĘTA. Reguła §4 (arming) tego nie
pokrywa (to nie arm-fail). Pytanie do CC/Olgi: czy 3.0 zostaje w siatce kryterialnej, skoro kampania
W-B lata w PĘTLI ŁAWKI na WŁASNEJ geometrii/takeoff (PRE W8), inny niż infra1 — no-climb może być
artefaktem sekwencji infra1 (AUTO takeoff()+OFFBOARD vel 0), nie limitem hoverowalności ławki.
Rekomendacja CC: boot-0 diagnostyczny ławki przy 3.0 w S2 (czy pętla ławki wznosi się przy 3.0) PRZED
uznaniem siatki; jeśli ławka też nie wznosi ⇒ 3.0 spada do noty H2-hover, siatka {0,1.5}.


§5. STATUS WSTĘPNY PREDYKCJI (BEZ ROZLICZANIA — rozliczenie tylko przy RAPORT_W)
------------------------------------------------------------------------------
- **P-W-3** (hover 3.0: dead_reckoning=false całe okno, eph_max<1 m): WSTĘPNIE ZGODNE co do sygnału
  (dead_reckoning=False, eph 0.152 przy 3.0), CHOĆ mierzone na ziemi (no-climb), nie w hoverze — słabsza
  ewidencja niż zakładano. Pełne rozliczenie wymaga hoveru 3.0 (ławka W-B).
- **P-W-5** (przechył rośnie monotonicznie i separuje 0 od 3): WSTĘPNIE — separacja 0↔1.5 potwierdzona
  (0.085°→9.14°); 3.0 NIEMIERZALNY w hoverze (no-climb). Nierozstrzygnięte co do 0↔3.
- **P-W-2** (arm z ziemi 4.5 = FAIL): WSTĘPNIE OBALONE — 4.5 arm_ok=True (uzbroił się). Próg arm-fail
  leży wyżej (≥6.0 wg reconu). [status wstępny, rozliczenie przy RAPORT_W]
- P-W-1/P-W-4: dotyczą siatki kryterialnej (W-B) — nie dotykane w W-A.


§6. ARTEFAKTY
-------------
results/W/probe/boot{1_s0,2_s1p5,3_s3,3b_s3,4_s4p5}/ — manifest pierwszej klasy, trace.jsonl, boot.ulg
(+sha, gitignore *.ulg), wa_metrics.json (offline), w_tilt.json (offline). launch logi boot3/3b/4.
Świat s4p5 sha cf9df7b8, s1p5 b8380e8a; s0/s3 reconu 921bdda7/73214a2d. Model wind_models/x500_base
(enable_wind) via GZ_SIM_RESOURCE_PATH prepend.
