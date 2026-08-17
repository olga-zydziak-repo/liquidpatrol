# ANEKS_D3 — DEMO-B blok B4: FREEZE sędziego ważności + rejestr rehearsali online

Aneks do `ANEKS_D1/D2`. Zapis §2 (FREEZE sędziego) i §3 (kadr-check + rehearsal online) bloku B4
(PROMPT_D_BUILD_4). Wzorzec korekt zachowany. Kanoniczny dla B5 (próby ≤3/akt).

## FREEZE sędziego (§2)

`tools/act_judge.py` — kryteria ważności PRE_D §5 implementowane 1:1. Po przejściu testów
(`tools/test_act_judge.py` 9/9) i rehearsali online **ZAMROŻONY**:

    sha256(tools/act_judge.py) = 79b1e9367b85bf7c29f97dc5ea9757052be68a26903e48c0a237f941526a671a

**Reguła (antyselekcja, SR-F3):** od tego momentu zmiana sędziego = **jawna adnotacja tu + ponowna
ratyfikacja Olgi**. Sędzia NIE może ewoluować pod próby. Kryteria (cytat PRE_D §5 → warunek):

| Akt | kryterium PRE_D §5 | warunek w act_judge.py |
|---|---|---|
| wspólne | „boot ANEKS-H ważny" | `aneks_h_valid`: headless ∧ RTF∈[0.97,1.03] ∧ timejump 0 ∧ EKF 0 ∧ world hash zgodny |
| wspólne | „trace kompletny" | `trace_complete`: wszystkie `gen_subtitles.REQUIRED_EVENTS[akt]` (jedno źródło) |
| A1 | „ENTRY w dwell 7–9 m" | `entry_in_dwell_ring`: range3d(dron,intr) ∈ ring_band(spec) przy 1. locku |
| A1 | „REFUSE(NO_AUTH) PRZED tokenem" | `no_auth_before_token`: t(refuse_no_auth) < t(grant) |
| A1 | „po tokenie OBSERVE, 0 naruszeń D_safe" | `observe_after_token_dsafe_ok`: min_d ≥ D_safe−0.5 (config_r02 5.32) |
| A2 | „EXPIRE na θ_age" | `expire_at_theta_age`: expire ∧ max age ≥ θ_age (config_r02 3.0) |
| A2 | „re-admisja pełną koniunkcją" | `readmit_full_conjunction`: przy re-ENTRY (admission_seq→1) conj box∧central∧mti_ok |
| A2 | „nowy token wymagany" | `new_token_required`: grant2 ∧ token ep0 skonsumowany |
| A3 | „REFUSE(POS_DEGRADED) ≤ 0.15 s" | `refuse_pos_within_015`: t(refuse_pos)−t(denial) ≤ 0.15 |
| A3 | „touchdown ≤ R_E" | `touchdown_within_R_E`: r_est przy touchdown ≤ R_E (r01.config 32) |

Powiązane (nie mrożone tu, referencyjnie): `sha256(gen_subtitles.py)[:16] = 4a0a84d735290d59`.

## Rehearsale online (§3) — integracja end-to-end, NIE próby (SR-F2)

Boot świata aktu (kamera filmowa), spawn intruza (MODEL, set_pose), scenariusz (token path B1),
trace v2, klatki filmowe (pipeline R2), sędzia „na sucho". Werdykty percepcji NIERAPORTOWALNE —
poniżej **werdykt integracji/sędziego** (kontrola/token/timing), nie roszczenie percepcji.

| Akt | świat (hash) | runner | ANEKS-H | sędzia (integracja) | uwaga |
|---|---|---|---|---|---|
| A1 | world_demo_A1 `d7e3db24` | gate_run_r02 SCEN=A1 GT-fed | headless, timejump 0, EKF 0 | **VALID** (5/5) | ENTRY r=8.03 m; NO_AUTH 25.3s < grant 28.4s; OBSERVE 447t, min_d 6.44, 0 naruszeń |
| A2 | world_demo_A2 `dd0c85e2` | gate_run_r02 SCEN=A2 GT-fed | headless, timejump 0, EKF 0 | **INVALID** (`trace_complete`: brak readmit/grant2) | ep0 pełne (NO_AUTH→token→OBSERVE→EXPIRE); re-admisja NIE (limit GT-fed — niżej) |
| A3 | world_demo_A3 `486a0cea` | gate_run_r03 SCEN=S2 (R0.3a) | headless, timejump 0, EKF 0 | **VALID** (4/4) | REFUSE(POS_DEGRADED) 0.102 s ≤ 0.15; touchdown r_est 14.81 m ≤ 32 |

### Kadr-check (§3, render bez GUI)
Klatka filmowa 1280×720 rgb8 uzyskana per akt (intruz w pierścieniu): A1 mean=200.2 min=22
(ciemne sylwetki dron/intruz obecne), A3 mean=210.6 min=39. Pipeline kamera→pliki działa
(21/21/16 klatek). **Frame'y `.npy` (56 MB/akt) NIE commitowane** (gitignore) — dowód renderu =
`kadr_check.log` (statystyki). Kadr geometrycznie poprawny (konwencja x=x codebase — B4 §Rozbieżność).
Ocena PIKSELOWA framingu = B5 (pierwsza próba).

**Światy NIE zmieniane po freeze B2** (SR-F4): hashe A1/A2/A3 identyczne z ANEKS_D2 — brak korekty kadru.

## Limit GT-fed (A2 re-admisja) — ZNALEZISKO

Kanał rehearsalu jest **GT-fed** (projekcja geometryczna, deterministyczna) — NIE modeluje ZASIĘGU
detekcji. Spec A2 `intruder_far_enu=[70,0,11.5]` (70 m PRZED dronem) jest geometrycznie WCIĄŻ w FOV →
projekcja zwraca box → brak EXPIRE-po-zasięgu → brak re-admisji w oknie. (A1 EXPIRE zadziałało bo
parking jest NISKO = poza FOV kamery poziomej.) **W locie LIVE (detektor z limitem zasięgu, B5) 70 m
jest niewykrywalne → EXPIRE.** Ścieżka re-admisji jest udowodniona deterministycznie:
`test_act_judge` (fixtures A2 VALID: EXPIRE+readmit+grant2) + `r01/test_token_authz` (consume_tokens,
admission_seq 0→1, nowy token). Poprawka choreografii A2 (FOV-exit) = domena B5 live albo osobna
adnotacja spec — NIE ruszam zamrożonego spec B2 w tej sesji.
